"""Audio manager for music and sound effect playback.

This component centralizes music and sound control (play/pause, volume,
previews) and stores audio preferences back to disk. It is used by UI
components to trigger short sound effects and to play ambient music for
different application states.
"""

import pygame
from settings import *
from settings import AUDIO_DATA_PATH
from Tools.data_loading_tools import save_data
from pygame import mixer
from Tools.timer import Timer
from Manifests.music_manifest import STATE_MUSIC_TRACKS


class AudioManager:
    """Manage music tracks and sound effects for the launcher."""

    def __init__(s, game):
        s.game = game

        # mapping: state name -> music track key
        s.state_music = STATE_MUSIC_TRACKS

        # music playback state
        s.current_track = None
        s.last_track = None  # caches the track to restore when music is re-enabled
        s.music_on = s.game.audio_data.get('music_on', True)
        s.music_volume = s.game.audio_data.get('music_volume', 1.0)

        # sound effects
        s.test_sound = pygame.mixer.Sound(join(BASE_DIR, 'audio', 'Sounds', 'select_sound.wav'))
        s.sound_on = s.game.audio_data.get('sound_on', True)
        s.sound_volume = s.game.audio_data.get('sound_volume', 1.0)

    def update(s, delta_time):
        """Optional per-frame update hook (unused)."""
        pass

    # Music control
    def pause_music(s):
        """Pause currently playing background music."""
        mixer.music.pause()

    def unpause_music(s):
        """Resume background music playback if music is enabled."""
        if s.music_on:
            mixer.music.unpause()

    def play_for_state(s, state_name):
        """Play the music track associated with `state_name`, if any."""
        track_name = s.state_music.get(state_name)
        if track_name:
            s.play_music(track_name)

    def play_music(s, track_name):
        """Load and play a named track (looping) unless music is disabled."""
        if not s.music_on:
            mixer.music.stop()
            s.current_track = None
            return

        if track_name != s.current_track:
            track_path = s.game.music_tracks.get(track_name)
            if track_path:
                mixer.music.load(track_path)
                mixer.music.set_volume(s.music_volume)
                mixer.music.play(-1)
                s.current_track = track_name
            else:
                mixer.music.stop()
                s.current_track = None

    def stop_music(s):
        """Stop music playback and clear the current track."""
        mixer.music.stop()
        s.current_track = None

    def set_music_volume(s, volume):
        """Set music volume and persist the preference."""
        s.music_volume = volume
        mixer.music.set_volume(volume)
        s.game.audio_data['music_volume'] = volume
        save_data(s.game.audio_data, AUDIO_DATA_PATH)

    def toggle_music(s):
        """Toggle music on/off and persist the choice.

        When enabling music again this will attempt to resume the last
        played track or play the track associated with the current state.
        """
        s.music_on = not s.music_on
        s.game.audio_data['music_on'] = s.music_on
        save_data(s.game.audio_data, AUDIO_DATA_PATH)
        if not s.music_on:
            s.last_track = s.current_track
            s.stop_music()
        else:
            if getattr(s, 'last_track', None):
                s.play_music(s.last_track)
            elif getattr(s.game, 'state_manager', None) and getattr(s.game.state_manager, 'active_state', None):
                # if we have an active state, attempt to play its music
                s.play_for_state(type(s.game.state_manager.active_state).__name__)

    # Sound effects
    def play_sound(s, sound):
        """Play a sound effect if sound effects are enabled."""
        if not s.sound_on:
            return None

        snd = sound
        if snd:
            snd.set_volume(s.sound_volume)
            return snd.play()
        else:
            print(f'[SOUND ERROR]: {snd}')
            return None

    def set_sound_volume(s, volume):
        s.sound_volume = volume
        s.game.audio_data['sound_volume'] = volume
        save_data(s.game.audio_data, AUDIO_DATA_PATH)

    def play_sound_preview(s):
        """Play a short preview sound for audio settings feedback."""
        s.play_sound(s.test_sound)

    def toggle_sound(s):
        s.sound_on = not s.sound_on
        s.game.audio_data['sound_on'] = s.sound_on
        save_data(s.game.audio_data, AUDIO_DATA_PATH)
        s.play_sound(s.game.select_sound)