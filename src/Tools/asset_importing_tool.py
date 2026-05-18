#IMPORTING LIBRARIES
import pygame
from os import walk
from os.path import join

#FUNCTION FOR IMPORTING AN IMAGE
def import_image(*path, alpha = True, format = '.png'):
    full_path = join(*path) + f'{format}'
    return pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()

#FUNCTION FOR IMPORTING A FOLDER OF IMAGES
def import_folder(*path):
	frames = []
	for folder_path, sub_folders, image_names in walk(join(*path)):
		for image_name in sorted(image_names, key = lambda name: int(name.split('.')[0])):
			full_path = join(folder_path, image_name)
			surf = pygame.image.load(full_path).convert_alpha()
			frames.append(surf)
	return frames

def import_folder_dict(*path):
	frames = {}
	for folder_path, sub_folders, image_names in walk(join(*path)):
		for image_name in image_names:
			full_path = join(folder_path, image_name)
			surf = pygame.image.load(full_path).convert_alpha()
			frames[image_name.split('.')[0]] = surf
	return frames