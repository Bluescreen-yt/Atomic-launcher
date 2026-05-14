#IMPORTING LIBRARIES
import pygame
from gpiozero import Button

#RASPBERRY PI GPIO CONTROLLER CLASS
class RaspberryPiGPIOController:

    #CONSTRUCTOR
    def __init__(s, gpio_controlls_data, keyboard_mapping):

        #SETTING UP THE BUTTONS
        s.buttons = {}
        for action, pin in gpio_controlls_data.items():
            if pin is not None:
                try:
                    btn = Button(pin, pull_up=True, bounce_time=0.05)
                    key = keyboard_mapping.get(action)
                    if key is not None:
                        btn.when_pressed = lambda k=key: s.post_key_event(k)
                    s.buttons[action] = btn
                except Exception as e:
                    print(f"Failed to initialize GPIO button for {action} on pin {pin}: {e}")
                    s.buttons[action] = None

    #POSTING THE KEY EVENT
    def post_key_event(s, key):
        if key:
            new_event = pygame.event.Event(pygame.KEYDOWN, {'key': key, 'mod': pygame.KMOD_NONE})
            pygame.event.post(new_event)

    #CHECKING IF A BUTTON IS PRESSED (FOR POLLING IF NEEDED)
    def is_pressed(s, action):
        if action in s.buttons and s.buttons[action] is not None:
            return s.buttons[action].is_pressed
        return False