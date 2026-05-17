#IMPORTING LIBRARIES
import pygame

#A MANAGER FOR MOVING TO DIFFERENT PARTS OF THE OS
class StateManager:
    def __init__(s, launcher):
        s.launcher = launcher
        s.states = {}
        s.active_state = None
        s.ui_focus = 'content'

    def add_state(s, name, state_object):
        s.states[name] = state_object

    def set_state(s, name):
        if name in s.states:
            s.active_state = s.states[name]
            print(f"State changed to: {name}")

            if hasattr(s.active_state, 'on_enter'):
                s.active_state.on_enter()

            s.launcher.audio_manager.play_for_state(name)

    def handling_events(s, events):
        # Retrieve the key map from settings
        options_key = s.launcher.controlls_data['keyboard']['options']

        for event in events:
            if event.type == pygame.KEYDOWN:
                # Check if the 'Options' button (e.g., TAB or GPIO 24) was pressed
                if event.key == options_key:
                    s.ui_focus = "sidebar" if s.ui_focus != "sidebar" else "content"

        # Pass input to the appropriate component
        if s.ui_focus == "sidebar":
            # Note: You should update sidebar.handle_input to accept 'events' 
            # instead of 'keys' to keep everything consistent!
            s.launcher.sidebar.handle_input(events)
        else:
            if s.active_state:
                s.active_state.handling_events(events)

    def update(s, delta_time):
        s.launcher.sidebar.update(delta_time)

        if s.active_state:
            s.active_state.update(delta_time)

    def draw(s, window):

        if s.active_state:
            s.active_state.draw(window)

        s.launcher.sidebar.draw(window)
