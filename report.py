# report.py
import json
import csv
import os

def salvar_resultados(resultados):
    if not resultados:
        print("Nenhum resultado para salvar")
        return

    # Criar pasta results se não existir
    os.makedirs("results", exist_ok=True)
    print(f"Salvando {len(resultados)} resultados na pasta 'results'")

    salvar_json_detalhado(resultados)
    salvar_relatorio_comparacao(resultados)
    salvar_csv(resultados)

    print("Arquivos salvos com sucesso na pasta 'results'")

def salvar_json_detalhado(resultados):
    try:
        with open("results/resultados.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        print("results/resultados.json salvo")
    except Exception as e:
        print(f"Erro ao salvar JSON: {e}")

def salvar_relatorio_comparacao(resultados):
    try:
        relatorio = gerar_relatorio_comparacao(resultados)
        with open("results/comparacao_modelos.json", "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        print("results/comparacao_modelos.json salvo")
    except Exception as e:
        print(f"Erro ao salvar relatório de comparação: {e}")

def salvar_csv(resultados):
    campos_csv = [
        'pergunta', 'modelo', 'resposta', 'queries_geradas',
        'faithfulness', 'answer_relevancy', 'rouge_1_f1', 'rouge_2_f1', 'bertscore_f1',
        'precision', 'recall', 'f1_custom',
        'num_contextos', 'tempo_geracao_queries', 'tempo_resposta', 'tokens_resposta'
    ]

    try:
        with open("results/resultados.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos_csv, extrasaction='ignore')
            writer.writeheader()
            for resultado in resultados:
                resultado_csv = resultado.copy()
                resultado_csv['queries_geradas'] = '; '.join(resultado.get('queries_geradas', []))
                writer.writerow(resultado_csv)
        print("results/resultados.csv salvo")
    except Exception as e:
        print(f"Erro ao salvar CSV: {e}")

def gerar_relatorio_comparacao(resultados):
    perguntas = {}
    modelos_stats = {}

    for resultado in resultados:
        pergunta = resultado['pergunta']
        modelo = resultado['modelo']

        if pergunta not in perguntas:
            perguntas[pergunta] = []
        perguntas[pergunta].append(resultado)

        if modelo not in modelos_stats:
            modelos_stats[modelo] = {
                'faithfulness': [], 'answer_relevancy': [], 'rouge_1_f1': [], 'rouge_2_f1': [], 'bertscore_f1': [],
                'precision': [], 'recall': [], 'f1_custom': [],
                'tempos_queries': [], 'tempos_resposta': [], 'num_contextos': [], 'tokens_resposta': []
            }

        modelos_stats[modelo]['faithfulness'].append(resultado.get('faithfulness', 0.0))
        modelos_stats[modelo]['answer_relevancy'].append(resultado.get('answer_relevancy', 0.0))
        modelos_stats[modelo]['rouge_1_f1'].append(resultado.get('rouge_1_f1', 0.0))
        modelos_stats[modelo]['rouge_2_f1'].append(resultado.get('rouge_2_f1', 0.0))
        modelos_stats[modelo]['bertscore_f1'].append(resultado.get('bertscore_f1', 0.0))
        modelos_stats[modelo]['precision'].append(resultado.get('precision', 0.0))
        modelos_stats[modelo]['recall'].append(resultado.get('recall', 0.0))
        modelos_stats[modelo]['f1_custom'].append(resultado.get('f1_custom', 0.0))
        modelos_stats[modelo]['tempos_queries'].append(resultado.get('tempo_geracao_queries', 0.0))
        modelos_stats[modelo]['tempos_resposta'].append(resultado.get('tempo_resposta', 0.0))
        modelos_stats[modelo]['num_contextos'].append(resultado.get('num_contextos', 0))
        modelos_stats[modelo]['tokens_resposta'].append(resultado.get('tokens_resposta', 0))

    comparacao = {
        'resumo_geral': {
            'total_perguntas': len(perguntas),
            'total_modelos': len(modelos_stats),
            'total_avaliacoes': len(resultados)
        },
        'comparacao_por_pergunta': {},
        'estatisticas_por_modelo': {},
        'ranking_modelos': []
    }

    for pergunta, resultados_pergunta in perguntas.items():
        comparacao['comparacao_por_pergunta'][pergunta] = {
            'modelos': {},
            'melhor_faithfulness': {'modelo': '', 'score': 0.0},
            'melhor_relevancy': {'modelo': '', 'score': 0.0}
        }

        for resultado in resultados_pergunta:
            modelo = resultado['modelo']
            faith = resultado.get('faithfulness', 0.0)
            relevancy = resultado.get('answer_relevancy', 0.0)

            comparacao['comparacao_por_pergunta'][pergunta]['modelos'][modelo] = {
                'faithfulness': faith,
                'answer_relevancy': relevancy,
                'rouge_1_f1': resultado.get('rouge_1_f1', 0.0),
                'rouge_2_f1': resultado.get('rouge_2_f1', 0.0),
                'bertscore_f1': resultado.get('bertscore_f1', 0.0),
                'num_contextos': resultado.get('num_contextos', 0),
                'tempo_total': resultado.get('tempo_geracao_queries', 0.0) + resultado.get('tempo_resposta', 0.0)
            }

            if faith > comparacao['comparacao_por_pergunta'][pergunta]['melhor_faithfulness']['score']:
                comparacao['comparacao_por_pergunta'][pergunta]['melhor_faithfulness'] = {'modelo': modelo, 'score': faith}

            if relevancy > comparacao['comparacao_por_pergunta'][pergunta]['melhor_relevancy']['score']:
                comparacao['comparacao_por_pergunta'][pergunta]['melhor_relevancy'] = {'modelo': modelo, 'score': relevancy}

    for modelo, stats in modelos_stats.items():
        def avg(lst):
            return sum(lst) / len(lst) if lst else 0.0

        comparacao['estatisticas_por_modelo'][modelo] = {
            'faithfulness_media': avg(stats['faithfulness']),
            'answer_relevancy_media': avg(stats['answer_relevancy']),
            'rouge_1_f1_media': avg(stats['rouge_1_f1']),
            'rouge_2_f1_media': avg(stats['rouge_2_f1']),
            'bertscore_f1_media': avg(stats['bertscore_f1']),
            'precision_media': avg(stats['precision']),
            'recall_media': avg(stats['recall']),
            'f1_custom_media': avg(stats['f1_custom']),
            'tempo_queries_medio': avg(stats['tempos_queries']),
            'tempo_resposta_medio': avg(stats['tempos_resposta']),
            'contextos_medio': avg(stats['num_contextos']),
            'tokens_medio': avg(stats['tokens_resposta']),
            'total_avaliacoes': len(stats['faithfulness'])
        }

    ranking = []
    for modelo, stats in comparacao['estatisticas_por_modelo'].items():
        score_combinado = (stats['faithfulness_media'] + stats['answer_relevancy_media']) / 2
        ranking.append({
            'modelo': modelo,
            'score_combinado': score_combinado,
            'faithfulness_media': stats['faithfulness_media'],
            'answer_relevancy_media': stats['answer_relevancy_media']
        })

    ranking.sort(key=lambda x: x['score_combinado'], reverse=True)
    comparacao['ranking_modelos'] = ranking

    return comparacao