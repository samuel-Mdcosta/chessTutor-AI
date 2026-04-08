import math
from app.ia.client import get_gemini_analysis


# --- Helpers ---

def _calc_accuracy(user_moves: list[dict]) -> float:
    """Aproximação da precisão usando fórmula baseada na perda média em centipeões."""
    if not user_moves:
        return 0.0
    avg_cp = sum(max(0, m.get("cp_loss", 0)) for m in user_moves) / len(user_moves)
    return round(max(0.0, min(100.0, 103.1668 * math.exp(-0.04354 * avg_cp) - 3.1669)), 1)


def _get_phase(move_number: int) -> str:
    """Classifica o lance em fase do jogo pelo número do semilance."""
    if move_number <= 14:
        return "opening"
    elif move_number <= 60:
        return "middlegame"
    else:
        return "endgame"


def _phase_quality(moves: list[dict]) -> str:
    """Retorna '✓ Boa' / '?! Regular' / '✗ Fraca' com base na taxa de erros."""
    if not moves:
        return "— Sem lances"
    total = len(moves)
    errors = sum(1 for m in moves if m["classification"] in ("Blunder", "Mistake", "Miss", "Inaccuracy"))
    rate = errors / total
    if rate <= 0.10:
        return "✓ Boa"
    elif rate <= 0.25:
        return "?! Regular"
    else:
        return "✗ Fraca"


def _format_move(m: dict) -> str:
    chess_num = (m["move_number"] + 1) // 2
    cp = m.get("cp_loss", 0)
    played = m.get("move_played", "?")
    best = m.get("best_move", "?")
    eval_data = m.get("evaluation", {})
    if eval_data.get("type") == "mate":
        eval_str = f"mate em {eval_data['value']}"
    else:
        val = eval_data.get("value", 0) or 0
        eval_str = f"{val / 100:.2f} pawns"
    return (
        f"  Lance {chess_num}: jogou {played} | melhor: {best} "
        f"| perda: {cp:.0f} cp | avaliação após: {eval_str}"
    )


# --- Main ---

async def generate_single_game_review(
    game_data: dict,
    player_name: str = None,
    player_color: str = None,
):
    headers = game_data.get("headers", {})

    # Determinar cor do usuário
    if player_color == "white":
        user_color = "White"
    elif player_color == "black":
        user_color = "Black"
    else:
        white_player = headers.get("White", "").lower().strip()
        black_player = headers.get("Black", "").lower().strip()
        target = player_name.lower().strip() if player_name else ""
        if target and target in black_player:
            user_color = "Black"
        elif target and target in white_player:
            user_color = "White"
        else:
            user_color = "White"

    display_player = headers.get(user_color, "Você")
    display_opponent = headers.get("Black" if user_color == "White" else "White", "Oponente")

    moves = game_data.get("analysis", [])
    user_moves = [m for m in moves if m.get("color", "").lower() == user_color.lower()]

    # --- Contagem de categorias ---
    counts = {
        "Brilhante": 0,       # Não detectado automaticamente ainda
        "Excelente": 0,
        "Livro": 0,
        "Melhor": 0,
        "Ótimo": 0,
        "Bom": 0,
        "Imprecisão": 0,
        "Erro": 0,
        "Chance Perdida": 0,
        "Capivarada": 0,
    }
    cls_map = {
        "Excellent": "Excelente",
        "Book":      "Livro",
        "Best Move": "Melhor",
        "Great":     "Ótimo",
        "Good":      "Bom",
        "Inaccuracy":"Imprecisão",
        "Mistake":   "Erro",
        "Miss":      "Chance Perdida",
        "Blunder":   "Capivarada",
    }
    for m in user_moves:
        pt = cls_map.get(m.get("classification", ""), None)
        if pt and pt in counts:
            counts[pt] += 1

    # --- Precisão ---
    accuracy = _calc_accuracy(user_moves)

    # --- Avaliação por fase ---
    opening_moves  = [m for m in user_moves if _get_phase(m["move_number"]) == "opening"]
    middle_moves   = [m for m in user_moves if _get_phase(m["move_number"]) == "middlegame"]
    endgame_moves  = [m for m in user_moves if _get_phase(m["move_number"]) == "endgame"]

    phase_eval = {
        "Abertura":   _phase_quality(opening_moves),
        "Meio-jogo":  _phase_quality(middle_moves),
        "Final":      _phase_quality(endgame_moves),
    }

    # --- Erros críticos para o prompt ---
    blunders  = [m for m in user_moves if m["classification"] == "Blunder"]
    mistakes  = [m for m in user_moves if m["classification"] == "Mistake"]
    misses    = [m for m in user_moves if m["classification"] == "Miss"]

    critical_lines = []
    if blunders:
        critical_lines.append("\nCAPIVARADAS (Blunders):")
        for m in sorted(blunders, key=lambda x: x.get("cp_loss", 0), reverse=True)[:5]:
            critical_lines.append(_format_move(m))
    if misses:
        critical_lines.append("\nCHANCES PERDIDAS (posição vencedora, continuação desperdiçada):")
        for m in sorted(misses, key=lambda x: x.get("cp_loss", 0), reverse=True)[:3]:
            critical_lines.append(_format_move(m))
    if mistakes:
        critical_lines.append("\nERROS (Mistakes):")
        for m in sorted(mistakes, key=lambda x: x.get("cp_loss", 0), reverse=True)[:5]:
            critical_lines.append(_format_move(m))

    critical_text = "\n".join(critical_lines) or "  Nenhum erro grave registrado."

    # --- Abertura ---
    opening_name = headers.get("Opening", headers.get("ECO", "Desconhecida"))
    eco = headers.get("ECO", "?")
    total_chess_moves = (len(moves) - 1 + 1) // 2

    # --- Rating ---
    rating = headers.get(f"WhiteElo" if user_color == "White" else "BlackElo", "?")

    # --- Montar bloco de estatísticas ---
    stats_block = f"""
ESTATÍSTICAS DA PARTIDA ({user_color} — {display_player}):
  Precisão:       {accuracy}%
  Rating:         {rating}
  Resultado:      {headers.get('Result', '?')}
  Total de lances do usuário: {len(user_moves)} (em {total_chess_moves} lances totais)

CONTAGEM DE LANCES:
  Brilhante:      {counts['Brilhante']}
  Excelente:      {counts['Excelente']}
  Livro:          {counts['Livro']}
  Melhor:         {counts['Melhor']}
  Ótimo:          {counts['Ótimo']}
  Bom:            {counts['Bom']}
  Imprecisão:     {counts['Imprecisão']}
  Erro:           {counts['Erro']}
  Chance Perdida: {counts['Chance Perdida']}
  Capivarada:     {counts['Capivarada']}

AVALIAÇÃO POR FASE:
  Abertura:   {phase_eval['Abertura']}
  Meio-jogo:  {phase_eval['Meio-jogo']}
  Final:       {phase_eval['Final']}

ABERTURA JOGADA:
  ECO: {eco} — {opening_name}
  Lances de teoria (Livro): {counts['Livro']}

ERROS CRÍTICOS (dados do Stockfish):
{critical_text}
"""

    prompt = f"""
Você é um Treinador de Xadrez Pessoal. Analise esta partida focando EXCLUSIVAMENTE no jogador de {user_color} ({display_player}).
Oponente: {display_opponent}.

DADOS OBJETIVOS (gerados pelo Stockfish — não altere nenhum valor):
{stats_block}

REGRAS ABSOLUTAS:
1. Cite os lances EXATAMENTE no formato UCI como estão nos dados (ex: e2e4, g1f3). NÃO converta para notação algébrica.
2. NÃO invente lances, avaliações ou variantes que não estejam nos dados.
3. Use apenas o que está nos dados acima como base factual.

ESTRUTURA OBRIGATÓRIA DA RESPOSTA (em Markdown, PT-BR):

### Ficha da Partida
Reproduza as estatísticas em formato de tabela ou lista organizada:
- Precisão, Rating, Resultado
- Contagem completa de lances (Brilhante até Capivarada)
- Avaliação por fase (Abertura, Meio-jogo, Final)

### Análise da Abertura
- Identifique a abertura ({eco} — {opening_name}) e explique brevemente seus princípios estratégicos
- Avalie se o jogador saiu da teoria cedo ou tarde (baseado nos {counts['Livro']} lances de livro)
- A fase de abertura foi classificada como: {phase_eval['Abertura']} — explique o que isso indica

### Análise do Meio-jogo
- A fase de meio-jogo foi classificada como: {phase_eval['Meio-jogo']} — explique causas com base nos erros listados
- Identifique o TEMA TÁTICO central que o jogador perdeu (garfo, fita, cravada, ataque ao rei, etc.) baseado nos lances errados
- Explique o que provavelmente aconteceu taticamente em cada blunder/miss/mistake listado
- Qual padrão recorrente causou a maioria dos erros nesta fase?

### Análise do Final
- A fase final foi classificada como: {phase_eval['Final']}
- Se houve erros no final, explique o conceito técnico que deveria ter sido aplicado

### Erros Críticos (análise individual)
Para cada Capivarada e Chance Perdida listada:
- Número do lance e o que foi jogado vs o que o Stockfish sugeria
- Breve explicação tática/estratégica do por que o lance do Stockfish seria superior
- Que tipo de erro foi: tático, estratégico ou cálculo?

### Plano de Melhoria
Curto prazo (baseado nos erros desta partida):
- Exercício específico para o padrão tático mais recorrente identificado

Longo prazo:
- 1-2 recomendações de estudo relacionadas às fraquezas identificadas
"""

    try:
        return await get_gemini_analysis(prompt)
    except Exception as e:
        return f"Erro na IA: {str(e)}"
