import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY


class NavigationTutorial:
    def __init__(self, launcher):
        self.launcher = launcher
        self.theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        
        self.width = int(WINDOW_WIDTH - 300)
        self.height = 700
        
        self.target_x = WINDOW_WIDTH - self.width - 40
        self.target_y = WINDOW_HEIGHT - self.height - 150
        self.x = self.target_x
        self.y = WINDOW_HEIGHT
        self.speed = 800
        self.state = 'entering' if not self.launcher.game_library_data.get('navigation_tutorial_shown', False) else 'hidden'

        self.title_font = pygame.font.SysFont(None, 40, bold=True)
        self.body_font = pygame.font.SysFont(None, 26)
        self.action_font = pygame.font.SysFont(None, 24, bold=True)

        # Map pygame.key.name strings to your exact launcher.button_images keys
        self.asset_mapping = {
            'up': 'up_arrow_button',
            'down': 'down_arrow_button',
            'left': 'left_arrow_button',
            'right': 'right_arrow_button',
            'return': 'enter_button',
            'tab': 'tab_button'
        }

    def is_active(self):
        return self.state in ('entering', 'visible')

    def handle_input(self, events):
        if self.state != 'visible':
            return False

        current_key = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key
                break 

        if current_key is None:
            return False

        controls = self.launcher.controlls_data['keyboard']
        
        if current_key == pygame.K_RETURN or current_key == controls.get('action_a'):
            self.dismiss()
            return True

        return False

    def dismiss(self):
        if self.state != 'exiting':
            self.state = 'exiting'
            self.launcher.game_library_data['navigation_tutorial_shown'] = True
            self.launcher.save()

    def update(self, delta_time):
        if self.state == 'entering':
            self.y = max(self.target_y, self.y - self.speed * delta_time)
            if self.y <= self.target_y:
                self.y = self.target_y
                self.state = 'visible'
        elif self.state == 'exiting':
            self.y += self.speed * delta_time
            if self.y >= WINDOW_HEIGHT:
                self.y = WINDOW_HEIGHT
                self.state = 'hidden'

    def draw(self, window):
        if self.state == 'hidden':
            return

        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        x, y = int(self.x), int(self.y)
        w, h = self.width, self.height
        padding = 20

        # 1. Drop Shadow
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 110))
        window.blit(shadow, (x + 10, y + 10))

        # 2. Main Window Surface
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((24, 26, 40, 230))
        pygame.draw.rect(overlay, (255, 255, 255, 20), overlay.get_rect(), border_radius=20)
        pygame.draw.rect(overlay, pygame.Color(theme['colour_2']), overlay.get_rect(), border_radius=20, width=2)

        # 3. Title
        title = self.title_font.render('Navigation Help', True, pygame.Color(theme['colour_3']))
        overlay.blit(title, (padding, padding))

        # 4. Get control mappings and real-time keyboard state
        controls = self.launcher.controlls_data['keyboard']
        pressed_keys = pygame.key.get_pressed()
        
        ui_lines = [
            ("Move", [controls['left'], controls['down'], controls['right'], controls['up']]),
            ("Select", [controls['action_a']]),
            ("Back", [controls['action_b']]),
            ("Sidebar", [controls['options']])
        ]

        start_y = padding + 45
        line_spacing = 38

        for index, (label_text, keys) in enumerate(ui_lines):
            current_line_y = start_y + (index * line_spacing)
            
            # Action Text Label
            label_surface = self.body_font.render(f"{label_text}:", True, pygame.Color('#D7D7E0'))
            overlay.blit(label_surface, (padding, current_line_y))
            
            current_button_x = padding + 90 
            
            for key in keys:
                pygame_name = pygame.key.name(key).lower()
                
                # Check mapping dictionary for specific assets, default to generic fallback naming scheme
                base_image_key = self.asset_mapping.get(pygame_name, f"{pygame_name}_button")
                
                # Dynamic visual feedback: append '_pressed' if the player is actively holding down the key
                if pressed_keys[key]:
                    image_key = f"{base_image_key}_pressed"
                else:
                    image_key = base_image_key

                # Blit image if found, else safely render plain text fallback
                if image_key in self.launcher.button_images:
                    btn_img = self.launcher.button_images[image_key]
                    img_rect = btn_img.get_rect(topleft=(current_button_x, current_line_y - 4))
                    overlay.blit(btn_img, img_rect.topleft)
                    current_button_x += img_rect.width + 6
                else:
                    # Alternative check: if holding down a key that doesn't have a specific "_pressed" asset,
                    # look for its unpressed variant before giving up on images entirely.
                    if base_image_key in self.launcher.button_images:
                        btn_img = self.launcher.button_images[base_image_key]
                        img_rect = btn_img.get_rect(topleft=(current_button_x, current_line_y - 4))
                        overlay.blit(btn_img, img_rect.topleft)
                        current_button_x += img_rect.width + 6
                    else:
                        # Full text fallback
                        fallback_text = self.action_font.render(pygame_name.upper(), True, pygame.Color(theme['colour_3']))
                        overlay.blit(fallback_text, (current_button_x, current_line_y))
                        current_button_x += fallback_text.get_width() + 12

        # 5. Dismiss Hint Button (Bottom Right)
        # Automatically updates visually if Enter/Return is pressed
        dismiss_img_key = 'enter_button_pressed' if pressed_keys[pygame.K_RETURN] else 'enter_button'
        
        if dismiss_img_key in self.launcher.button_images:
            dismiss_img = self.launcher.button_images[dismiss_img_key]
            d_rect = dismiss_img.get_rect(bottomright=(w - padding, h - padding))
            overlay.blit(dismiss_img, d_rect.topleft)
        else:
            # Code-drawn button graphic fallback if enter_button asset is missing
            button_w, button_h = 65, 24
            button_rect = pygame.Rect(w - padding - button_w, h - padding - button_h, button_w, button_h)
            pygame.draw.rect(overlay, pygame.Color(theme['colour_3']), button_rect, border_radius=6)
            r_text = self.action_font.render('ENTER', True, pygame.Color(theme['colour_1']))
            r_rect = r_text.get_rect(center=button_rect.center)
            overlay.blit(r_text, r_rect)

        # Final Blit onto Main Window
        window.blit(overlay, (x, y))


'''
class NavigationTutorial:
    def __init__(self, launcher):
        self.launcher = launcher
        self.theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        self.width = int(WINDOW_WIDTH * 0.32)
        self.height = 198
        self.target_x = WINDOW_WIDTH - self.width - 40
        self.target_y = WINDOW_HEIGHT - self.height - 40
        self.x = self.target_x
        self.y = WINDOW_HEIGHT
        self.speed = 800
        self.state = 'entering' if not self.launcher.game_library_data.get('navigation_tutorial_shown', False) else 'hidden'

        self.title_font = pygame.font.SysFont(None, 45, bold=True)
        self.body_font = pygame.font.SysFont(None, 32)
        self.action_font = pygame.font.SysFont(None, 28, bold=True)

    def is_active(self):
        return self.state in ('entering', 'visible')

    def handle_input(self, events):
        if self.state != 'visible':
            return False

        # 1. Capture the single KEYDOWN event from the queue
        current_key = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key
                break 

        if current_key is None:
            return False

        # 2. Get the control map
        controls = self.launcher.controlls_data['keyboard']
        
        # 3. Check for dismissal (Action A or Enter)
        if current_key == pygame.K_RETURN or current_key == controls.get('action_a'):
            self.dismiss()
            return True

        return False

    def dismiss(self):
        if self.state != 'exiting':
            self.state = 'exiting'
            self.launcher.game_library_data['navigation_tutorial_shown'] = True
            self.launcher.save()

    def update(self, delta_time):
        if self.state == 'entering':
            self.y = max(self.target_y, self.y - self.speed * delta_time)
            if self.y <= self.target_y:
                self.y = self.target_y
                self.state = 'visible'
        elif self.state == 'exiting':
            self.y += self.speed * delta_time
            if self.y >= WINDOW_HEIGHT:
                self.y = WINDOW_HEIGHT
                self.state = 'hidden'

    def draw(self, window):
        if self.state == 'hidden':
            return

        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        x = int(self.x)
        y = int(self.y)
        w = self.width
        h = self.height
        padding = 22

        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 110))
        window.blit(shadow, (x + 10, y + 10))

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((24, 26, 40, 230))
        pygame.draw.rect(overlay, (255, 255, 255, 20), overlay.get_rect(), border_radius=20)
        pygame.draw.rect(overlay, pygame.Color(theme['colour_2']), overlay.get_rect(), border_radius=20, width=2)

        title = self.title_font.render('Navigation Help', True, pygame.Color(theme['colour_3']))
        overlay.blit(title, (padding, padding))

        controls = self.launcher.controlls_data['keyboard']
        lines = [
            f"Move: {pygame.key.name(controls['up']).upper()}, {pygame.key.name(controls['down']).upper()}, {pygame.key.name(controls['left']).upper()}, {pygame.key.name(controls['right']).upper()}",
            f"Select: {pygame.key.name(controls['action_a']).upper()}",
            f"Back: {pygame.key.name(controls['action_b']).upper()}",
            f"Sidebar: {pygame.key.name(controls['options']).upper()}",
        ]

        for index, text_line in enumerate(lines):
            rendered = self.body_font.render(text_line, True, pygame.Color('#D7D7E0'))
            overlay.blit(rendered, (padding, padding + 48 + index * 28))

        button_size = 52
        button_rect = pygame.Rect(w - padding - button_size, h - padding - button_size, button_size, button_size)
        pygame.draw.rect(overlay, pygame.Color(theme['colour_3']), button_rect, border_radius=14)
        r_text = self.action_font.render('R', True, pygame.Color(theme['colour_1']))
        r_rect = r_text.get_rect(center=button_rect.center)
        overlay.blit(r_text, r_rect)

        window.blit(overlay, (x, y))
'''