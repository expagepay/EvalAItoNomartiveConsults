# main.py
from models import consultar_modelos
from metrics import avaliar_respostas
from report import salvar_resultados

# System Prompts Editáveis
SYSTEM_PROMPTS = {
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
}

def main():
    print("🎯 [MAIN] Iniciando pipeline de avaliação de modelos")
    print(f"📋 [MAIN] System Prompts configurados:")
    print(f"   - Queries: {len(SYSTEM_PROMPTS['queries'])} caracteres")
    print(f"   - Resposta: {len(SYSTEM_PROMPTS['resposta'])} caracteres")
    
    perguntas = [
        "Quais são os direitos do consumidor no Brasil?",
        "Como funciona o processo de aposentadoria no INSS?",
        "Quais são as regras para abertura de empresa no Brasil?"
    ]
    
    print(f"📝 [MAIN] {len(perguntas)} perguntas serão processadas")
    
    todos_resultados = []
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n{'='*60}")
        print(f"🔄 [MAIN] Processando pergunta {i}/{len(perguntas)}")
        print(f"❓ [MAIN] Pergunta: '{pergunta}'")
        print(f"{'='*60}")
        
        try:
            # Consultar modelos com system prompts
            print(f"🤖 [MAIN] Consultando modelos...")
            respostas, logs, queries, contextos = consultar_modelos(pergunta, SYSTEM_PROMPTS)
            print(f"✅ [MAIN] Respostas obtidas de {len(respostas)} modelos")
            
            # Avaliar respostas
            print(f"📊 [MAIN] Iniciando avaliação das respostas...")
            metricas = avaliar_respostas(respostas, contextos, pergunta, logs)
            print(f"✅ [MAIN] Avaliação concluída")
            
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
                    "faithfulness": metricas.get(modelo, {}).get("faithfulness", 0.0),
                    "answer_relevancy": metricas.get(modelo, {}).get("answer_relevancy", 0.0),
                    "system_prompt_queries": SYSTEM_PROMPTS["queries"],
                    "system_prompt_resposta": SYSTEM_PROMPTS["resposta"]
                }
                todos_resultados.append(resultado)
                print(f"📋 [MAIN] Resultado compilado para {modelo}: faithfulness={resultado['faithfulness']:.3f}, relevancy={resultado['answer_relevancy']:.3f}")
                
        except Exception as e:
            print(f"❌ [MAIN] Erro ao processar pergunta '{pergunta}': {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"💾 [MAIN] Salvando {len(todos_resultados)} resultados...")
    
    # Salvar resultados
    try:
        salvar_resultados(todos_resultados)
        print(f"✅ [MAIN] Resultados salvos com sucesso!")
    except Exception as e:
        print(f"❌ [MAIN] Erro ao salvar resultados: {e}")
    
    print(f"🎉 [MAIN] Pipeline concluído!")

if __name__ == "__main__":
    main()
