import copy
from typing import List, Tuple, Optional

# --- GLOBAL CONSTANTS ---
ROW_COUNT = 6    # Number of rows (0 is bottom)
COL_COUNT = 7    # Number of columns
EMPTY = 0
AI_PIECE = 2
HUMAN_PIECE = 1

Board = List[List[int]]

# ----------------------------------------------------------------------
# BOARD MANIPULATION FUNCTIONS
# ----------------------------------------------------------------------

def create_board() -> Board:
    """Initializes a new 6x7 board filled with zeros (EMPTY)."""
    # Note: Connect 4 typically has Row 0 as the bottom, but we define it 
    # as the top row for list-of-list indexing convenience, and flip for printing.
    return [[EMPTY for _ in range(COL_COUNT)] for _ in range(ROW_COUNT)]

def get_valid_locations(board: Board) -> List[int]:
    """Returns a list of columns that are not full."""
    valid_locations = []
    # Check if the top-most row (Row 0) in the list is empty for a given column
    for col in range(COL_COUNT):
        if board[0][col] == EMPTY:
            valid_locations.append(col)
    return valid_locations

def get_next_open_row(board: Board, col: int) -> Optional[int]:
    """Returns the highest empty row index (closest to the top/Row 0) in the column."""
    # We iterate from the bottom-most row (ROW_COUNT - 1) up to the top (Row 0)
    for r in range(ROW_COUNT - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None # Column is full

def drop_piece(board: Board, row: int, col: int, piece: int) -> Board:
    """Places the piece on the board[row][col]. Returns a new board copy."""
    # Crucial for search algorithms: Create a deep copy to ensure immutability
    new_board = copy.deepcopy(board)
    new_board[row][col] = piece
    return new_board

# ----------------------------------------------------------------------
# TERMINAL / SCORE CHECKING FUNCTIONS
# ----------------------------------------------------------------------

def check_window_for_score(window: List[int], piece: int) -> int:
    """Checks a 4-cell window for a connected-four of the given piece."""
    return 1 if window.count(piece) == 4 else 0

def check_final_score(board: Board, piece: int) -> int:
    """
    Counts the total number of connected-fours for the specified piece (N-3 logic).
    Used for the game-ending condition and the heuristic.
    """
    score = 0
    
    # 1. Horizontal Score Check
    for r in range(ROW_COUNT):
        for c in range(COL_COUNT - 3):
            # Explicit list slice for the window
            window = board[r][c:c+4]
            score += check_window_for_score(window, piece)

    # 2. Vertical Score Check
    for c in range(COL_COUNT):
        for r in range(ROW_COUNT - 3):
            window = [board[r+i][c] for i in range(4)]
            score += check_window_for_score(window, piece)

    # 3. Positive Diagonal Check (Bottom-Left to Top-Right)
    # Iterates through the board starting from the bottom-left corners that can host a diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COL_COUNT - 3):
            # Window goes up-right: (r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)
            window = [board[r+i][c+i] for i in range(4)]
            score += check_window_for_score(window, piece)

    # 4. Negative Diagonal Check (Top-Left to Bottom-Right)
    # Iterates through the board starting from the top-left corners that can host a downward diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(3, COL_COUNT):
            # Window goes up-left: (r, c), (r+1, c-1), (r+2, c-2), (r+3, c-3)
            # We must iterate down the rows but up the columns (r+i, c-i)
            window = [board[r+i][c-i] for i in range(4)]
            score += check_window_for_score(window, piece)
            
    return score

def is_terminal_node(board: Board) -> bool:
    """Checks if the game has ended (board is full)."""
    # In this assignment, the game only ends when the board is full.
    return len(get_valid_locations(board)) == 0

def print_board(board: Board):
    """Prints the board to the console, flipping rows for proper Connect 4 view."""
    print("-----------------------------")
    # Print from top to bottom (row 0 to ROW_COUNT-1)
    for r in range(ROW_COUNT):
        print(f"| {' | '.join(map(str, board[r]))} |")
    print("-----------------------------")
    print(f"| 1 | 2 | 3 | 4 | 5 | 6 | 7 |")

if __name__ == '__main__':
    # Simple test case for board creation and move logic
    game_board = create_board()
    print("Initial Board:")
    print_board(game_board)
    
    # Test drop piece
    r = get_next_open_row(game_board, 3)
    game_board = drop_piece(game_board, r, 3, HUMAN_PIECE)
    print("\nBoard after one move:")
    print_board(game_board)