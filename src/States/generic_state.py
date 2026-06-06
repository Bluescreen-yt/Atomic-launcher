"""Base state class for application screens.

All concrete states should inherit from `BaseState` and implement the
`handling_events`, `update` and `draw` methods. Global navigation and
sidebar focus is managed by `StateManager`, so state implementations can
focus on content-specific behaviour.
"""

import pygame


class BaseState:
    def __init__(self, launcher):
        self.launcher = launcher
        self.system = launcher.system

    def handling_events(self, events):
        """Handle input events specific to this state.

        Note: global keys (e.g. toggle sidebar) are handled by the
        `StateManager`, so state handlers receive only content-relevant events.
        """
        pass

    def update(self, delta_time):
        """Update state logic. Sidebar and focus management are outside this method."""
        pass

    def draw(self, window):
        """Render the state's content into the provided surface."""
        pass

    def on_enter(self):
        """Optional lifecycle hook called when this state becomes active."""
        pass
