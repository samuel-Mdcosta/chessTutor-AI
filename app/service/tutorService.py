from fastapi import HTTPException
import logging
import asyncio
from datetime import datetime, timezone
from app.database.mongo import get_database
from app.ia.client import get_gemini_analysis
from app.service.game_analysis import process_full_game

logger = logging.getLogger("tutorService")


def _aggregate_stockfish_data(games_analysis: list[dict], username: str) -> dict:
    """Agrega dados do Stockfish de múltiplas partidas em estatísticas por cor."""
    stats = {
        "White": {"wins": 0, "losses": 0, "draws": 0, "blunders": 0, "mistakes": 0, "inaccuracies": 0, "best_moves": 0, "total_moves": 0, "games": 0},
        "Black": {"wins": 0, "losses": 0, "draws": 0, "blunders": 0, "mistakes": 0, "inaccuracies": 0, "best_moves": 0, "total_moves": 0, "games": 0},
    }
    openings = {"White": {}, "Black": {}}
    worst_blunders = []

    for game in games_analysis:
        headers = game.get("headers", {})
        analysis = game.get("analysis", [])
        result = headers.get("Result", "*")
        eco = headers.get("ECO", "?")
        opening = headers.get("Opening", headers.get("ECO", "Desconhecida"))
        white = headers.get("White", "").lower()
        black = headers.get("Black", "").lower()
        target = username.lower()

        if target in white:
            color = "White"
            won = result == "1-0"
            lost = result == "0-1"
        elif target in black:
            color = "Black"
            won = result == "0-1"
            lost = result == "1-0"
        else:
            continue

        drew = result == "1/2-1/2"
        s = stats[color]
        s["games"] += 1
        if won:
            s["wins"] += 1
        elif lost:
            s["losses"] += 1
        elif drew:
            s["draws"] += 1

        # Contagem de abertura
        eco_key = f"{eco} — {opening}" if eco != "?" else opening
        openings[color][eco_key] = openings[color].get(eco_key, 0) + 1

        user_moves = [m for m in analysis if m.get("color", "").lower() == color.lower()]
        s["total_moves"] += len(user_moves)
        for m in user_moves:
            cls = m.get("classification", "")
            if cls == "Blunder":
                s["blunders"] += 1
                worst_blunders.append({
                    "game": f"{headers.get('White')} vs {headers.get('Black')} ({result})",
                    "color": color,
                    "move_number": (m["move_number"] + 1) // 2,
                    "move_played": m.get("move_played", "?"),
                    "best_move": m.get("best_move", "?"),
                    "cp_loss": m.get("cp_loss", 0),
                })
            elif cls == "Mistake":
                s["mistakes"] += 1
            elif cls == "Inaccuracy":
                s["inaccuracies"] += 1
            elif cls in ("Best Move", "Excellent"):
                s["best_moves"] += 1

    worst_blunders.sort(key=lambda x: x["cp_loss"], reverse=True)

    return {
        "stats": stats,
        "openings": openings,
        "worst_blunders": worst_blunders[:10],
    }


def _build_grounded_prompt(username: str, aggregated: dict, total_games: int) -> str:
    stats = aggregated["stats"]
    openings = aggregated["openings"]
    worst_blunders = aggregated["worst_blunders"]

    def fmt_color(color: str) -> str:
        s = stats[color]
        if s["games"] == 0:
            return f"  {color}: sem partidas registradas"
        accuracy = round(s["best_moves"] / s["total_moves"] * 100, 1) if s["total_moves"] > 0 else 0
        blunder_rate = round(s["blunders"] / s["total_moves"] * 100, 1) if s["total_moves"] > 0 else 0
        top_openings = sorted(openings[color].items(), key=lambda x: x[1], reverse=True)[:5]
        openings_str = "\n".join(f"    - {name}: {count}x" for name, count in top_openings) or "    - Nenhuma registrada"
        return (
            f"  {color}:\n"
            f"    Partidas: {s['games']} | Vitórias: {s['wins']} | Derrotas: {s['losses']} | Empates: {s['draws']}\n"
            f"    Lances analisados: {s['total_moves']}\n"
            f"    Blunders: {s['blunders']} ({blunder_rate}% dos lances) | Mistakes: {s['mistakes']} | Imprecisões: {s['inaccuracies']}\n"
            f"    Melhores lances / Excelentes: {s['best_moves']} ({accuracy}% dos lances)\n"
            f"    Aberturas mais usadas:\n{openings_str}"
        )

    blunders_str = ""
    if worst_blunders:
        lines = []
        for b in worst_blunders:
            lines.append(
                f"  - Partida: {b['game']} | Lance {b['move_number']} | "
                f"Jogou: {b['move_played']} | Melhor: {b['best_move']} | Perda: {b['cp_loss']:.0f} cp"
            )
        blunders_str = "\n".join(lines)
    else:
        blunders_str = "  Nenhum blunder registrado."

    return f"""Você é um treinador de xadrez experiente. Analise o desempenho do jogador **{username}** com base EXCLUSIVAMENTE nos dados estatísticos abaixo, gerados pelo motor Stockfish. Não invente lances, avaliações ou padrões que não estejam nos dados fornecidos.

DADOS OBJETIVOS (gerados pelo Stockfish — {total_games} partidas analisadas):

DESEMPENHO POR COR:
{fmt_color("White")}

{fmt_color("Black")}

PIORES BLUNDERS (ordenados por perda em centipeões):
{blunders_str}

TAREFAS (baseie-se SOMENTE nos dados acima):

1. DESEMPENHO POR COR
   - Compare vitórias/derrotas/empates e taxa de blunders entre brancas e pretas
   - Identifique com qual cor o jogador é mais consistente e explique por quê com base nos números

2. ANÁLISE DE ABERTURAS
   - Com base nas aberturas mais jogadas, comente se há concentração em um repertório específico
   - Indique se a diversidade ou falta dela pode estar impactando o desempenho (use os números de vitórias/derrotas por abertura se disponíveis)

3. PADRÕES DE ERRO
   - Analise os blunders listados: há padrões (fase do jogo, cor, tipo de lance)?
   - Classifique os erros como táticos, estratégicos ou de cálculo com base no contexto dos lances fornecidos

4. PLANO DE TREINO PERSONALIZADO
   Curto prazo (até 2 semanas):
   - Exercícios táticos baseados nos padrões de erro identificados
   - Foco objetivo e mensurável

   Médio prazo (até 1 mês):
   - Consolidação de repertório de aberturas
   - Fase do jogo mais frágil (deduza da taxa de erros)

   Longo prazo:
   - Recomende 2-3 livros clássicos relevantes para as fraquezas identificadas
   - Sugira temas de estudo contínuo

REGRAS:
- Use apenas os dados fornecidos
- Se um dado não for conclusivo, diga explicitamente
- Linguagem técnica, clara e motivadora em PT-BR
- Formato Markdown com títulos
"""


async def generate_coach_report(username: str):
    db = await get_database()

    user = await db["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    cursor = db["games"].find({"user_id": str(user["_id"])}).sort("created_at", -1).limit(20)
    games = await cursor.to_list(length=None)

    if not games:
        return {
            "player": username,
            "message": "Nenhuma partida encontrada para análise. Jogue ou importe partidas primeiro."
        }

    logger.info(f"Rodando Stockfish em {len(games)} partidas para {username}")

    tasks = [
        process_full_game(game.get("original_pgn") or game.get("pgn", ""))
        for game in games
        if (game.get("original_pgn") or game.get("pgn", "")).strip()
    ]
    games_analysis = await asyncio.gather(*tasks, return_exceptions=True)

    valid_analyses = [g for g in games_analysis if isinstance(g, dict) and "analysis" in g]

    if not valid_analyses:
        raise HTTPException(status_code=422, detail="Não foi possível analisar nenhuma partida.")

    aggregated = _aggregate_stockfish_data(valid_analyses, username)
    prompt = _build_grounded_prompt(username, aggregated, len(valid_analyses))

    logger.info(f"Gerando relatório para {username} com {len(valid_analyses)} partidas analisadas pelo Stockfish")
    ai_response = await get_gemini_analysis(prompt)

    return {
        "player": username,
        "games_analyzed": len(valid_analyses),
        "tutor_report": ai_response
    }


async def get_chache(pgn_hash: str):
    db = await get_database()
    chached = await db["tutor_cache"].find_one({"pgn_hash": pgn_hash})
    if chached:
        return chached['result']
    return None


async def save_cache(pgn_hash: str, result: str):
    db = await get_database()
    await db["tutor_cache"].update_one(
        {"pgn_hash": pgn_hash},
        {"$set": {"result": result, "created_at": datetime.now(timezone.utc)}},
        upsert=True
    )
