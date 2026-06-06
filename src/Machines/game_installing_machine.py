"""Game installation and update management for repository-based games.

`GameInstaller` handles cloning, updating, deleting, and queuing game
repositories. It is designed to support both Windows and Unix-like
platforms, including a portable Git fallback for Windows.
"""

from pathlib import Path
import subprocess
import shutil
import json
import os
import stat
from typing import Optional
import threading
import platform


class GameInstaller:
    """Install, update, and remove game packages from the launcher."""

    def __init__(self, games_dir: str):
        """Initialize the installer and ensure the game directory exists."""

        self.games_dir = Path(games_dir)
        self.games_dir.mkdir(parents=True, exist_ok=True)

        #INSTALLATION STATES
        self.is_downloading = False
        self.current_game_id = None
        self.download_progress = 0
        self.download_queue = []
        self.current_process = None

    def remove_readonly(self, func, path, excinfo):
        """Callback for `shutil.rmtree` that clears read-only file attributes."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def _get_git_executable(self) -> str:
        """Find an available Git executable on the host machine."""

        is_windows = platform.system() == "Windows"

        #IF WINDOWS, FIRST CHECK PORTABLE GIT, THEN COMMON INSTALLATION PATHS
        if is_windows:
            root_dir = Path(__file__).resolve().parent.parent.parent
            portable_git_path = root_dir / "PortableGit" / "cmd" / "git.exe"
            
            if portable_git_path.exists():
                return str(portable_git_path)

            possible_paths = [
                r"C:\Program Files\Git\bin\git.exe",
                r"C:\Program Files\Git\cmd\git.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path

        #UNIX-LIKE SYSTEMS OR FALLBACK FOR WINDOWS - CHECKING PATH ENVIRONMENT VARIABLE
        git_path = shutil.which("git")
        if git_path:
            return git_path
        
        #IF GIT IS NOT FOUND, RETURNING "git" TO ALLOW SYSTEM TO HANDLE THE ERROR (USER WILL GET A CLEAR MESSAGE ABOUT MISSING GIT)
        return "git"

    def is_installed(self, game_id: str) -> bool:
        """Return True when the requested game exists in the games directory."""
        return (self.games_dir / game_id).exists()

    def get_local_version(self, game_id: str) -> Optional[str]:
        """Read the locally installed game version from version.json."""
        path = self.games_dir / game_id / "version.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("version")
        except Exception as e:
            print(f"[Installer] Failed to read version.json ({game_id}): {e}")
            return None

    def write_local_version(self, game_id: str, version: str) -> None:
        """Persist the installed game version to version.json."""
        path = self.games_dir / game_id / "version.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"version": version}, f, indent=2)
        except Exception as e:
            print(f"[Installer] Failed to write version.json ({game_id}): {e}")

    def has_update(self, game_id: str, manifest_version: str) -> bool:
        """Return True when a local game version differs from the manifest version."""
        local = self.get_local_version(game_id)
        if local is None:
            return False
        return local != manifest_version

    def install(self, game_id, repo_url, manifest_version, branch="main") -> bool:
        """Clone a game repository and write the installed version on success."""
        target = self.games_dir / game_id
        self.current_game_id = game_id
        self.download_progress = 0
        
        git_cmd = self._get_git_executable()

        try:
            #USING SUBPROCESS TO CLONE THE REPOSITORY, WITH PROGRESS OUTPUT
            process = subprocess.Popen(
                [git_cmd, "clone", "--progress", "--depth", "1", "-b", branch, repo_url, str(target)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.current_process = process

            #READING THE OUTPUT LINE BY LINE TO EXTRACT PROGRESS INFORMATION
            for line in process.stdout:

                #PRINTING THE RAW OUTPUT FOR DEBUGGING PURPOSES
                if "%" in line:
                    parts = line.split("%")[0].split()
                    if parts:
                        try:
                            #TRYING TO EXTRACT THE PROGRESS VALUE FROM THE OUTPUT
                            val = int(parts[-1])
                            self.download_progress = val
                        except ValueError:
                            pass

            process.wait()

            if process.returncode == 0:
                self.write_local_version(game_id, manifest_version)
                return True
            else:
                if target.exists(): shutil.rmtree(target, onerror=self.remove_readonly)
                return False

        finally:
            self.current_game_id = None
            self.download_progress = 0
            self.current_process = None

    def update(
        self,
        game_id: str,
        manifest_version: str,
        branch: str = "main"
    ) -> bool:
        """Fetch and reset the installed repository to match the remote branch."""
        target = self.games_dir / game_id

        if not self.is_installed(game_id):
            print(f"[Installer] {game_id} is not installed.")
            return False
        
        #SETTING THE CURRENT GAME ID TO BLOCK OTHER INSTALLATIONS/UPDATES WHILE THIS ONE IS IN PROGRESS.
        self.current_game_id = game_id
        
        git_cmd = self._get_git_executable()

        try:
            print(f"[Installer] Updating {game_id}...")

            #FETCHING THE LATEST CHANGES FROM THE REMOTE REPOSITORY
            subprocess.run(
                [git_cmd, "fetch", "origin", branch],
                cwd=target,
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                [git_cmd, "reset", "--hard", f"origin/{branch}"],
                cwd=target,
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                [git_cmd, "clean", "-fd"],
                cwd=target,
                check=True,
                capture_output=True,
                text=True
            )

            #SYNCHRONIZING THE LOCAL VERSION WITH THE MANIFEST VERSION AFTER A SUCCESSFUL UPDATE
            self.write_local_version(game_id, manifest_version)

            print(f"[Installer] {game_id} updated successfully.")
            return True

        except subprocess.CalledProcessError as e:
            #EXTRACTING THE ERROR MESSAGE FROM THE SUBPROCESS EXCEPTION TO PROVIDE MORE DETAILED FEEDBACK TO THE USER
            error_msg = e.stderr if e.stderr else str(e)
            print(f"[Installer] UPDATE error for {game_id}: {error_msg}")
            return False
        
        except Exception as e:
            print(f"[Installer] Unexpected error while updating: {e}")
            return False

        finally:
            #RESETTING THE CURRENT GAME ID AND PROGRESS TO ALLOW OTHER INSTALLATIONS/UPDATES TO PROCEED
            self.current_game_id = None
            self.process_queue()

    def process_queue(self):
        """Start the next queued download if no installation is currently active."""
        if self.download_queue and not self.is_downloading:
            game_id, repo, version = self.download_queue.pop(0)
            self._start_download(game_id, repo, version)

    def _start_download(self, game_id, repo, version):
        """Begin a background thread to download a queued game."""
        self.is_downloading = True
        self.current_game_id = game_id
        self.download_progress = 0
        threading.Thread(target=self._download_game, args=(game_id, repo, version), daemon=True).start()

    def _download_game(self, game_id, repo, version):
        """Internal worker method that runs the install and continues the queue."""
        try:
            self.install(game_id, repo, version)
        finally:
            self.is_downloading = False
            self.current_game_id = None
            self.process_queue()

    def cancel_download(self):
        """Cancel any pending download queue and terminate the current process."""
        self.download_queue = []
        self.is_downloading = False
        self.current_game_id = None
        if self.current_process:
            self.current_process.terminate()
            self.current_process = None

    # ==================================================
    # REMOVE
    # ==================================================
    def remove(self, game_id: str) -> bool:
        """Delete an installed game folder from disk."""
        target = self.games_dir / game_id
        if not self.is_installed(game_id):
            return False
        try:
            shutil.rmtree(target, onerror=self.remove_readonly)
            print(f"[Installer] {game_id} removed successfully.")
            return True
        except Exception as e:
            print(f"[Installer] Error removing {game_id}: {e}")
            return False