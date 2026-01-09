from app.service.pgn_parser import parse_pgn

def analyze_game(pgn_text: str):
    positions = parse_pgn(pgn_text)

    return {
        "total_moves": len(positions),
        "positions": positions
    }
