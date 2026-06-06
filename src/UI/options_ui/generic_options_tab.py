"""Generic base class for options tabs.

Each options tab should inherit from `GenericOptionsTab` and implement the
`update`, `draw`, and `handling_events` methods. This base class holds the
common `launcher` reference so tabs can access shared data and services.
"""

class GenericOptionsTab:

    def __init__(s, launcher):
        s.launcher = launcher

    def update(s, delta_time):
        """Update tab-specific animations, timers, or transient UI state."""
        pass

    def draw(s, window):
        """Render the tab content into the provided surface."""
        pass
