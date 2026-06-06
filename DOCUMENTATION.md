# Atomic Launcher - Developer Documentation

**Version:** 1.0 (Alpha Stage)

**Repository:** [mironczuk-dar/Atomic-launcher](https://github.com/mironczuk-dar/Atomic-launcher.git)

> **Note to Contributors:** Atomic Launcher is currently in Alpha. We are actively seeking pull requests, bug reports, and feature suggestions!

---

## Table of Contents

1. [Introduction](https://www.google.com/search?q=%231-introduction)
2. [Getting Started (Setup Guide)](https://www.google.com/search?q=%232-getting-started-setup-guide)
3. [Project Architecture Overview](https://www.google.com/search?q=%233-project-architecture-overview)
4. [Under the Hood: How it Works](https://www.google.com/search?q=%234-under-the-hood-how-it-works)
5. [Adding a New Game](https://www.google.com/search?q=%235-adding-a-new-game-to-the-launcher)
6. [Contribution Guidelines](https://www.google.com/search?q=%236-contribution-guidelines)

---

## 1. Introduction

Welcome to the official developer documentation for **Atomic Launcher**!

Atomic Launcher is an award-winning, open-source application specifically designed to manage and execute Pygame-based games. By providing an integrated ecosystem, the launcher allows players to easily browse their library, manage save files, and boot up Pygame titles (such as *Monster Masters*) from a single, unified interface.

This document is designed to help new developers understand the core architecture of the launcher, how individual elements interact, and how to start contributing or modding the application.

---

## 2. Getting Started (Setup Guide)

To run the Atomic Launcher locally and begin development, you will need a basic Python environment.

### Prerequisites

* **Python:** Version 3.8 or higher.
* **Pygame:** The core rendering and input engine.
* **Git:** For version control.

### Installation Steps

1. **Clone the repository:**
```bash
git clone https://github.com/mironczuk-dar/Atomic-launcher.git
cd Atomic-launcher
```


2. **Create and activate a virtual environment (Recommended):**
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate 

# On Windows:
venv\Scripts\activate
```


3. **Install dependencies:**
```bash
pip install -r requirements.txt
```


> *If a `requirements.txt` is not yet present in the branch, simply run `pip install pygame`.*


4. **Run the Launcher:**
```bash
python main.py
```

---

## 3. Project Architecture Overview

Atomic Launcher prioritizes **Clean Code** principles. The repository is heavily modularized, meaning that different responsibilities of the launcher are separated into distinct, intuitive directories.

### Directory Structure

```text
Atomic-launcher/
├── assets/             # Global launcher images, fonts, and icons
├── games/              # Installed Pygame projects (e.g., Monster Masters)
├── menus/              # State machine logic for different screens
├── save_wizard/        # Data serialization and save file management
├── ui_elements/        # Reusable OOP visual components
└── main.py             # Application entry point
```

### Component Breakdown

| Module / Directory | Core Responsibility | Key Characteristics |
| --- | --- | --- |
| `main.py` | Entry point | Contains the primary Pygame event loop and screen rendering logic. |
| `/ui_elements/` | Visual Building Blocks | Object-oriented base classes for Buttons, Text boxes, Sliders, etc. |
| `/menus/` | UI State Logic | Handles the Main Menu, Game Library, and Settings logic. |
| `/save_wizard/` | Data Management | Reads, writes, and parses game save data (JSON, DAT, PKL) and configs. |
| `/games/` | Game Storage | The sandbox where individual Pygame projects are stored and executed. |

---

## 4. Under the Hood: How it Works

Understanding how the launcher operates is crucial for adding new features without breaking existing functionality.

### A. UI Elements

Instead of drawing shapes directly onto the screen in the main loop, Atomic Launcher uses object-oriented UI components.

* **Interaction:** A `Button` class takes parameters like `x`, `y`, `width`, `height`, `text`, and a `callback_function`. It handles its own hover and click detection, triggering the callback when activated.
* **Modding:** To change the global look of the launcher, modify the base classes inside `/ui_elements/`. All menus inheriting these classes will automatically update their appearance.

### B. The Menu System (State Machine)

The launcher operates using a **State Machine** pattern. Only one menu (or "state") is active at any given time.

* The `main.py` loop calls the `update()` and `draw()` methods of the *current active state*.
* Clicking "Library" triggers a function that changes the active state from `MainMenu` to `GameLibrary`. This ensures the codebase remains clean and avoids tangled `if/else` statements.

### C. The Save Wizard

Acts as the bridge between the launcher and the games it hosts.

* **Functionality:** Scans local directories for `.json`, `.dat`, or `.pkl` files belonging to specific games.
* **Safety:** Ensures game data is backed up or properly loaded before launch.
* **Extensibility:** If you are adding a new data type or a cloud-sync feature, this module (utilizing Python's native file I/O and `json` libraries) is where you'll work.

### D. Game Execution Pipeline

When a user hits "Play" on a game:

1. The launcher pauses its own main Pygame loop.
2. It dynamically imports or executes the target game's main Python script.
3. It securely hands over display control to the game's Pygame instance.
4. Upon game exit, control returns to the launcher, and the Save Wizard syncs playtime and save data.

---

## 5. Adding a New Game to the Launcher

Integrating a new Pygame project into Atomic Launcher is fully automated via metadata.

1. **Move the Game Files:** Place the new game's directory inside the launcher's `/games/` folder.
2. **Create a Metadata File:** Create a `config.json` inside the game's root folder. It should look like this:
```json
{
    "title": "My Awesome Game",
    "developer": "Your Name",
    "executable": "main.py",
    "thumbnail": "assets/banner.png",
    "version": "1.0.0"
}
```


3. **Restart the Launcher:** The `/menus/` and `/save_wizard/` modules will automatically parse this new folder, generate UI elements in the Game Library, and make the game playable.

---

## 6. Contribution Guidelines

Atomic Launcher is an open-source project that welcomes contributions from developers of all skill levels!

### How to Contribute

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally.
3. **Create a feature branch:** 
```bash
git checkout -b feature/NewAwesomeMenu
```


4. **Write clean, commented code.** If adding a new UI element, ensure it matches the styling conventions in `/ui_elements/`.
5. **Commit and Push:**
```bash
git commit -m "Added a new dropdown UI element"
git push origin feature/NewAwesomeMenu
```


6. **Open a Pull Request (PR)** on the main repository describing your changes and the problems they solve.

### Current Alpha Roadmap (Looking for help!)

* 🚀 **Asset Loading:** Improving the dynamic loading and caching of game assets.
* ☁️ **Cloud Saves:** Enhancing the Save Wizard to support remote/cloud backups.
* ✨ **UI Polish:** Adding smooth animations for UI element transitions.

*Thank you for helping make Atomic Launcher the best home for Pygame creations!*