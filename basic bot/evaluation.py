import chess

class Evaluation:
    def __init__(self, model):
        self.model = model
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
        
        # Knight piece-square table (centralisation bonus)
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
    
        # Bishop piece-square table (long diagonals are valuable)
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
    
        # Rook piece-square table (open files are valuable)
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
    
        # Queen piece-square table (centralization, but not too aggressive early)
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
    
        # King piece-square table (early game: hide, endgame: centralize)
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


    """
    Scores a position in centipawns (100 = 1 pawn).
    Positive = advantage for White, Negative = advantage for Black.
    """

    # Bonus centipawns for piece placement (piece-square tables)
    # From white's perspective; for black, mirror the board.

    # Pawn piece-square table (white perspective)

    # Pawn structure evaluation: isolated, doubled, passed pawns

    def evaluate_pawn_structure(self, board, side):

        score = 0
        pawns = board.pieces(chess.PAWN, side)
        
        for pawn_square in pawns:
            file = chess.square_file(pawn_square)
            rank = chess.square_rank(pawn_square)
            
            # Isolated pawns (no pawns on adjacent files) - penalize
            left_file = file - 1
            right_file = file + 1
            
            has_left_support = False
            has_right_support = False
            
            if left_file >= 0:
                for other_pawn in pawns:
                    if chess.square_file(other_pawn) == left_file:
                        has_left_support = True
                        break
            
            if right_file <= 7:
                for other_pawn in pawns:
                    if chess.square_file(other_pawn) == right_file:
                        has_right_support = True
                        break
            
            if not has_left_support and not has_right_support:
                score -= 20  # Isolated pawn penalty
            
            # Doubled pawns (two pawns on same file) - penalize
            same_file_count = sum(1 for p in pawns if chess.square_file(p) == file)
            if same_file_count > 1:
                score -= 20 * (same_file_count - 1)
            
            # Passed pawn (no enemy pawns in front or on adjacent files) - reward
            is_passed = True
            if side == chess.WHITE:
                # Check ranks ahead of this pawn
                for check_rank in range(rank + 1, 8):
                    check_square_center = chess.square(file, check_rank)
                    check_square_left = chess.square(file - 1, check_rank) if file > 0 else None
                    check_square_right = chess.square(file + 1, check_rank) if file < 7 else None
                    
                    enemy_pawns = board.pieces(chess.PAWN, chess.BLACK)
                    if (check_square_center in enemy_pawns or
                        (check_square_left and check_square_left in enemy_pawns) or
                        (check_square_right and check_square_right in enemy_pawns)):
                        is_passed = False
                        break
            else:
                # Black: check ranks below
                for check_rank in range(rank - 1, -1, -1):
                    check_square_center = chess.square(file, check_rank)
                    check_square_left = chess.square(file - 1, check_rank) if file > 0 else None
                    check_square_right = chess.square(file + 1, check_rank) if file < 7 else None
                    
                    enemy_pawns = board.pieces(chess.PAWN, chess.WHITE)
                    if (check_square_center in enemy_pawns or
                        (check_square_left and check_square_left in enemy_pawns) or
                        (check_square_right and check_square_right in enemy_pawns)):
                        is_passed = False
                        break
            
            if is_passed:
                score += 30 + (10 * rank if side == chess.WHITE else 10 * (7 - rank))
        
        return score

    # Piece mobility evaluation: how many squares pieces can move to

    def evaluate_mobility(self, board, side):
        """
        Evaluate piece mobility (how many squares pieces can move to).
        More mobile pieces = better.
        """
        score = 0
        
        # Count legal moves for this side (rough proxy for mobility)
        # Note: This is expensive, so in production you might cache this
        legal_moves = list(board.legal_moves)
        
        # Very rough: more legal moves = better position (but this is crude)
        # A better approach would be to count attacked/controlled squares per piece
        mobility_bonus = len(legal_moves) * 2  # 2 centipawns per legal move
        
        if board.turn == side:
            score += mobility_bonus
        
        return score


    # King safety evaluation: castling rights, pawn shield, exposure

    def evaluate_king_safety(self, board, side):
        """
        Evaluate king safety: castling rights, pawn shield, exposure.
        """
        score = 0
        king_square = board.king(side)
        
        # Castling rights still available - bonus (more escape routes)
        if side == chess.WHITE:
            if board.has_kingside_castling_rights(chess.WHITE):
                score += 30
            if board.has_queenside_castling_rights(chess.WHITE):
                score += 30
        else:
            if board.has_kingside_castling_rights(chess.BLACK):
                score += 30
            if board.has_queenside_castling_rights(chess.BLACK):
                score += 30
        
        # Pawn shield around king (f, g, h files for white kingside, etc.)
        # Bonus if pawns are near king
        if side == chess.WHITE:
            # Check for pawns on f2, g2, h2, f3, g3, h3
            pawn_shield_squares = [chess.F2, chess.G2, chess.H2, chess.F3, chess.G3, chess.H3]
        else:
            # Check for pawns on f7, g7, h7, f6, g6, h6
            pawn_shield_squares = [chess.F7, chess.G7, chess.H7, chess.F6, chess.G6, chess.H6]
        
        pawns = board.pieces(chess.PAWN, side)
        for sq in pawn_shield_squares:
            if sq in pawns:
                score += 10
        
        return score


    # Material evaluation: sum of piece values, adjusted for color

    def evaluate_material(self, board):
        """
        Simple material count: pieces worth more than pawns.
        """

        score = sum(
            self.piece_values[piece_type] * 
            (len(board.pieces(piece_type, chess.WHITE)) - len(board.pieces(piece_type, chess.BLACK))) 
                for piece_type in self.piece_values
        )
        
        return score


    # Piece square evaluation: bonus for pieces on good squares, penalty for bad squares

    def evaluate_piece_squares(self, board):
        """
        Evaluate piece placement using piece-square tables.
        """
        score = 0
        
        # White pawns
        for square in board.pieces(chess.PAWN, chess.WHITE):
            score += self.PAWN_SQUARES[square]
        
        # Black pawns (mirror the board)
        for square in board.pieces(chess.PAWN, chess.BLACK):
            score -= self.PAWN_SQUARES[chess.square_mirror(square)]
        
        # White knights
        for square in board.pieces(chess.KNIGHT, chess.WHITE):
            score += self.KNIGHT_SQUARES[square]
        
        # Black knights
        for square in board.pieces(chess.KNIGHT, chess.BLACK):
            score -= self.KNIGHT_SQUARES[chess.square_mirror(square)]
        
        # White bishops
        for square in board.pieces(chess.BISHOP, chess.WHITE):
            score += self.BISHOP_SQUARES[square]
        
        # Black bishops
        for square in board.pieces(chess.BISHOP, chess.BLACK):
            score -= self.BISHOP_SQUARES[chess.square_mirror(square)]
        
        # White rooks
        for square in board.pieces(chess.ROOK, chess.WHITE):
            score += self.ROOK_SQUARES[square]
        
        # Black rooks
        for square in board.pieces(chess.ROOK, chess.BLACK):
            score -= self.ROOK_SQUARES[chess.square_mirror(square)]
        
        # White queen
        for square in board.pieces(chess.QUEEN, chess.WHITE):
            score += self.QUEEN_SQUARES[square]
        
        # Black queen
        for square in board.pieces(chess.QUEEN, chess.BLACK):
            score -= self.QUEEN_SQUARES[chess.square_mirror(square)]
        
        # King (use endgame table if few pieces remain, else midgame)
        total_pieces = len(board.pieces(chess.PAWN, chess.WHITE)) + len(board.pieces(chess.PAWN, chess.BLACK))
        total_pieces += len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK))
        total_pieces += len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK))
        total_pieces += len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK))
        total_pieces += len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
        
        is_endgame = total_pieces <= 8  # Rough endgame detection
        
        king_table = self.KING_ENDGAME if is_endgame else self.KING_MIDGAME
        
        white_king_square = board.king(chess.WHITE)
        if white_king_square is not None:
            score += king_table[white_king_square]
        
        black_king_square = board.king(chess.BLACK)
        if black_king_square is not None:
            score -= king_table[chess.square_mirror(black_king_square)]
        
        return score


    

    def evaluate(self, board):
        """
        Comprehensive evaluation of a chess position.
        
        Returns score in centipawns:
        - Positive = White is better
        - Negative = Black is better
        - 0 = Roughly equal
        
        Args:
            board: python-chess Board object
        
        Returns:
            int: Score in centipawns
        """
        
        # Check for checkmate or stalemate (game-ending positions)
        if board.is_checkmate():
            # If it's white's turn and checkmate, black has won
            return -9999 if board.turn == chess.WHITE else 9999
        
        if board.is_stalemate():
            return 0  # Stalemate is a draw
        
        # Component scores
        material_score = self.evaluate_material(board)
        piece_square_score = self.evaluate_piece_squares(board)
        pawn_structure_white = self.evaluate_pawn_structure(board, chess.WHITE)
        pawn_structure_black = self.evaluate_pawn_structure(board, chess.BLACK)
        pawn_structure_score = pawn_structure_white - pawn_structure_black
        king_safety_white = self.evaluate_king_safety(board, chess.WHITE)
        king_safety_black = self.evaluate_king_safety(board, chess.BLACK)
        king_safety_score = king_safety_white - king_safety_black
        
        # Combine scores with weights
        # Adjust these weights to tune evaluation characteristics
        total_score = material_score * 1.0 + piece_square_score * 0.3 + pawn_structure_score * 0.5 + king_safety_score * 0.4 
        
        
        # Tempo bonus: small bonus for side to move
        if board.turn == chess.WHITE:
            total_score += 20
        else:
            total_score -= 20
        
        return int(total_score)
