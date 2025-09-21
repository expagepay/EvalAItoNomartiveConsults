# metrics.py
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision
from datasets import Dataset
from langchain_openai import ChatOpenAI
import os
import sys
import io
from dotenv import load_dotenv
#import traceback

from langchain_community.embeddings import HuggingFaceEmbeddings
from rouge_score import rouge_scorer
from bert_score import score as bert_score_fn
#import re
from sentence_transformers import util
#import pandas as pd
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

embeddings_model = None

def avaliar_respostas(respostas, contextos, pergunta, logs, ground_truth=None):
    global embeddings_model
    print("[INFO] Iniciando avaliação das respostas dos modelos")
    avaliacoes = {}

    # Configurar LLM com parâmetros otimizados para RAGAS e ground truth
    llm = ChatOpenAI(
        model="google/gemini-2.5-flash",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=10000,
        temperature=0.0,
        request_timeout=300,
        max_retries=3
    )

    if embeddings_model is None:
        print("[INFO] Carregando modelo de embeddings (pode demorar na primeira execução)...")
        import time
        start = time.time()
        embeddings_model = HuggingFaceEmbeddings(model_name='paraphrase-multilingual-MiniLM-L12-v2')
        end = time.time()
        print(f"[INFO] Embeddings carregados em {end - start:.2f}s")

    for modelo, resposta in respostas.items():
        modelo_nome = modelo.split('/')[-1]
        print(f"[INFO] Avaliando modelo: {modelo_nome}")
        contexto_modelo = contextos.get(modelo, [])
        
        # Garantir lista
        if isinstance(contexto_modelo, str):
            contexto_modelo = [contexto_modelo]
        
        print(f"[DEBUG] Contexto disponível: {len(contexto_modelo)} itens")
        
        if len(contexto_modelo) == 0:
            print(f"[WARN] Nenhum contexto para {modelo_nome} - pulando métricas")
            avaliacoes[modelo] = {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
                "rouge_1_f1": 0.0,
                "rouge_2_f1": 0.0,
                "bertscore_f1": 0.0
            }
            continue
        

        # Truncar pergunta se necessário
        pergunta_truncada = pergunta
        MAX_PERGUNTA_LENGTH = 128000 
        if len(pergunta) > MAX_PERGUNTA_LENGTH:
            pergunta_truncada = pergunta[:MAX_PERGUNTA_LENGTH] + "..."
            print(f"[WARN] Pergunta truncada para {len(pergunta_truncada)} chars")
        

        # Ground truth
        if ground_truth and ground_truth.strip():
            reference_str = ground_truth.strip()
            print("[INFO] Usando ground truth fornecido")
        else:
            print("[INFO] Gerando ground truth simulado (aproximado)")
            prompt_gt = f"Baseado na pergunta: '{pergunta_truncada}' e contexts legais, gere uma resposta de referência concisa, no estilo de normativas. Apenas gere a resposta e nada mais."
            ground_truth = llm.invoke([{"role": "user", "content": prompt_gt}]).content

        try:
            reference_str = ground_truth

            # Faithfulness
            if not resposta or len(resposta.strip()) < 50:
                print("[WARN] Resposta muito curta - pulando faithfulness")
                faithfulness_score = 0.0
                relevancy_score = 0.0
                context_precision_score = 0.0
            else:
                print("[INFO] Calculando faithfulness...")
                faithfulness_score = 0.0
                relevancy_score = 0.0
                context_precision_score = 0.0
                try:
                    contexts_str = [json.dumps(ctx) if isinstance(ctx, dict) else str(ctx) for ctx in contexto_modelo]
                    data_faith = Dataset.from_dict({
                        "question": [pergunta_truncada],
                        "answer": [resposta],
                        "contexts": [contexts_str],
                    })
                    faithfulness_metric = Faithfulness()
                    resultado_faith = evaluate(data_faith, metrics=[faithfulness_metric], llm=llm)
                    if resultado_faith is not None:
                        df_faith = resultado_faith.to_pandas()
                        if 'faithfulness' in df_faith.columns and len(df_faith) > 0:
                            faith_val = df_faith['faithfulness'].iloc[0]
                            if faith_val is not None and str(faith_val).lower() not in ['nan', 'none']:
                                faithfulness_score = float(faith_val)
                    print(f"[DEBUG] Faithfulness: {faithfulness_score}")
                except Exception as faith_error:
                    print(f"[ERROR] Erro em faithfulness: {faith_error}")
                    faithfulness_score = 0.0
                
                # Answer Relevancy
                print("[INFO] Calculando relevância da resposta...")
                try:
                    data_rel = Dataset.from_dict({
                        "question": [pergunta_truncada],
                        "answer": [resposta]
                    })
                    relevancy_metric = AnswerRelevancy(embeddings=embeddings_model)
                    resultado_rel = evaluate(data_rel, metrics=[relevancy_metric], llm=llm)
                    if resultado_rel is not None:
                        df_rel = resultado_rel.to_pandas()
                        if 'answer_relevancy' in df_rel.columns and len(df_rel) > 0:
                            rel_val = df_rel['answer_relevancy'].iloc[0]
                            if rel_val is not None and str(rel_val).lower() not in ['nan', 'none']:
                                relevancy_score = float(rel_val)
                    print(f"[DEBUG] Relevancy: {relevancy_score}")
                except Exception as rel_error:
                    print(f"[ERROR] Erro em relevancy: {rel_error}")
                    relevancy_score = 0.0

                # Context Precision
                print("[INFO] Calculando relevância da resposta...")
                try:
                    print("Calculando context_precision...")
                    data_precision = Dataset.from_dict({
                        "question": [pergunta_truncada],
                        "contexts": [contexts_str],
                        "ground_truth": [reference_str]
                    })
                    precision_metric = ContextPrecision()
                    resultado_precision = evaluate(data_precision, metrics=[precision_metric], llm=llm)
                    if resultado_precision is not None:
                        df_precision = resultado_precision.to_pandas()
                        if 'context_precision' in df_precision.columns and len(df_precision) > 0:
                            precision_val = df_precision['context_precision'].iloc[0]
                            if precision_val is not None and str(precision_val).lower() not in ['nan', 'none']:
                                context_precision_score = float(precision_val)
                    print(f"[DEBUG] Context Precision: {context_precision_score}")
                except Exception as e:
                    print(f"[ERROR] Erro em context_precision: {e}")
                    context_precision_score = 0.0

            

            # ROUGE e BERTScore
            # =====================================================
            if not resposta or not reference_str:
                print("[WARN] Resposta ou referência ausente - pulando ROUGE e BERTScore")
                bertscore_f1 = 0.0
                rouge_1_f1 = 0.0
                rouge_2_f1 = 0.0
            else:
                print("[INFO] Calculando métricas textuais...")
                rouge_scorer_obj = rouge_scorer.RougeScorer(['rouge1', 'rouge2'], use_stemmer=True)
                rouge_scores = rouge_scorer_obj.score(reference_str, resposta)
                rouge_1_f1 = rouge_scores['rouge1'].fmeasure
                rouge_2_f1 = rouge_scores['rouge2'].fmeasure
                
                try:
                    os.environ['TRANSFORMERS_CACHE'] = os.environ.get('HF_HUB_CACHE', r'D:\HF_Cache')
                    
                    P, R, F1_bert = bert_score_fn([resposta], [reference_str], model_type='bert-base-multilingual-cased',lang='pt', rescale_with_baseline=True)
                    bertscore_f1 = F1_bert.mean().item() if F1_bert.numel() > 0 else 0.0
                except Exception as e:
                    print(f"[WARN] Erro em BERTScore: {e} - usando fallback")
                    model_emb = embeddings_model
                    emb_resp = model_emb.encode([resposta], convert_to_tensor=True)
                    emb_ref = model_emb.encode(reference_str, convert_to_tensor=True)
                    bertscore_f1 = util.cos_sim(emb_resp, emb_ref).item()


                print(f"[DEBUG] ROUGE-1: {rouge_1_f1:.3f}, ROUGE-2: {rouge_2_f1:.3f}, BERTScore: {bertscore_f1:.3f}, Context Precision: {context_precision_score:.3f}")
    
            avaliacoes[modelo] = {
                "faithfulness": faithfulness_score,
                "answer_relevancy": relevancy_score,
                "context_precision": context_precision_score,
                "rouge_1_f1": rouge_1_f1,
                "rouge_2_f1": rouge_2_f1,
                "bertscore_f1": bertscore_f1
            }

        except Exception as e:
            print(f"[ERROR] Erro geral na avaliação de {modelo_nome}: {e}")
            avaliacoes[modelo] = {
                "erro": "Erro na avaliação",
            }

    print("[INFO] Avaliação concluída")
    return avaliacoes
