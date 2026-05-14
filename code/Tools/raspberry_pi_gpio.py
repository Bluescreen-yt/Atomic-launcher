#IMPORTING LIBRARIES
import pygame
import queue
from gpiozero import Button

#RASPBERRY PI GPIO CONTROLLER CLASS
class RaspberryPiGPIOController:

    #CONSTRUCTOR
    def __init__(s, gpio_controlls_data, keyboard_mapping):

        #SETTING UP THE BUTTONS
        s.buttons = {}
        s.pending_keys = queue.Queue()
        s.prev_states = {}

        for action, pin in gpio_controlls_data.items():
            if pin is not None:
                try:
                    btn = Button(pin, pull_up=True, bounce_time=0.05)
                    key = keyboard_mapping.get(action)
                    if key is not None:
                        btn.when_pressed = lambda k=key: s.pending_keys.put(k)
                    s.buttons[action] = btn
                    s.prev_states[action] = False
                except Exception as e:
                    print(f"Failed to initialize GPIO button for {action} on pin {pin}: {e}")
                    s.buttons[action] = None

    #GET PENDING KEYS FROM THE GPIO CALLBACK QUEUE
    def get_pending_keys(s):
        keys = []
        while True:
            try:
                keys.append(s.pending_keys.get_nowait())
            except queue.Empty:
                break
        return keys

    #CHECKING IF A BUTTON IS PRESSED (FOR POLLING IF NEEDED)
    def is_pressed(s, action):
        if action in s.buttons and s.buttons[action] is not None:
            return s.buttons[action].is_pressed
        return False