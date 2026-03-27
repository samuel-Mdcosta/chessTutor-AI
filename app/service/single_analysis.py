from app.ia.client import get_gemini_analysis

def _format_move_detail(m: dict) -> str:
    chess_num = (m['move_number'] + 1) // 2
    cp_loss = m.get('cp_loss', 0)
    move_played = m.get('move_played', '?')
    best_move = m.get('best_move', '?')
    eval_data = m.get('evaluation', {})
    if eval_data.get('type') == 'mate':
        eval_str = f"mate em {eval_data['value']}"
    else:
        val = eval_data.get('value', 0) or 0
        eval_str = f"{val/100:.2f} pawns"
    return f"  Lance {chess_num}: jogou {move_played} | melhor: {best_move} | perda: {cp_loss:.0f} cp | avaliação após: {eval_str}"

async def generate_single_game_review(game_data: dict, player_name: str = None, player_color: str = None):
    """
    Gera análise para o usuário. Se player_color for fornecido ('white'/'black'),
    usa esse valor diretamente. Caso contrário, tenta detectar pelo nome.
    """

    headers = game_data.get("headers", {})

    user_color = ""

    if player_color == "white":
        user_color = "White"
    elif player_color == "black":
        user_color = "Black"
    else:
        white_player = headers.get('White', '').lower().strip()
        black_player = headers.get('Black', '').lower().strip()

        target_name = player_name.lower().strip() if player_name else ""
        if target_name and target_name in black_player:
            user_color = "Black"
        elif target_name and target_name in white_player:
            user_color = "White"

    if user_color == "White":
        display_player = headers.get('White', 'Você')
        display_opponent = headers.get('Black', 'Oponente')
    else:
        display_player = headers.get('Black', 'Você')
        display_opponent = headers.get('White', 'Oponente')

    moves = game_data.get("analysis", [])

    total_plies = len(moves) - 1
    total_chess_moves = (total_plies + 1) // 2

    user_moves = [m for m in moves if m.get("color", "").lower() == user_color.lower()]

    blunders = [m for m in user_moves if m["classification"] == "Blunder"]
    mistakes = [m for m in user_moves if m["classification"] == "Mistake"]
    inaccuracies = [m for m in user_moves if m["classification"] == "Inaccuracy"]
    brilliants = [m for m in user_moves if m["classification"] in ["Best Move", "Excellent"]]

    worst_move = None
    if user_moves:
        worst_move = max(user_moves, key=lambda x: x.get("cp_loss", 0))

    worst_move_chess_number = (worst_move['move_number'] + 1) // 2 if worst_move else None

    # Detalhes dos erros mais críticos para embasar os comentários da IA
    critical_moves_lines = []
    if blunders:
        critical_moves_lines.append("\nERROS GRAVES (Blunders) — avaliados pelo Stockfish:")
        for m in sorted(blunders, key=lambda x: x.get("cp_loss", 0), reverse=True)[:5]:
            critical_moves_lines.append(_format_move_detail(m))
    if mistakes:
        critical_moves_lines.append("\nERROS (Mistakes) — avaliados pelo Stockfish:")
        for m in sorted(mistakes, key=lambda x: x.get("cp_loss", 0), reverse=True)[:5]:
            critical_moves_lines.append(_format_move_detail(m))

    critical_moves_text = "\n".join(critical_moves_lines)

    worst_move_detail = ""
    if worst_move:
        worst_move_detail = (
            f"Lance {worst_move_chess_number}: jogou {worst_move.get('move_played', '?')} "
            f"| melhor: {worst_move.get('best_move', '?')} "
            f"| perda: {worst_move.get('cp_loss', 0):.0f} cp"
        )

    game_summary = f"""
    CONTEXTO:
    - O Usuário ({player_name}) jogando de: {user_color}
    - Nome no PGN: {display_player}
    - Oponente: {display_opponent}
    - Resultado: {headers.get('Result', '?')}
    - Total de lances na partida: {total_chess_moves} (lances de xadrez reais)
    - Total de lances do usuário analisados: {len(user_moves)}

    ESTATÍSTICAS ({user_color}):
    - Melhores Lances/Excelentes: {len(brilliants)}
    - Erros Graves (Blunders): {len(blunders)}
    - Erros (Mistakes): {len(mistakes)}
    - Imprecisões: {len(inaccuracies)}

    PIOR MOMENTO:
    - Lance de xadrez número {worst_move_chess_number if worst_move else '?'} (de {total_chess_moves} no total)
    {worst_move_detail}
    {critical_moves_text}
    """

    prompt = f"""
    Atue como um Treinador de Xadrez Pessoal.
    Analise a partida focando EXCLUSIVAMENTE no jogador de {user_color} (que é o usuário).

    DADOS (gerados pelo motor Stockfish — avaliações são objetivas):
    {game_summary}

    NOTAÇÃO: Os lances estão em UCI (origem+destino). Exemplos: e2e4 = peão e2→e4, g1f3 = cavalo g1→f3, e1g1 = roque curto das brancas. Converta para notação algébrica ao citar os lances.

    TAREFA E REGRAS:
    1. Escreva um feedback curto, útil e motivador em Markdown (PT-BR).
    2. Não critique o oponente, foque em como o aluno pode melhorar.
    3. CRÍTICO: Use APENAS os dados fornecidos acima. NUNCA invente lances ou avaliações diferentes dos que estão nos dados.
    4. Para cada blunder/mistake listado, explique brevemente o que provavelmente aconteceu e por que o lance sugerido pelo Stockfish seria superior.
    5. Baseie comentários táticos SOMENTE nos lances listados. Não analise posições não fornecidas.
    """

    try:
        return await get_gemini_analysis(prompt)
    except Exception as e:
        return f"Erro na IA: {str(e)}"