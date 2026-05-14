#IMPORTING LIBRARIES
import pygame
from sys import exit
from os import environ
import platform
import socket

try:
    from gpiozero import Button
except ImportError:
    Button = None

#IMPORTING FILES
from settings import *
from Tools.data_loading_tools import load_data, save_data

#IMPROTING STATES AND STATE MANAGERS
from Tools.game_installer import GameInstaller
from States.state_manager import StateManager
from UI.sidebar import Sidebar
from States.library import Library
from States.store import Store
from States.options import Options
from Store.game_preview import GamePreview


#LAUNCHER CLASS
class Launcher:

    #INFORMATION ABOUT THE LAUNCHER
    def __str__(s):
        return'''
        A launcher for Pygame applications.
        '''
    
    #CONSTRUCTOR
    def __init__(s):

        #CHECKING THE SYSTEM THE DEVICE IS RUNNING ON
        s.system = s.checking_operating_system()

        #CHECKING INTERNET ACCESS
        s.online_mode = s.checking_internet_connection()

        #INITALIZING PYGAME
        pygame.init()

        #LOADING IN LAUNCHER DATA
        s.loading_in_launcher_data()

        #INITIALIZING GPIO BUTTONS
        if s.is_pi:
            if Button is not None:
                s.init_gpio_buttons()
            else:
                print('GPIO initialization skipped: gpiozero library not installed.')

        #INITIALIZING CONTROLLER SUPPORT
        s.init_controller()

        #SETTING UP THE DISPLAY
        s.setting_up_display()

        #INITALIZING DISPLAY
        s.display = pygame.display.set_mode((s.window_data['width'], s.window_data['height']), s.flags)
        s.window = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('[ATOMIC LAUNCHER]')

        #INITALIZING CLOCK
        s.clock = pygame.time.Clock()
        s.fps = s.window_data['fps']

        #CREATING THE GAME INSTALLER
        s.installer = GameInstaller(GAMES_DIR)

        #CREATING STATE MANAGER AND STATES
        s.state_manager = StateManager(s)
        s.creating_states()
        s.sidebar = Sidebar(s)

        #GAME PROCESS
        s.game_process = None
        s.game_running = False

    #METHOD FOR CHECKING OPERATING SYSTEM
    def checking_operating_system(s):
        s.os_type = platform.system()
        try:
            with open('/proc/device-tree/model', 'r') as f:
                s.is_pi = 'Raspberry Pi' in f.read()
        except FileNotFoundError:
            s.is_pi = False

        return 'Raspberry Pi Os' if s.is_pi else s.os_type
    
    #METHOD FOR CHECKING INTERNET CONNECTION
    def checking_internet_connection(s, timeout = 2):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except OSError:
            return False

    #METHOD FOR LOADING IN LAUNCHER DATA
    def loading_in_launcher_data(s):
        s.window_data = load_data(WINDOW_DATA_PATH, DEFUALT_WINDOW_DATA)
        s.audio_data = load_data(AUDIO_DATA_PATH, DEFAULT_AUDIO_DATA)
        s.theme_data = load_data(THEMES_DATA_PATH, DEFAULT_THEME_DATA)
        s.performance_settings_data = load_data(PERFORMANCE_SETTINGS_DATA_PATH, DEFAULT_PERFORMANCE_SETTINGS_DATA)
        s.controlls_data = load_data(CONTROLLS_DATA_PATH, DEFAULT_CONTROLLS_DATA)
        s.game_library_data = load_data(GAME_LIBRARY_DATA_PATH, DEFAULT_GAME_LIBRARY_DATA)
        s.gpio_controlls_data = load_data(GPIO_CONTROLLS_DATA_PATH, DEFAULT_GPIO_CONTROLLS_DATA)

    #METHOD FOR CREATING STATE AND OS ELEMENTS (LIBRARY, STORE, SETTINGS, ...)
    def creating_states(s):
        s.state_manager.add_state('Library', Library(s))
        s.state_manager.add_state('Store', Store(s))
        s.state_manager.add_state('Options', Options(s))
        s.state_manager.add_state('Game preview', GamePreview(s))

        #SETTING CURRENT STATE
        s.state_manager.set_state('Library')

    #METHOD FOR SCALING MOUSE POSITTION
    def get_scaled_mouse_pos(s):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        scaled_x = mouse_x * (s.screen.get_width() / s.display.get_width())
        scaled_y = mouse_y * (s.screen.get_height() / s.display.get_height())

        return int(scaled_x), int(scaled_y)
    
    #METHOD FOR SETTING UP THE DISPLAY
    def setting_up_display(s):
        s.fullscreen = s.window_data['fullscreen']
        s.last_window_size = (s.window_data['width'], s.window_data['height'])

        if s.fullscreen:
            s.flags = pygame.FULLSCREEN
        else:
            s.flags = pygame.RESIZABLE

    #INITIALIZING PHYSICAL BUTTONS
    def init_gpio_buttons(s):
        s.physical_buttons = {}
        
        #MAPPING GPIO LABELS TO THEIR CORRESPONDING KEYBOARD KEYS
        key_mapping = {
            'up': s.controlls_data['keyboard']['up'],
            'down': s.controlls_data['keyboard']['down'],
            'left': s.controlls_data['keyboard']['left'],
            'right': s.controlls_data['keyboard']['right'],
            'options': s.controlls_data['keyboard']['options'],
            'action_a': s.controlls_data['keyboard']['action_a'],
            'action_b': s.controlls_data['keyboard']['action_b'],
            'action_x': s.controlls_data['keyboard']['action_x'],
            'action_y': s.controlls_data['keyboard']['action_y']
        }

        try:
            for action, pin in s.gpio_controlls_data.items():
                if pin is not None:
                    btn = Button(pin, pull_up=True, bounce_time=0.05)
                    
                    # Using a lambda to pass the specific key to the handler
                    target_key = key_mapping.get(action)
                    btn.when_pressed = lambda k=target_key: s.post_gpio_event(k)
                    
                    s.physical_buttons[action] = btn
            print("GPIO Buttons initialized successfully.")
        except Exception as e:
            print(f"GPIO initialization skipped: {e}")

    #INITIALIZING CONTROLLER SUPPORT
    def init_controller(s, device_index=0):
        s.prev_button_states = {}
        s.prev_hat_state = (0, 0)
        s.prev_axis_state = {'x': 0, 'y': 0}
        s.controller_button_action_map = {
            0: 'action_a',
            1: 'action_b',
            2: 'action_x',
            3: 'action_y',
            6: 'action_b',
            7: 'options'
        }
        s.controller_hat_action_map = {
            (0, 1): 'up',
            (0, -1): 'down',
            (-1, 0): 'left',
            (1, 0): 'right'
        }

        try:
            pygame.joystick.init()
            pygame.event.pump()
            count = pygame.joystick.get_count()
            if count > 0 and device_index < count:
                s.controller = pygame.joystick.Joystick(device_index)
                s.controller.init()
                s.controller_instance_id = getattr(s.controller, 'get_instance_id', lambda: None)()
                print(f"Controller initialized ({device_index}): {s.controller.get_name()}")
            else:
                s.controller = None
                s.controller_instance_id = None
                print("No controller detected.")
        except Exception as e:
            s.controller = None
            s.controller_instance_id = None
            print(f"Controller initialization failed: {e}")

    def poll_controller_input(s):
        if s.controller is None:
            return

        # BUTTON ACTIONS
        for button_index, action in s.controller_button_action_map.items():
            try:
                pressed = bool(s.controller.get_button(button_index))
            except pygame.error:
                pressed = False

            if pressed and not s.prev_button_states.get(button_index, False):
                key = s.controlls_data['keyboard'].get(action)
                if key is not None:
                    s.post_gpio_event(key)

            s.prev_button_states[button_index] = pressed

        # HAT / D-PAD ACTIONS
        try:
            hat_value = s.controller.get_hat(0)
        except pygame.error:
            hat_value = (0, 0)

        if hat_value != s.prev_hat_state:
            action = s.controller_hat_action_map.get(hat_value)
            if action:
                key = s.controlls_data['keyboard'].get(action)
                if key is not None:
                    s.post_gpio_event(key)
            s.prev_hat_state = hat_value

        # AXIS FALLBACK FOR LEFT STICK
        try:
            x_axis = s.controller.get_axis(0)
            y_axis = s.controller.get_axis(1)
        except pygame.error:
            x_axis = y_axis = 0.0

        if x_axis <= -0.6 and s.prev_axis_state['x'] != -1:
            key = s.controlls_data['keyboard'].get('left')
            if key is not None:
                s.post_gpio_event(key)
            s.prev_axis_state['x'] = -1
        elif x_axis >= 0.6 and s.prev_axis_state['x'] != 1:
            key = s.controlls_data['keyboard'].get('right')
            if key is not None:
                s.post_gpio_event(key)
            s.prev_axis_state['x'] = 1
        elif abs(x_axis) < 0.4:
            s.prev_axis_state['x'] = 0

        if y_axis <= -0.6 and s.prev_axis_state['y'] != -1:
            key = s.controlls_data['keyboard'].get('up')
            if key is not None:
                s.post_gpio_event(key)
            s.prev_axis_state['y'] = -1
        elif y_axis >= 0.6 and s.prev_axis_state['y'] != 1:
            key = s.controlls_data['keyboard'].get('down')
            if key is not None:
                s.post_gpio_event(key)
            s.prev_axis_state['y'] = 1
        elif abs(y_axis) < 0.4:
            s.prev_axis_state['y'] = 0

    #POSTING THE EVENT
    def post_gpio_event(s, key):
        if key:
            #CREATING A NEW KEYDOWN EVENT WITH THE SPECIFIED KEY
            new_event = pygame.event.Event(pygame.KEYDOWN, {'key': key, 'mod': pygame.KMOD_NONE})
            pygame.event.post(new_event)

    #METHOD FOR SAVING THE LAUNCHER SETTINGS
    def save(s):
        save_data(s.window_data, WINDOW_DATA_PATH)
        save_data(s.audio_data, AUDIO_DATA_PATH)
        save_data(s.theme_data, THEMES_DATA_PATH)
        save_data(s.performance_settings_data, PERFORMANCE_SETTINGS_DATA_PATH)
        save_data(s.controlls_data, CONTROLLS_DATA_PATH)
        save_data(s.game_library_data, GAME_LIBRARY_DATA_PATH)
        save_data(s.gpio_controlls_data, GPIO_CONTROLLS_DATA_PATH)

    #METHOD FOR HANDLING EVENTS
    def handling_events(s):
        events = pygame.event.get()
        s.poll_controller_input()

        for event in events:

            #CLOSING THE LAUNCHER IF WINDOW IS CLOSED
            if event.type == pygame.QUIT:
                s.save()
                pygame.quit()
                exit()

            # JOYSTICK DEVICE ADDED/REMOVED
            if event.type == pygame.JOYDEVICEADDED:
                s.init_controller(event.device_index)
                continue
            if event.type == pygame.JOYDEVICEREMOVED:
                if s.controller and event.instance_id == s.controller.get_instance_id():
                    s.controller = None
                continue

            # JOYSTICK BUTTONS / HAT / AXIS
            if event.type == pygame.JOYBUTTONDOWN:
                button_action = s.controller_button_action_map.get(event.button)
                if button_action:
                    key = s.controlls_data['keyboard'].get(button_action)
                    if key is not None:
                        s.post_gpio_event(key)
                continue

            if event.type == pygame.JOYHATMOTION:
                action = s.controller_hat_action_map.get(event.value)
                if action:
                    key = s.controlls_data['keyboard'].get(action)
                    if key is not None:
                        s.post_gpio_event(key)
                continue

            if event.type == pygame.JOYAXISMOTION:
                if event.axis in (0, 1):
                    axis_value = event.value
                    if event.axis == 0:
                        if axis_value <= -0.6:
                            action = 'left'
                        elif axis_value >= 0.6:
                            action = 'right'
                        else:
                            action = None
                    else:
                        if axis_value <= -0.6:
                            action = 'up'
                        elif axis_value >= 0.6:
                            action = 'down'
                        else:
                            action = None
                    if action:
                        key = s.controlls_data['keyboard'].get(action)
                        if key is not None:
                            s.post_gpio_event(key)
                continue

            #HANDLING WINDOW RESIZE
            if event.type == pygame.VIDEORESIZE and not s.fullscreen:

                #SAVING THE LAST NOT FULLSCREENED WINDOW SIZE
                s.window_data['width'] = event.w
                s.window_data['height'] = event.h

                #SETTING FULLSCREEN
                s.display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                s.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

                #SAVING CHANGES
                save_data(s.window_data, WINDOW_DATA_PATH)

            #USER BUTTON INPUT
            if event.type == pygame.KEYDOWN:

                #CLOSING LAUNCHER IF 'ESCAPE' BUTTON PRESSED
                if event.key == pygame.K_ESCAPE:
                    s.save()
                    pygame.quit()
                    exit()

                #TOGGLING FULLSCREEN MODE
                if event.key == pygame.K_9:
                    s.fullscreen = not s.fullscreen
                    s.window_data['fullscreen'] = s.fullscreen

                    if s.fullscreen:
                        s.last_window_size = (s.display.get_width(), s.display.get_height())
                        s.flags = pygame.FULLSCREEN
                        s.display = pygame.display.set_mode((s.window_data['width'], s.window_data['height']), s.flags)
                    else:
                        s.flags = pygame.RESIZABLE
                        s.display = pygame.display.set_mode(s.last_window_size, s.flags)
                        s.window_data['width'], s.window_data['height'] = s.last_window_size

                    save_data(s.window_data, WINDOW_DATA_PATH)

        #PASSING EVENTS TO THE CURRENT STATE
        s.state_manager.handling_events(events)

    #METHOD FOR UPDATING THE LAUNCHER
    def update(s):
        # LOWERING FPS IF THERE'S A GAME RUNNING
        if s.game_running:
            s.delta_time = s.clock.tick(s.performance_settings_data['decrease_launcher_fps_when_game_active']) / 1000
        else:
            if s.fps is None:
                s.delta_time = s.clock.tick() / 1000
            else:
                s.delta_time = s.clock.tick(s.fps) / 1000


        # UPDATING CURRENT STATE
        s.state_manager.update(s.delta_time)

    #METHOD FOR DRAWING THE LAUNCHER
    def draw(s):

        #FILLING THE WINDOW BLACK
        s.window.fill((255,0,0))

        #DRAWING THE CURRENT STATE
        s.state_manager.draw(s.window)

        #TRANSFORMING THE WINDOW TO PROPER DISPLAY | S.WINDOW ---> S.DISPLAY
        scaled_window = pygame.transform.scale(s.window, (s.display.get_width(), s.display.get_height()))

        #BLITTING THE SCALED WINDOW TO THE DISPLAY
        s.display.blit(scaled_window, (0,0))

        #UPDATING THE DISPLAY
        pygame.display.update()

    #METHOD FOR RUNNING THE LAUNCHER
    def run(s):

        #MAIN APPLICATION LOOP
        while True:

            #HANDILING EVENTS
            s.handling_events()

            #UPDATING THE LAUNCHER
            s.update()

            #DRAWING THE LAUNCHER
            s.draw()

#RUNNING THE LAUNCHER ONLY FROM THE MAIN FILE
if __name__ == '__main__':
    
    try:

        #RUNNING THE LAUNCHER
        launcher = Launcher()
        print(launcher)
        launcher.run()

    #CATCHING ANY ERRORS SO THE USER CAN TROUBLESHOOT
    except Exception as e:
        import traceback
        traceback.print_exc()
        input('Press [ENTER] to exit...')