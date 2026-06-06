"""Background asset loader for audio, graphics, and other launcher assets.

These functions are intended to run in a worker thread during startup so
that the UI becomes responsive while asset loading completes.
"""

import pygame
from pygame import mixer
from pytmx.util_pygame import load_pygame
from os.path import join

from Tools.asset_importing_tool import *
from Tools.asset_scaling_tool import *
from settings import BASE_DIR


def load_audio(game):
    """Load launcher music and sound effect assets into the game context."""

    # Initialize the mixer before loading sounds
    mixer.init()

    game.music_tracks = {
        'Menu music' : join(BASE_DIR, 'audio', 'Music', 'menu_music.ogg'),
        'Options music' : join(BASE_DIR, 'audio', 'Music', 'options_music.ogg'),
    }

    game.select_sound = pygame.mixer.Sound(join(BASE_DIR, 'audio', 'Sounds', 'select_sound.wav'))
    game.switch_sound = pygame.mixer.Sound(join(BASE_DIR, 'audio', 'Sounds', 'switch_sound.wav'))


def load_maps(game):
    """Placeholder for loading tile maps or game level layouts."""
    pass

#LOADING LEVEL ASSETS
def load_assets(game):
    """Load and scale shared sprite assets used by the launcher UI."""
    game.button_images = import_folder_dict(join(BASE_DIR, 'assets', 'button_assets'))
    game.button_images = scale_asset(game.button_images, 10)

#LOADING GAME FONTS
def load_fonts(game):
    pass