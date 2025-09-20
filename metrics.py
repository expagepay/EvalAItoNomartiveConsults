# metrics.py
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy
from datasets import Dataset
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import traceback

from langchain_huggingface import HuggingFaceEmbeddings
from rouge_score import rouge_scorer
from bert_score import score as bert_score_fn
#from nltk.corpus import stopwords
#from nltk.tokenize import word_tokenize
import re
from sentence_transformers import SentenceTransformer, util
import pandas as pd

embeddings_model = HuggingFaceEmbeddings(model_name='paraphrase-multilingual-MiniLM-L12-v2')
load_dotenv()

def avaliar_respostas(respostas, contextos, pergunta, logs, ground_truth=None):
    print("Iniciando avaliação das respostas")
    avaliacoes = {}

    # Configurar LLM com parâmetros otimizados para RAGAS
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=2000,
        temperature=0.0,
        request_timeout=300,
        max_retries=3
    )

    for modelo, resposta in respostas.items():
        modelo_nome = modelo.split('/')[-1]
        print(f"Avaliando {modelo_nome}")
        contexto_modelo = contextos.get(modelo, [])
        
        # Corrigir formatação dos contextos
        contextos_formatados = []
        
        for item in contexto_modelo:
            if isinstance(item, dict):
                titulo = item.get('titulo', '').strip()
                ementa = item.get('ementa', '').strip()
                autor = item.get('autor', '').strip()
                data = item.get('data', '').strip()
                
                partes = []
                if titulo and titulo != 'Título não disponível':
                    partes.append(f"Título: {titulo}")
                if ementa and ementa != 'Ementa não disponível':
                    partes.append(f"Ementa: {ementa}")
                if autor and autor != 'Autor não informado':
                    partes.append(f"Autor: {autor}")
                if data and data != 'Data não informada':
                    partes.append(f"Data: {data}")
                
                if partes:
                    contexto_texto = '. '.join(partes)
                    contextos_formatados.append(contexto_texto)
            elif isinstance(item, str) and item.strip():
                contextos_formatados.append(item.strip())
        
        print(f"Contextos: {len(contexto_modelo)} -> válidos: {len(contextos_formatados)}")
        
        if not contextos_formatados:
            print(f"Nenhum contexto válido para {modelo_nome} - métricas = 0.0")
            avaliacoes[modelo] = {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "rouge_1_f1": 0.0,
                "rouge_2_f1": 0.0,
                "bertscore_f1": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_custom": 0.0
            }
            continue
        
        # Truncar contextos se necessário
        contextos_str = '\n'.join(contextos_formatados)
        MAX_CONTEXT_LENGTH = 15000
        
        if len(contextos_str) > MAX_CONTEXT_LENGTH:
            print(f"Contextos muito grandes ({len(contextos_str)} chars), truncando para {MAX_CONTEXT_LENGTH}...")
            contextos_str = contextos_str[:MAX_CONTEXT_LENGTH] + "..."
            contextos_formatados = [contextos_str]
        
        # Truncar resposta e pergunta
        resposta_truncada = resposta
        if len(resposta) > 3000:
            resposta_truncada = resposta[:3000] + "..."
            print(f"Resposta truncada de {len(resposta)} para 3000 chars")
        
        pergunta_truncada = pergunta
        if len(pergunta) > 1000:
            pergunta_truncada = pergunta[:1000] + "..."


        # Ground truth: use fornecido ou gere simulado
        if ground_truth and ground_truth.strip():
            reference_str = ground_truth.strip()
        else:
            # Gera ground truth simulado via LLM (para casos sem referência)
            prompt_gt = f"Baseado na pergunta: '{pergunta_truncada}' e contexts legais, gere uma resposta de referência concis, no estilo de normativas."
            ground_truth = llm.invoke([{"role": "user", "content": prompt_gt}]).content
            print("Aviso: Ground truth gerado automaticamente (aproximado). Para precisão, forneça reais.")

        try:
            # Reference para métricas customizadas
            reference_str = ground_truth
            # Avaliação com RAGAS
            faithfulness_score = 0.0
            relevancy_score = 0.0
            
            # Avaliar faithfulness
            try:
                print("Avaliando faithfulness...")
                data_faith = Dataset.from_dict({
                    "question": [pergunta_truncada],
                    "answer": [resposta_truncada],
                    "contexts": [contextos_formatados],
                })
                faithfulness_metric = Faithfulness()
                resultado_faith = evaluate(data_faith, metrics=[faithfulness_metric], llm=llm)
                if resultado_faith is not None:
                    df_faith = resultado_faith.to_pandas()
                    if 'faithfulness' in df_faith.columns and len(df_faith) > 0:
                        faith_val = df_faith['faithfulness'].iloc[0]
                        if faith_val is not None and str(faith_val).lower() not in ['nan', 'none']:
                            try:
                                faithfulness_score = float(faith_val)
                            except (ValueError, TypeError):
                                faithfulness_score = 0.0
                print(f"Faithfulness calculado: {faithfulness_score}")
            except Exception as faith_error:
                print(f"Erro no faithfulness: {faith_error}")
                faithfulness_score = 0.0
            
            # Avaliar answer_relevancy
            try:
                print("Avaliando answer_relevancy...")
                data_rel = Dataset.from_dict({
                    "question": [pergunta_truncada],
                    "answer": [resposta_truncada]
                })
                relevancy_metric = AnswerRelevancy(embeddings=embeddings_model)
                resultado_rel = evaluate(data_rel, metrics=[relevancy_metric], llm=llm)
                if resultado_rel is not None:
                    df_rel = resultado_rel.to_pandas()
                    if 'answer_relevancy' in df_rel.columns and len(df_rel) > 0:
                        rel_val = df_rel['answer_relevancy'].iloc[0]
                        if rel_val is not None and str(rel_val).lower() not in ['nan', 'none']:
                            try:
                                relevancy_score = float(rel_val)
                            except (ValueError, TypeError):
                                relevancy_score = 0.0
                print(f"Answer relevancy calculado: {relevancy_score}")
            except Exception as rel_error:
                print(f"Erro no answer_relevancy: {rel_error}")
                traceback.print_exc()
                relevancy_score = 0.0
            
            print(f"Debug - Faithfulness: {faithfulness_score}, Relevancy: {relevancy_score}")
            
            # ROUGE (comparação textual)
            rouge_scorer_obj = rouge_scorer.RougeScorer(['rouge1', 'rouge2'], use_stemmer=True)
            rouge_scores = rouge_scorer_obj.score(reference_str, resposta_truncada)
            rouge_1_f1 = rouge_scores['rouge1'].fmeasure
            rouge_2_f1 = rouge_scores['rouge2'].fmeasure
            
            # BERTScore (similaridade semântica)
            try:
                # Configurar BERTScore para usar o cache customizado
                os.environ['TRANSFORMERS_CACHE'] = os.environ.get('HF_HUB_CACHE', r'D:\HF_Cache')
                
                P, R, F1_bert = bert_score_fn([resposta_truncada], [reference_str], model_type='bert-base-multilingual-cased',lang='pt', rescale_with_baseline=True)
                bertscore_f1 = F1_bert.mean().item() if F1_bert.numel() > 0 else 0.0
            except Exception as e:
                print(f"Erro BERTScore: {e} - Usando backup cosine similarity")
                # Backup com cosine similarity se BERT falhar
                model_emb = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                emb_resp = model_emb.encode(resposta_truncada, convert_to_tensor=True)
                emb_ref = model_emb.encode(reference_str, convert_to_tensor=True)
                bertscore_f1 = util.cos_sim(emb_resp, emb_ref).item()

            print(f"Debug - ROUGE-1: {rouge_1_f1}, ROUGE-2: {rouge_2_f1}, BERTScore: {bertscore_f1}")
    
            avaliacoes[modelo] = {
                "faithfulness": faithfulness_score,
                "answer_relevancy": relevancy_score,
                "rouge_1_f1": rouge_1_f1,
                "rouge_2_f1": rouge_2_f1,
                "bertscore_f1": bertscore_f1
            }

        except Exception as e:
            print(f"ERRO na avaliação de {modelo_nome}: {e}")
            traceback.print_exc()
            avaliacoes[modelo] = {
                "erro": "Ocorreu um erro na avaliação",
            }

    print("Avaliação concluída")
    return avaliacoes
