from app.ia.client import get_gemini_analysis

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
    """

    prompt = f"""
    Atue como um Treinador de Xadrez Pessoal.
    Analise a partida focando EXCLUSIVAMENTE no jogador de {user_color} (que é o usuário).

    DADOS:
    {game_summary}

    TAREFA E REGRAS:
    1. Escreva um feedback curto, útil e motivador em Markdown (PT-BR).
    2. Não critique o oponente, foque em como o aluno pode melhorar.
    3. CRÍTICO: Use APENAS os números fornecidos nos dados acima. NUNCA invente lances, movimentos ou números diferentes dos que estão nos dados.
    4. IMPORTANTE: Você NÃO tem acesso ao tabuleiro. NÃO invente análises táticas específicas, NÃO adivinhe quais peças estavam envolvidas e NÃO suponha a fase do jogo.
    5. Limite seus conselhos à consistência geral baseada no número de erros e acertos fornecidos.
    """

    try:
        return await get_gemini_analysis(prompt)
    except Exception as e:
        return f"Erro na IA: {str(e)}"