# Codduo - Xadrez - Jogo de xadrez em Pygame

import sys
import pygame as p
import time
import json
import os
from engine import GameState, Move

p.mixer.init()
move_sound = p.mixer.Sound("sounds/move-sound.mp3")
capture_sound = p.mixer.Sound("sounds/capture.mp3")
promote_sound = p.mixer.Sound("sounds/promote.mp3")

# Configurações do jogo
class GameConfig:
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        default_config = {
            "board_size": 512,
            "max_fps": 60,
            "auto_rotate": True,
            "timer_minutes": 10,
            "show_timer": True,
            "timer_mode": "countdown",
            "rotation_animation": True,
            "rotation_speed": 2.0,
            "resolution_preset": "800x600",  # Available presets
            "window_width": 800,
            "window_height": 600
        }
        
        self.resolution_presets = {
            "800x600": {"width": 800, "height": 600, "board_size": 512},
            "1024x768": {"width": 1024, "height": 768, "board_size": 640},
            "1280x720": {"width": 1280, "height": 720, "board_size": 640},
            "1366x768": {"width": 1366, "height": 768, "board_size": 680},
            "1600x900": {"width": 1600, "height": 900, "board_size": 720},
            "1920x1080": {"width": 1920, "height": 1080, "board_size": 800},
            "2560x1440": {"width": 2560, "height": 1440, "board_size": 1000}
        }
        
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    loaded_config = json.load(f)
                    self.config = {**default_config, **loaded_config}
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)
    
    def get(self, key):
        return self.config.get(key)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()
    
    def apply_resolution_preset(self, preset):
        if preset in self.resolution_presets:
            preset_data = self.resolution_presets[preset]
            self.config["window_width"] = preset_data["width"]
            self.config["window_height"] = preset_data["height"]
            self.config["board_size"] = preset_data["board_size"]
            self.config["resolution_preset"] = preset
            self.save_config()
    
    def get_available_presets(self):
        return list(self.resolution_presets.keys())
    
    def get_next_preset(self, current_preset):
        presets = self.get_available_presets()
        try:
            current_index = presets.index(current_preset)
            next_index = (current_index + 1) % len(presets)
            return presets[next_index]
        except ValueError:
            return presets[0]

config = GameConfig()

BOARD_WIDTH = BOARD_HEIGHT = config.get("board_size")
WINDOW_WIDTH = config.get("window_width")
WINDOW_HEIGHT = config.get("window_height")
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = config.get("max_fps")
IMAGES = {}

class GameTimer:
    def __init__(self, minutes_per_player, mode="countdown"):
        self.mode = mode
        if mode == "countdown":
            self.white_time = minutes_per_player * 60
            self.black_time = minutes_per_player * 60
        else:
            self.white_time = 0
            self.black_time = 0
        self.current_turn_start = None
        self.active = False
        
    def start_turn(self, is_white_turn):
        if self.current_turn_start is not None:
            elapsed = time.time() - self.current_turn_start
            if self.mode == "countdown":
                if is_white_turn:
                    self.black_time = max(0, self.black_time - elapsed)
                else:
                    self.white_time = max(0, self.white_time - elapsed)
            else:
                if is_white_turn:
                    self.black_time += elapsed
                else:
                    self.white_time += elapsed
        
        self.current_turn_start = time.time()
        self.active = True
    
    def get_current_times(self, is_white_turn):
        if not self.active or self.current_turn_start is None:
            return self.white_time, self.black_time
            
        elapsed = time.time() - self.current_turn_start
        
        if self.mode == "countdown":
            if is_white_turn:
                current_white = max(0, self.white_time - elapsed)
                return current_white, self.black_time
            else:
                current_black = max(0, self.black_time - elapsed)
                return self.white_time, current_black
        else:  # stopwatch mode
            if is_white_turn:
                current_white = self.white_time + elapsed
                return current_white, self.black_time
            else:
                current_black = self.black_time + elapsed
                return self.white_time, current_black
    
    def is_time_up(self, is_white_turn):
        if self.mode == "stopwatch":
            return False
        white_time, black_time = self.get_current_times(is_white_turn)
        return white_time <= 0 or black_time <= 0

LIGHT_SQUARE_COLOR = (237, 238, 209)
DARK_SQUARE_COLOR = (119, 153, 82)
MOVE_HIGHLIGHT_COLOR = (84, 115, 161)
POSSIBLE_MOVE_COLOR = (255, 255, 51)

MENU_BG_COLOR = (25, 30, 40)
MENU_BUTTON_COLOR = (45, 55, 75)
MENU_BUTTON_HOVER_COLOR = (65, 75, 95)
MENU_ACCENT_COLOR = (100, 150, 255)
MENU_TEXT_COLOR = (240, 245, 255)
GAME_BG_COLOR = (20, 25, 35)
TIMER_BG_COLOR = (35, 42, 55)
TIMER_BORDER_COLOR = (80, 90, 110)


def loadImages():
    pieces = ['bR', 'bN', 'bB', 'bQ', 'bK', 'bp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'wp']
    for piece in pieces:
        image_path = "images1/" + piece + ".png"
        original_image = p.image.load(image_path)
        IMAGES[piece] = p.transform.smoothscale(original_image, (SQ_SIZE, SQ_SIZE))

def loadLogo():
    try:
        logo_image = p.image.load("Logo.png")
        return logo_image
    except:
        return None


def draw_button(screen, rect, text, font, is_hovered=False):
    shadow_rect = rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 3
    p.draw.rect(screen, (10, 15, 25), shadow_rect, border_radius=8)
    
    color = MENU_BUTTON_HOVER_COLOR if is_hovered else MENU_BUTTON_COLOR
    p.draw.rect(screen, color, rect, border_radius=8)
    
    border_color = MENU_ACCENT_COLOR if is_hovered else TIMER_BORDER_COLOR
    p.draw.rect(screen, border_color, rect, 2, border_radius=8)
    
    text_color = MENU_ACCENT_COLOR if is_hovered else MENU_TEXT_COLOR
    
    shadow_text = font.render(text, True, (10, 15, 25))
    shadow_rect = shadow_text.get_rect(center=(rect.centerx + 1, rect.centery + 1))
    screen.blit(shadow_text, shadow_rect)
    
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)

def show_main_menu(screen):
    font_title = p.font.SysFont("Arial", 54, True)
    font_subtitle = p.font.SysFont("Arial", 28)
    font_button = p.font.SysFont("Arial", 20, True)
    
    # Carregar logo
    logo = loadLogo()
    
    # Botões do menu
    button_width, button_height = 240, 55
    center_x = WINDOW_WIDTH // 2
    
    # Posições ajustadas baseadas no tamanho da tela
    title_y = WINDOW_HEIGHT // 4
    buttons_start_y = title_y + 180
    
    start_button = p.Rect(center_x - button_width//2, buttons_start_y, button_width, button_height)
    config_button = p.Rect(center_x - button_width//2, buttons_start_y + 80, button_width, button_height)
    quit_button = p.Rect(center_x - button_width//2, buttons_start_y + 160, button_width, button_height)
    
    clock = p.time.Clock()
    
    while True:
        mouse_pos = p.mouse.get_pos()
        
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                if start_button.collidepoint(mouse_pos):
                    return "start"
                elif config_button.collidepoint(mouse_pos):
                    return "config"
                elif quit_button.collidepoint(mouse_pos):
                    p.quit()
                    sys.exit()
        
        # Desenhar menu com gradiente
        screen.fill(MENU_BG_COLOR)
        
        # Adicionar efeito de gradiente sutil
        for i in range(WINDOW_HEIGHT // 4):
            alpha = int(15 * (i / (WINDOW_HEIGHT // 4)))
            gradient_color = (MENU_BG_COLOR[0] + alpha, MENU_BG_COLOR[1] + alpha, MENU_BG_COLOR[2] + alpha)
            p.draw.rect(screen, gradient_color, (0, i * 4, WINDOW_WIDTH, 4))
        
        # Logo (se existir)
        if logo:
            logo_scaled = p.transform.smoothscale(logo, (120, 120))
            logo_rect = logo_scaled.get_rect(center=(WINDOW_WIDTH//2, title_y - 80))
            screen.blit(logo_scaled, logo_rect)
        
        # Título estilizado
        title = font_title.render("CODDUO", True, MENU_ACCENT_COLOR)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, title_y))
        
        # Sombra do título
        title_shadow = font_title.render("CODDUO", True, (10, 15, 25))
        shadow_rect = title_shadow.get_rect(center=(WINDOW_WIDTH//2 + 2, title_y + 2))
        screen.blit(title_shadow, shadow_rect)
        screen.blit(title, title_rect)
        
        # Subtítulo
        subtitle = font_subtitle.render("XADREZ", True, MENU_TEXT_COLOR)
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH//2, title_y + 50))
        screen.blit(subtitle, subtitle_rect)
        
        # Linha decorativa
        line_y = title_y + 80
        p.draw.line(screen, MENU_ACCENT_COLOR, 
                   (WINDOW_WIDTH//2 - 100, line_y), 
                   (WINDOW_WIDTH//2 + 100, line_y), 3)
        
        # Botões elegantes
        draw_button(screen, start_button, "INICIAR JOGO", font_button, start_button.collidepoint(mouse_pos))
        draw_button(screen, config_button, "CONFIGURAÇÕES", font_button, config_button.collidepoint(mouse_pos))
        draw_button(screen, quit_button, "SAIR", font_button, quit_button.collidepoint(mouse_pos))
        
        # Versão no canto
        version_font = p.font.SysFont("Arial", 16)
        version_text = version_font.render("v2.0", True, (100, 110, 130))
        screen.blit(version_text, (WINDOW_WIDTH - 50, WINDOW_HEIGHT - 30))
        
        p.display.flip()
        clock.tick(60)

def show_config_menu(screen):
    font_title = p.font.SysFont("Arial", 32, True)
    font_text = p.font.SysFont("Arial", 18)
    font_button = p.font.SysFont("Arial", 16)
    
    button_width, button_height = 150, 35
    center_x = WINDOW_WIDTH // 2
    
    # Botões de configuração
    resolution_toggle = p.Rect(center_x - 75, 150, button_width, button_height)
    
    timer_minus = p.Rect(center_x - 100, 200, 30, 30)
    timer_plus = p.Rect(center_x + 70, 200, 30, 30)
    
    timer_mode_toggle = p.Rect(center_x - 75, 250, button_width, button_height)
    
    rotation_toggle = p.Rect(center_x - 75, 300, button_width, button_height)
    rotation_anim_toggle = p.Rect(center_x - 75, 350, button_width, button_height)
    timer_toggle = p.Rect(center_x - 75, 400, button_width, button_height)
    
    back_button = p.Rect(50, WINDOW_HEIGHT - 80, 100, 40)
    
    clock = p.time.Clock()
    
    while True:
        mouse_pos = p.mouse.get_pos()
        
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                if back_button.collidepoint(mouse_pos):
                    return
                elif resolution_toggle.collidepoint(mouse_pos):
                    current_preset = config.get("resolution_preset")
                    next_preset = config.get_next_preset(current_preset)
                    config.apply_resolution_preset(next_preset)
                elif timer_minus.collidepoint(mouse_pos):
                    current_timer = config.get("timer_minutes")
                    if current_timer > 1:
                        config.set("timer_minutes", current_timer - 1)
                elif timer_plus.collidepoint(mouse_pos):
                    current_timer = config.get("timer_minutes")
                    if current_timer < 120:  # Increased max time to 120 minutes
                        config.set("timer_minutes", current_timer + 1)
                elif timer_mode_toggle.collidepoint(mouse_pos):
                    current_mode = config.get("timer_mode")
                    new_mode = "stopwatch" if current_mode == "countdown" else "countdown"
                    config.set("timer_mode", new_mode)
                elif rotation_toggle.collidepoint(mouse_pos):
                    config.set("auto_rotate", not config.get("auto_rotate"))
                elif rotation_anim_toggle.collidepoint(mouse_pos):
                    config.set("rotation_animation", not config.get("rotation_animation"))
                elif timer_toggle.collidepoint(mouse_pos):
                    config.set("show_timer", not config.get("show_timer"))
        
        # Desenhar menu de configurações
        screen.fill(MENU_BG_COLOR)
        
        # Gradiente sutil
        for i in range(WINDOW_HEIGHT // 4):
            alpha = int(15 * (i / (WINDOW_HEIGHT // 4)))
            gradient_color = (MENU_BG_COLOR[0] + alpha, MENU_BG_COLOR[1] + alpha, MENU_BG_COLOR[2] + alpha)
            p.draw.rect(screen, gradient_color, (0, i * 4, WINDOW_WIDTH, 4))
        
        # Título estilizado
        title = font_title.render("CONFIGURAÇÕES", True, MENU_ACCENT_COLOR)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 80))
        
        # Sombra do título
        title_shadow = font_title.render("CONFIGURAÇÕES", True, (10, 15, 25))
        shadow_rect = title_shadow.get_rect(center=(WINDOW_WIDTH//2 + 2, 82))
        screen.blit(title_shadow, shadow_rect)
        screen.blit(title, title_rect)
        
        # Linha decorativa
        p.draw.line(screen, MENU_ACCENT_COLOR, 
                   (WINDOW_WIDTH//2 - 120, 110), 
                   (WINDOW_WIDTH//2 + 120, 110), 2)
        
        # Resolução
        resolution_text = f"Resolução: {config.get('resolution_preset')}"
        draw_button(screen, resolution_toggle, resolution_text, font_button, resolution_toggle.collidepoint(mouse_pos))
        
        # Timer
        timer_text = font_text.render(f"Tempo por Jogador: {config.get('timer_minutes')} min", True, MENU_TEXT_COLOR)
        screen.blit(timer_text, (center_x - 120, 205))
        draw_button(screen, timer_minus, "-", font_button, timer_minus.collidepoint(mouse_pos))
        draw_button(screen, timer_plus, "+", font_button, timer_plus.collidepoint(mouse_pos))
        
        # Modo do timer
        timer_mode = config.get("timer_mode")
        mode_text = "Cronômetro" if timer_mode == "stopwatch" else "Contagem Regressiva"
        draw_button(screen, timer_mode_toggle, f"Modo: {mode_text}", font_button, timer_mode_toggle.collidepoint(mouse_pos))
        
        # Rotação automática
        rotation_text = "Rotação Auto: " + ("ON" if config.get("auto_rotate") else "OFF")
        draw_button(screen, rotation_toggle, rotation_text, font_button, rotation_toggle.collidepoint(mouse_pos))
        
        # Animação de rotação
        rotation_anim_text = "Animação Rot.: " + ("ON" if config.get("rotation_animation") else "OFF")
        draw_button(screen, rotation_anim_toggle, rotation_anim_text, font_button, rotation_anim_toggle.collidepoint(mouse_pos))
        
        # Mostrar timer
        timer_show_text = "Mostrar Timer: " + ("ON" if config.get("show_timer") else "OFF")
        draw_button(screen, timer_toggle, timer_show_text, font_button, timer_toggle.collidepoint(mouse_pos))
        
        # Botão voltar
        draw_button(screen, back_button, "VOLTAR", font_button, back_button.collidepoint(mouse_pos))
        
        p.display.flip()
        clock.tick(60)

def pawnPromotionPopup(screen, gs):
    # Get current screen size
    screen_width, screen_height = screen.get_size()
    
    # Create overlay
    overlay = p.Surface((screen_width, screen_height))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    
    font_title = p.font.SysFont("Arial", 28, True)
    font_label = p.font.SysFont("Arial", 16)
    
    # Create centered popup
    popup_width, popup_height = 500, 250
    popup_x = (screen_width - popup_width) // 2
    popup_y = (screen_height - popup_height) // 2
    
    popup_rect = p.Rect(popup_x, popup_y, popup_width, popup_height)
    
    # Create buttons for promotion choices with images
    button_size = 80
    button_spacing = 100
    start_x = popup_x + (popup_width - (4 * button_spacing - 20)) // 2
    button_y = popup_y + 100
    
    buttons = [
        p.Rect(start_x + i * button_spacing, button_y, button_size, button_size)
        for i in range(4)
    ]
    
    # Determine piece color based on whose turn it was BEFORE the move
    piece_color = 'w' if not gs.whiteToMove else 'b'  # Opposite of current turn
    
    button_pieces = [f"{piece_color}Q", f"{piece_color}R", f"{piece_color}B", f"{piece_color}N"]
    piece_names = ["Rainha", "Torre", "Bispo", "Cavalo"]

    while True:
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                mouse_pos = e.pos
                for i, button in enumerate(buttons):
                    if button.collidepoint(mouse_pos):
                        return ["Q", "R", "B", "N"][i]

        # Draw everything on the current screen without changing its size
        screen.blit(overlay, (0, 0))
        
        # Draw popup background
        shadow_rect = popup_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        p.draw.rect(screen, (10, 15, 25), shadow_rect, border_radius=15)
        p.draw.rect(screen, TIMER_BG_COLOR, popup_rect, border_radius=15)
        p.draw.rect(screen, MENU_ACCENT_COLOR, popup_rect, 3, border_radius=15)
        
        # Title
        title_text = font_title.render("Promoção do Peão", True, MENU_ACCENT_COLOR)
        title_rect = title_text.get_rect(center=(popup_x + popup_width//2, popup_y + 40))
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle = font_label.render("Escolha a peça para promoção:", True, MENU_TEXT_COLOR)
        subtitle_rect = subtitle.get_rect(center=(popup_x + popup_width//2, popup_y + 70))
        screen.blit(subtitle, subtitle_rect)

        # Draw buttons and pieces
        mouse_pos = p.mouse.get_pos()
        for i, (button, piece, name) in enumerate(zip(buttons, button_pieces, piece_names)):
            is_hovered = button.collidepoint(mouse_pos)
            
            # Button background
            button_color = MENU_BUTTON_HOVER_COLOR if is_hovered else MENU_BUTTON_COLOR
            shadow_button = button.copy()
            shadow_button.x += 2
            shadow_button.y += 2
            p.draw.rect(screen, (10, 15, 25), shadow_button, border_radius=8)
            p.draw.rect(screen, button_color, button, border_radius=8)
            border_color = MENU_ACCENT_COLOR if is_hovered else TIMER_BORDER_COLOR
            p.draw.rect(screen, border_color, button, 2, border_radius=8)
            
            # Draw piece image
            if piece in IMAGES:
                piece_img = p.transform.scale(IMAGES[piece], (button_size - 10, button_size - 10))
                img_rect = piece_img.get_rect(center=button.center)
                screen.blit(piece_img, img_rect)
            
            # Label below button
            label = font_label.render(name, True, MENU_TEXT_COLOR)
            label_rect = label.get_rect(center=(button.centerx, button.bottom + 15))
            screen.blit(label, label_rect)

        p.display.flip()

def showConfirmationDialog(screen, title, message):
    # Get current screen size
    screen_width, screen_height = screen.get_size()
    
    # Create overlay
    overlay = p.Surface((screen_width, screen_height))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    
    font_title = p.font.SysFont("Arial", 24, True)
    font_message = p.font.SysFont("Arial", 18)
    font_button = p.font.SysFont("Arial", 16, True)
    
    # Create centered popup
    popup_width, popup_height = 400, 200
    popup_x = (screen_width - popup_width) // 2
    popup_y = (screen_height - popup_height) // 2
    
    popup_rect = p.Rect(popup_x, popup_y, popup_width, popup_height)
    
    # Create buttons
    button_width, button_height = 80, 40
    yes_button = p.Rect(popup_x + 80, popup_y + 140, button_width, button_height)
    no_button = p.Rect(popup_x + 240, popup_y + 140, button_width, button_height)
    
    while True:
        for e in p.event.get():
            if e.type == p.QUIT:
                return False  # Don't quit game, just cancel
            elif e.type == p.KEYDOWN:
                if e.key == p.K_ESCAPE:
                    return False
                elif e.key == p.K_RETURN or e.key == p.K_r:
                    return True
                elif e.key == p.K_n:
                    return False
            elif e.type == p.MOUSEBUTTONDOWN:
                mouse_pos = e.pos
                if yes_button.collidepoint(mouse_pos):
                    return True
                elif no_button.collidepoint(mouse_pos):
                    return False
        
        # Draw everything on the current screen
        screen.blit(overlay, (0, 0))
        
        # Draw popup background
        shadow_rect = popup_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        p.draw.rect(screen, (10, 15, 25), shadow_rect, border_radius=15)
        p.draw.rect(screen, TIMER_BG_COLOR, popup_rect, border_radius=15)
        p.draw.rect(screen, MENU_ACCENT_COLOR, popup_rect, 3, border_radius=15)
        
        # Title
        title_text = font_title.render(title, True, MENU_ACCENT_COLOR)
        title_rect = title_text.get_rect(center=(popup_x + popup_width//2, popup_y + 40))
        screen.blit(title_text, title_rect)
        
        # Message
        message_text = font_message.render(message, True, MENU_TEXT_COLOR)
        message_rect = message_text.get_rect(center=(popup_x + popup_width//2, popup_y + 80))
        screen.blit(message_text, message_rect)
        
        # Instructions
        instructions = font_message.render("Pressione R para Sim, ESC para Não", True, (180, 180, 180))
        inst_rect = instructions.get_rect(center=(popup_x + popup_width//2, popup_y + 110))
        screen.blit(instructions, inst_rect)
        
        # Draw buttons
        mouse_pos = p.mouse.get_pos()
        
        # Yes button
        yes_hovered = yes_button.collidepoint(mouse_pos)
        yes_color = MENU_BUTTON_HOVER_COLOR if yes_hovered else MENU_BUTTON_COLOR
        shadow_yes = yes_button.copy()
        shadow_yes.x += 2
        shadow_yes.y += 2
        p.draw.rect(screen, (10, 15, 25), shadow_yes, border_radius=8)
        p.draw.rect(screen, yes_color, yes_button, border_radius=8)
        yes_border = MENU_ACCENT_COLOR if yes_hovered else TIMER_BORDER_COLOR
        p.draw.rect(screen, yes_border, yes_button, 2, border_radius=8)
        
        yes_text = font_button.render("SIM", True, MENU_TEXT_COLOR)
        yes_text_rect = yes_text.get_rect(center=yes_button.center)
        screen.blit(yes_text, yes_text_rect)
        
        # No button
        no_hovered = no_button.collidepoint(mouse_pos)
        no_color = MENU_BUTTON_HOVER_COLOR if no_hovered else MENU_BUTTON_COLOR
        shadow_no = no_button.copy()
        shadow_no.x += 2
        shadow_no.y += 2
        p.draw.rect(screen, (10, 15, 25), shadow_no, border_radius=8)
        p.draw.rect(screen, no_color, no_button, border_radius=8)
        no_border = MENU_ACCENT_COLOR if no_hovered else TIMER_BORDER_COLOR
        p.draw.rect(screen, no_border, no_button, 2, border_radius=8)
        
        no_text = font_button.render("NÃO", True, MENU_TEXT_COLOR)
        no_text_rect = no_text.get_rect(center=no_button.center)
        screen.blit(no_text, no_text_rect)
        
        p.display.flip()




def game_loop(screen, clock):
    # Recarregar configurações atualizadas
    global BOARD_WIDTH, BOARD_HEIGHT, SQ_SIZE, IMAGES, WINDOW_WIDTH, WINDOW_HEIGHT
    
    # Apply current resolution settings
    WINDOW_WIDTH = config.get("window_width")
    WINDOW_HEIGHT = config.get("window_height")
    BOARD_WIDTH = BOARD_HEIGHT = config.get("board_size")
    SQ_SIZE = BOARD_HEIGHT // DIMENSION
    
    # Recarregar imagens com novo tamanho
    loadImages()
    
    # Redimensionar tela com base nas configurações
    timer_width = 250 if config.get("show_timer") else 0
    captured_area_width = 200  # Área para peças capturadas
    total_width = BOARD_WIDTH + timer_width + captured_area_width
    
    # Centralizar o tabuleiro na tela (sem contar peças capturadas na centralização)
    board_offset_x = (WINDOW_WIDTH - BOARD_WIDTH - timer_width) // 2
    board_offset_y = (WINDOW_HEIGHT - BOARD_HEIGHT) // 2
    
    # Área das peças capturadas - agora no lado direito
    captured_offset_x = board_offset_x + BOARD_WIDTH + 20
    
    # Redimensionar janela se necessário (forçar redimensionamento)
    current_size = p.display.get_surface().get_size() if p.display.get_surface() else (0, 0)
    if current_size != (WINDOW_WIDTH, WINDOW_HEIGHT):
        screen = p.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), p.RESIZABLE)
    p.display.set_caption(f"Codduo - Xadrez [{config.get('resolution_preset')}]")
    
    # Creating gamestate object calling our constructor
    gs = GameState()
    if (gs.playerWantsToPlayAsBlack):
        gs.board = gs.board1
    
    # Timer do jogo
    timer_mode = config.get("timer_mode")
    game_timer = GameTimer(config.get("timer_minutes"), timer_mode)
    if config.get("show_timer"):
        game_timer.start_turn(gs.whiteToMove)
    
    # if a user makes a move we can ckeck if its in the list of valid moves
    validMoves = gs.getValidMoves()
    moveMade = False  # if user makes a valid moves and the gamestate changes then we should generate new set of valid move
    animate = False  # flag var for when we should animate a move
    running = True
    squareSelected = ()  # keep tracks of last click
    # clicking to own piece and location where to move[(6,6),(4,4)]
    playerClicks = []
    gameOver = False  # gameover if checkmate or stalemate
    moveUndone = False
    pieceCaptured = False
    positionHistory = ""
    previousPos = ""
    countMovesForDraw = 0
    COUNT_DRAW = 0
    board_rotated = False  # Track if board is currently rotated
    rotation_animation_active = False
    rotation_start_time = 0
    target_rotation = False
    
    # Listas para peças capturadas
    white_captured = []  # Peças brancas capturadas pelo preto
    black_captured = []  # Peças pretas capturadas pelo branco
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # Mouse Handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and not rotation_animation_active:  # allow mouse handling only if its not game over and not rotating
                    location = p.mouse.get_pos()
                    # Adjust for board offset
                    adjusted_x = location[0] - board_offset_x
                    adjusted_y = location[1] - board_offset_y
                    
                    if adjusted_x >= 0 and adjusted_y >= 0:
                        clicked_col = adjusted_x // SQ_SIZE
                        clicked_row = adjusted_y // SQ_SIZE
                        
                        # Convert clicked coordinates back to board coordinates if rotated
                        if board_rotated:
                            row = 7 - clicked_row
                            col = 7 - clicked_col
                        else:
                            row = clicked_row
                            col = clicked_col
                        
                        # if user clicked on same square twice or user click outside board
                        if squareSelected == (row, col) or clicked_col >= 8 or clicked_row >= 8:
                            squareSelected = ()  # deselect
                            playerClicks = []  # clear player clicks
                        else:
                            squareSelected = (row, col)
                            # append player both clicks (place and destination)
                            playerClicks.append(squareSelected)
                    # after second click (at destination)
                    if len(playerClicks) == 2:
                        # user generated a move
                        move = Move(playerClicks[0], playerClicks[1], gs.board)
                        for i in range(len(validMoves)):
                            # check if the move is in the validMoves
                            if move == validMoves[i]:
                                # Check if a piece is captured at the destination square
                                captured_piece = gs.board[validMoves[i].endRow][validMoves[i].endCol]
                                if captured_piece != '--':
                                    pieceCaptured = True
                                    # Add captured piece to appropriate list
                                    if captured_piece[0] == 'w':  # White piece captured
                                        white_captured.append(captured_piece)
                                    else:  # Black piece captured
                                        black_captured.append(captured_piece)
                                
                                # Check for en passant capture
                                if validMoves[i].isEnpassantMove:
                                    # En passant capture - the captured pawn is not at the end square
                                    enpassant_row = validMoves[i].endRow + (1 if validMoves[i].pieceMoved[0] == 'b' else -1)
                                    captured_piece = gs.board[enpassant_row][validMoves[i].endCol]
                                    if captured_piece != '--':
                                        if captured_piece[0] == 'w':
                                            white_captured.append(captured_piece)
                                        else:
                                            black_captured.append(captured_piece)
                                
                                gs.makeMove(validMoves[i])
                                if (move.isPawnPromotion):
                                    # Show pawn promotion popup and get the selected piece
                                    promotion_choice = pawnPromotionPopup(
                                        screen, gs)
                                    # Set the promoted piece on the board
                                    gs.board[move.endRow][move.endCol] = move.pieceMoved[0] + \
                                        promotion_choice
                                    promote_sound.play()
                                    pieceCaptured = False
                                # add sound for human move
                                if (pieceCaptured or move.isEnpassantMove):
                                    # Play capture sound
                                    capture_sound.play()
                                    # print("capture sound")
                                elif not move.isPawnPromotion:
                                    # Play move sound
                                    move_sound.play()
                                    # print("move sound")
                                pieceCaptured = False
                                moveMade = True
                                animate = True
                                squareSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [squareSelected]

            # Key Handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo when z is pressed
                    gs.undoMove()
                    # when user undo move valid move change, here we could use [ validMoves = gs.getValidMoves() ] which would update the current validMoves after undo
                    moveMade = True
                    animate = False
                    gameOver = False
                    moveUndone = True
                if e.key == p.K_r:  # reset board when 'r' is pressed
                    # Show confirmation dialog
                    confirmed = showConfirmationDialog(screen, "Reiniciar Jogo", "Deseja realmente reiniciar a partida?")
                    if confirmed:
                        gs = GameState()
                        validMoves = gs.getValidMoves()
                        squareSelected = ()
                        playerClicks = []
                        moveMade = False
                        animate = False
                        gameOver = False
                        moveUndone = True
                        board_rotated = False
                        rotation_animation_active = False
                        # Reset captured pieces
                        white_captured.clear()
                        black_captured.clear()
                        if config.get("show_timer"):
                            timer_mode = config.get("timer_mode")
                            game_timer = GameTimer(config.get("timer_minutes"), timer_mode)
                            game_timer.start_turn(gs.whiteToMove)
                if e.key == p.K_ESCAPE:  # Voltar ao menu
                    return "menu"


        if moveMade:
            # Update timer
            if config.get("show_timer"):
                game_timer.start_turn(gs.whiteToMove)
                
            # Auto-rotate board if enabled
            if config.get("auto_rotate"):
                new_rotation = not gs.whiteToMove  # Black's turn = rotated
                if new_rotation != board_rotated:
                    if config.get("rotation_animation"):
                        # Start rotation animation
                        rotation_animation_active = True
                        rotation_start_time = time.time()
                        target_rotation = new_rotation
                    else:
                        # Instant rotation
                        board_rotated = new_rotation
                
            if countMovesForDraw == 0 or countMovesForDraw == 1 or countMovesForDraw == 2 or countMovesForDraw == 3:
                countMovesForDraw += 1
            if countMovesForDraw == 4:
                positionHistory += gs.getBoardString()
                if previousPos == positionHistory:
                    COUNT_DRAW += 1
                    positionHistory = ""
                    countMovesForDraw = 0
                else:
                    previousPos = positionHistory
                    positionHistory = ""
                    countMovesForDraw = 0
                    COUNT_DRAW = 0
            # Call animateMove to animate the move
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock, board_rotated)
            # genetare new set of valid move if valid move is made
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        # Update rotation animation
        if rotation_animation_active:
            elapsed = time.time() - rotation_start_time
            rotation_duration = config.get("rotation_speed")
            if elapsed >= rotation_duration:
                # Animation complete
                rotation_animation_active = False
                board_rotated = target_rotation
            
        # Check timer
        if config.get("show_timer") and game_timer.is_time_up(gs.whiteToMove):
            gameOver = True
            winner = "Black" if gs.whiteToMove else "White"
            text = f'{winner} wins by time!'
            drawEndGameText(screen, text)

        # Calculate current rotation for animation
        current_rotation = board_rotated
        if rotation_animation_active:
            elapsed = time.time() - rotation_start_time
            rotation_duration = config.get("rotation_speed")
            progress = min(elapsed / rotation_duration, 1.0)
            # Simple flip animation (could be enhanced with smooth rotation)
            if progress > 0.5:
                current_rotation = target_rotation
                
        drawGameState(screen, gs, validMoves, squareSelected, current_rotation, 
                     game_timer if config.get("show_timer") else None, 
                     board_offset_x, board_offset_y, white_captured, black_captured, captured_offset_x)

        if COUNT_DRAW == 1:
            gameOver = True
            text = 'Draw due to repetition'
            drawEndGameText(screen, text)
        if gs.stalemate:
            gameOver = True
            text = 'Stalemate'
            drawEndGameText(screen, text)
        elif gs.checkmate:
            gameOver = True
            text = 'Black wins by checkmate' if gs.whiteToMove else 'White wins by checkmate'
            drawEndGameText(screen, text)

        clock.tick(MAX_FPS)
        p.display.flip()


def drawGameState(screen, gs, validMoves, squareSelected, board_rotated=False, timer=None, offset_x=0, offset_y=0, white_captured=None, black_captured=None, captured_offset_x=0):
    # Fill background with elegant dark color
    screen.fill(GAME_BG_COLOR)
    
    # Adicionar sombra ao tabuleiro
    shadow_rect = p.Rect(offset_x + 4, offset_y + 4, BOARD_WIDTH, BOARD_HEIGHT)
    p.draw.rect(screen, (10, 15, 20), shadow_rect, border_radius=8)
    
    # Borda elegante do tabuleiro
    board_rect = p.Rect(offset_x - 2, offset_y - 2, BOARD_WIDTH + 4, BOARD_HEIGHT + 4)
    p.draw.rect(screen, TIMER_BORDER_COLOR, board_rect, border_radius=8)
    
    drawSquare(screen, board_rotated, offset_x, offset_y)  # draw square on board
    highlightSquares(screen, gs, validMoves, squareSelected, board_rotated, offset_x, offset_y)
    drawPieces(screen, gs.board, board_rotated, offset_x, offset_y)
    
    # Draw captured pieces
    if white_captured is not None and black_captured is not None:
        drawCapturedPieces(screen, white_captured, black_captured, captured_offset_x, offset_y, board_rotated)
    
    if timer:
        drawTimer(screen, timer, gs.whiteToMove, offset_x, offset_y)
    
    # Draw instructions at bottom
    font_instructions = p.font.SysFont("Arial", 14)
    instructions = "R = Reiniciar  |  Z = Desfazer  |  ESC = Menu"
    inst_text = font_instructions.render(instructions, True, (120, 130, 150))
    screen.blit(inst_text, (10, screen.get_height() - 25))


def drawSquare(screen, board_rotated=False, offset_x=0, offset_y=0):
    global colors
    colors = [p.Color(LIGHT_SQUARE_COLOR), p.Color(DARK_SQUARE_COLOR)]
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            # Rotate coordinates if board is rotated
            if board_rotated:
                display_row = 7 - row
                display_col = 7 - col
            else:
                display_row = row
                display_col = col
                
            color = colors[((row + col) % 2)]
            p.draw.rect(screen, color, p.Rect(
                offset_x + display_col * SQ_SIZE, offset_y + display_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def highlightSquares(screen, gs, validMoves, squareSelected, board_rotated=False, offset_x=0, offset_y=0):
    if squareSelected != ():  # make sure there is a square to select
        row, col = squareSelected
        # make sure they click there own piece
        if gs.board[row][col][0] == ('w' if gs.whiteToMove else 'b'):
            # highlight selected piece square
            # Surface in pygame used to add images or transperency feature
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            # set_alpha --> transperancy value (0 transparent)
            s.set_alpha(100)
            s.fill(p.Color(MOVE_HIGHLIGHT_COLOR))
            
            # Rotate coordinates if board is rotated
            if board_rotated:
                display_row = 7 - row
                display_col = 7 - col
            else:
                display_row = row
                display_col = col
            
            screen.blit(s, (offset_x + display_col*SQ_SIZE, offset_y + display_row*SQ_SIZE))
            
            # highlighting valid square
            s.fill(p.Color(POSSIBLE_MOVE_COLOR))
            for move in validMoves:
                if move.startRow == row and move.startCol == col:
                    if board_rotated:
                        end_display_row = 7 - move.endRow
                        end_display_col = 7 - move.endCol
                    else:
                        end_display_row = move.endRow
                        end_display_col = move.endCol
                    screen.blit(s, (offset_x + end_display_col*SQ_SIZE, offset_y + end_display_row*SQ_SIZE))


def drawPieces(screen, board, board_rotated=False, offset_x=0, offset_y=0):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                # Rotate coordinates if board is rotated
                if board_rotated:
                    display_row = 7 - row
                    display_col = 7 - col
                else:
                    display_row = row
                    display_col = col
                    
                screen.blit(IMAGES[piece], p.Rect(
                    offset_x + display_col * SQ_SIZE, offset_y + display_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawCapturedPieces(screen, white_captured, black_captured, captured_x, board_y, board_rotated):
    if captured_x < 0 or not white_captured and not black_captured:
        return  # Don't draw if position is invalid or no pieces captured
        
    font = p.font.SysFont("Arial", 16, True)
    small_piece_size = 35  # Tamanho menor para peças capturadas
    
    # Área para peças capturadas
    captured_width = 170
    captured_height = BOARD_HEIGHT
    
    # Verificar se há espaço suficiente
    if captured_x < 10:
        captured_x = 10
    
    # Background para área de peças capturadas
    captured_rect = p.Rect(captured_x, board_y, captured_width, captured_height)
    shadow_rect = p.Rect(captured_x + 2, board_y + 2, captured_width, captured_height)
    
    # Sombra
    p.draw.rect(screen, (10, 15, 20), shadow_rect, border_radius=8)
    # Fundo principal
    p.draw.rect(screen, TIMER_BG_COLOR, captured_rect, border_radius=8)
    p.draw.rect(screen, TIMER_BORDER_COLOR, captured_rect, 2, border_radius=8)
    
    # Título da seção
    title_text = font.render("Capturadas", True, MENU_ACCENT_COLOR)
    screen.blit(title_text, (captured_x + 8, board_y + 8))
    
    # Dividir em duas áreas: superior e inferior
    mid_y = board_y + captured_height // 2
    
    # Determinar qual lado é qual baseado na rotação
    if board_rotated:
        # Quando rotacionado, branco fica em cima
        white_area_y = board_y + 35
        black_area_y = mid_y + 10
        white_label = "Suas"
        black_label = "Oponente"
    else:
        # Normal, preto em cima
        black_area_y = board_y + 35
        white_area_y = mid_y + 10
        white_label = "Oponente"
        black_label = "Suas"
    
    # Labels
    small_font = p.font.SysFont("Arial", 12)
    
    # Only show labels if there are captured pieces
    if black_captured:
        black_text = small_font.render(black_label, True, MENU_TEXT_COLOR)
        screen.blit(black_text, (captured_x + 8, black_area_y - 18))
    
    if white_captured:
        white_text = small_font.render(white_label, True, MENU_TEXT_COLOR)
        screen.blit(white_text, (captured_x + 8, white_area_y - 18))
    
    # Desenhar peças pretas capturadas (capturadas pelo branco)
    for i, piece in enumerate(black_captured):
        if i >= 16:  # Limit to avoid overflow
            break
        row = i // 4
        col = i % 4
        piece_x = captured_x + 8 + col * (small_piece_size + 3)
        piece_y = black_area_y + row * (small_piece_size + 3)
        
        # Verificar se a peça cabe na área
        if piece_y + small_piece_size <= mid_y - 5:
            if piece in IMAGES:
                piece_img = p.transform.scale(IMAGES[piece], (small_piece_size, small_piece_size))
                screen.blit(piece_img, (piece_x, piece_y))
    
    # Desenhar peças brancas capturadas (capturadas pelo preto)
    for i, piece in enumerate(white_captured):
        if i >= 16:  # Limit to avoid overflow
            break
        row = i // 4
        col = i % 4
        piece_x = captured_x + 8 + col * (small_piece_size + 3)
        piece_y = white_area_y + row * (small_piece_size + 3)
        
        # Verificar se a peça cabe na área
        if piece_y + small_piece_size <= board_y + captured_height - 5:
            if piece in IMAGES:
                piece_img = p.transform.scale(IMAGES[piece], (small_piece_size, small_piece_size))
                screen.blit(piece_img, (piece_x, piece_y))

def drawTimer(screen, timer, is_white_turn, offset_x=0, offset_y=0):
    font = p.font.SysFont("Arial", 24, True)
    small_font = p.font.SysFont("Arial", 16)
    
    white_time, black_time = timer.get_current_times(is_white_turn)
    
    # Convert seconds to minutes:seconds format
    white_minutes = int(white_time // 60)
    white_seconds = int(white_time % 60)
    black_minutes = int(black_time // 60)
    black_seconds = int(black_time % 60)
    
    # Timer display based on mode
    if timer.mode == "countdown":
        white_text = f"Branco: {white_minutes:02d}:{white_seconds:02d}"
        black_text = f"Preto: {black_minutes:02d}:{black_seconds:02d}"
        mode_text = "Contagem Regressiva"
    else:
        white_text = f"Branco: {white_minutes:02d}:{white_seconds:02d}"
        black_text = f"Preto: {black_minutes:02d}:{black_seconds:02d}"
        mode_text = "Cronômetro"
    
    # Timer panel area - posicionar após peças capturadas
    timer_x = offset_x + BOARD_WIDTH + 200 + 40  # Board + captured area + spacing
    timer_width = 220
    
    # Sombra do timer
    shadow_timer_rect = p.Rect(timer_x + 3, offset_y + 53, timer_width, 200)
    p.draw.rect(screen, (10, 15, 20), shadow_timer_rect, border_radius=12)
    
    # Background elegante para timer
    timer_rect = p.Rect(timer_x, offset_y + 50, timer_width, 200)
    p.draw.rect(screen, TIMER_BG_COLOR, timer_rect, border_radius=12)
    p.draw.rect(screen, TIMER_BORDER_COLOR, timer_rect, 2, border_radius=12)
    
    # Mode indicator
    mode_surface = small_font.render(mode_text, True, MENU_ACCENT_COLOR)
    screen.blit(mode_surface, (timer_x + 10, offset_y + 60))
    
    # Warning for countdown mode
    warning_colors = timer.mode == "countdown" and (white_time <= 30 or black_time <= 30)
    
    # White timer
    white_color = MENU_TEXT_COLOR if is_white_turn else (150, 155, 165)
    if timer.mode == "countdown" and white_time <= 30:
        white_color = (255, 120, 120)
    
    white_surface = font.render(white_text, True, white_color)
    screen.blit(white_surface, (timer_x + 10, offset_y + 180))
    
    # Black timer
    black_color = MENU_TEXT_COLOR if not is_white_turn else (150, 155, 165)
    if timer.mode == "countdown" and black_time <= 30:
        black_color = (255, 120, 120)
    
    black_surface = font.render(black_text, True, black_color)
    screen.blit(black_surface, (timer_x + 10, offset_y + 100))
    
    # Current turn indicator
    turn_text = "Vez do: " + ("Branco" if is_white_turn else "Preto")
    turn_surface = font.render(turn_text, True, MENU_ACCENT_COLOR)
    screen.blit(turn_surface, (timer_x + 10, offset_y + 220))




# animating a move
def animateMove(move, screen, board, clock, board_rotated=False):
    global colors
    # change in row, col
    deltaRow = move.endRow - move.startRow
    deltaCol = move.endCol - move.startCol
    framesPerSquare = 5  # frames move one square
    # how many frame the animation will take
    frameCount = (abs(deltaRow) + abs(deltaCol)) * framesPerSquare
    # generate all the coordinates
    for frame in range(frameCount + 1):
        # how much does the row and col move by
        row, col = ((move.startRow + deltaRow*frame/frameCount, move.startCol +
                    deltaCol*frame/frameCount))  # how far through the animation
        
        # Rotate coordinates if board is rotated
        if board_rotated:
            display_row = 7 - row
            display_col = 7 - col
            end_display_row = 7 - move.endRow
            end_display_col = 7 - move.endCol
        else:
            display_row = row
            display_col = col
            end_display_row = move.endRow
            end_display_col = move.endCol
            
        # for each frame draw the moved piece
        drawSquare(screen, board_rotated)
        drawPieces(screen, board, board_rotated)

        # erase the piece moved from its ending squares
        color = colors[(move.endRow + move.endCol) %
                       2]  # get color of the square
        endSquare = p.Rect(end_display_col*SQ_SIZE, end_display_row *
                           SQ_SIZE, SQ_SIZE, SQ_SIZE)  # pygame rectangle
        p.draw.rect(screen, color, endSquare)

        # draw the captured piece back
        if move.pieceCaptured != '--':
            if move.isEnpassantMove:
                enPassantRow = move.endRow + \
                    1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
                if board_rotated:
                    enPassant_display_row = 7 - enPassantRow
                    enPassant_display_col = 7 - move.endCol
                else:
                    enPassant_display_row = enPassantRow
                    enPassant_display_col = move.endCol
                endSquare = p.Rect(enPassant_display_col*SQ_SIZE, enPassant_display_row *
                                   SQ_SIZE, SQ_SIZE, SQ_SIZE)  # pygame rectangle
            screen.blit(IMAGES[move.pieceCaptured], endSquare)

        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(
            display_col*SQ_SIZE, display_row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

        p.display.flip()
        clock.tick(240)


def drawEndGameText(screen, text):
    # create font object with type and size of font you want
    font = p.font.SysFont("Times New Roman", 30, False, False)
    # use the above font and render text (0 ? antialias)
    textObject = font.render(text, True, p.Color('black'))

    # Get the width and height of the textObject
    text_width = textObject.get_width()
    text_height = textObject.get_height()

    # Calculate the position to center the text on the screen
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
        BOARD_WIDTH/2 - text_width/2, BOARD_HEIGHT/2 - text_height/2)

    # Blit the textObject onto the screen at the calculated position
    screen.blit(textObject, textLocation)

    # Create a second rendering of the text with a slight offset for a shadow effect
    textObject = font.render(text, 0, p.Color('Black'))
    screen.blit(textObject, textLocation.move(1, 1))


def main():
    # initialize pygame
    p.init()
    p.display.set_caption("Codduo - Xadrez")
    
    # Create main window with resizable flag
    screen = p.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), p.RESIZABLE)
    clock = p.time.Clock()
    
    while True:
        # Show main menu
        menu_choice = show_main_menu(screen)
        
        if menu_choice == "start":
            # Start game loop
            result = game_loop(screen, clock)
            if result == "menu":
                continue  # Go back to menu
        elif menu_choice == "config":
            # Show config menu
            show_config_menu(screen)

# if we import main then main function wont run it will run only while running this file
if __name__ == "__main__":
    main()
