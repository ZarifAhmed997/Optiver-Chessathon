import time
import chess
from math import inf as INF
from collections import OrderedDict

class Search:
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.CHECKMATE_SCORE = 999999
    
        # Transposition table entry flags
        self.TT_EXACT = 0   # Exact score
        self.TT_LOWER = 1   # Alpha (lower bound)
        self.TT_UPPER = 2   # Beta (upper bound)

        # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
        self.PIECE_VALUES = {
            chess.PAWN:   100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK:   500,
            chess.QUEEN:  900,
            chess.KING:   20000, 
        }

        self.nodes_searched = 0
        self.aborted = False 
    
        self.transposition_table = OrderedDict()
        self.TT_MAX_SIZE = 8000000
    

    def tt_lookup(self, key, depth, alpha, beta):
        entry = self.transposition_table.get(key)

        if entry is None:
            return None, None

        self.transposition_table.move_to_end(key)
        
        tt_depth, tt_score, tt_flag, tt_move = entry
        
        if tt_depth >= depth:
            if tt_flag == self.TT_EXACT:
                return tt_score, tt_move
            elif tt_flag == self.TT_LOWER and tt_score >= beta:
                return tt_score, tt_move
            elif tt_flag == self.TT_UPPER and tt_score <= alpha:
                return tt_score, tt_move
        
        return None, tt_move


    def tt_store(self, key, depth, score, flag, best_move):
        if key in self.transposition_table:
            self.transposition_table.move_to_end(key)

        self.transposition_table[key] = (depth, score, flag, best_move)

        if len(self.transposition_table) > self.TT_MAX_SIZE:
            self.transposition_table.popitem(last=False)


    def mvv_lva_score(self, board, move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim is None or attacker is None:
            return 0
        return self.PIECE_VALUES[victim.piece_type] * 10 - self.PIECE_VALUES[attacker.piece_type]


    def order_moves(self, board, moves, tt_move=None):
        scored = []
        
        for move in moves:
            score = 0
            
            if move == tt_move:
                score = 1_000_000
            elif board.is_capture(move):
                score = 100_000 + self.mvv_lva_score(board, move)
            elif move.promotion is not None:
                score = 90_000 + self.PIECE_VALUES.get(move.promotion, 0)
            else:
                if board.gives_check(move):
                    score = 50_000
            
            scored.append((score, move))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in scored]


    def quiescence(self, board, alpha, beta, time_limit):
        if time.time() >= time_limit:
            self.aborted = True
            return 0
        
        stand_pat = self.evaluator.evaluate_relative(board)

        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        
        captures = list(board.generate_legal_captures())
        captures = self.order_moves(board, captures)
        
        for move in captures:
            board.push(move)
            score = -self.quiescence(board, -beta, -alpha, time_limit)  # negamax
            board.pop()

            if time.time() >= time_limit:
                self.aborted = True
                return 0
            
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        
        return alpha


    def alpha_beta(self, board, depth, alpha, beta, time_limit):
        self.nodes_searched += 1
        
        if time.time() >= time_limit:
            self.aborted = True
            return 0
        
        # Draw detection
        if board.is_repetition(2):
            material = self.evaluator.evaluate_material(board)
            # Convert to current player's perspective (negamax)
            relative_material = material if board.turn == chess.WHITE else -material
            
            if relative_material > 0:
                # We're winning — make repetition very unattractive
                # Penalty scales with how much we're winning
                # If up 500cp, repetition costs 400cp — huge deterrent
                return -int(relative_material * 0.8)
            else:
                # We're losing — repetition is fine, return 0 (draw is good)
                return 0

        if board.is_fifty_moves() or board.is_insufficient_material():
            return 0
        
        tt_key = board._transposition_key()
        tt_score, tt_move = self.tt_lookup(tt_key, depth, alpha, beta)
        if tt_score is not None:
            return tt_score
        
        if depth == 0:
            return self.quiescence(board, alpha, beta, time_limit)
        
        legal_moves = list(board.legal_moves)
        
        if not legal_moves:
            if board.is_checkmate():
                return -self.CHECKMATE_SCORE + depth  # current player got mated
            return 0  # stalemate
        
        ordered_moves = self.order_moves(board, legal_moves, tt_move)
        
        best_move = ordered_moves[0]
        original_alpha = alpha
        best_score = -INF
        
        for move in ordered_moves:
            board.push(move)
            score = -self.alpha_beta(board, depth - 1, -beta, -alpha, time_limit)  # negamax
            board.pop()

            if self.aborted:
                return 0
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, best_score)
            
            if alpha >= beta:
                break
        
        flag = self.TT_EXACT if original_alpha < best_score < beta else (self.TT_LOWER if best_score >= beta else self.TT_UPPER)
        self.tt_store(tt_key, depth, best_score, flag, best_move)
        
        return best_score


    def iterative_deepening(self, board, time_budget_ms):
        self.nodes_searched = 0
        self.aborted = False  # Reset for next move
        
        time_limit = time.time() + (time_budget_ms / 1000.0)
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        best_move = legal_moves[0]

        for depth in range(1, 50):
            if time.time() >= time_limit:
                break

            best_score = -INF
            current_best = None
            alpha = -INF
            beta = INF
            depth_complete = True

            tt_key = board._transposition_key()
            _, tt_move = self.tt_lookup(tt_key, depth, alpha, beta)
            ordered_moves = self.order_moves(board, list(board.legal_moves), tt_move)

            for move in ordered_moves:
                if time.time() >= time_limit:
                    depth_complete = False
                    break

                board.push(move)
                score = -self.alpha_beta(board, depth - 1, -beta, -alpha, time_limit)  # negamax
                board.pop()

                if self.aborted:
                    depth_complete = False
                    break

                if score > best_score:
                    best_score = score
                    current_best = move

                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break

            if depth_complete and current_best is not None:
                best_move = current_best
                print(f"Depth {depth}: score={best_score}, move={best_move}, nodes={self.nodes_searched}")
            else:
                print(f"Depth {depth} incomplete — using depth {depth-1} result")
                break

        return best_move


    def calculate_time_budget(self, time_left_ms, move_number=None):
        SAFETY_BUFFER_MS = 1_000
        usable_time = max(0, time_left_ms - SAFETY_BUFFER_MS)
        
        if usable_time <= 0:
            return 100
        
        EXPECTED_MOVES_REMAINING = 30
        base_budget = usable_time / EXPECTED_MOVES_REMAINING + 500
        max_budget = usable_time * 0.10
        budget = min(base_budget, max_budget)
        budget = max(budget, 200)
        
        return int(budget)


    def get_move(self, fen: str, time_left_ms: int) -> str:
        board = chess.Board(fen)
        time_budget = self.calculate_time_budget(time_left_ms)
        print(f"Time left: {time_left_ms}ms, Budget: {time_budget}ms")
        
        best_move = self.iterative_deepening(board, time_budget)
        
        if best_move is None:
            legal = list(board.legal_moves)
            return legal[0].uci() if legal else "0000"
        
        return best_move.uci()