import google.generativeai as genai
import os

async def generate_single_game_review(game_data: dict, player_name: str = None):
    """
    Gera análise tentando detectar automaticamente a cor do usuário.
    """
    
    headers = game_data.get("headers", {})
    
    user_color = "White" 
    
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
    
    user_moves = [m for m in moves if m.get("color", "").lower() == user_color.lower()]
    
    blunders = [m for m in user_moves if m["classification"] == "Blunder"]
    mistakes = [m for m in user_moves if m["classification"] == "Mistake"]
    inaccuracies = [m for m in user_moves if m["classification"] == "Inaccuracy"]
    brilliants = [m for m in user_moves if m["classification"] in ["Best Move", "Excellent"]]

    worst_move = None
    if user_moves:
        worst_move = max(user_moves, key=lambda x: x.get("cp_loss", 0))

    game_summary = f"""
    CONTEXTO:
    - O Usuário ({player_name}) foi identificado jogando de: {user_color}
    - Nome no PGN: {display_player}
    - Oponente: {display_opponent}
    - Resultado: {headers.get('Result', '?')}
    
    ESTATÍSTICAS ({user_color}):
    - Melhores Lances/Excelentes: {len(brilliants)}
    - Erros Graves (Blunders): {len(blunders)}
    - Erros (Mistakes): {len(mistakes)}
    
    PIOR MOMENTO:
    - Lance {worst_move['move_number'] if worst_move else '?'}: {worst_move['move_played'] if worst_move else '?'}
    """

    prompt = f"""
    Atue como um Treinador de Xadrez Pessoal.
    Analise a partida focando EXCLUSIVAMENTE no jogador de {user_color} (que é o usuário).
    
    DADOS:
    {game_summary}
    
    TAREFA E REGRAS:
    1. Escreva um feedback curto, útil e motivador em Markdown (PT-BR).
    2. Não critique o oponente, foque em como o aluno pode melhorar.
    3. IMPORTANTE: Você NÃO tem acesso ao tabuleiro (FEN). Portanto, NÃO invente análises táticas específicas, NÃO adivinhe quais peças estavam envolvidas no pior lance e NÃO suponha a fase do jogo (abertura, meio-jogo ou final).
    4. Limite seus conselhos à consistência geral baseada no número de erros e acertos.
    """

    try:
        model = genai.GenerativeModel('gemini-flash-latest') 
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        return f"Erro na IA: {str(e)}"