from app.service.pgn_parser import parse_pgn
import chess.pgn
import io
import asyncio
from app.core.stockfish import analyze_position, acquire_engine, release_engine

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

def get_move_category(diff_cp, player_was_winning: bool = False, is_opening: bool = False):
    if is_opening and diff_cp <= 0:
        return "Book"           # Teoria de abertura
    if diff_cp <= 0:
        return "Best Move"      # Melhor lance possível
    elif diff_cp <= 25:
        return "Excellent"      # Excelente
    elif diff_cp <= 50:
        return "Great"          # Ótimo
    elif diff_cp <= 100:
        return "Good"           # Bom
    elif diff_cp <= 200:
        return "Inaccuracy"     # ?! Imprecisão
    elif diff_cp <= 400:
        if player_was_winning:
            return "Miss"       # Chance Perdida — posição vencedora, mas perdeu a continuação
        return "Mistake"        # ? Erro
    else:
        return "Blunder"        # ?? Capivarada

def _run_stockfish_analysis(pgn_text: str):
    """Executa análise Stockfish de forma síncrona (será chamada em thread separada)."""
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)

    if not game:
        return {"error": "Invalid PGN"}

    board = game.board()
    analysis_results = []

    engine = acquire_engine()

    try:
        initial_event = analyze_position(engine, board, time_limit=0.1)
        prev_score_val = normalize_score(initial_event["evaluation"])

        prev_best_move = initial_event.get("best_move")

        analysis_results.append({
            "move_number": 0,
            "move_played": "Start",
            "evaluation": initial_event["evaluation"],
            "classification": "Book"
        })
        move_count = 1
        for move in game.mainline_moves():
            white_turn = board.turn
            best_move_for_this_turn = prev_best_move
            board.push(move)

            eval_data = analyze_position(engine, board, time_limit=0.1)
            current_score_val = normalize_score(eval_data["evaluation"])

            if white_turn:
                cp_loss = prev_score_val - current_score_val
                player_was_winning = prev_score_val > 300
            else:
                cp_loss = current_score_val - prev_score_val
                player_was_winning = prev_score_val < -300

            is_opening = move_count <= 14  # ~7 lances por lado = fase de abertura
            classification = get_move_category(cp_loss, player_was_winning=player_was_winning, is_opening=is_opening)
            analysis_results.append({
                "move_number": move_count,
                "color": "White" if white_turn else "Black",
                "move_played": str(move),
                "best_move": best_move_for_this_turn,
                "classification": classification,
                "cp_loss": cp_loss,
                **eval_data
            })

            prev_score_val = current_score_val
            prev_best_move = eval_data.get("best_move")
            move_count += 1

    finally:
        release_engine(engine)

    return {
        "headers": dict(game.headers),
        "analysis": analysis_results
    }

async def process_full_game(pgn_text: str):
    """Roda análise Stockfish em thread separada para não bloquear o event loop."""
    return await asyncio.to_thread(_run_stockfish_analysis, pgn_text)