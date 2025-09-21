# models.py
import time
import requests
import json
import random
from retriever import buscar_lexml
from dotenv import load_dotenv
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def chamar_openrouter(modelo: str, system_prompt: str, user_prompt: str, json_output: bool = False):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
    
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

    max_retries = 5
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            print(f"Chamando {modelo.split('/')[-1]} (tentativa {attempt + 1})...")
            
            inicio = time.time()
            resp = requests.post(url, headers=headers, json=payload, timeout=300)
            resp.raise_for_status()
            resp_json = resp.json()
            fim = time.time()
            
            conteudo = resp_json["choices"][0]["message"]["content"]
            print(f"Resposta recebida em {fim - inicio:.2f}s")
            return conteudo, fim - inicio
        
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Erro na tentativa {attempt + 1}: {e}. Tentando novamente em {delay:.2f}s...")
                time.sleep(delay)
            else:
                print(f"Falha após {max_retries} tentativas: {e}")
                return "", 0.0
        except KeyError as e:
            print(f"ERRO na resposta: {resp_json if 'resp_json' in locals() else 'Resposta inválida'}")
            return "", 0.0

def consultar_modelos(pergunta: str, system_prompts: dict, num_queries: int = 3, modelos: list = ["meta-llama/llama-3.3-70b-instruct", "mistralai/mistral-7b-instruct"]):
    print(f"Iniciando consulta: '{pergunta[:50]}...'")
    respostas = {}
    logs = {}
    queries_geradas = {}
    contextos = {}

    for modelo in modelos:
        modelo_nome = modelo.split('/')[-1]
        print(f"\nProcessando {modelo_nome}")
        
        # 1. Gerar Queries com System Prompt
        print(f"Gerando {num_queries} queries...")
        user_prompt_queries = f"Para a pergunta '{pergunta}', gere exatamente {num_queries} queries de busca em português. As queries devem estar em um formato JSON, como uma lista de strings na chave 'queries'. Exemplo: {{'queries': ['query 1', 'query 2']}}"
        
        queries_json_str, tempo_queries = chamar_openrouter(
            modelo, 
            system_prompts["queries"], 
            user_prompt_queries, 
            json_output=True
        )
        
        try:
            queries = json.loads(queries_json_str).get("queries", [])
            print(f"Queries geradas: {len(queries)}")
        except (json.JSONDecodeError, AttributeError):
            print(f"ERRO ao processar queries JSON")
            queries = []

        queries_geradas[modelo] = queries
        
        # 2. Buscar Contexto
        print(f"Buscando contexto...")
        contexto_modelo = []
        for query in queries[:num_queries]:
            resultados = buscar_lexml(query)
            contexto_modelo.extend(resultados)
        
        print(f"Contextos coletados: {len(contexto_modelo)}")
        contextos[modelo] = contexto_modelo

        # 3. Gerar Resposta com System Prompt
        print("Gerando resposta...")
        MAX_CONTEXT_LENGTH = 50000  # Aumentado para reduzir perda de contexto
        contextos_str = json.dumps(contexto_modelo)
        if len(contextos_str) > MAX_CONTEXT_LENGTH:
            # Tentar resumir o contexto usando o modelo
            print(f"Contexto muito grande ({len(contextos_str)} chars), gerando resumo...")
            resumo_prompt = f"Resuma o seguinte contexto legal em português, focando em informações chave e mantendo pelo menos 500 palavras essenciais: {contextos_str[:MAX_CONTEXT_LENGTH//2]}"
            contexto_resumido, _ = chamar_openrouter(modelo, system_prompts["resposta"], resumo_prompt)

            # Verificação: Se resumo muito curto, use original truncado
            if len(contexto_resumido.strip()) < 100:  # Mínimo 100 chars
                print("Resumo muito curto - usando contexto original truncado")
                contexto_resumido = contextos_str[:MAX_CONTEXT_LENGTH]

            contextos_str = contexto_resumido[:MAX_CONTEXT_LENGTH]
            print(f"Contexto resumido para {len(contextos_str)} chars")
        else:
            print(f"Contexto dentro do limite: {len(contextos_str)} chars")

        user_prompt_resposta = f"Pergunta: {pergunta}\nContexto: {contextos_str}\nResponda de forma clara e objetiva."
        
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
        
        print(f"{modelo_nome} processado: {len(resposta)} chars, {logs[modelo]['tokens_resposta']} tokens")

    print("Consulta concluída")
    return respostas, logs, queries_geradas, contextos
