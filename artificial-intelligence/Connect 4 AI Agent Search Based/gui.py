import pygame
import sys
import math
import random
import time
import multiprocessing
from game import (
    create_board, drop_piece, get_next_open_row, get_valid_locations, 
    is_terminal_node, check_final_score, 
    ROW_COUNT, COL_COUNT, AI_PIECE, HUMAN_PIECE, EMPTY
)
from ai_agent import find_best_move, get_probabilities

# ==============================================================================
#   ⚙️ GAME CONFIGURATION
# ==============================================================================
DEFAULT_SEARCH_DEPTH = 5
DEFAULT_VIZ_DEPTH = 3
DEFAULT_ALGO = 'MINIMAX_ALPHA_BETA'
DEFAULT_STARTER = HUMAN_PIECE

# ==============================================================================
#   🎨 VISUAL CONFIGURATION: CLASSIC COLORS x MODERN AESTHETIC
# ==============================================================================
VISUAL_CONFIG = {
    # --- DIMENSIONS ---
    'SQUARESIZE': 100,
    'TREE_PANEL_WIDTH': 900,
    'PIECE_PADDING': 10,
    
    # --- MAIN THEME (Deep Slate / Dark Mode) ---
    'BG_COLOR': (15, 23, 35),       # Dark Slate Blue Background (Not pure black)
    'TEXT_WHITE': (240, 248, 255),  # Alice Blue
    'TEXT_GRAY': (148, 163, 184),   # Slate Gray
    'TRANSPARENT_KEY': (255, 0, 255), 

    # --- BOARD VISUALS (Classic Blue, but Electric) ---
    'BOARD': {
        'COLOR_DARK': (0, 60, 180),     # Deep Classic Blue
        'COLOR_LIGHT': (0, 90, 255),    # Electric Blue
        'BORDER_WIDTH': 0,
        'SHADOW_COLOR': (0, 20, 80),
        'RIM_HIGHLIGHT': (80, 200, 255), # Cyan Glow on edges
        'RIM_SHADOW': (0, 40, 140),
    },

    # --- PIECE COLORS (Classic Red & Yellow, High Gloss) ---
    'HUMAN_PIECE': {
        'MAIN': (220, 20, 60),       # Crimson / Cherry Red
        'EDGE': (100, 0, 20),        # Dark Maroon Edge
        'HIGHLIGHT': (255, 100, 100),# Soft Pinkish Highlight
    },
    'AI_PIECE': {
        'MAIN': (255, 215, 0),       # Golden Yellow
        'EDGE': (184, 134, 11),      # Dark Gold Edge
        'HIGHLIGHT': (255, 255, 180),# Pale Yellow Highlight
    },

    # --- TREE VISUALIZATION (Matching the Pieces) ---
    'TREE': {
        'BG_COLOR': (15, 20, 30),        # Very Dark Blue-Grey
        'LINE_COLOR': (80, 90, 110),     # Steel Grey
        'LINE_WIDTH': 1,
        'VERTICAL_SPACING': 85,
        
        'NODE_SIZE': 22,
        'COLOR_MAX': (255, 215, 0),      # AI = Yellow
        'COLOR_MIN': (220, 20, 60),      # Human = Red
        'COLOR_PRUNED': (60, 60, 70),    # Dark Grey
        'BORDER_COLOR': (255, 255, 255),
        
        'TEXT_SCORE_COLOR': (255, 255, 255),
        'TEXT_METADATA_COLOR': (150, 150, 150),
    },

    # --- UI BUTTONS (Clean & Flat) ---
    'UI': {
        'BTN_DEFAULT': (30, 50, 80),     # Dark Blue Button
        'BTN_HOVER': (0, 120, 215),      # Windows Blue
        'BTN_SELECTED': (0, 180, 100),   # Success Green
        'BTN_TEXT_DEFAULT': (230, 230, 230),
        'BTN_TEXT_HOVER': (255, 255, 255),
    }
}

# ==============================================================================
#   CALCULATED CONSTANTS & ALIASES
# ==============================================================================
RADIUS = int(VISUAL_CONFIG['SQUARESIZE'] / 2 - VISUAL_CONFIG['PIECE_PADDING'])
GAME_WIDTH = COL_COUNT * VISUAL_CONFIG['SQUARESIZE']
WIDTH = GAME_WIDTH 
HEIGHT = (ROW_COUNT + 1) * VISUAL_CONFIG['SQUARESIZE']
TREE_WIDTH = VISUAL_CONFIG['TREE_PANEL_WIDTH'] 
SIZE = (GAME_WIDTH, HEIGHT)

BLACK = VISUAL_CONFIG['BG_COLOR']
WHITE = VISUAL_CONFIG['TEXT_WHITE']
TRANSPARENT_KEY = VISUAL_CONFIG['TRANSPARENT_KEY']

# --- PYGAME GLOBALS ---
font_small = None
font_medium = None
font_large = None
font_tiny = None
board_overlay = None
main_screen = None

# --- TREE VISUALIZER PROCESS ---
class TreeState:
    def __init__(self):
        self.nodes = {}
        self.reset()
        
    def reset(self):
        self.nodes = {}
        
    def update_node(self, data):
        nid = data['id']
        if nid not in self.nodes:
            self.nodes[nid] = {
                'id': nid,
                'parent': ".".join(nid.split(".")[:-1]) if "." in nid else None,
                'level': data.get('level', 0),
                'type': 'MAX' if data.get('maximizing') else 'MIN',
                'score': None,
                'alpha': data.get('alpha', '-inf'),
                'beta': data.get('beta', '+inf'),
                'pruned': False,
                'children': []
            }
            pid = self.nodes[nid]['parent']
            if pid and pid in self.nodes:
                if nid not in self.nodes[pid]['children']:
                    self.nodes[pid]['children'].append(nid)
        
        node = self.nodes[nid]
        if 'score' in data: node['score'] = data['score']
        if 'alpha' in data: node['alpha'] = data['alpha']
        if 'beta' in data: node['beta'] = data['beta']
        if data.get('type') == 'prune': node['pruned'] = True

def draw_tree_recursive(surface, state, node_id, x, y, width_alloc, font):
    if node_id not in state.nodes: return
    node = state.nodes[node_id]
    
    cfg = VISUAL_CONFIG['TREE']
    node_size = cfg['NODE_SIZE']

    # Draw Lines First
    if node['children']:
        child_y = y + cfg['VERTICAL_SPACING']
        step = width_alloc / max(len(node['children']), 1)
        start_x = x - (width_alloc / 2) + (step / 2)
        
        for i, child_id in enumerate(node['children']):
            child_x = start_x + i * step
            pygame.draw.aaline(surface, cfg['LINE_COLOR'], (x, y + node_size), (child_x, child_y - node_size))
            draw_tree_recursive(surface, state, child_id, child_x, child_y, step, font)

    # Determine Node Color
    color = cfg['COLOR_MAX'] if node['type'] == 'MAX' else cfg['COLOR_MIN']
    if node['pruned']: color = cfg['COLOR_PRUNED']
    
    # Draw Shape (Triangle vs Inverted Triangle)
    if node['type'] == 'MAX':
        points = [(x, y - node_size), (x - node_size, y + node_size), (x + node_size, y + node_size)]
    else:
        points = [(x - node_size, y - node_size), (x + node_size, y - node_size), (x, y + node_size)]
    
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (200,200,200), points, 1) # Soft border
    
    # Draw Score
    if node['score'] is not None:
        s_txt = str(node['score'])
        if len(s_txt) > 5: s_txt = "Win" if float(s_txt)>0 else "Loss"
        
        lbl = font.render(s_txt, True, cfg['TEXT_SCORE_COLOR'])
        text_y = y - node_size - 15 if node['type'] == 'MAX' else y + node_size + 5
        surface.blit(lbl, (x - lbl.get_width()//2, text_y))

def tree_process_main(queue):
    pygame.init()
    w, h = VISUAL_CONFIG['TREE_PANEL_WIDTH'], HEIGHT
    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    pygame.display.set_caption("Minimax Tree Visualization")
    
    t_font = pygame.font.SysFont("consolas", 14, bold=True)
    state = TreeState()
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                w, h = event.w, event.h
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)

        try:
            while not queue.empty():
                msg = queue.get_nowait()
                if msg == "RESET": state.reset()
                elif msg == "QUIT": running = False
                else: state.update_node(msg)
        except: pass

        screen.fill(VISUAL_CONFIG['TREE']['BG_COLOR'])
        if 'root' in state.nodes:
            draw_tree_recursive(screen, state, 'root', w//2, 50, w * 0.95, t_font)
            
        pygame.display.update()
        clock.tick(30)
    
    pygame.quit()
    sys.exit()

# --- UI CLASSES ---
class Button:
    def __init__(self, x, y, w, h, text, callback, val=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.val = val
        self.hovered = False
        self.selected = False

    def draw(self, surface):
        cfg = VISUAL_CONFIG['UI']
        
        if self.selected:
            fill_color = cfg['BTN_SELECTED']
            txt_color = (255, 255, 255)
            border_color = (255,255,255)
        elif self.hovered:
            fill_color = cfg['BTN_HOVER']
            txt_color = cfg['BTN_TEXT_HOVER']
            border_color = cfg['BTN_HOVER']
        else:
            fill_color = cfg['BTN_DEFAULT']
            txt_color = cfg['BTN_TEXT_DEFAULT']
            border_color = (60, 70, 90)

        pygame.draw.rect(surface, fill_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)
        
        lbl = font_small.render(self.text, True, txt_color)
        surface.blit(lbl, (self.rect.centerx - lbl.get_width()//2, self.rect.centery - lbl.get_height()//2))

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def handle_click(self):
        if self.hovered:
            if self.val is not None: return self.callback(self.val)
            return self.callback()
        return None

# --- CONFIG ---
config = {
    'algo': DEFAULT_ALGO,
    'depth': DEFAULT_SEARCH_DEPTH,
    'gui_depth': DEFAULT_VIZ_DEPTH,
    'starter': DEFAULT_STARTER
}

def set_algo(val): config['algo'] = val
def set_starter(val): config['starter'] = val
def inc_depth(): config['depth'] = min(7, config['depth'] + 1)
def dec_depth(): config['depth'] = max(1, config['depth'] - 1)
def inc_gui_depth(): config['gui_depth'] = min(7, config['gui_depth'] + 1)
def dec_gui_depth(): config['gui_depth'] = max(1, config['gui_depth'] - 1)

# --- GRAPHICS HELPERS ---
def create_board_overlay():
    overlay = pygame.Surface((GAME_WIDTH, HEIGHT - VISUAL_CONFIG['SQUARESIZE']))
    cfg_b = VISUAL_CONFIG['BOARD']
    
    # Vertical Gradient for the Board
    for y in range(HEIGHT - VISUAL_CONFIG['SQUARESIZE']):
        ratio = y / (HEIGHT - VISUAL_CONFIG['SQUARESIZE'])
        c1 = cfg_b['COLOR_LIGHT']
        c2 = cfg_b['COLOR_DARK']
        r = int(c1[0] * (1-ratio) + c2[0] * ratio)
        g = int(c1[1] * (1-ratio) + c2[1] * ratio)
        b = int(c1[2] * (1-ratio) + c2[2] * ratio)
        pygame.draw.line(overlay, (r, g, b), (0, y), (GAME_WIDTH, y))
    
    key = VISUAL_CONFIG['TRANSPARENT_KEY']
    for c in range(COL_COUNT):
        for r in range(ROW_COUNT):
            cx = int(c * VISUAL_CONFIG['SQUARESIZE'] + VISUAL_CONFIG['SQUARESIZE'] / 2)
            cy = int(r * VISUAL_CONFIG['SQUARESIZE'] + VISUAL_CONFIG['SQUARESIZE'] / 2)
            
            # Cyan/Blue Neon Ring around the holes
            pygame.draw.circle(overlay, cfg_b['RIM_HIGHLIGHT'], (cx, cy), RADIUS + 2)
            pygame.draw.circle(overlay, cfg_b['RIM_SHADOW'], (cx, cy), RADIUS + 1)
            # The Hole itself
            pygame.draw.circle(overlay, key, (cx, cy), RADIUS)
    
    overlay.set_colorkey(key)
    return overlay

def draw_piece_3d(surface, x, y, piece_type):
    if piece_type == HUMAN_PIECE:
        p_cfg = VISUAL_CONFIG['HUMAN_PIECE']
    else:
        p_cfg = VISUAL_CONFIG['AI_PIECE']

    # 1. Edge
    pygame.draw.circle(surface, p_cfg['EDGE'], (x, y), RADIUS)
    
    # 2. Main Body
    pygame.draw.circle(surface, p_cfg['MAIN'], (x, y), RADIUS - 3)
    
    # 3. Specular Highlight (Gloss)
    pygame.draw.ellipse(surface, p_cfg['HIGHLIGHT'], 
                       (x - RADIUS//2, y - RADIUS//1.8, RADIUS, RADIUS//1.5))

def draw_static_pieces(board):
    for c in range(COL_COUNT):
        for r in range(ROW_COUNT):
            if board[r][c] != EMPTY:
                cx = int(c * VISUAL_CONFIG['SQUARESIZE'] + VISUAL_CONFIG['SQUARESIZE'] / 2)
                cy = int((r + 1) * VISUAL_CONFIG['SQUARESIZE'] + VISUAL_CONFIG['SQUARESIZE'] / 2)
                draw_piece_3d(main_screen, cx, cy, board[r][c])

def render_game_frame(board, show_phantom_col=None, phantom_piece=None, turn_msg=""):
    global board_overlay
    if board_overlay is None: board_overlay = create_board_overlay()
    
    pygame.draw.rect(main_screen, VISUAL_CONFIG['BG_COLOR'], (0, 0, GAME_WIDTH, HEIGHT))
    
    if show_phantom_col is not None and phantom_piece is not None:
        px = int(show_phantom_col * VISUAL_CONFIG['SQUARESIZE'] + VISUAL_CONFIG['SQUARESIZE'] / 2)
        py = int(VISUAL_CONFIG['SQUARESIZE'] / 2)
        draw_piece_3d(main_screen, px, py, phantom_piece)

    if turn_msg:
        color = VISUAL_CONFIG['HUMAN_PIECE']['MAIN'] if "YOUR" in turn_msg else VISUAL_CONFIG['AI_PIECE']['MAIN']
        # Shadow
        lbl_s = font_medium.render(turn_msg, True, (0,0,0))
        main_screen.blit(lbl_s, (GAME_WIDTH//2 - lbl_s.get_width()//2 + 2, 27))
        
        lbl = font_medium.render(turn_msg, True, color)
        main_screen.blit(lbl, (GAME_WIDTH//2 - lbl.get_width()//2, 25))
        
    draw_static_pieces(board)
    main_screen.blit(board_overlay, (0, VISUAL_CONFIG['SQUARESIZE']))
    pygame.display.update()

def animate_drop(board, col, row, piece):
    global board_overlay
    if board_overlay is None: board_overlay = create_board_overlay()
    visual_x = int(col * VISUAL_CONFIG['SQUARESIZE'] + VISUAL_CONFIG['SQUARESIZE'] / 2)
    target_y = int((row + 1) * VISUAL_CONFIG['SQUARESIZE'] + VISUAL_CONFIG['SQUARESIZE'] / 2)
    y_pos = int(VISUAL_CONFIG['SQUARESIZE'] / 2)
    speed = 0
    gravity = 2.5
    while y_pos < target_y:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
        speed += gravity
        y_pos += speed
        if y_pos > target_y: y_pos = target_y
        
        pygame.draw.rect(main_screen, VISUAL_CONFIG['BG_COLOR'], (0, 0, GAME_WIDTH, HEIGHT))
        draw_static_pieces(board)
        draw_piece_3d(main_screen, visual_x, y_pos, piece)
        main_screen.blit(board_overlay, (0, VISUAL_CONFIG['SQUARESIZE']))
        pygame.display.update()
        pygame.time.Clock().tick(60)
        if y_pos == target_y: break

def execute_visual_stochastic(board, intended_col):
    rand = random.random()
    probs = get_probabilities(intended_col)
    final_col = intended_col
    cum_prob = 0.0
    for p, c in probs:
        cum_prob += p
        if rand < cum_prob: final_col = c; break
    return final_col

# --- MAIN LOOP ---
def menu_screen():
    running = True
    mid_x = GAME_WIDTH // 2
    
    btns = [
        Button(50, 120, 180, 45, "Minimax", lambda: set_algo('MINIMAX_NO_PRUNING')),
        Button(240, 120, 200, 45, "Alpha-Beta", lambda: set_algo('MINIMAX_ALPHA_BETA')),
        Button(450, 120, 200, 45, "Expectiminimax", lambda: set_algo('EXPECTIMINIMAX')),
        
        Button(mid_x - 100, 260, 60, 50, "-", dec_depth),
        Button(mid_x + 40, 260, 60, 50, "+", inc_depth),
        
        Button(mid_x - 100, 370, 60, 50, "-", dec_gui_depth),
        Button(mid_x + 40, 370, 60, 50, "+", inc_gui_depth),
        
        Button(mid_x - 160, 480, 150, 50, "Human Start", lambda: set_starter(HUMAN_PIECE)),
        Button(mid_x + 10, 480, 150, 50, "AI Start", lambda: set_starter(AI_PIECE))
    ]
    play_btn = Button(mid_x - 100, 600, 200, 70, "START GAME", lambda: "PLAY")
    play_btn.selected = True
    
    while running:
        main_screen.fill(VISUAL_CONFIG['BG_COLOR'])
        
        title = font_large.render("CONNECT 4 AI", True, VISUAL_CONFIG['TEXT_WHITE'])
        main_screen.blit(title, (GAME_WIDTH//2 - title.get_width()//2, 30))
        
        lbl_alg = font_small.render(f"ALGORITHM: {config['algo'].replace('_', ' ')}", True, VISUAL_CONFIG['TEXT_GRAY'])
        main_screen.blit(lbl_alg, (GAME_WIDTH//2 - lbl_alg.get_width()//2, 90))
        
        lbl_depth = font_small.render("SEARCH DEPTH (K)", True, VISUAL_CONFIG['TEXT_GRAY'])
        main_screen.blit(lbl_depth, (GAME_WIDTH//2 - lbl_depth.get_width()//2, 220))
        depth_val = font_large.render(str(config['depth']), True, VISUAL_CONFIG['AI_PIECE']['MAIN'])
        main_screen.blit(depth_val, (GAME_WIDTH//2 - depth_val.get_width()//2, 255))

        lbl_viz = font_small.render("TREE VIZ DEPTH", True, VISUAL_CONFIG['TEXT_GRAY'])
        main_screen.blit(lbl_viz, (GAME_WIDTH//2 - lbl_viz.get_width()//2, 340))
        viz_val = font_large.render(str(config['gui_depth']), True, VISUAL_CONFIG['TEXT_WHITE'])
        main_screen.blit(viz_val, (GAME_WIDTH//2 - viz_val.get_width()//2, 365))
        
        lbl_start = font_small.render("FIRST PLAYER", True, VISUAL_CONFIG['TEXT_GRAY'])
        main_screen.blit(lbl_start, (GAME_WIDTH//2 - lbl_start.get_width()//2, 450))
        
        mouse_pos = pygame.mouse.get_pos()
        for b in btns:
            b.check_hover(mouse_pos)
            if "Minimax" in b.text and config['algo'] == 'MINIMAX_NO_PRUNING': b.selected = True
            elif "Alpha" in b.text and config['algo'] == 'MINIMAX_ALPHA_BETA': b.selected = True
            elif "Expecti" in b.text and config['algo'] == 'EXPECTIMINIMAX': b.selected = True
            elif "Human" in b.text and config['starter'] == HUMAN_PIECE: b.selected = True
            elif "AI" in b.text and config['starter'] == AI_PIECE: b.selected = True
            else: b.selected = False
            b.draw(main_screen)
            
        play_btn.check_hover(mouse_pos)
        play_btn.selected = play_btn.hovered
        play_btn.draw(main_screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for b in btns: b.handle_click()
                if play_btn.handle_click() == "PLAY": return
        pygame.display.update()

def game_screen():
    global board_overlay
    board_overlay = create_board_overlay()
    board = create_board()
    game_over = False
    turn = config['starter']
    
    tree_queue = multiprocessing.Queue()
    tree_p = multiprocessing.Process(target=tree_process_main, args=(tree_queue,))
    tree_p.start()
    
    def tree_callback(data):
        if tree_p.is_alive():
            if data is not None:
                try: tree_queue.put(data)
                except: pass
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if tree_p.is_alive(): tree_p.terminate()
                sys.exit()

    render_game_frame(board, turn_msg="AI INITIALIZING..." if turn == AI_PIECE else "YOUR TURN")
    if turn == AI_PIECE: pygame.time.wait(800)
    
    while not game_over:
        current_msg = "YOUR TURN" if turn == HUMAN_PIECE else f"AI COMPUTING (Depth {config['depth']})..."
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if tree_p.is_alive(): tree_p.terminate()
                sys.exit()
            
            if turn == HUMAN_PIECE:
                if event.type == pygame.MOUSEMOTION:
                    posx = event.pos[0]
                    if posx < GAME_WIDTH:
                        col = int(math.floor(posx / VISUAL_CONFIG['SQUARESIZE']))
                        render_game_frame(board, show_phantom_col=col, phantom_piece=HUMAN_PIECE, turn_msg=current_msg)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    posx = event.pos[0]
                    if posx < GAME_WIDTH:
                        col = int(math.floor(posx / VISUAL_CONFIG['SQUARESIZE']))
                        if col in get_valid_locations(board):
                            row = get_next_open_row(board, col)
                            animate_drop(board, col, row, HUMAN_PIECE)
                            board = drop_piece(board, row, col, HUMAN_PIECE)
                            if is_terminal_node(board): game_over = True
                            turn = AI_PIECE
                            if tree_p.is_alive(): tree_queue.put("RESET")
                            render_game_frame(board, turn_msg=f"AI THINKING...")
                            pygame.time.wait(200)

        if turn == AI_PIECE and not game_over:
            render_game_frame(board, turn_msg=current_msg)
            
            score, col, elapsed = find_best_move(board, config['algo'], config['depth'], tree_callback, config['gui_depth'])
            
            final_col = col
            if config['algo'] == 'EXPECTIMINIMAX':
                final_col = execute_visual_stochastic(board, col)
            
            if final_col in get_valid_locations(board):
                row = get_next_open_row(board, final_col)
                animate_drop(board, final_col, row, AI_PIECE)
                board = drop_piece(board, row, final_col, AI_PIECE)
            
            if is_terminal_node(board): game_over = True
            turn = HUMAN_PIECE
            render_game_frame(board, turn_msg="YOUR TURN", phantom_piece=HUMAN_PIECE)

    if game_over:
        ai_score = check_final_score(board, AI_PIECE)
        hu_score = check_final_score(board, HUMAN_PIECE)
        
        if ai_score > hu_score:
            winner_text, color = "AI WINS", VISUAL_CONFIG['AI_PIECE']['MAIN']
        elif hu_score > ai_score:
            winner_text, color = "YOU WIN", VISUAL_CONFIG['HUMAN_PIECE']['MAIN']
        else:
            winner_text, color = "DRAW", WHITE
        
        s = pygame.Surface((GAME_WIDTH, HEIGHT))
        s.set_alpha(240); s.fill((10,15,25))
        main_screen.blit(s, (0,0))
        
        t1 = font_large.render("GAME OVER", True, WHITE)
        t2 = font_large.render(winner_text, True, color)
        t3 = font_small.render(f"HUMAN: {hu_score}  |  AI: {ai_score}", True, VISUAL_CONFIG['TEXT_GRAY'])
        t4 = font_small.render("CLICK TO RESET", True, VISUAL_CONFIG['UI']['BTN_SELECTED'])
        
        main_screen.blit(t1, (GAME_WIDTH//2 - t1.get_width()//2, 150))
        main_screen.blit(t2, (GAME_WIDTH//2 - t2.get_width()//2, 240))
        main_screen.blit(t3, (GAME_WIDTH//2 - t3.get_width()//2, 350))
        main_screen.blit(t4, (GAME_WIDTH//2 - t4.get_width()//2, 500))
        pygame.display.update()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if tree_p.is_alive(): tree_p.terminate()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
                    if tree_p.is_alive(): tree_p.terminate()
                    return

if __name__ == '__main__':
    multiprocessing.freeze_support()
    pygame.init()
    
    fonts = ['segoeui', 'arial', 'helvetica', 'freesansbold']
    font_small = pygame.font.SysFont(fonts, 22)
    font_tiny = pygame.font.SysFont("consolas", 14)
    font_medium = pygame.font.SysFont(fonts, 35, bold=True)
    font_large = pygame.font.SysFont(fonts, 50, bold=True)
    
    main_screen = pygame.display.set_mode(SIZE, pygame.DOUBLEBUF | pygame.HWSURFACE, 32)
    pygame.display.set_caption("Modern Connect 4")
    
    while True:
        menu_screen()
        game_screen()