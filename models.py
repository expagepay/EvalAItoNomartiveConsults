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
        resp_json = {}
        try:
            print(f"[DEBUG] Chamando {modelo.split('/')[-1]} (tentativa {attempt + 1})...")
            
            inicio = time.time()
            resp = requests.post(url, headers=headers, json=payload, timeout=300)
            resp.raise_for_status()
            resp_json = resp.json()
            fim = time.time()
            
            conteudo = resp_json["choices"][0]["message"]["content"]
            print(f"[INFO] Resposta recebida em {fim - inicio:.2f}s")
            return conteudo, fim - inicio, None
        
        except requests.exceptions.RequestException as e:
            if hasattr(resp, 'status_code'):
                status = resp.status_code
                error_msg = resp_json.get("error", {}).get("message", "").lower()
                
                if status == 400 and ("token" in error_msg or "limit" in error_msg or "context" in error_msg or "maximum" in error_msg or not error_msg):
                    print(f"[WARN] Erro de limite de tokens/context detectado (status {status}, message: '{error_msg}')")
                    return "", 0.0, "token_limit"
                elif status == 429:
                    print(f"[WARN] Rate limit excedido (status {status}). Aguardando mais tempo...")
                    if attempt < max_retries - 1:
                        delay = base_delay * (3 ** attempt) + random.uniform(5, 10)
                        print(f"[WARN] Tentando novamente em {delay:.2f}s...")
                        time.sleep(delay)
                        continue
                elif status == 500:
                    print(f"[WARN] Erro interno do servidor (status {status}). Tentando novamente...")
                elif status == 402:
                    print(f"[ERROR] Créditos insuficientes (status {status})")
                    return "", 0.0, "insufficient_credits"
                else:
                    print(f"[ERROR] Erro inesperado (status {status}, message: '{error_msg}')")
            
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"[WARN] Erro na tentativa {attempt + 1}: {e}. Resposta: {resp_json}. Tentando novamente em {delay:.2f}s...")
                time.sleep(delay)
            else:
                print(f"[ERROR] Falha após {max_retries} tentativas: {e}")
                return "", 0.0, "other"
        except KeyError as e:
            print(f"[ERROR] Resposta inválida da API: {resp_json}")
            return "", 0.0, "other"

def consultar_modelos(pergunta: str, system_prompts: dict, num_queries: int = 3, modelos: list = ["meta-llama/llama-3.3-70b-instruct", "mistralai/mistral-7b-instruct"], modo_contexto: str = "truncar", max_contexto_padrao: int = 700000):
    print(f"[INFO] Iniciando consulta para pergunta: '{pergunta[:50]}...'")
    respostas = {}
    logs = {}
    queries_geradas = {}
    contextos = {}
    issues = {}
    for modelo in modelos:
        issues[modelo] = []

    for modelo in modelos:
        modelo_nome = modelo.split('/')[-1]
        print(f"[INFO] Processando modelo: {modelo_nome}")
        
        # 1. Gerar Queries
        print(f"[INFO] Gerando {num_queries} queries de busca...")
        user_prompt_queries = f"Para a pergunta '{pergunta}', gere exatamente {num_queries} queries de busca em português. As queries devem estar em um formato JSON, como uma lista de strings na chave 'queries'. Exemplo: {{'queries': ['query 1', 'query 2']}}"
        
        queries_json_str, tempo_queries, erro_queries = chamar_openrouter(
            modelo, 
            system_prompts["queries"], 
            user_prompt_queries, 
            json_output=True
        )
        
        if erro_queries:
            print(f"[ERROR] Falha ao gerar queries para {modelo_nome}: {erro_queries}")
            queries = []
            issues[modelo].append(f"Erro ao gerar queries: {erro_queries}")
            continue
        
        try:
            # Parsing robusto de JSON
            queries_json_str = queries_json_str.strip()
            print(f"[DEBUG] Resposta JSON bruta (primeiros 200 chars): {queries_json_str[:200]}...")
            
            def parse_json_robust(text):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    corrected = text.replace("'", '"')
                    try:
                        return json.loads(corrected)
                    except json.JSONDecodeError:
                        return None
            
            queries_data = parse_json_robust(queries_json_str)
            if queries_data is None or not isinstance(queries_data, dict):
                raise ValueError("Parsing falhou")
            queries = queries_data.get("queries", [])
            if not isinstance(queries, list):
                raise ValueError("Queries não é uma lista")
            print(f"[INFO] Queries geradas com sucesso: {len(queries)}")
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            print(f"[ERROR] Falha no parsing JSON de queries: {e}. Usando fallback...")
            # Fallback: extrair queries manualmente se possível
            queries = []
            lines = queries_json_str.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('"') and line.endswith('"'):
                    queries.append(line.strip('"'))
                elif line.startswith('- ') or line.startswith('* '):
                    queries.append(line[2:].strip())
            if queries:
                print(f"[INFO] Fallback: {len(queries)} queries extraídas")
            else:
                print("[WARN] Fallback falhou - prosseguindo sem queries")
                issues[modelo].append(f"Falha no parsing de queries JSON: {e}")
        
        queries_geradas[modelo] = queries
        
        # 2. Buscar Contexto
        print(f"[INFO] Buscando contexto com {len(queries)} queries...")
        contexto_modelo = []
        for query in queries[:num_queries]:
            resultados = buscar_lexml(query)
            contexto_modelo.extend(resultados)
        
        print(f"[INFO] Contexto coletado: {len(contexto_modelo)} documentos ({len(json.dumps(contexto_modelo))} chars)")
        contextos[modelo] = contexto_modelo

        if len(contexto_modelo) == 0:
            print(f"[WARN] Nenhum contexto recuperado para {modelo_nome} - pulando geração de resposta")
            issues[modelo].append("Nenhum contexto recuperado - indica queries de pesquisa ruins ou erro na busca")
            resposta = ""
            tempo_resposta = 0.0
            erro = None
        else:
            # 3. Gerar Resposta
            print("[INFO] Gerando resposta baseada no contexto...")
            
            # Truncamento padrão
            MAX_CONTEXT_LENGTH_PADRAO = max_contexto_padrao
            contextos_str = json.dumps(contexto_modelo)
            if len(contextos_str) > MAX_CONTEXT_LENGTH_PADRAO:
                # Truncar a lista de contextos, não a string
                if contexto_modelo:
                    avg_size = len(contextos_str) / len(contexto_modelo)
                    num_items = max(1, int(MAX_CONTEXT_LENGTH_PADRAO / avg_size))
                    contexto_truncado = contexto_modelo[:num_items]
                    contextos_str = json.dumps(contexto_truncado)
                    while len(contextos_str) > MAX_CONTEXT_LENGTH_PADRAO and num_items > 1:
                        num_items -= 1
                        contexto_truncado = contexto_modelo[:num_items]
                        contextos_str = json.dumps(contexto_truncado)
                print(f"[INFO] Contexto truncado para {len(contexto_modelo)} itens ({len(contextos_str)} chars, limite 700k)")
            else:
                contexto_truncado = contexto_modelo
                print(f"[INFO] Contexto dentro do limite: {len(contextos_str)} chars")

            user_prompt_resposta = f"Pergunta: {pergunta}\nContexto: {contextos_str}\nResponda de forma clara e objetiva."
            
            resposta, tempo_resposta, erro = chamar_openrouter(
                modelo, 
                system_prompts["resposta"], 
                user_prompt_resposta
            )
            
            if erro == "token_limit":
                print(f"[WARN] Limite de tokens atingido para {modelo_nome} - aplicando estratégia '{modo_contexto}'")
                if modo_contexto == "truncar":
                    print("[INFO] Aplicando truncamento regressivo...")
                    for limite in [100000, 50000, 28000]:
                        if contexto_modelo:
                            avg_size = len(json.dumps(contexto_modelo)) / len(contexto_modelo)
                            num_items = max(1, int(limite / avg_size))
                            contexto_truncado = contexto_modelo[:num_items]
                            contextos_str = json.dumps(contexto_truncado)
                            while len(contextos_str) > limite and num_items > 1:
                                num_items -= 1
                                contexto_truncado = contexto_modelo[:num_items]
                                contextos_str = json.dumps(contexto_truncado)
                        else:
                            contexto_truncado = []
                            contextos_str = "[]"
                        user_prompt_resposta = f"Pergunta: {pergunta}\nContexto: {contextos_str}\nResponda de forma clara e objetiva."
                        resposta, tempo_resposta, erro = chamar_openrouter(modelo, system_prompts["resposta"], user_prompt_resposta)
                        if erro is None:
                            print(f"[INFO] Sucesso com truncamento de {limite} chars")
                            contextos[modelo] = contexto_truncado
                            break
                    else:
                        print("[ERROR] Falha mesmo com truncamento mínimo")
                        resposta = ""
                        contextos[modelo] = []
                elif modo_contexto == "resumir":
                    print("[INFO] Gerando resumo com Gemini...")
                    system_prompt_resumo = "Você é um assistente especializado em resumir textos legais. Sua tarefa é criar um resumo bem estruturado e rico do contexto fornecido, preservando todos os detalhes essenciais, dados importantes e informações chave. Não invente nada novo; use apenas o conteúdo existente. Estruture o resumo de forma clara, mantendo a riqueza do original."
                    resumo, _, erro_resumo = chamar_openrouter("google/gemini-2.5-flash", system_prompt_resumo, f"Resuma o seguinte contexto: {contextos_str}", json_output=False)
                    if erro_resumo is None:
                        contextos_str = resumo
                        user_prompt_resposta = f"Pergunta: {pergunta}\nContexto: {contextos_str}\nResponda de forma clara e objetiva."
                        resposta, tempo_resposta, erro = chamar_openrouter(modelo, system_prompts["resposta"], user_prompt_resposta)
                        print("[INFO] Resumo gerado e resposta obtida")
                        contextos[modelo] = resumo
                    else:
                        print("[ERROR] Falha ao gerar resumo")
                        resposta = ""
                        contextos[modelo] = []
            else:
                print("[INFO] Resposta gerada com sucesso na primeira tentativa")
                contextos[modelo] = contexto_truncado
        
        if not resposta or len(resposta.strip()) < 10:
            issues[modelo].append("Resposta vazia ou muito curta gerada pelo modelo")
        
        respostas[modelo] = resposta
        logs[modelo] = {
            "tempo_geracao_queries": tempo_queries,
            "tempo_resposta": tempo_resposta,
            "tokens_resposta": len(resposta.split())
        }
        
        print(f"[INFO] {modelo_nome} concluído: {len(resposta)} chars, {logs[modelo]['tokens_resposta']} tokens estimados")

    print("[INFO] Consulta concluída para todos os modelos")
    return respostas, logs, queries_geradas, contextos, issues
