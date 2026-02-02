import google.generativeai as genai
import os

async def generate_single_game_review(game_data: dict, player_name: str = None):
    """
    Gera uma análise narrativa, detectando a cor do usuário automaticamente.
    """
    
    headers = game_data.get("headers", {})
    
    user_color = "White"
    opponent_name = "Oponente"

    white_player = headers.get('White', '').lower()
    black_player = headers.get('Black', '').lower()
    target_name = player_name.lower() if player_name else ""

    if target_name and target_name in black_player:
        user_color = "Black"
        opponent_name = headers.get('White', 'Oponente')
    elif target_name and target_name in white_player:
        user_color = "White"
        opponent_name = headers.get('Black', 'Oponente')

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
    CONTEXTO DO JOGO:
    - Jogador Analisado ({user_color}): {player_name if player_name else 'Usuário'}
    - Oponente: {opponent_name}
    - Evento: {headers.get('Event', 'Partida Casual')}
    - Resultado: {headers.get('Result', '?')}
    
    PERFORMANCE DO JOGADOR ({user_color}):
    - Lances Brilhantes/Bons: {len(brilliants)}
    - Imprecisões: {len(inaccuracies)}
    - Erros (Mistakes): {len(mistakes)}
    - Erros Graves (Blunders): {len(blunders)}
    
    O MOMENTO CRÍTICO (Onde {user_color} pode ter errado):
    - Lance número: {worst_move['move_number'] if worst_move else 'N/A'}
    - Lance jogado: {worst_move['move_played'] if worst_move else 'N/A'}
    - Perda de vantagem (CP Loss): {worst_move['cp_loss']:.2f}
    """

    prompt = f"""
    Atue como um Grande Mestre de Xadrez e treinador.
    Analise o jogo focando APENAS na performance do jogador de {user_color} (que é o meu aluno, {player_name}).
    Ignore os erros do oponente, foque no que o aluno fez.

    DADOS DA PARTIDA:
    {game_summary}

    SUA TAREFA:
    Escreva um feedback direto para o aluno ({user_color}) em formato Markdown.
    
    ESTRUTURA:
    ### ♟️ Resumo da Partida
    (Como {player_name} se saiu contra {opponent_name}?)

    ### 🚨 O Momento Decisivo
    (Analise o erro crítico do aluno).

    ### 💡 Dica para o Próximo Jogo
    (Conselho prático).

    Tom: Educativo e motivador. Português do Brasil.
    """

    try:
        model = genai.GenerativeModel('gemini-flash-latest') 
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        return f"Desculpe, não consegui analisar sua partida agora. Erro: {str(e)}"