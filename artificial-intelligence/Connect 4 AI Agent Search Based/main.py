import random
import time
from typing import Optional
from game import (
    ROW_COUNT, COL_COUNT, AI_PIECE, HUMAN_PIECE, EMPTY, Board,
    create_board, get_valid_locations, get_next_open_row, drop_piece, 
    is_terminal_node, check_final_score, print_board
)
from ai_agent import find_best_move, get_probabilities

# ----------------------------------------------------------------------
# HELPER FUNCTIONS FOR GAME EXECUTION
# ----------------------------------------------------------------------

def execute_stochastic_move(board: Board, chosen_col: int, piece: int) -> Board:
    """
    Executes the move on the board using RNG to determine the final landing column.
    Uses the 0.6/0.2/0.2 or 0.6/0.4 distribution.
    """
    rand = random.random()
    
    # Get the probability distribution for the chosen column
    probabilities = get_probabilities(chosen_col)
    
    # Calculate cumulative ranges for RNG mapping
    cumulative_prob = 0.0
    landing_col = chosen_col # Default fallback
    
    print(f"   -> Stochastic Roll: {rand:.4f}")
    
    for prob, target_c in probabilities:
        cumulative_prob += prob
        if rand < cumulative_prob:
            landing_col = target_c
            break
            
    # Convert to 1-based for display
    print(f"   -> Intended: Col {chosen_col + 1}, Actual Landing: Col {landing_col + 1}")

    # Check if the final landing column is valid (not full)
    row = get_next_open_row(board, landing_col)
    if row is not None:
        new_board = drop_piece(board, row, landing_col, piece)
        return new_board
    else:
        print(f"\n! WARNING: Piece aimed at {chosen_col + 1} slipped into full column {landing_col + 1}!")
        return board 

# ----------------------------------------------------------------------
# MAIN GAME LOOP
# ----------------------------------------------------------------------

def run_game():
    print("\n--- Alexandria University Connect 4 AI Agent ---")
    
    # Algorithm Selection
    algorithm_map = {
        '1': 'MINIMAX_NO_PRUNING',
        '2': 'MINIMAX_ALPHA_BETA',
        '3': 'EXPECTIMINIMAX'
    }
    try:
        alg_choice = input("Select Algorithm (1: Minimax, 2: Alpha-Beta, 3: Expected Minimax): ")
        if alg_choice in ['1', '2', '3']:
            algorithm = algorithm_map.get(alg_choice, 'MINIMAX_ALPHA_BETA')
            print(f"Algorithm is set to {algorithm}.")
        else:
            raise ValueError
    except ValueError:
        alg_choice = '2'
        print(f"Invalid. Algorithm is automatically set to Minimax with Alpha-Beta Pruning.")
    algorithm = algorithm_map.get(alg_choice, 'MINIMAX_ALPHA_BETA')
    
    # Depth Selection
    try:
        depth = int(input("Enter Search Depth K (e.g., 5): "))
        print(f"Depth set to {depth}.")
    except ValueError:
        depth = 7
        print(f"Invalid. Depth automatically set to {depth}.")
        
    # First Player Selection
    try:
        player1 = input("Do you want to go first? (y/n): ").lower()
        if player1 == 'y':
            current_player = HUMAN_PIECE
            print(f"Human starts the game.")
        elif player1 == 'n':
            current_player = AI_PIECE
            print(f"AI starts the game.")
        else:
            raise ValueError
    except ValueError:
        current_player = AI_PIECE 
        print(f"Invalid. AI automatically starts the game.")
    
    # Initialize
    game_board = create_board()
    game_over = False
    
    while not game_over:
        print_board(game_board)
        
        # --- HUMAN TURN ---
        if current_player == HUMAN_PIECE:
            print("\n<<< HUMAN Player's Turn >>>")
            # Get valid internal indices (0-6)
            valid_internals = get_valid_locations(game_board)
            # Create display indices (1-7)
            valid_displays = [c + 1 for c in valid_internals]
            
            if not valid_internals: break 
            
            while True:
                try:
                    choice = int(input(f"Choose a column {valid_displays}: "))
                    if choice in valid_displays:
                        col = choice - 1  # Convert 1-based input to 0-based index
                        row = get_next_open_row(game_board, col)
                        game_board = drop_piece(game_board, row, col, HUMAN_PIECE)
                        break
                    else:
                        print(f"Invalid column. Please choose from {valid_displays}")
                except ValueError:
                    print("Invalid input. Please enter a number.")

        # --- AI TURN ---
        elif current_player == AI_PIECE:
            print(f"\n<<< AI Agent's Turn ({algorithm}) >>>")
            
            score, col, elapsed_time = find_best_move(game_board, algorithm, depth)
            
            print(f"AI chose column: {col + 1}")
            print(f"Time taken: {elapsed_time:.4f} seconds")
            
            if algorithm == 'EXPECTIMINIMAX':
                game_board = execute_stochastic_move(game_board, col, AI_PIECE)
            else:
                row = get_next_open_row(game_board, col)
                game_board = drop_piece(game_board, row, col, AI_PIECE)
        
        # Check for game end
        game_over = is_terminal_node(game_board)
        current_player = HUMAN_PIECE if current_player == AI_PIECE else AI_PIECE


    # --- GAME ENDING ---
    print("\n\n--- GAME OVER ---")
    print_board(game_board)
    
    ai_final_score = check_final_score(game_board, AI_PIECE)
    human_final_score = check_final_score(game_board, HUMAN_PIECE)
    
    print(f"\nAI Final Score: {ai_final_score}")
    print(f"Human Final Score: {human_final_score}")
    
    if ai_final_score > human_final_score:
        print("🎉 AI Agent WINS! 🎉")
    elif human_final_score > ai_final_score:
        print("😭 HUMAN Player WINS! 😭")
    else:
        print("🤝 DRAW 🤝")

if __name__ == '__main__':
    run_game()