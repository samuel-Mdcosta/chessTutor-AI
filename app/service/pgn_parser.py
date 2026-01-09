import chess.pgn
from io import StringIO

def parse_pgn(pgn_text: str):
    game = chess.pgn.read_game(StringIO(pgn_text))

    if game is None:
        raise ValueError("PGN inválido ou vazio")

    board = game.board()
    positions = []

    for move in game.mainline_moves():
        board.push(move)
        positions.append({
            "fen": board.fen(),
            "move": board.peek().uci()
        })

    return positions
