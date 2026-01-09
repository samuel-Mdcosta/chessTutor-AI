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

def normalize_score(evaluation):
    if evaluation["type"] == "mate":
        sign = 1 if evaluation["value"] > 0 else -1
        return sign * (10000 - abs(evaluation["value"]) * 100)
    return evaluation["value"]

def get_move_category(diff_cp):
    if diff_cp <= 0:
        return "Best Move"      # Jogou tão bem quanto (ou melhor que) a engine esperava
    elif diff_cp <= 25:
        return "Excellent"      # Perda insignificante
    elif diff_cp <= 75:
        return "Good"           # Perda pequena
    elif diff_cp <= 150:
        return "Inaccuracy"     # ?! Imprecisão
    elif diff_cp <= 400:
        return "Mistake"        # ? Erro
    else:
        return "Blunder"        # ?? Erro Grave (Capivarada)

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
        initial_event = analyze_position(engine, board, time_limit=0.1)
        prev_score_val = normalize_score(initial_event["evaluation"])
        analysis_results.append({
            "move_number": 0,
            "move_played": "Start",
            **initial_event,
            "classification": "Book" #posicao inicial#
        })
        move_count = 1
        for move in game.mainline_moves():
            #verifica quem joga#
            white_turn = board.turn

            board.push(move)

            eval_data = analyze_position(engine, board, time_limit=0.1)
            current_score_val = normalize_score(eval_data["evaluation"])

            if white_turn:
                cp_loss = prev_score_val - current_score_val
            else:
                cp_loss = current_score_val - prev_score_val

            classification = get_move_category(cp_loss)
            analysis_results.append({
                "move_number": move_count,
                "color": "White" if white_turn else "Black",
                "move_played": str(move),
                "classification": classification,
                "cp_loss": cp_loss,
                **eval_data # Os dados do Stockfish (melhor lance, avaliação)
            })

            prev_score_val = current_score_val
            move_count += 1
            
    finally:
        engine.quit()

    return {
            "headers": dict(game.headers),
            "analysis": analysis_results
        }