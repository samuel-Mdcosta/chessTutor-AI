from app.service.pgn_parser import parse_pgn
import chess.pgn
import io
from app.core.stockfish import analyze_position, get_engine

def analyze_game(pgn_text: str):
    positions = parse_pgn(pgn_text)

    return {
        "total_moves": len(positions),
        "positions": positions
    }

async def process_full_game(pgn_text: str):
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)

    if not game:
        return {"error": "Invalid PGN"}
    
    board = game.board()
    analysis_results = []

    engine = get_engine()

    # Analisa cada posicao no jogo #
    try:
        initial_event = analyze_position(engine, board)
        analysis_results.append({
            "move_number": 0,
            "move_played": "Start",
            **initial_event
        })
        move_count = 1
        for move in game.mainline_moves():
            board.push(move)
            eval_data = analyze_position(engine, board, time_limit=0.1)
            analysis_results.append({
                "move_number": move_count,
                "move_played": str(move), # O lance que o humano fez
                **eval_data # Os dados do Stockfish (melhor lance, avaliação)
            })
            move_count += 1
    finally:
        engine.quit()

    return {
            "headers": dict(game.headers),
            "analysis": analysis_results
        }