"""FPS preview ball used in the video settings tab.

This simple animated ball provides a visual way to demonstrate the current
frame rate setting inside the performance options tab.
"""

import pygame

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY


class Ball:
    """Animated ball used to preview visual framerate."""

    def __init__(s, initial_pos, color):
        s.radius = 80
        s.pos_x = initial_pos[0]
        s.pos_y = initial_pos[1]
        s.speed = 1600

        s.image = pygame.Surface((s.radius*2, s.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s.image, color, (s.radius, s.radius), s.radius)

        s.rect = s.image.get_rect(center=(s.pos_x, s.pos_y))

    def draw(s, window):
        window.blit(s.image, s.rect)

    def update(s, delta_time):
        s.rect.centery += s.speed * delta_time
        if s.rect.top >= WINDOW_HEIGHT+s.speed/5:
            s.rect.centery = -s.radius - s.speed/5

