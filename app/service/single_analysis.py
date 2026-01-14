import google.generativeai as genai
import os

# Certifique-se de configurar sua chave em algum lugar do projeto
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_single_game_review(game_data: dict, user_color: str):
    """
    Gera uma análise narrativa para uma única partida.
    
    :param game_data: O dicionário retornado pela sua função 'process_full_game'
    :param user_color: "White" ou "Black" (a cor que o usuário jogou)
    :return: String (Markdown) com a análise da IA.
    """
    
    # 1. Extraindo dados básicos do JSON do Stockfish
    headers = game_data.get("headers", {})
    moves = game_data.get("analysis", [])
    
    # Filtra apenas os lances do usuário
    user_moves = [m for m in moves if m.get("color", "").lower() == user_color.lower()]
    
    # Coleta estatísticas rápidas
    blunders = [m for m in user_moves if m["classification"] == "Blunder"]
    mistakes = [m for m in user_moves if m["classification"] == "Mistake"]
    inaccuracies = [m for m in user_moves if m["classification"] == "Inaccuracy"]
    brilliants = [m for m in user_moves if m["classification"] in ["Best Move", "Excellent"]]

    # Encontra o PIOR lance da partida (maior perda de centipawns)
    worst_move = None
    if user_moves:
        worst_move = max(user_moves, key=lambda x: x.get("cp_loss", 0))

    # 2. Montando o Prompt Simplificado
    # Em vez de mandar o PGN cru, mandamos o "Boletim" que o Python gerou.
    
    game_summary = f"""
    CONTEXTO DO JOGO:
    - Evento: {headers.get('Event', 'Partida Casual')}
    - Jogador ({user_color}): {headers.get('White' if user_color == 'White' else 'Black', 'Usuário')}
    - ELO: {headers.get('WhiteElo' if user_color == 'White' else 'BlackElo', '?')}
    - Resultado: {headers.get('Result', '?')}
    
    PERFORMANCE DO JOGADOR:
    - Lances Brilhantes/Bons: {len(brilliants)}
    - Imprecisões: {len(inaccuracies)}
    - Erros (Mistakes): {len(mistakes)}
    - Erros Graves (Blunders): {len(blunders)}
    
    O MOMENTO CRÍTICO (Onde o jogo pode ter sido perdido):
    - Lance número: {worst_move['move_number'] if worst_move else 'N/A'}
    - Lance jogado: {worst_move['move_played'] if worst_move else 'N/A'}
    - Perda de vantagem (CP Loss): {worst_move['cp_loss']:.2f} (quanto maior, pior)
    - O que a engine sugeriu: Tente olhar os dados, mas explique de forma humana.
    """

    prompt = f"""
    Atue como um Grande Mestre de Xadrez que é um treinador pessoal gentil e perspicaz.
    Analise o resumo estatístico desta partida específica que seu aluno acabou de jogar.

    DADOS DA PARTIDA:
    {game_summary}

    SUA TAREFA:
    Escreva um feedback direto para o aluno ({user_color}) em formato Markdown.
    
    ESTRUTURA DA RESPOSTA:
    ### ♟️ Resumo da Partida
    (Em 2 frases: O aluno dominou? Foi uma luta acirrada? Ou ele entregou o jogo?)

    ### 🚨 O Momento Decisivo
    (Analise o "Momento Crítico" citado nos dados. Explique por que cometer um erro grave nesse ponto custa caro. Não use muitos números, explique o conceito).

    ### 💡 Dica para o Próximo Jogo
    (Baseado na quantidade de erros vs acertos, dê 1 conselho prático. Ex: Se teve muitos Blunders, diga para checar peças penduradas. Se teve erros posicionais, fale sobre planos).

    Tom: Educativo, curto e motivador. Português do Brasil.
    """

    # 3. Chamada para a IA
    try:
        # Usando o flash para ser rápido na aba de análise, ou pro para melhor qualidade
        model = genai.GenerativeModel('gemini-flash-latest') 
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        return f"Desculpe, não consegui analisar sua partida agora. Erro: {str(e)}"