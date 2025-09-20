# main.py
from models import consultar_modelos
from metrics import avaliar_respostas
from report import salvar_resultados

def run_pipeline(config):
    # Usar config para system prompts
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
    
    print("Iniciando pipeline de avaliação de modelos")
    print(f"System Prompts: queries={len(SYSTEM_PROMPTS['queries'])} chars, resposta={len(SYSTEM_PROMPTS['resposta'])} chars")
    
    perguntas = config.get('perguntas', [
        "Quais são os direitos do consumidor no Brasil?",
        "Como funciona o processo de aposentadoria no INSS?",
        "Quais são as regras para abertura de empresa no Brasil?"
    ])
    
    ground_truths = config.get('ground_truth', [])  # Now a list
    
    print(f"Processando {len(perguntas)} perguntas")
    
    todos_resultados = []
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n--- Pergunta {i}/{len(perguntas)} ---")
        print(f"'{pergunta}'")
        
        # Get ground truth for this question (None if not provided or empty)
        ground_truth_for_this = None
        if i-1 < len(ground_truths) and ground_truths[i-1].strip():
            ground_truth_for_this = ground_truths[i-1].strip()
        
        try:
            # Consultar modelos com system prompts
            print("Consultando modelos...")
            respostas, logs, queries, contextos = consultar_modelos(pergunta, SYSTEM_PROMPTS, num_queries=config.get('num_queries'), modelos=config.get('modelos'))
            print(f"Respostas obtidas: {len(respostas)} modelos")
            
            # Avaliar respostas
            print("Avaliando respostas...")
            metricas = avaliar_respostas(respostas, contextos, pergunta, logs, ground_truth_for_this)  # Pass per-question ground truth
            print("Avaliação concluída")
            
            # Compilar resultados
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
                    "rouge_1_f1": metricas.get(modelo, {}).get("rouge_1_f1", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "rouge_2_f1": metricas.get(modelo, {}).get("rouge_2_f1", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "bertscore_f1": metricas.get(modelo, {}).get("bertscore_f1", 0.0) if isinstance(metricas.get(modelo, {}), dict) else 0.0,
                    "system_prompt_queries": SYSTEM_PROMPTS["queries"],
                    "system_prompt_resposta": SYSTEM_PROMPTS["resposta"]
                }
                todos_resultados.append(resultado)
                print(f"{modelo}: faithfulness={resultado['faithfulness']:.3f}, relevancy={resultado['answer_relevancy']:.3f}")
                
        except Exception as e:
            print(f"ERRO ao processar pergunta '{pergunta}': {e}")
            continue
    
    print(f"\nSalvando {len(todos_resultados)} resultados...")
    
    # Salvar resultados
    try:
        salvar_resultados(todos_resultados)
        print("Resultados salvos com sucesso")
    except Exception as e:
        print(f"ERRO ao salvar resultados: {e}")
    
    print("Pipeline concluído")
