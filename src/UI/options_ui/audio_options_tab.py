"""Audio options tab: volume controls and audio toggles.

This tab exposes music and sound sliders and allows the user to toggle
background music and sound effects on or off. It also performs a preview
sound effect after the user changes the sound volume, throttled by a
cooldown timer.

Developer notes
+- `handling_events` supports both keyboard navigation and raw UI element
+  mouse events. If you add new UI elements, ensure they implement
+  `handling_events(events, ctrl)` or fallback gracefully.
+- Audio state is written through `launcher.audio_manager` and should stay
+  consistent with `launcher.audio_data`.
"""

import pygame

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.options_ui.generic_options_tab import GenericOptionsTab
from UI.ui_elements.slider import Slider
from UI.ui_elements.buttons import GenericToggleButton

class AudioOptionsTab(GenericOptionsTab):
    """Options tab for audio volume and toggle settings.

    This tab controls music and sound settings through `AudioManager` and
    schedules preview audio playback whenever the sound volume changes.
    """

    def __init__(s, launcher):
        super().__init__(launcher)
        
        # Pull the current theme just like in VideoOptionsTab
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        
        s.ui_elements = []
        s.selected_index = 0  # Used for tracking keyboard navigation focus
        
        # Cooldown properties for the volume preview sound
        s.preview_cooldown_timer = 0.0
        s.preview_cooldown_duration = 0.3  # Interval in seconds between preview sounds
        s.sound_changed_flag = False        # Tracks if the volume was adjusted
        
        s.setup()

    def setup(s):
        slider_size = (800, 40)
        
        music_slider = Slider(
            s.launcher,
            pos=(WINDOW_WIDTH/2 - slider_size[0]/2, WINDOW_HEIGHT/3),
            size=slider_size,
            min_val=0,
            max_val=1,
            start_val=s.launcher.audio_data.get("music_volume", 1.0),
            on_change=lambda v: s.launcher.audio_manager.set_music_volume(v)
        )

        # Redirected on_change to our custom tracker method
        sound_slider = Slider(
            s.launcher,
            pos=(WINDOW_WIDTH/2 - slider_size[0]/2, WINDOW_HEIGHT/3*2),
            size=slider_size,
            min_val=0,
            max_val=1,
            start_val=s.launcher.audio_data.get("sound_volume", 1.0),
            on_change=s.handle_sound_volume_change
        )

        music_toggle = GenericToggleButton(
            s.launcher,
            size=(220, 50),
            pos=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3 + slider_size[1] + 50),
            text="Music",
            action=s.launcher.audio_manager.toggle_music
        )

        sound_toggle = GenericToggleButton(
            s.launcher,
            size=(220, 50),
            pos=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3*2 + slider_size[1] + 50),
            text="Sound",
            action=s.launcher.audio_manager.toggle_sound
        )

        s.ui_elements.extend([
            music_slider,
            music_toggle,
            sound_slider,
            sound_toggle
        ])

    def handle_sound_volume_change(s, v):
        """Update the sound volume and mark the change for a preview sound."""
        s.launcher.audio_manager.set_sound_volume(v)
        s.sound_changed_flag = True

    def handling_events(s, events, ctrl):
        """Handle keyboard and UI element events inside the audio tab."""
        if s.launcher.state_manager.ui_focus != 'content':
            return

        # 1. Capture the single KEYDOWN event from the queue
        current_key = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key
                break 

        if current_key is None:
            # Still process mouse events for elements if needed
            for element in s.ui_elements:
                if hasattr(element, 'handling_events'):
                    try:
                        element.handling_events(events, ctrl)
                    except TypeError:
                        element.handling_events(events)
            return

        # 2. Map current_key to logical navigation actions
        is_up = current_key == ctrl['up']
        is_down = current_key == ctrl['down']
        is_left = current_key == ctrl['left']
        is_right = current_key == ctrl['right']
        is_confirm = current_key in [ctrl['action_a'], pygame.K_RETURN]

        # --- VERTICAL NAVIGATION ---
        if is_up:
            s.selected_index = (s.selected_index - 1) % len(s.ui_elements)
        elif is_down:
            s.selected_index = (s.selected_index + 1) % len(s.ui_elements)

        # Update the s.is_selected flags so elements know who has focus
        for i, element in enumerate(s.ui_elements):
            if hasattr(element, 'is_selected'):
                element.is_selected = (i == s.selected_index)

        # 3. --- DISPATCH INTERACTION TO ACTIVE ELEMENT ---
        active_element = s.ui_elements[s.selected_index]

        # Case A: Active element is a Slider
        if active_element.__class__.__name__ == "Slider":
            if is_left:
                active_element.change_value(-active_element.step)
            elif is_right:
                active_element.change_value(active_element.step)

        # Case B: Active element is a Button / Toggle Button
        elif is_confirm:
            if hasattr(active_element, 'activate'):
                active_element.activate()
            elif hasattr(active_element, 'action') and active_element.action:
                active_element.action()

        # Pass remaining raw events (like mouse events) safely down to the element
        if hasattr(active_element, 'handling_events'):
            try:
                active_element.handling_events(events, ctrl)
            except TypeError:
                active_element.handling_events(events)

    def update(s, delta_time):
        """Update internal timers and UI elements each frame."""
        # Update logic for sliders/buttons
        for element in s.ui_elements:
            if hasattr(element, 'update'):
                element.update(delta_time)

        # --- PREVIEW COOLDOWN TIMER ---
        if s.preview_cooldown_timer > 0:
            s.preview_cooldown_timer -= delta_time

        # If a sound volume change occurred and our cooldown is ready, play sound
        if s.sound_changed_flag and s.preview_cooldown_timer <= 0:
            # Calls your audio manager to trigger a quick test blip/noise
            if hasattr(s.launcher.audio_manager, 'play_sound_preview'):
                s.launcher.audio_manager.play_sound_preview()
            elif hasattr(s.launcher.audio_manager, 'play_preview_sound'):
                s.launcher.audio_manager.play_preview_sound()

            s.sound_changed_flag = False
            s.preview_cooldown_timer = s.preview_cooldown_duration

    def draw(s, window):
        """Draw the audio controls and highlight the focused element."""
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        
        for i, element in enumerate(s.ui_elements):
            is_selected = (i == s.selected_index)
            
            if hasattr(element, 'draw'):
                try:
                    element.draw(window, is_focused=(is_selected and has_focus))
                except TypeError:
                    element.draw(window)