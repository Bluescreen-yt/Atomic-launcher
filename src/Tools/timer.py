"""Simple timer utility used for delayed or repeating callbacks.

The Timer wraps Pygame's millisecond clock to provide an easy-to-use
countdown mechanism for UI effects and time-based events.
"""

import pygame


class Timer:
    """A lightweight countdown timer that triggers an optional callback.

    Parameters
    - duration: milliseconds until the timer fires
    - autostart: if True, timer begins immediately after construction
    - function: optional callable to invoke when the timer completes
    - repeat: if True, the timer restarts automatically after firing
    """

    def __init__(s, duration, autostart=False, function=None, repeat=False):
        s.duration = duration
        s.function = function
        s.start_time = 0
        s.active = False
        s.repeat = repeat
        s.autostart = autostart

        if s.autostart:
            s.activate()

    def activate(s):
        """Start or restart the timer."""
        s.active = True
        s.start_time = pygame.time.get_ticks()

    def deactivate(s):
        """Stop the timer. If `repeat` is set, the timer restarts."""
        s.active = False
        s.start_time = 0

        if s.repeat:
            s.activate()

    def update(s):
        """Call periodically (e.g. each frame). Executes `function` when due."""
        if not s.active:
            return

        current_time = pygame.time.get_ticks()

        if current_time - s.start_time >= s.duration:
            if s.function and s.start_time != 0:
                s.function()
            s.deactivate()