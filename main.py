# main.py
from models import consultar_modelos
from metrics import avaliar_respostas
from report import salvar_resultados

def run_pipeline(config):
    import time
    start_total = time.time()
    print("[INFO] Iniciando pipeline de avaliação de modelos de IA")
    
    SYSTEM_PROMPTS = config.get('system_prompts', {
        "queries": """Você é um especialista em pesquisa jurídica brasileira. Sua tarefa é gerar queries de busca precisas e eficazes para encontrar informações relevantes sobre legislação, jurisprudência e normas brasileiras.

Diretrizes:
- Use termos jurídicos específicos e precisos
- Inclua sinônimos e variações terminológicas
- Considere diferentes níveis de governo (federal, estadual, municipal)
- Foque em aspectos práticos e procedimentais
- Use linguagem formal e técnica apropriada""",
        
        "resposta": """Você é um assistente jurídico especializado em direito brasileiro. Sua função é fornecer respostas claras, precisas e bem fundamentadas sobre questões legais, baseando-se exclusivamente no contexto fornecido.

Diretrizes:
- Base suas respostas APENAS no contexto fornecido
- Cite as fontes legais quando disponíveis (leis, decretos, etc.)
- Use linguagem clara e acessível, mas tecnicamente precisa
- Estruture a resposta de forma lógica e organizada
- Se o contexto for insuficiente, indique claramente essa limitação
- Não invente informações que não estejam no contexto"""
    })
    
    print(f"[DEBUG] System prompts carregados: queries ({len(SYSTEM_PROMPTS['queries'])} chars), resposta ({len(SYSTEM_PROMPTS['resposta'])} chars)")
    
    perguntas = config.get('perguntas', [
        "Quais são os direitos do consumidor no Brasil?",
        "Como funciona o processo de aposentadoria no INSS?",
        "Quais são as regras para abertura de empresa no Brasil?"
    ])
    
    ground_truths = config.get('ground_truth', [])
    modo_contexto = config.get('modo_contexto', 'truncar')
    print(f"[INFO] Processando {len(perguntas)} perguntas com modo_contexto='{modo_contexto}'")
    
    todos_resultados = []
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"[INFO] Pergunta {i}/{len(perguntas)}: '{pergunta[:50]}...'")
        
        ground_truth_for_this = None
        if i-1 < len(ground_truths) and ground_truths[i-1].strip():
            ground_truth_for_this = ground_truths[i-1].strip()
        
        try:
            print("[INFO] Consultando modelos...")
            start_consulta = time.time()
            respostas, logs, queries, contextos, issues = consultar_modelos(pergunta, SYSTEM_PROMPTS, num_queries=config.get('num_queries'), modelos=config.get('modelos'), modo_contexto=modo_contexto)
            end_consulta = time.time()
            print(f"[INFO] Consulta concluída em {end_consulta - start_consulta:.2f}s. Respostas obtidas de {len(respostas)} modelos")
            
            print("[INFO] Avaliando respostas...")
            start_avalia = time.time()
            metricas = avaliar_respostas(respostas, contextos, pergunta, logs, ground_truth_for_this) 
            end_avalia = time.time()
            print(f"[INFO] Avaliação concluída em {end_avalia - start_avalia:.2f}s")
            
            for modelo in respostas:
                resultado = {
                    "pergunta": pergunta,
                    "modelo": modelo,
                    "resposta": respostas[modelo],
                    "queries_geradas": queries.get(modelo, []),
                    "num_contextos": len(contextos.get(modelo, [])),
                    "tempo_geracao_queries": logs[modelo]["tempo_geracao_queries"],
                    "tempo_resposta": logs[modelo]["tempo_resposta"],
                    "tokens_resposta": logs[modelo]["tokens_resposta"],
                    "faithfulness": metricas.get(modelo, {}).get("faithfulness", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "answer_relevancy": metricas.get(modelo, {}).get("answer_relevancy", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "context_precision": metricas.get(modelo, {}).get("context_precision", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "rouge_1_f1": metricas.get(modelo, {}).get("rouge_1_f1", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "rouge_2_f1": metricas.get(modelo, {}).get("rouge_2_f1", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "bertscore_f1": metricas.get(modelo, {}).get("bertscore_f1", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "issues": issues.get(modelo, []),
                    "system_prompt_queries": SYSTEM_PROMPTS["queries"],
                    "system_prompt_resposta": SYSTEM_PROMPTS["resposta"]
                }
                todos_resultados.append(resultado)
                
        except Exception as e:
            print(f"[ERROR] Erro ao processar pergunta '{pergunta}': {e}")
            continue
    
    print(f"[INFO] Salvando {len(todos_resultados)} resultados...")
    
    try:
        salvar_resultados(todos_resultados)
        print("[INFO] Resultados salvos com sucesso")
    except Exception as e:
        print(f"[ERROR] Erro ao salvar resultados: {e}")
    
    end_total = time.time()
    print(f"[INFO] Pipeline concluído em {end_total - start_total:.2f}s total")
