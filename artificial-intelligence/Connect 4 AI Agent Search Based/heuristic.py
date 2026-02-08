from typing import List, Tuple, Dict
from game import ROW_COUNT, COL_COUNT, EMPTY, AI_PIECE, HUMAN_PIECE, Board

class BoardEvaluator:
    """
    Advanced Heuristic Evaluator for Connect 4.
    Optimized for O(1) window access and O(N) board scan.
    Includes:
    1. Window Scoring (N-in-a-row)
    2. Center Column Control (Positional Strategy)
    3. Double Threat / Fork Detection (7-shape logic)
    4. Parity/Zugzwang Awareness (Odd/Even row strategy)
    """
    def __init__(self):
        # Pre-calculate all 69 winning window indices for O(1) access
        self.window_indices: List[List[Tuple[int, int]]] = []
        self.generate_window_indices()
        
        # Pre-calculate a positional weight matrix (Center Control)
        # Prefer center columns: [3, 4, 5, 7, 5, 4, 3]
        self.positional_weights = [
            [3, 4, 5, 7, 5, 4, 3],  # Row 0 (Top)
            [4, 6, 8, 10, 8, 6, 4],
            [5, 8, 11, 13, 11, 8, 5],
            [5, 8, 11, 13, 11, 8, 5],
            [4, 6, 8, 10, 8, 6, 4],
            [3, 4, 5, 7, 5, 4, 3]   # Row 5 (Bottom)
        ]

    def generate_window_indices(self):
        # 1. Horizontal
        for r in range(ROW_COUNT):
            for c in range(COL_COUNT - 3):
                self.window_indices.append([(r, c + i) for i in range(4)])
        # 2. Vertical
        for c in range(COL_COUNT):
            for r in range(ROW_COUNT - 3):
                self.window_indices.append([(r + i, c) for i in range(4)])
        # 3. Positive Diagonal
        for r in range(ROW_COUNT - 3):
            for c in range(COL_COUNT - 3):
                self.window_indices.append([(r + i, c + i) for i in range(4)])
        # 4. Negative Diagonal
        for r in range(ROW_COUNT - 3):
            for c in range(3, COL_COUNT):
                self.window_indices.append([(r + i, c - i) for i in range(4)])

    def evaluate(self, board: Board, scoring_mode: str = 'FULL') -> float:
        """
        Master evaluation function.
        """
        score = 0.0
        
        # --- 1. POSITIONAL SCORE (Center Control) ---
        # Fast lookup of piece positions to encourage center play
        for r in range(ROW_COUNT):
            for c in range(COL_COUNT):
                piece = board[r][c]
                if piece == AI_PIECE:
                    score += self.positional_weights[r][c]
                elif piece == HUMAN_PIECE:
                    score -= self.positional_weights[r][c]

        if scoring_mode == 'LITE':
            return score + self._evaluate_windows_lite(board)
        
        # --- 2. ADVANCED THREAT SCORE (Full Depth) ---
        score += self._evaluate_advanced_threats(board)
        return score

    def _evaluate_windows_lite(self, board: Board) -> float:
        """Fast scoring for Expectiminimax (Win/Loss only)."""
        score = 0.0
        for indices in self.window_indices:
            # Fast unpacking
            cells = [board[r][c] for r, c in indices]
            ai_count = cells.count(AI_PIECE)
            human_count = cells.count(HUMAN_PIECE)
            empty_count = cells.count(EMPTY)

            if ai_count == 4: return 1000000
            if human_count == 4: return -1000000
            # Simple blocking logic
            if human_count == 3 and empty_count == 1: score -= 5000
        return score

    def _evaluate_advanced_threats(self, board: Board) -> float:
        score = 0.0
        
        # Threat Maps: Track where winning spots are for Double Threat detection
        # Dictionary key: (row, col), Value: count of winning lines passing through this empty spot
        ai_threats: Dict[Tuple[int, int], int] = {}
        human_threats: Dict[Tuple[int, int], int] = {}

        for indices in self.window_indices:
            cells = [board[r][c] for r, c in indices]
            ai_count = cells.count(AI_PIECE)
            human_count = cells.count(HUMAN_PIECE)
            empty_count = cells.count(EMPTY)

            # --- STANDARD WINDOW SCORING ---
            if ai_count == 4: return 1000000
            if human_count == 4: return -1000000
            
            # AI Threats (3 AI + 1 Empty)
            if ai_count == 3 and empty_count == 1:
                score += 100  # Base score for having 3
                # Find the empty spot coordinate
                for r, c in indices:
                    if board[r][c] == EMPTY:
                        ai_threats[(r, c)] = ai_threats.get((r, c), 0) + 1
            
            # Human Threats (3 Human + 1 Empty)
            elif human_count == 3 and empty_count == 1:
                score -= 100
                for r, c in indices:
                    if board[r][c] == EMPTY:
                        human_threats[(r, c)] = human_threats.get((r, c), 0) + 1

            # Setup potential (2 pieces)
            elif ai_count == 2 and empty_count == 2:
                score += 5
            elif human_count == 2 and empty_count == 2:
                score -= 5

        # --- 3. DOUBLE THREAT & PARITY LOGIC ---
        
        # Analyze AI Threats
        for (r, c), count in ai_threats.items():
            # Double Threat: If one empty spot completes >= 2 winning lines
            if count >= 2:
                score += 5000  # Huge bonus for creating a fork
            
            # Parity / Zugzwang Strategy
            # If the threat is on an EVEN row (0, 2, 4) (Visual bottom is 5, logic is inverted)
            # Note: Adjust parity logic based on who went first. 
            # Assuming AI tries to maximize its own parity rows.
            # Standard logic: Bottom row is 5 (inverted in list), top is 0.
            # A "playable" spot depends on gravity.
            
            # If a spot is an "Odd" threat (Row index % 2 != 0), it's usually stronger for Player 1
            if r % 2 != 0: 
                score += 50 # Slight bonus for favorable parity

        # Analyze Human Threats (Defensive)
        for (r, c), count in human_threats.items():
            if count >= 2:
                score -= 5000 # Must block double threats immediately!

        return score

if __name__ == '__main__':
    # Simple test for index generation
    evaluator = BoardEvaluator()
    print(f"Total windows calculated: {len(evaluator.window_indices)}")
    print(f"Example Horizontal Window: {evaluator.window_indices[0]}")
    print(f"Example Vertical Window: { evaluator.window_indices[40]}") # Approx center of vertical windows