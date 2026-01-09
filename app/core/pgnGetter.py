import chess.pgn
from io import StringIO

def pgn_game(pgn_text):
    game = chess.pgn.read_game(StringIO(pgn_text))
    board = game.board()
    moves = []

    for move in game.mainline_moves():
        board.push(move)
        moves.append(board.fen())

    return moves