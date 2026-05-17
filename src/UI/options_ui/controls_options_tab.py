#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from settings import get_contrast_text_color
from Tools.data_loading_tools import save_data
from settings import CONTROLLS_DATA_PATH
from settings import THEME_LIBRARY
from settings import WINDOW_WIDTH
from settings import THEME_LIBRARY, WINDOW_WIDTH
from UI.options_ui.generic_options_tab import GenericOptionsTab


class ControlsOptionsTab(GenericOptionsTab):
    def __init__(s, launcher):
        super().__init__(launcher)
        
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        s.initial_pos = (WINDOW_WIDTH * 0.30, 480) 
        s.button_size = (280, 80)
        s.spacing = 15
        s.column_spacing = 600
        
        s.font = pygame.font.SysFont(None, 60, False)
        s.title_font = pygame.font.SysFont(None, 50, True)
        s.value_font = pygame.font.SysFont(None, 45, False)

        # --- PRESET CONFIGURATION ---
        s.preset_names = ['Arrows', 'WASD', 'Custom']
        s.presets = {
            'Arrows': {
                'up': pygame.K_UP, 'down': pygame.K_DOWN, 
                'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
                'action_a': pygame.K_r, 'action_b': pygame.K_e
            },
            'WASD': {
                'up': pygame.K_w, 'down': pygame.K_s, 
                'left': pygame.K_a, 'right': pygame.K_d,
                'action_a': pygame.K_p, 'action_b': pygame.K_o
            }
        }
        
        s.focus_area = 'preset'  # Starts on 'preset', can switch to 'bindings'
        s.preset_idx = 2         # The currently active preset (Defaults to Custom)
        s.preset_focus_idx = 2   # Which preset button the cursor is hovering over
        
        # Check current keys on boot
        s.evaluate_current_preset()

        # Definiujemy grupy klawiszy dla dwóch kolumn
        s.columns = {
            'left': ['up', 'down', 'left', 'right'],
            'right': ['options', 'action_a', 'action_b']
        }
        s.column_names = ['left', 'right']
        s.column_titles = ['Movement Buttons', 'Action Buttons']
        
        s.active_col_idx = 0  # 0: lewa, 1: prawa
        s.selected_index = 0  # Indeks wewnątrz danej kolumny
        
        s.waiting_for_key = False

    def evaluate_current_preset(s):
        """Checks if the currently loaded keys match WASD or Arrows perfectly."""
        ctrl = s.launcher.controlls_data['keyboard']
        s.preset_idx = 2  # Default to Custom
        for idx, name in enumerate(['Arrows', 'WASD']):
            preset = s.presets[name]
            # Check if all keys defined in the preset match the current bindings
            if all(ctrl.get(k) == preset[k] for k in preset):
                s.preset_idx = idx
                break
        
        s.preset_focus_idx = s.preset_idx

    def apply_preset(s):
        """Applies the selected preset to the launcher data and saves it."""
        preset_name = s.preset_names[s.preset_idx]
        if preset_name == 'Custom':
            return  # Do nothing if custom is selected
        
        preset_data = s.presets[preset_name]
        for key, val in preset_data.items():
            s.launcher.controlls_data['keyboard'][key] = val
            
        save_data(s.launcher.controlls_data, CONTROLLS_DATA_PATH)

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        current_key = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key
                
                # --- LOGIC FOR REBINDING KEYS ---
                if s.waiting_for_key:
                    if current_key != pygame.K_ESCAPE:
                        col_key = s.column_names[s.active_col_idx]
                        action_name = s.columns[col_key][s.selected_index]
                        s.update_control(action_name, current_key)
                        
                        # Modifying a key manually automatically makes it Custom
                        s.preset_idx = 2 
                        s.preset_focus_idx = 2
                        
                    s.waiting_for_key = False
                    return 

        if s.waiting_for_key or current_key is None:
            return

        is_up = current_key == ctrl['up']
        is_down = current_key == ctrl['down']
        is_left = current_key == ctrl['left']
        is_right = current_key == ctrl['right']
        is_confirm = current_key in [ctrl['action_a'], pygame.K_RETURN]

        # --- PRESET SELECTOR NAVIGATION ---
        if s.focus_area == 'preset':
            if is_left:
                s.preset_focus_idx = max(0, s.preset_focus_idx - 1)
            elif is_right:
                s.preset_focus_idx = min(len(s.preset_names) - 1, s.preset_focus_idx + 1)
            elif is_confirm:
                s.preset_idx = s.preset_focus_idx
                s.apply_preset()
            elif is_down:
                s.focus_area = 'bindings'  
            return  

        # --- BINDINGS COLUMN NAVIGATION ---
        current_col_key = s.column_names[s.active_col_idx]
        num_items = len(s.columns[current_col_key])

        if is_left:
            s.active_col_idx = max(0, s.active_col_idx - 1)
            s.selected_index = min(s.selected_index, len(s.columns[s.column_names[s.active_col_idx]]) - 1)
        elif is_right:
            s.active_col_idx = min(len(s.column_names) - 1, s.active_col_idx + 1)
            s.selected_index = min(s.selected_index, len(s.columns[s.column_names[s.active_col_idx]]) - 1)

        if is_up:
            if s.selected_index == 0:
                s.focus_area = 'preset'
                s.preset_focus_idx = s.preset_idx # Snap cursor back to the active preset
            else:
                s.selected_index -= 1
        elif is_down:
            s.selected_index = min(num_items - 1, s.selected_index + 1)

        if is_confirm:
            s.waiting_for_key = True

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        
        # ---------------------------------------------------------
        # 1. DRAW PRESET SELECTOR (3 SEPARATE BUTTONS)
        # ---------------------------------------------------------
        preset_y = s.initial_pos[1] - 160
        
        # Sizing and spacing for the 3 buttons
        p_btn_w = 200
        p_btn_h = 60
        p_spacing = 30
        total_preset_width = (p_btn_w * 3) + (p_spacing * 2)
        start_x = (WINDOW_WIDTH - total_preset_width) // 2

        # Draw Title
        p_title_surf = s.value_font.render("Control Scheme", True, s.current_theme['colour_2'])
        window.blit(p_title_surf, p_title_surf.get_rect(midbottom=(WINDOW_WIDTH // 2, preset_y - 20)))

        for i, preset_name in enumerate(s.preset_names):
            x = start_x + i * (p_btn_w + p_spacing)
            rect = pygame.Rect(x, preset_y, p_btn_w, p_btn_h)
            
            is_active = (i == s.preset_idx)
            is_focused = (i == s.preset_focus_idx and s.focus_area == 'preset' and has_focus)

            # Highlight the currently applied preset using your primary theme colour
            if is_active:
                bg_colour = s.current_theme['colour_2']
            else:
                bg_colour = s.current_theme['colour_4']
                
            text_colour = get_contrast_text_color(bg_colour)

            pygame.draw.rect(window, bg_colour, rect, border_radius=10)
            
            # Highlight the focused element with the yellow outline
            if is_focused:
                pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=10)

            # Draw Button Text
            text_surf = s.title_font.render(preset_name, True, text_colour)
            text_rect = text_surf.get_rect(center=rect.center)
            window.blit(text_surf, text_rect)

        # ---------------------------------------------------------
        # 2. DRAW BINDINGS COLUMNS
        # ---------------------------------------------------------
        for col_idx, col_name in enumerate(s.column_names):
            title = s.column_titles[col_idx]
            x = s.initial_pos[0] + col_idx * s.column_spacing + s.button_size[0] // 2
            y = s.initial_pos[1] - 60
            
            title_surf = s.title_font.render(title, True, s.current_theme['colour_2'])
            title_rect = title_surf.get_rect(center=(x, y))
            window.blit(title_surf, title_rect)
        
        for col_idx, col_name in enumerate(s.column_names):
            actions = s.columns[col_name]
            
            for row_idx, action_name in enumerate(actions):
                is_selected = (col_idx == s.active_col_idx and row_idx == s.selected_index and s.focus_area == 'bindings')
                is_waiting = (is_selected and s.waiting_for_key)
                
                if is_waiting:
                    bg_colour = (200, 50, 50)
                elif is_selected and has_focus:
                    bg_colour = s.current_theme['colour_2']
                else:
                    bg_colour = s.current_theme['colour_4']

                text_colour = get_contrast_text_color(bg_colour)

                x = s.initial_pos[0] + col_idx * s.column_spacing
                y = s.initial_pos[1] + row_idx * (s.button_size[1] + s.spacing)

                rect = pygame.Rect(x, y, s.button_size[0], s.button_size[1])
                pygame.draw.rect(window, bg_colour, rect)
                
                if is_selected and has_focus:
                    pygame.draw.rect(window, (255, 200, 0), rect, 4)
                
                key_code = s.launcher.controlls_data['keyboard'][action_name]
                key_name = pygame.key.name(key_code).upper()
                
                label = action_name.replace('_', ' ').title()
                display_text = f"{label}: {key_name}" if not is_waiting else "PRESS..."
                
                text_surf = s.value_font.render(display_text, True, text_colour)
                text_rect = text_surf.get_rect(center=rect.center)
                window.blit(text_surf, text_rect)

    def update_control(s, action_name, new_key):
        s.launcher.controlls_data['keyboard'][action_name] = new_key
        save_data(s.launcher.controlls_data, CONTROLLS_DATA_PATH)