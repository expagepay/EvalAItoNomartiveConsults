# models.py
import time
import requests
import json
from retriever import buscar_lexml

OPENROUTER_API_KEY = "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"

def chamar_openrouter(modelo: str, system_prompt: str, user_prompt: str, json_output: bool = False):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    payload = {
        "model": modelo,
        "messages": messages
    }
    if json_output:
        payload["response_format"] = {"type": "json_object"}

    print(f"🔄 [API] Chamando {modelo}...")
    print(f"📋 [API] System prompt: {len(system_prompt)} chars")
    print(f"📋 [API] User prompt: {len(user_prompt)} chars")
    
    inicio = time.time()
    resp = requests.post(url, headers=headers, json=payload).json()
    fim = time.time()
    
    try:
        conteudo = resp["choices"][0]["message"]["content"]
        print(f"✅ [API] Resposta recebida de {modelo} em {fim - inicio:.2f}s")
    except KeyError:
        print(f"❌ [API] Erro na resposta de {modelo}: {resp}")
        conteudo = ""
        
    tempo = fim - inicio
    
    return conteudo, tempo

def consultar_modelos(pergunta: str, system_prompts: dict, num_queries: int = 3):
    print(f"🚀 [MODELS] Iniciando consulta para: '{pergunta}'")
    respostas = {}
    logs = {}
    queries_geradas = {}
    contextos = {}

    for modelo in ["meta-llama/llama-3-8b-instruct", "mistralai/mistral-7b-instruct"]:
        print(f"\n📋 [MODELS] Processando modelo: {modelo}")
        
        # 1. Gerar Queries com System Prompt
        print(f"🔍 [MODELS] Gerando {num_queries} queries de busca...")
        user_prompt_queries = f"Para a pergunta '{pergunta}', gere {num_queries} queries de busca em português. As queries devem estar em um formato JSON, como uma lista de strings na chave 'queries'. Exemplo: {{'queries': ['query 1', 'query 2']}}"
        
        queries_json_str, tempo_queries = chamar_openrouter(
            modelo, 
            system_prompts["queries"], 
            user_prompt_queries, 
            json_output=True
        )
        
        try:
            queries = json.loads(queries_json_str).get("queries", [])
            print(f"✅ [MODELS] {len(queries)} queries geradas: {queries}")
        except (json.JSONDecodeError, AttributeError):
            print(f"❌ [MODELS] Erro ao processar queries JSON para {modelo}")
            queries = []

        queries_geradas[modelo] = queries
        
        # 2. Buscar Contexto
        print(f"🔎 [MODELS] Buscando contexto para {len(queries)} queries...")
        contexto_modelo = []
        for i, query in enumerate(queries, 1):
            print(f"   Query {i}/{len(queries)}: '{query}'")
            resultados = buscar_lexml(query)
            contexto_modelo.extend(resultados)
            print(f"   → {len(resultados)} resultados encontrados")
        
        print(f"📚 [MODELS] Total de contextos coletados: {len(contexto_modelo)}")
        contextos[modelo] = contexto_modelo

        # 3. Gerar Resposta com System Prompt
        print(f"💭 [MODELS] Gerando resposta com contexto...")
        MAX_CONTEXT_LENGTH = 28000
        contexto_str = json.dumps(contexto_modelo)
        if len(contexto_str) > MAX_CONTEXT_LENGTH:
            contexto_str = contexto_str[:MAX_CONTEXT_LENGTH]
            print(f"⚠️ [MODELS] Contexto truncado para {MAX_CONTEXT_LENGTH} caracteres")

        user_prompt_resposta = f"Pergunta: {pergunta}\nContexto: {contexto_str}\nResponda de forma clara e objetiva."
        
        resposta, tempo_resposta = chamar_openrouter(
            modelo, 
            system_prompts["resposta"], 
            user_prompt_resposta
        )
        
        respostas[modelo] = resposta
        logs[modelo] = {
            "tempo_geracao_queries": tempo_queries,
            "tempo_resposta": tempo_resposta,
            "tokens_resposta": len(resposta.split())
        }
        
        print(f"✅ [MODELS] Modelo {modelo} processado - Resposta: {len(resposta)} chars, {logs[modelo]['tokens_resposta']} tokens")

    print(f"\n🎯 [MODELS] Consulta concluída para todos os modelos")
    return respostas, logs, queries_geradas, contextos
