import streamlit as st
import subprocess
import os
import tempfile
import json
from pathlib import Path

st.set_page_config(page_title="Avaliação de Modelos Jurídicos", page_icon="⚖️")

st.title("⚖️ Avaliação de Modelos de IA para Consultas Jurídicas Brasileiras")

st.markdown("""
### Guia Rápido:
1. **Configure sua API Key do OpenRouter** (obrigatório).
2. **Escolha o modo de avaliação**.
3. **Personalize system prompts** (opcional).
4. **Selecione os modelos A e B**.
5. **Clique em "Executar Avaliação"**.
""")

# Campo obrigatório para API Key
api_key = st.text_input("API Key do OpenRouter", type="password", help="Obrigatório. Obtenha em https://openrouter.ai/")

if not api_key:
    st.warning("Por favor, insira sua API Key do OpenRouter para continuar.")
    st.stop()

# Modo de avaliação
modo = st.radio("Modo de Avaliação", ["Avaliação Rápida", "Perguntas Customizadas", "Arquivo CSV"])

perguntas = ""
ground_truth = ""
csv_file = None

if modo == "Perguntas Customizadas":
    perguntas = st.text_area("Perguntas (uma por linha)", placeholder="Digite suas perguntas aqui...")
    ground_truth = st.text_area("Respostas Ideais (uma por pergunta, opcional)", placeholder="Deixe vazio para auto-gerar...")

elif modo == "Arquivo CSV":
    csv_file = st.file_uploader("Upload CSV", type="csv", help="Arquivo com colunas 'pergunta' e 'ground_truth'")

# System Prompts
st.subheader("🎯 System Prompts (Opcional)")
with st.expander("Editar System Prompts"):
    system_queries = st.text_area("System Prompt para Queries", 
                                  value="""Você é um especialista em pesquisa jurídica brasileira. Sua tarefa é gerar queries de busca precisas e eficazes para encontrar informações relevantes sobre legislação, jurisprudência e normas brasileiras.

Diretrizes:
- Use termos jurídicos específicos e precisos
- Inclua sinônimos e variações terminológicas
- Considere diferentes níveis de governo (federal, estadual, municipal)
- Foque em aspectos práticos e procedimentais
- Use linguagem formal e técnica apropriada""",
                                  height=150,
                                  help="Prompt para gerar queries de busca")

    system_resposta = st.text_area("System Prompt para Respostas",
                                   value="""Você é um assistente jurídico especializado em direito brasileiro. Sua função é fornecer respostas claras, precisas e bem fundamentadas sobre questões legais, baseando-se exclusivamente no contexto fornecido.

Diretrizes:
- Base suas respostas APENAS no contexto fornecido
- Cite as fontes legais quando disponíveis (leis, decretos, etc.)
- Use linguagem clara e acessível, mas tecnicamente precisa
- Estruture a resposta de forma lógica e organizada
- Se o contexto for insuficiente, indique claramente essa limitação
- Não invente informações que não estejam no contexto""",
                                   height=150,
                                   help="Prompt para gerar respostas")

# Seleção de Modelos
st.subheader("🤖 Seleção de Modelos")

# Modelos que suportam saída estruturada em JSON
modelos_disponiveis = {
    "GPT-4o": "openai/gpt-4o",
    "GPT-4o Mini": "openai/gpt-4o-mini", 
    "Claude 3.5 Sonnet": "anthropic/claude-3.5-sonnet",
    "Claude 3 Haiku": "anthropic/claude-3-haiku",
    "Gemini 1.5 Pro": "google/gemini-pro-1.5",
    "Grok 2": "xai/grok-2-1212",
    "Command R+": "cohere/command-r-plus",
    "Qwen 2.5 72B": "qwen/qwen-2.5-72b-instruct",
    "Yi 1.5 34B": "01-ai/yi-1.5-34b-chat",
    "Mistral 7B": "mistralai/mistral-7b-instruct",
    "Mistral 7B v0.1": "mistralai/mistral-7b-instruct-v0.1",
    "Mixtral 8x7B": "mistralai/mixtral-8x7b-instruct",
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct",
    "Llama 3.1 8B": "meta-llama/llama-3.1-8b-instruct",
    "Llama 3.1 70B": "meta-llama/llama-3.1-70b-instruct",
    "Llama 3.1 405B": "meta-llama/llama-3.1-405b-instruct"
}

col1, col2 = st.columns(2)
with col1:
    modelo_a = st.selectbox("Modelo A", list(modelos_disponiveis.keys()), index=0, help="Primeiro modelo para comparação")
with col2:
    modelo_b = st.selectbox("Modelo B", list(modelos_disponiveis.keys()), index=1, help="Segundo modelo para comparação")

modelos_selecionados = [modelos_disponiveis[modelo_a], modelos_disponiveis[modelo_b]]

# Modo de Contexto
st.subheader("📄 Modo de Tratamento de Contexto")
modo_contexto = st.selectbox(
    "Modo de Contexto",
    ["truncar", "resumir"],
    index=0,
    help='Modo de tratamento de contexto quando excede o limite de tokens: "truncar" (reduz regressivamente o tamanho: 100k → 50k → 28k) ou "resumir" (gera resumo com Gemini 2.5 Flash)'
)

# Parâmetros opcionais
num_queries = st.number_input("Número de Queries", min_value=1, max_value=10, value=3)

# Botão executar
if st.button("Executar Avaliação"):
    # Caminho absoluto para run.py
    run_py_path = os.path.join(Path(__file__).parent.parent, 'run.py')
    
    # Preparar argumentos
    args = ["python", run_py_path]

    if modo == "Avaliação Rápida":
        args.append("--quick_eval")
    elif modo == "Perguntas Customizadas":
        if perguntas:
            for p in perguntas.split('\n'):
                if p.strip():
                    args.extend(["--perguntas", p.strip()])
        if ground_truth:
            for gt in ground_truth.split('\n'):
                args.extend(["--ground_truth", gt.strip() or ""])
    elif modo == "Arquivo CSV" and csv_file:
        # Salvar temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(csv_file.getvalue())
            args.extend(["--csv_file", tmp.name])

    args.extend(["--num_queries", str(num_queries)])
    
    # Alternativa: passar como lista única
    args.extend(["--modelos"] + modelos_selecionados)
    args.extend(["--modo_contexto", modo_contexto])

    # Tratar system prompts - usar arquivos se tiverem quebras de linha
    if '\n' in system_queries:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt", encoding='utf-8') as tmp:
            tmp.write(system_queries)
            args.extend(["--system_queries_file", tmp.name])
    else:
        args.extend(["--system_queries", system_queries])
    
    if '\n' in system_resposta:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt", encoding='utf-8') as tmp:
            tmp.write(system_resposta)
            args.extend(["--system_resposta_file", tmp.name])
    else:
        args.extend(["--system_resposta", system_resposta])
    
    # Debug: mostrar modelos e argumentos
    st.write(f"**Modelos selecionados:** {modelos_selecionados}")
    st.write(f"**Modo de contexto:** {modo_contexto}")
    st.write(f"**Argumentos:** {' '.join(args)}")

    # Definir API key no ambiente
    env = os.environ.copy()
    env['OPENAI_API_KEY'] = api_key

    # Executar
    st.info("Iniciando avaliação... Isso pode levar alguns minutos.")

    progress_bar = st.progress(0)
    status_text = st.empty()
    log_area = st.empty()

    logs = []

    try:
        process = subprocess.Popen(args, cwd=Path(__file__).parent.parent, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1, universal_newlines=True)

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logs.append(output.strip())
                log_area.code("\n".join(logs), language="text")  # Mostra todos os logs com scroll

        progress_bar.progress(100)
        status_text.success("Avaliação concluída! Verifique os resultados abaixo.")

        # Exibir comparação de resultados
        st.subheader("📊 Comparação de Modelos")
        results_path = os.path.join(Path(__file__).parent.parent, 'results', 'comparacao_modelos.json')
        if os.path.exists(results_path):
            with open(results_path, 'r', encoding='utf-8') as f:
                comparacao = json.load(f)
            
            stats = comparacao.get('estatisticas_por_modelo', {})
            ranking = comparacao.get('ranking_modelos', [])
            
            if ranking:
                vencedor = ranking[0]['modelo']
                st.success(f"🏆 **Modelo Vencedor**: {vencedor}")
            
            # Tabela de comparação
            import pandas as pd
            data = []
            for modelo, stat in stats.items():
                data.append({
                    'Modelo': modelo,
                    'Faithfulness': f"{stat['faithfulness_media']:.3f}",
                    'Relevancy': f"{stat['answer_relevancy_media']:.3f}",
                    'Context Precision': f"{stat.get('context_precision_media', 0.0):.3f}",
                    'ROUGE-1': f"{stat['rouge_1_f1_media']:.3f}",
                    'BERTScore': f"{stat['bertscore_f1_media']:.3f}",
                    'Tempo Médio (s)': f"{stat['tempo_resposta_medio']:.2f}"
                })
            df = pd.DataFrame(data)
            st.table(df)

            # Issues Identificados
            st.subheader("📋 Issues Identificados")
            try:
                results_path = os.path.join(Path(__file__).parent.parent, 'results', 'resultados.json')
                with open(results_path, 'r', encoding='utf-8') as f:
                    resultados = json.load(f)
                
                issues_por_modelo = {}
                for res in resultados:
                    modelo = res['modelo']
                    issues = res.get('issues', [])
                    if issues:
                        if modelo not in issues_por_modelo:
                            issues_por_modelo[modelo] = []
                        issues_por_modelo[modelo].extend(issues)
                
                if issues_por_modelo:
                    for modelo, issues in issues_por_modelo.items():
                        st.write(f"**{modelo}:**")
                        for issue in issues:
                            st.write(f"- {issue}")
                else:
                    st.write("Nenhum issue identificado.")
            except Exception as e:
                st.write(f"Erro ao carregar issues: {e}")
    except Exception as e:
        st.error(f"Erro durante execução: {e}")

# Guia sobre métricas e system prompts
st.markdown("---")
st.subheader("📖 Guias")

tab1, tab2 = st.tabs(["System Prompts", "Métricas"])

with tab1:
    st.markdown("""
    #### O que são System Prompts?
    System prompts são instruções especiais dadas aos modelos de IA para definir seu comportamento e contexto.
    
    - **System Queries**: Define como o modelo deve gerar queries de busca. Deve ser focado em pesquisa jurídica brasileira.
    - **System Resposta**: Define como o modelo deve gerar respostas. Deve enfatizar precisão jurídica e uso do contexto.
    
    #### Dicas para Customização:
    - Mantenha linguagem formal e técnica para contexto jurídico.
    - Inclua diretrizes específicas sobre fontes legais.
    - Evite prompts muito longos para não sobrecarregar o modelo.
    """)

with tab2:
    st.markdown("""
    #### Métricas de Avaliação:
    - **Faithfulness (Fidelidade)**: Mede se a resposta é consistente com o contexto fornecido. Valores próximos de 1.0 indicam alta fidelidade.
    - **Answer Relevancy (Relevância)**: Avalia se a resposta é relevante para a pergunta feita. Importante para garantir que o modelo não se desvie do tópico.
    - **ROUGE Scores**: Compara a resposta gerada com a resposta ideal (se fornecida). ROUGE-1 foca em unigramas, ROUGE-2 em bigramas.
    - **BERTScore**: Usa embeddings BERT para comparar similaridade semântica entre resposta gerada e ideal.
    - **Tempo de Resposta**: Mede a eficiência do modelo em termos de velocidade.

    #### Importância:
    Essas métricas ajudam a identificar o melhor modelo para seu caso de uso. Por exemplo:
    - Para precisão jurídica, priorize **Faithfulness** e **Relevancy**.
    - Para eficiência, considere o **Tempo de Resposta**.
    - O **vencedor** é determinado pela combinação de Faithfulness e Relevancy.
    """)

st.markdown("---")
st.markdown("**Nota**: Certifique-se de que o repositório está clonado e as dependências instaladas no diretório pai.")