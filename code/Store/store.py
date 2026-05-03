import pygame
from os.path import join
import math

from settings import BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY, get_contrast_text_color
from UI.store_ui.store_entry import StoreEntry, GameStatus
from UI.searchbar import SearchBar
from UI.store_ui.progress_bar import Bar
from States.generic_state import BaseState
from Tools.data_loading_tools import load_data
from Tools.asset_importing_tool import import_image


class Store(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)

        # INTERNET
        s.online = launcher.checking_internet_connection()

        # SEARCHBAR
        # SearchBar now handles internal keyboard logic and typing state[cite: 16]
        s.search_query = ""
        s.searchbar = SearchBar(
            launcher,
            on_change=s.on_search_change,
            width=500,
            height=60
        )

        # CATEGORY TABS
        s.tabs = ["All", "Arcade", "Adventure & RPG", "Cozy", "Horror"]
        s.selected_tab_index = 0

        # SORTING
        s.sort_mode = "A-Z"

        # GRID SETTINGS
        s.columns = 2
        s.entry_height = 200
        s.spacing = 25

        # DATA
        s.manifest = {}
        s.all_games = []
        s.filtered_games = []
        s.entries = []

        s.selected_index = 0
        s.scroll = 0
        s.target_scroll = 0 

        # LOAD MANIFEST
        s.manifest_path = join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        s.manifest = load_data(s.manifest_path, {})

        s.was_downloading = False

    def update_statuses(s):
        for entry in s.entries:
            game_id = entry.game_id
            data = s.manifest[game_id]
            manifest_version = data.get('version')

            if s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == game_id:
                entry.status = GameStatus.DOWNLOADING
            elif any(q[0] == game_id for q in s.launcher.installer.download_queue):
                entry.status = GameStatus.QUEUED
            elif not s.launcher.installer.is_installed(game_id):
                entry.status = GameStatus.NOT_INSTALLED
            elif s.launcher.installer.has_update(game_id, manifest_version):
                entry.status = GameStatus.UPDATE_AVAILABLE
            else:
                entry.status = GameStatus.INSTALLED

    def draw_download_panel(s, window, theme):
        if not (s.launcher.installer.is_downloading or s.launcher.installer.download_queue):
            return

        x_start = s.launcher.sidebar.base_w + 40
        y_current = 20

        # Current downloading
        if s.launcher.installer.is_downloading:
            current_id = s.launcher.installer.current_game_id
            # Icon
            icon_path = join(BASE_DIR, 'assets', 'store_assets', current_id, 'icon')
            try:
                icon = import_image(icon_path)
                icon = pygame.transform.smoothscale(icon, (60, 60))
                window.blit(icon, (x_start, y_current))
            except:
                pass

            # Title
            title_font = pygame.font.SysFont(None, 28)
            title_surf = title_font.render(s.manifest[current_id]['name'], True, theme['colour_3'])
            window.blit(title_surf, (x_start + 70, y_current + 10))

            # Progress bar
            bar_x = x_start + 70
            bar_y = y_current + 45
            bar = Bar(bar_x, bar_y, 200, 20)
            bar.set_progress(s.launcher.installer.download_progress)
            bar.draw(window)

            # Cancel button
            cancel_x = bar_x + 220
            cancel_y = bar_y - 5
            s.cancel_rect = pygame.Rect(cancel_x, cancel_y, 60, 30)
            pygame.draw.rect(window, (200, 50, 50), s.cancel_rect, border_radius=5)
            if s.launcher.state_manager.ui_focus == "download":
                pygame.draw.rect(window, theme['colour_2'], s.cancel_rect, 3, border_radius=7)
            cancel_font = pygame.font.SysFont(None, 20)
            cancel_surf = cancel_font.render("Cancel", True, (255, 255, 255))
            window.blit(cancel_surf, cancel_surf.get_rect(center=s.cancel_rect.center))

        # Next in queue
        if s.launcher.installer.download_queue:
            next_x = x_start + 500 if s.launcher.installer.is_downloading else x_start
            next_id = s.launcher.installer.download_queue[0][0]
            # Icon
            icon_path = join(BASE_DIR, 'assets', 'store_assets', next_id, 'icon')
            try:
                icon = import_image(icon_path)
                icon = pygame.transform.smoothscale(icon, (30, 30))
                window.blit(icon, (next_x, y_current))
            except:
                pass

            # Title
            next_font = pygame.font.SysFont(None, 24)
            next_surf = next_font.render(f"Next: {s.manifest[next_id]['name']}", True, theme['colour_3'])
            window.blit(next_surf, (next_x + 40, y_current + 5))

    def on_search_change(s, query):
        s.search_query = query
        s.apply_filters()

    def apply_filters(s):
        if not s.online:
            return

        query = s.search_query.lower()
        active_tab = s.tabs[s.selected_tab_index]

        s.filtered_games = []

        for game_id in s.all_games:
            data = s.manifest[game_id]
            name = data.get('name', '').lower()
            tags = data.get('tags', [])

            if query and query not in name:
                continue

            if active_tab == "Arcade" and "arcade" not in tags:
                continue
            if active_tab == "Adventure & RPG" and not any(t in tags for t in ["adventure", "rpg"]):
                continue
            if active_tab == "Cozy" and "cozzy" not in tags:
                continue
            if active_tab == "Horror" and "horror" not in tags:
                continue

            s.filtered_games.append(game_id)

        if s.sort_mode == "A-Z":
            s.filtered_games.sort(key=lambda gid: s.manifest[gid]['name'])
        else:
            s.filtered_games.sort(key=lambda gid: s.manifest[gid]['name'], reverse=True)

        s.selected_index = 0
        s.target_scroll = 0
        s.scroll = 0
        s.load_store_entries()

    def load_store_entries(s):
        s.entries.clear()

        if not s.online:
            return

        fixed_sidebar_w = s.launcher.sidebar.base_w
        panel_padding = 40
        available_width = WINDOW_WIDTH - fixed_sidebar_w - (panel_padding * 2)
        entry_width = (available_width - s.spacing) // s.columns

        start_x = fixed_sidebar_w + panel_padding
        start_y = 200

        for i, game_id in enumerate(s.filtered_games):
            data = s.manifest[game_id]
            manifest_version = data.get('version')

            if s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == game_id:
                status = GameStatus.DOWNLOADING
            elif any(q[0] == game_id for q in s.launcher.installer.download_queue):
                status = GameStatus.QUEUED
            elif not s.launcher.installer.is_installed(game_id):
                status = GameStatus.NOT_INSTALLED
            elif s.launcher.installer.has_update(game_id, manifest_version):
                status = GameStatus.UPDATE_AVAILABLE
            else:
                status = GameStatus.INSTALLED

            row = i // s.columns
            col = i % s.columns

            x = start_x + col * (entry_width + s.spacing)
            y = start_y + row * (s.entry_height + s.spacing)

            entry = StoreEntry(
                launcher=s.launcher,
                game_id=game_id,
                game_data=data,
                status=status,
                size=(entry_width, s.entry_height),
                position=(x, y)
            )

            s.entries.append(entry)

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()
        state_manager = s.launcher.state_manager
        controlls = getattr(s.launcher, 'controlls_data', {})
        
        action_confirm = keys[controlls.get('action_a', pygame.K_RETURN)] or keys[pygame.K_RETURN]
        action_back = keys[controlls.get('action_b', pygame.K_ESCAPE)] or keys[pygame.K_ESCAPE]
        
        btn_left = controlls.get('left', pygame.K_LEFT)
        btn_right = controlls.get('right', pygame.K_RIGHT)
        btn_up = controlls.get('up', pygame.K_UP)
        btn_down = controlls.get('down', pygame.K_DOWN)

        # 1. SEARCHBAR FOCUS LOGIC[cite: 16, 18]
        if state_manager.ui_focus == "searchbar":
            if s.searchbar.active:
                # If currently typing, let the searchbar consume events[cite: 16]
                if s.searchbar.handle_events(events):
                    state_manager.ui_focus = "tabs"
                return # Don't process other keys while typing
            else:
                # Navigating the searchbar area
                if action_confirm:
                    s.searchbar.open_keyboard()
                elif keys[btn_down]:
                    state_manager.ui_focus = "tabs"
                elif keys[btn_left]:
                    if s.launcher.installer.is_downloading:
                        state_manager.ui_focus = "download"
            return

        # 2. TABS FOCUS LOGIC[cite: 18]
        if state_manager.ui_focus == "tabs":
            if keys[btn_left] or action_back:
                if s.selected_tab_index > 0:
                    s.selected_tab_index -= 1
                    s.apply_filters()
            elif keys[btn_right]:
                s.selected_tab_index = min(len(s.tabs) - 1, s.selected_tab_index + 1)
                s.apply_filters()
            elif keys[btn_up]:
                state_manager.ui_focus = "searchbar"
            elif keys[btn_down]:
                if s.launcher.installer.is_downloading:
                    state_manager.ui_focus = "download"
                elif s.entries:
                    state_manager.ui_focus = "content"
            return

        # 3. CONTENT FOCUS LOGIC[cite: 18]
        if state_manager.ui_focus == "content":
            if keys[btn_up]:
                if s.selected_index < s.columns:
                    if s.launcher.installer.is_downloading:
                        state_manager.ui_focus = "download"
                    else:
                        state_manager.ui_focus = "tabs"
                else:
                    s.selected_index -= s.columns
            elif keys[btn_down]:
                if s.selected_index + s.columns < len(s.entries):
                    s.selected_index += s.columns
            elif keys[btn_left] or action_back:
                if s.selected_index % s.columns != 0:
                    s.selected_index -= 1
            elif keys[btn_right]:
                if (s.selected_index + 1) % s.columns != 0 and s.selected_index + 1 < len(s.entries):
                    s.selected_index += 1
            elif action_confirm:
                s.enter_game_preview()

        # 4. DOWNLOAD FOCUS LOGIC
        if state_manager.ui_focus == "download":
            if action_confirm and s.launcher.installer.is_downloading:
                s.launcher.installer.cancel_download()
            elif keys[btn_up]:
                state_manager.ui_focus = "tabs"
            elif keys[btn_down]:
                state_manager.ui_focus = "content"

        # Global Hotkeys
        if keys[pygame.K_s]:
            s.sort_mode = "Z-A" if s.sort_mode == "A-Z" else "A-Z"
            s.apply_filters()

        s.handle_mouse_events(events)

    def handle_mouse_events(s, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(s, 'cancel_rect') and s.cancel_rect.collidepoint(event.pos):
                    s.launcher.installer.cancel_download()

    def update(s, delta_time):
        super().update(delta_time)
        if not s.online or not s.entries:
            return

        # Check if downloading status changed
        current_downloading = s.launcher.installer.is_downloading
        if current_downloading != s.was_downloading:
            s.was_downloading = current_downloading
            if not current_downloading:
                s.update_statuses()

        row = s.selected_index // s.columns
        start_y = 190
        current_y = start_y + row * (s.entry_height + s.spacing)
        panel_y = 190
        panel_h = WINDOW_HEIGHT - 210

        if current_y + s.entry_height > s.target_scroll + panel_y + panel_h - 20:
            s.target_scroll = current_y + s.entry_height - (panel_y + panel_h - 20)
        if current_y < s.target_scroll + panel_y + 20:
            s.target_scroll = current_y - (panel_y + 20)

        s.target_scroll = max(0, s.target_scroll)
        total_rows = math.ceil(len(s.entries) / s.columns)
        total_content_height = (total_rows * (s.entry_height + s.spacing)) + 40
        max_scroll = max(0, total_content_height - panel_h)
        s.target_scroll = min(s.target_scroll, max_scroll)

        lerp_speed = min(1.0, 15 * delta_time) if delta_time < 1.0 else 0.15
        s.scroll += (s.target_scroll - s.scroll) * lerp_speed
        if abs(s.target_scroll - s.scroll) < 0.5:
            s.scroll = s.target_scroll

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        # ---------- HEADER ----------
        header_h = 120
        pygame.draw.rect(window, theme['colour_4'], (s.launcher.sidebar.base_w, 0, WINDOW_WIDTH, header_h))

        # Download panel
        s.draw_download_panel(window, theme)

        # ---------- TABS ----------
        s.draw_tabs(window, theme)

        # ---------- LEGEND & CONTROLS ----------
        info_font = pygame.font.SysFont(None, 24)
        controls_text = f"Hotkeys: [TAB] Sidebar | [E] Back | [R] Details | [S] Sort: {s.sort_mode}"
        sort_text = info_font.render(controls_text, True, theme['colour_4'])
        text_x = WINDOW_WIDTH - sort_text.get_width() - 40
        window.blit(sort_text, (text_x, 155))

        # ---------- CONTENT PANEL ----------
        panel_rect = pygame.Rect(
            s.launcher.sidebar.base_w + 20,
            190,
            WINDOW_WIDTH - s.launcher.sidebar.base_w - 40,
            WINDOW_HEIGHT - 210
        )

        pygame.draw.rect(window, theme['colour_4'], panel_rect, border_radius=16)
        pygame.draw.rect(window, theme['colour_3'], panel_rect, 2, border_radius=16)

        clip_rect = panel_rect.inflate(-6, -6)
        window.set_clip(clip_rect)

        for i, entry in enumerate(s.entries):
            selected = i == s.selected_index and s.launcher.state_manager.ui_focus == "content"
            row = i // s.columns
            start_y = 200
            original_y = start_y + row * (s.entry_height + s.spacing)
            entry.rect.top = original_y - s.scroll

            if entry.rect.bottom > panel_rect.top and entry.rect.top < panel_rect.bottom:
                entry.draw(window)
                if selected:
                    highlight = entry.rect.inflate(14, 14)
                    pygame.draw.rect(window, theme['colour_2'], highlight, 8, border_radius=14)

        # ---------- CUSTOM SCROLLBAR ----------
        total_rows = math.ceil(len(s.entries) / s.columns)
        total_content_height = (total_rows * (s.entry_height + s.spacing)) + 40
        if total_content_height > panel_rect.height:
            scrollbar_w = 8
            visible_ratio = panel_rect.height / total_content_height
            scrollbar_h = max(40, panel_rect.height * visible_ratio)
            max_scroll = total_content_height - panel_rect.height
            scroll_progress = s.scroll / max_scroll if max_scroll > 0 else 0
            scrollbar_y = panel_rect.top + 5 + scroll_progress * (panel_rect.height - scrollbar_h - 10)
            scrollbar_x = panel_rect.right - 15
            
            track_rect = pygame.Rect(scrollbar_x, panel_rect.top + 5, scrollbar_w, panel_rect.height - 10)
            pygame.draw.rect(window, theme['colour_1'], track_rect, border_radius=4)
            
            scroll_rect = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_w, scrollbar_h)
            pygame.draw.rect(window, theme['colour_2'], scroll_rect, border_radius=4)

        window.set_clip(None)

        # ---------- SEARCH BAR (DRAWN LAST) ----------
        # Moving this here ensures the internal keyboard overlay is drawn on top of EVERYTHING[cite: 16]
        s.searchbar.custom_x = WINDOW_WIDTH - 600
        s.searchbar.custom_y = 25
        search_focused = s.launcher.state_manager.ui_focus == "searchbar"
        s.searchbar.draw(window, focused=search_focused)

        super().draw(window)

    def draw_tabs(s, window, theme):
        font = pygame.font.SysFont(None, 26, bold=True)
        x = s.launcher.sidebar.base_w + 40
        y = 130

        for i, tab in enumerate(s.tabs):
            active = i == s.selected_tab_index
            focused = s.launcher.state_manager.ui_focus == "tabs"

            bg_color = theme['colour_2'] if active else theme['colour_4']
            text_color = bg_color
            text = font.render(tab, True, text_color)

            rect = pygame.Rect(x, y, text.get_width() + 32, text.get_height() + 16)

            if active:
                pygame.draw.rect(window, theme['colour_2'], rect, 3, border_radius=20)
            else:
                pygame.draw.rect(window, theme['colour_3'], rect, 2, border_radius=20)

            if active and focused:
                pygame.draw.rect(window, theme['colour_4'], rect.inflate(6, 6), 4, border_radius=22)

            window.blit(text, (rect.x + 16, rect.y + 8))
            x += rect.width + 15

    def enter_game_preview(s):
        if not s.entries:
            return
        entry = s.entries[s.selected_index]
        preview = s.launcher.state_manager.states.get('Game preview')
        if preview:
            preview.setup(entry.game_id, entry.game_data)
            s.launcher.state_manager.set_state('Game preview')

    def on_enter(s):
        s.online = s.launcher.checking_internet_connection()
        s.manifest = load_data(s.manifest_path, {})
        if s.online:
            s.all_games = list(s.manifest.keys())
            s.apply_filters()