# metrics.py
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def avaliar_respostas(respostas, contextos, pergunta, logs):
    print("🔍 [METRICS] Iniciando avaliação das respostas...")
    avaliacoes = {}

    llm = ChatOpenAI(
        model="mistralai/mistral-7b-instruct",
        api_key="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",
        base_url="https://openrouter.ai/api/v1"
    )

    for modelo, resposta in respostas.items():
        print(f"📊 [METRICS] Avaliando modelo: {modelo}")
        contexto_modelo = contextos.get(modelo, [])
        
        # Corrigir formatação dos contextos - usar ementa e titulo em vez de 'resumo'
        contextos_formatados = []
        for item in contexto_modelo:
            if isinstance(item, dict):
                # Combinar título e ementa para formar o contexto
                titulo = item.get('titulo', '').strip()
                ementa = item.get('ementa', '').strip()
                contexto_texto = f"{titulo}. {ementa}".strip()
                if contexto_texto and contexto_texto != '.':
                    contextos_formatados.append(contexto_texto)
        
        print(f"📋 [METRICS] Contextos encontrados: {len(contexto_modelo)} -> Contextos válidos: {len(contextos_formatados)}")
        
        # Debug: mostrar alguns contextos
        if contextos_formatados:
            print(f"🔍 [METRICS] Exemplo de contexto: {contextos_formatados[0][:100]}...")
        
        # Verificar se há contextos válidos
        if not contextos_formatados:
            print(f"⚠️ [METRICS] Nenhum contexto válido encontrado para {modelo}. Definindo métricas como 0.0")
            avaliacoes[modelo] = {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0
            }
            continue
        
        data = Dataset.from_dict({
            "question": [pergunta],
            "answer": [resposta],
            "contexts": [contextos_formatados],
        })
        
        try:
            print(f"🔄 [METRICS] Executando avaliação para {modelo}...")
            resultado = evaluate(
                data, metrics=[faithfulness, answer_relevancy], llm=llm
            )
            
            # Extrair valores das métricas
            resultado_dict = resultado.to_pandas().to_dict()
            faithfulness_score = list(resultado_dict.get('faithfulness', {0: 0.0}).values())[0]
            relevancy_score = list(resultado_dict.get('answer_relevancy', {0: 0.0}).values())[0]
            
            avaliacoes[modelo] = {
                "faithfulness": faithfulness_score,
                "answer_relevancy": relevancy_score
            }
            print(f"✅ [METRICS] Avaliação concluída para {modelo}: faithfulness={faithfulness_score:.3f}, relevancy={relevancy_score:.3f}")
            
        except Exception as e:
            print(f"❌ [METRICS] Erro na avaliação de {modelo}: {e}")
            avaliacoes[modelo] = {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0
            }
    
    print("✅ [METRICS] Avaliação de todas as respostas concluída")
    return avaliacoes
