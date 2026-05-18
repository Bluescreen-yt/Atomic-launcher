#IMPORTING LIBRARIES
from pygame import mixer
from pytmx.util_pygame import load_pygame

#IMPORTING FILES
from Tools.asset_importing_tool import *
from Tools.asset_scaling_tool import *
from settings import BASE_DIR


#LOADING IN AUDIO FILES
def load_audio(game):

    #INITIALIZING MIXER
    mixer.init()

    game.music_tracks = {
        'Menu music' : join(BASE_DIR, 'audio', 'Music', 'menu_music.ogg'),
        'Options music' : join(BASE_DIR, 'audio', 'Music', 'options_music.ogg'),
    }

    game.select_sound = pygame.mixer.Sound(join(BASE_DIR, 'audio', 'Sounds', 'select_sound.wav'))
    game.switch_sound = pygame.mixer.Sound(join(BASE_DIR, 'audio', 'Sounds', 'switch_sound.wav'))


#LOADING GAME MAPS
def load_maps(game):
    pass

#LOADING LEVEL ASSETS
def load_assets(game):
    
    game.button_images = import_folder_dict(join(BASE_DIR, 'assets', 'button_assets'))
    game.button_images = scale_asset(game.button_images, 10)

#LOADING GAME FONTS
def load_fonts(game):
    pass