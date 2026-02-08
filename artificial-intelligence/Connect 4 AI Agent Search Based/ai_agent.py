import time
from typing import Tuple, Optional
from game import (
    ROW_COUNT, COL_COUNT, AI_PIECE, HUMAN_PIECE, Board,
    get_valid_locations, get_next_open_row, drop_piece, is_terminal_node
)
from heuristic import BoardEvaluator

# --- CONFIGURATION ---
EVALUATOR = BoardEvaluator()
INF = float('inf')
WIN_SCORE = 10000000.0

# VISUALIZATION SETTINGS (FOR CONSOLE ONLY)
# Level 0 = Root, Level 1 = Human, Level 2 = AI, Level 3 = Leaves
VISUALIZATION_LIMIT = 3

class TreeVisualizer:
    def __init__(self):
        self.nodes_visited = 0

    def _fmt_score(self, score):
        if score == INF: return "+inf"
        if score == -INF: return "-inf"
        return f"{score:.0f}"

    def _fmt_col(self, col):
        return f"{col + 1}"

    def _get_indent(self, level):
        return "    " * level

    def print_header(self, level, is_maximizing, alpha, beta, use_pruning):
        if level >= VISUALIZATION_LIMIT: return

        indent = self._get_indent(level)
        
        if is_maximizing:
            label = f"▲ [MAX] AI (Depth {level})"
        else:
            label = f"▼ [MIN] Human (Depth {level})"

        info = ""
        if use_pruning:
            info = f" [α: {self._fmt_score(alpha)} | β: {self._fmt_score(beta)}]"

        print(f"{indent}├── {label}{info}")

    def print_scores_summary(self, level, is_leaf_layer, scores):
        """Prints the list of scores from the children."""
        if level >= VISUALIZATION_LIMIT: return
        
        indent = self._get_indent(level)
        child_depth = level + 1
        
        label = "Leaves" if is_leaf_layer else "Child Scores"
        formatted = ", ".join([self._fmt_score(s) for s in scores])
        
        print(f"{indent}│") 
        print(f"{indent}└── {label}: [ {formatted} ]  (Depth {child_depth})")

    def print_selection(self, level, best_col, best_score, is_maximizing):
        if level >= VISUALIZATION_LIMIT: return
        
        indent = self._get_indent(level)
        tag = "[AI/MAX]" if is_maximizing else "[HU/MIN]"
        print(f"{indent}└── >> {tag} Select Col {self._fmt_col(best_col)} (Val: {self._fmt_score(best_score)})")

    def print_prune(self, level, alpha, beta):
        if level >= VISUALIZATION_LIMIT: return
        indent = self._get_indent(level)
        print(f"{indent}    └── PRUNED (Alpha {self._fmt_score(alpha)} >= Beta {self._fmt_score(beta)})")

    def print_chance(self, level, col, math_str):
        if level >= VISUALIZATION_LIMIT: return
        indent = self._get_indent(level)
        print(f"{indent}├── Chance Node (Col {self._fmt_col(col)}) Depth {level}: {math_str}")

    def print_spacer(self, level):
        if level >= VISUALIZATION_LIMIT: return
        indent = "    " * level
        print(f"{indent}│")

VISUALIZER = TreeVisualizer()

# ----------------------------------------------------------------------
# 1. MINIMAX / ALPHA-BETA
# ----------------------------------------------------------------------

def minimax_alphabeta(board: Board, depth: int, alpha: float, beta: float, 
                      maximizing_player: bool, use_pruning: bool, 
                      scoring_mode: str, current_level: int, 
                      path_id: str, gui_callback=None, gui_depth_limit=3) -> float:
    
    VISUALIZER.nodes_visited += 1
    is_terminal = is_terminal_node(board)
    
    # --- GUI UPDATE: NODE VISIT ---
    if gui_callback and current_level <= gui_depth_limit: 
        gui_callback({
            'type': 'visit',
            'id': path_id,
            'level': current_level,
            'maximizing': maximizing_player,
            'alpha': alpha,
            'beta': beta,
            'score': None
        })

    # --- BASE CASE ---
    if depth == 0 or is_terminal:
        if is_terminal:
            score = EVALUATOR.evaluate(board, scoring_mode=scoring_mode)
            if score >= 10000: final = WIN_SCORE 
            elif score <= -10000: final = -WIN_SCORE
            else: final = 0.0
        else:
            final = EVALUATOR.evaluate(board, scoring_mode=scoring_mode)
        
        if gui_callback and current_level <= gui_depth_limit:
            gui_callback({'type': 'return', 'id': path_id, 'score': final})
        return final

    valid_locations = get_valid_locations(board)
    next_is_leaf = (depth == 1)

    # --- CONSOLE VIS ---
    if current_level > 0:
        VISUALIZER.print_spacer(current_level)
        VISUALIZER.print_header(current_level, maximizing_player, alpha, beta, use_pruning)

    # --- RECURSION ---
    if maximizing_player:
        value = -INF
        best_col = valid_locations[0]
        scores = [] 

        for i, col in enumerate(valid_locations):
            row = get_next_open_row(board, col)
            new_board = drop_piece(board, row, col, AI_PIECE)
            
            # Recurse
            child_id = f"{path_id}.{i}"
            score = minimax_alphabeta(new_board, depth - 1, alpha, beta, False, use_pruning, scoring_mode, current_level + 1, child_id, gui_callback, gui_depth_limit)
            scores.append(score)

            if score > value:
                value = score
                best_col = col
            
            if use_pruning:
                alpha = max(alpha, value)
                # GUI Update for Alpha Change
                if gui_callback and current_level <= gui_depth_limit:
                    gui_callback({'type': 'update', 'id': path_id, 'alpha': alpha, 'beta': beta, 'temp_val': value})

                if alpha >= beta:
                    VISUALIZER.print_scores_summary(current_level, next_is_leaf, scores)
                    VISUALIZER.print_prune(current_level, alpha, beta)
                    if gui_callback and current_level <= gui_depth_limit:
                        gui_callback({'type': 'prune', 'id': path_id})
                    break
        
        if not use_pruning or alpha < beta:
            VISUALIZER.print_scores_summary(current_level, next_is_leaf, scores)

        if current_level > 0:
            VISUALIZER.print_selection(current_level, best_col, value, True)
        
        if gui_callback and current_level <= gui_depth_limit:
            gui_callback({'type': 'return', 'id': path_id, 'score': value, 'best_col': best_col})
        return value

    else: 
        value = INF
        best_col = valid_locations[0]
        scores = []

        for i, col in enumerate(valid_locations):
            row = get_next_open_row(board, col)
            new_board = drop_piece(board, row, col, HUMAN_PIECE)
            
            # Recurse
            child_id = f"{path_id}.{i}"
            score = minimax_alphabeta(new_board, depth - 1, alpha, beta, True, use_pruning, scoring_mode, current_level + 1, child_id, gui_callback, gui_depth_limit)
            scores.append(score)

            if score < value:
                value = score
                best_col = col
            
            if use_pruning:
                beta = min(beta, value)
                # GUI Update for Beta Change
                if gui_callback and current_level <= gui_depth_limit:
                    gui_callback({'type': 'update', 'id': path_id, 'alpha': alpha, 'beta': beta, 'temp_val': value})

                if alpha >= beta:
                    VISUALIZER.print_scores_summary(current_level, next_is_leaf, scores)
                    VISUALIZER.print_prune(current_level, alpha, beta)
                    if gui_callback and current_level <= gui_depth_limit:
                        gui_callback({'type': 'prune', 'id': path_id})
                    break
        
        if not use_pruning or alpha < beta:
            VISUALIZER.print_scores_summary(current_level, next_is_leaf, scores)

        if current_level > 0:
            VISUALIZER.print_selection(current_level, best_col, value, False)
            
        if gui_callback and current_level <= gui_depth_limit:
            gui_callback({'type': 'return', 'id': path_id, 'score': value, 'best_col': best_col})
        return value

# ----------------------------------------------------------------------
# 2. EXPECTIMINIMAX LOGIC
# ----------------------------------------------------------------------

def get_probabilities(col: int) -> list:
    if col == 0: return [(0.6, 0), (0.4, 1)]
    elif col == COL_COUNT - 1: return [(0.4, col - 1), (0.6, col)]
    else: return [(0.2, col - 1), (0.6, col), (0.2, col + 1)]

def calculate_chance_node(board: Board, depth: int, intended_col: int, current_level: int, path_id: str, gui_callback=None, gui_depth_limit=3) -> float:
    expected_value = 0.0
    probabilities = get_probabilities(intended_col)
    math_parts = []
    
    # GUI Chance Visit
    if gui_callback and current_level <= gui_depth_limit:
        gui_callback({'type': 'visit', 'id': path_id, 'level': current_level, 'maximizing': True, 'node_type': 'chance'})

    for i, (prob, final_col) in enumerate(probabilities):
        row = get_next_open_row(board, final_col)
        if row is not None:
            new_board = drop_piece(board, row, final_col, AI_PIECE)
            # Recurse (Human Turn Next)
            child_id = f"{path_id}.{i}"
            child_score = expectiminimax(new_board, depth, False, current_level + 1, child_id, gui_callback, gui_depth_limit) 
            expected_value += prob * child_score
            math_parts.append(f"{prob}*{child_score:.0f}")
        else:
            penalty = -WIN_SCORE * 0.5
            expected_value += prob * penalty
            math_parts.append(f"{prob}*(Full)")

    math_str = " + ".join(math_parts) + f" = {expected_value:.1f}"
    VISUALIZER.print_chance(current_level, intended_col, math_str)
    
    if gui_callback and current_level <= gui_depth_limit:
        gui_callback({'type': 'return', 'id': path_id, 'score': expected_value})
        
    return expected_value

def expectiminimax(board: Board, depth: int, is_maximizing: bool, current_level: int, path_id: str = "root", gui_callback=None, gui_depth_limit=3) -> float:
    VISUALIZER.nodes_visited += 1
    is_terminal = is_terminal_node(board)
    
    if gui_callback and current_level <= gui_depth_limit:
        gui_callback({'type': 'visit', 'id': path_id, 'level': current_level, 'maximizing': is_maximizing, 'alpha': -INF, 'beta': INF})

    if depth == 0 or is_terminal:
        score = EVALUATOR.evaluate(board, scoring_mode='LITE')
        if score >= 10000: final = WIN_SCORE 
        elif score <= -10000: final = -WIN_SCORE 
        else: final = score
        if gui_callback and current_level <= gui_depth_limit:
            gui_callback({'type': 'return', 'id': path_id, 'score': final})
        return final

    valid_locations = get_valid_locations(board)
    next_is_leaf = (depth == 1)

    if is_maximizing:
        value = -INF
        if current_level > 0:
            VISUALIZER.print_spacer(current_level)
            VISUALIZER.print_header(current_level, True, 0, 0, False)
        
        best_col = valid_locations[0]
        for i, col in enumerate(valid_locations):
            child_id = f"{path_id}.{i}"
            expected_score = calculate_chance_node(board, depth - 1, col, current_level, child_id, gui_callback, gui_depth_limit)
            if expected_score > value:
                value = expected_score
                best_col = col
        
        if current_level > 0:
            VISUALIZER.print_selection(current_level, best_col, value, True)
            
        if gui_callback and current_level <= gui_depth_limit:
            gui_callback({'type': 'return', 'id': path_id, 'score': value})
        return value

    else:
        value = INF
        if current_level > 0:
            VISUALIZER.print_spacer(current_level)
            VISUALIZER.print_header(current_level, False, 0, 0, False)
        scores = []
        best_col = valid_locations[0]

        for i, col in enumerate(valid_locations):
            row = get_next_open_row(board, col)
            new_board = drop_piece(board, row, col, HUMAN_PIECE)
            child_id = f"{path_id}.{i}"
            score = expectiminimax(new_board, depth - 1, True, current_level + 1, child_id, gui_callback, gui_depth_limit)
            scores.append(score)
            if score < value:
                value = score
                best_col = col
        
        VISUALIZER.print_scores_summary(current_level, next_is_leaf, scores)
        if current_level > 0:
            VISUALIZER.print_selection(current_level, best_col, value, False)
            
        if gui_callback and current_level <= gui_depth_limit:
            gui_callback({'type': 'return', 'id': path_id, 'score': value})
        return value

# ----------------------------------------------------------------------
# 3. MAIN WRAPPER
# ----------------------------------------------------------------------

def find_best_move(board: Board, algorithm: str, depth: int, gui_callback=None, gui_depth_limit=3) -> Tuple[float, int, float]:
    print("\n" + "="*60)
    print(f"  SEARCH: {algorithm:<25} DEPTH: {depth}")
    print(f"  VISUALIZATION LIMIT: Top {VISUALIZATION_LIMIT} Levels (Console)")
    print("="*60 + "\n")
    
    start_time = time.time()
    VISUALIZER.nodes_visited = 0
    
    valid_locations = get_valid_locations(board)
    best_score = -INF
    best_col = valid_locations[0]
    
    scoring_mode = 'LITE' if algorithm == 'EXPECTIMINIMAX' else 'FULL'
    use_pruning = True if algorithm == 'MINIMAX_ALPHA_BETA' else False

    print("[AI/MAX] AI Thinking (Depth 0)...")
    
    # GUI: Initialize Root
    if gui_callback:
        gui_callback({'type': 'visit', 'id': 'root', 'level': 0, 'maximizing': True, 'alpha': -INF, 'beta': INF, 'score': None})

    for i, col in enumerate(valid_locations):
        row = get_next_open_row(board, col)
        new_board = drop_piece(board, row, col, AI_PIECE)
        
        child_id = f"root.{i}"
        
        if algorithm == 'EXPECTIMINIMAX':
             score = calculate_chance_node(board, depth - 1, col, 0, child_id, gui_callback, gui_depth_limit)
        else:
            score = minimax_alphabeta(new_board, depth - 1, -INF, INF, False, use_pruning, scoring_mode, 1, child_id, gui_callback, gui_depth_limit)
        
        print("") 
        print("│")
        print(f"├── [AI/MAX] Option Col {col + 1} -> Score: {score:.1f}")
        
        if score > best_score:
            best_score = score
            best_col = col
            
        # Update root display
        if gui_callback:
             gui_callback({'type': 'update', 'id': 'root', 'temp_val': best_score})
            
    if gui_callback:
        gui_callback({'type': 'return', 'id': 'root', 'score': best_score})

    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print("\n" + "-"*60)
    print(f"   >> BEST MOVE: Column {best_col + 1}")
    print(f"   >> SCORE: {best_score:.0f}")
    print(f"   >> TIME: {elapsed_time:.4f}s  |  NODES: {VISUALIZER.nodes_visited}")
    print("-" * 60 + "\n")
    
    return best_score, best_col, elapsed_time