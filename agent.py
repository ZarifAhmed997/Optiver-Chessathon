

from evaluation import Evaluation
from search import Search
import chess.polyglot
import chess

# Import time runs once per game, inside a 60 second budget, before your clock starts.
# Load weights and build tables out here, not inside get_move.

book = {}
with chess.polyglot.open_reader("book.bin") as reader:
    for entry in reader:
        key = entry.key  
        if key not in book:
            book[key] = entry.move

def get_book_move(board):
    key = chess.polyglot.zobrist_hash(board)
    move = book.get(key)
    return move.uci() if move else None

evaluator = Evaluation()
search = Search(evaluator)

def get_move(fen: str, time_left_ms: int) -> str:
    """Return a legal move in UCI notation.

    fen           the position to move in; your colour is the side to move
    time_left_ms  your clock before this move, in milliseconds
    returns       "e2e4", or "e7e8q" for a promotion

    The process stays alive between your moves, so state you keep on a module or in a
    closure survives to the next call. It does not survive to the next game.

    print() is safe. Your stdout is redirected away from the protocol stream, discarded
    during rated games and shown back to you in the validation log.
    """

    board = chess.Board(fen)

    book_move = get_book_move(board)
    if book_move:
        print(f"Book move: {book_move}")
        return book_move

    move = search.get_move(fen, time_left_ms)
    print(f"Move {board.fullmove_number}: {move}")

    # Everything from here down is yours to replace. baselines/greedy searches one ply,
    # baselines/minimax searches two. Neither is strong. Reading them is the fastest way
    # to see the shape of a search, and beating them is the first real milestone.
    return move


