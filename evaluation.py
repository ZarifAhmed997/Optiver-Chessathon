import chess

class Evaluation:
    def __init__(self):
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900
        }

        self.PAWN_SQUARES = [
                0,   0,   0,   0,   0,   0,   0,   0,
                50,  50,  50,  50,  50,  50,  50,  50,
                10,  10,  20,  30,  30,  20,  10,  10,
                5,   5,   10,  25,  25,  10,  5,   5,
                0,   0,   0,   20,  20,  0,   0,   0,
                5,   -5,  -10, 0,   0,   -10, -5,  5,
                5,   10,  10,  -20, -20, 10,  10,  5,
                0,   0,   0,   0,   0,   0,   0,   0,
            ]
        
        self.KNIGHT_SQUARES = [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20, 0,   5,   5,   0,   -20, -40,
            -30, 5,   10,  15,  15,  10,  5,   -30,
            -30, 5,   15,  20,  20,  15,  5,   -30,
            -30, 5,   15,  20,  20,  15,  5,   -30,
            -30, 5,   10,  15,  15,  10,  5,   -30,
            -40, -20, 0,   5,   5,   0,   -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50,
        ]
    
        self.BISHOP_SQUARES = [
            -20, -10, -10, -10, -10, -10, -10, -20,
            -10, 0,   0,   0,   0,   0,   0,   -10,
            -10, 0,   5,   10,  10,  5,   0,   -10,
            -10, 5,   5,   10,  10,  5,   5,   -10,
            -10, 0,   10,  10,  10,  10,  0,   -10,
            -10, 10,  10,  10,  10,  10,  10,  -10,
            -10, 5,   0,   0,   0,   0,   5,   -10,
            -20, -10, -10, -10, -10, -10, -10, -20,
        ]
    
        self.ROOK_SQUARES = [
            0,   0,   0,   0,   0,   0,   0,   0,
            5,   10,  10,  10,  10,  10,  10,  5,
            -5,  0,   0,   0,   0,   0,   0,   -5,
            -5,  0,   0,   0,   0,   0,   0,   -5,
            -5,  0,   0,   0,   0,   0,   0,   -5,
            -5,  0,   0,   0,   0,   0,   0,   -5,
            -5,  0,   0,   0,   0,   0,   0,   -5,
            0,   0,   0,   5,   5,   0,   0,   0,
        ]
    
        self.QUEEN_SQUARES = [
            -20, -10, -10, -5,  -5,  -10, -10, -20,
            -10, 0,   0,   0,   0,   0,   0,   -10,
            -10, 0,   5,   5,   5,   5,   0,   -10,
            -5,  0,   5,   5,   5,   5,   0,   -5,
            0,   0,   5,   5,   5,   5,   0,   -5,
            -10, 5,   5,   5,   5,   5,   0,   -10,
            -10, 0,   5,   0,   0,   0,   0,   -10,
            -20, -10, -10, -5,  -5,  -10, -10, -20,
        ]
    
        self.KING_MIDGAME = [
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -20, -30, -30, -40, -40, -30, -30, -20,
            -10, -20, -20, -20, -20, -20, -20, -10,
            20,  20,  0,   0,   0,   0,   20,  20,
            20,  30,  10,  0,   0,   10,  30,  20,
        ]
    
        self.KING_ENDGAME = [
            -50, -40, -30, -20, -20, -30, -40, -50,
            -30, -20, -10, 0,   0,   -10, -20, -30,
            -30, -10, 20,  30,  30,  20,  -10, -30,
            -30, -10, 30,  40,  40,  30,  -10, -30,
            -30, -10, 30,  40,  40,  30,  -10, -30,
            -30, -10, 20,  30,  30,  20,  -10, -30,
            -30, -30, 0,   0,   0,   0,   -30, -30,
            -50, -40, -30, -20, -20, -30, -40, -50,
        ]

        # Pawn hash table: cache expensive pawn structure evaluations
        self.pawn_hash_table = {}
        self.PAWN_TT_MAX_SIZE = 5_000_000

    def evaluate_pawn_structure(self, board, side):
        # Cache key: just the pawn bitboards (cheap to compute, pawns don't move every turn)
        white_pawns_bb = board.pawns & board.occupied_co[chess.WHITE]
        black_pawns_bb = board.pawns & board.occupied_co[chess.BLACK]
        cache_key = (white_pawns_bb, black_pawns_bb, side)

        if cache_key in self.pawn_hash_table:
            return self.pawn_hash_table[cache_key]

        score = 0
        pawns = board.pieces(chess.PAWN, side)

        # Compute enemy pawns ONCE outside the loop (fixes the O(P^2) bottleneck)
        enemy_pawns = board.pieces(chess.PAWN, chess.BLACK if side == chess.WHITE else chess.WHITE)

        for pawn_square in pawns:
            file = chess.square_file(pawn_square)
            rank = chess.square_rank(pawn_square)

            # Isolated pawns
            has_support = any(
                chess.square_file(p) in (file - 1, file + 1) for p in pawns
            )
            if not has_support:
                score -= 20

            # Doubled pawns
            same_file_count = sum(1 for p in pawns if chess.square_file(p) == file)
            if same_file_count > 1:
                score -= 20 * (same_file_count - 1)

            # Passed pawn — enemy_pawns computed once outside loop
            is_passed = True
            rank_range = range(rank + 1, 8) if side == chess.WHITE else range(rank - 1, -1, -1)
            for check_rank in rank_range:
                files_to_check = [f for f in (file - 1, file, file + 1) if 0 <= f <= 7]
                if any(chess.square(f, check_rank) in enemy_pawns for f in files_to_check):
                    is_passed = False
                    break

            if is_passed:
                score += 30 + (10 * rank if side == chess.WHITE else 10 * (7 - rank))

        if len(self.pawn_hash_table) < self.PAWN_TT_MAX_SIZE:
            self.pawn_hash_table[cache_key] = score

        return score

    def evaluate_king_safety(self, board, side):
        score = 0

        if side == chess.WHITE:
            if board.has_kingside_castling_rights(chess.WHITE):
                score += 30
            if board.has_queenside_castling_rights(chess.WHITE):
                score += 30
            pawn_shield_squares = [chess.F2, chess.G2, chess.H2, chess.F3, chess.G3, chess.H3]
        else:
            if board.has_kingside_castling_rights(chess.BLACK):
                score += 30
            if board.has_queenside_castling_rights(chess.BLACK):
                score += 30
            pawn_shield_squares = [chess.F7, chess.G7, chess.H7, chess.F6, chess.G6, chess.H6]

        pawns = board.pieces(chess.PAWN, side)
        for sq in pawn_shield_squares:
            if sq in pawns:
                score += 10

        return score

    def evaluate_material(self, board):
        return sum(
            self.piece_values[pt] * (len(board.pieces(pt, chess.WHITE)) - len(board.pieces(pt, chess.BLACK)))
            for pt in self.piece_values
        )

    def evaluate_piece_squares(self, board):
        score = 0

        for square in board.pieces(chess.PAWN, chess.WHITE):
            score += self.PAWN_SQUARES[square]
        for square in board.pieces(chess.PAWN, chess.BLACK):
            score -= self.PAWN_SQUARES[chess.square_mirror(square)]

        for square in board.pieces(chess.KNIGHT, chess.WHITE):
            score += self.KNIGHT_SQUARES[square]
        for square in board.pieces(chess.KNIGHT, chess.BLACK):
            score -= self.KNIGHT_SQUARES[chess.square_mirror(square)]

        for square in board.pieces(chess.BISHOP, chess.WHITE):
            score += self.BISHOP_SQUARES[square]
        for square in board.pieces(chess.BISHOP, chess.BLACK):
            score -= self.BISHOP_SQUARES[chess.square_mirror(square)]

        for square in board.pieces(chess.ROOK, chess.WHITE):
            score += self.ROOK_SQUARES[square]
        for square in board.pieces(chess.ROOK, chess.BLACK):
            score -= self.ROOK_SQUARES[chess.square_mirror(square)]

        for square in board.pieces(chess.QUEEN, chess.WHITE):
            score += self.QUEEN_SQUARES[square]
        for square in board.pieces(chess.QUEEN, chess.BLACK):
            score -= self.QUEEN_SQUARES[chess.square_mirror(square)]

        # Endgame detection
        total_pieces = sum(
            len(board.pieces(pt, c))
            for pt in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
            for c in [chess.WHITE, chess.BLACK]
        )
        king_table = self.KING_ENDGAME if total_pieces <= 8 else self.KING_MIDGAME

        white_king = board.king(chess.WHITE)
        if white_king is not None:
            score += king_table[white_king]

        black_king = board.king(chess.BLACK)
        if black_king is not None:
            score -= king_table[chess.square_mirror(black_king)]

        return score

    def evaluate_relative(self, board):
        """Score from current player's perspective (not always white's)."""
        score = self.evaluate(board)
        return score if board.turn == chess.WHITE else -score

    def evaluate(self, board):
        if board.is_checkmate():
            return -9999 if board.turn == chess.WHITE else 9999
        if board.is_stalemate():
            return 0

        material_score = self.evaluate_material(board)
        piece_square_score = self.evaluate_piece_squares(board)
        pawn_structure_score = self.evaluate_pawn_structure(board, chess.WHITE) - self.evaluate_pawn_structure(board, chess.BLACK)
        king_safety_score = self.evaluate_king_safety(board, chess.WHITE) - self.evaluate_king_safety(board, chess.BLACK)

        total_score = (
            material_score * 1.0 +
            piece_square_score * 0.3 +
            pawn_structure_score * 0.5 +
            king_safety_score * 0.4
        )

        # Tempo bonus
        total_score += 20 if board.turn == chess.WHITE else -20

        return int(total_score)