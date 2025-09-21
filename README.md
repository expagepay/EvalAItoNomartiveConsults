# EvalAItoNomartiveConsults

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1HThgioW620LWUm4G6vCqE17_tcxtsdUf?usp=sharing)

Uma ferramenta completa para avaliação comparativa de modelos de IA em consultas jurídicas brasileiras. O sistema automatiza o pipeline RAG (Retrieval-Augmented Generation): gera queries de busca, coleta contextos legais da LexML, produz respostas e avalia múltiplas métricas de qualidade.

## 🚀 Recursos Principais

- **Avaliação Automática**: Compare modelos de IA em tarefas jurídicas brasileiras.
- **Métricas Abrangentes**: Faithfulness, Relevancy, Context Precision, ROUGE, BERTScore.
- **Estratégias de Contexto**: Truncamento regressivo ou resumo inteligente para limites de tokens.
- **Interface Web**: Fácil de usar via Streamlit, sem necessidade de código.
- **Flexibilidade**: Modelos personalizados, perguntas customizadas, ground truths opcionais.
- **Relatórios Detalhados**: Resultados em JSON, CSV e rankings comparativos.

## 📋 Pré-requisitos

- **Python 3.8+** instalado.
- **Chave de API do OpenRouter** (gratuita para testes, paga para uso intensivo).
- **Conexão com internet** para acesso aos modelos e busca de contextos.

## 🛠️ Instalação

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/expagepay/EvalAItoNomartiveConsults.git
   cd EvalAItoNomartiveConsults
   ```

2. **Configure o ambiente**:
   - Use o launcher da interface web (cria venv automaticamente):
     ```bash
     cd web_interface
     python launcher.py
     ```
     Isso instala `requirements.txt` e configura o ambiente.

3. **Configure a API**:
   - Crie `.env` na raiz:
     ```
     OPENAI_API_KEY=sk-or-v1-sua-chave-openrouter
     ```
   - Obtenha em [OpenRouter Keys](https://openrouter.ai/keys).

4. **Configure cache (opcional, acelera inicializações)**:
   - Adicione ao `.env`:
     ```
     HF_HUB_CACHE=./HF_Cache
     ```

## 🎯 Uso Básico

### Interface Web (Recomendado)

```bash
cd web_interface
python launcher.py
```
Acesse `http://localhost:8501`. Configure perguntas, modelos e execute avaliações interativamente.

### CLI (Linha de Comando)

```bash
# Avaliação rápida com perguntas padrão
python run.py --quick_eval

# Com perguntas customizadas
python run.py --perguntas "O que é LGPD?" "Direitos do consumidor"

# Com arquivo CSV (colunas: pergunta, ground_truth)
python run.py --csv_file meu_arquivo.csv

# Ver opções completas
python run.py --help
```

### Notebook Colab

Abra o [notebook Colab](https://colab.research.google.com/drive/1HThgioW620LWUm4G6vCqE17_tcxtsdUf?usp=sharing) para execução na nuvem.

## ⚙️ Configurações Avançadas

### Modelos Personalizados

Use qualquer modelo do [OpenRouter](https://openrouter.ai/models). Exemplos:

```bash
# Modelos padrão
python run.py --modelos meta-llama/llama-3.3-70b-instruct mistralai/mistral-7b-instruct

# Modelos customizados
python run.py --modelos openai/gpt-4o anthropic/claude-3.5-sonnet google/gemini-pro-1.5
```

**Dicas**:
- Modelos maiores (>100k tokens) são melhores para contexto jurídico.
- Teste limites: GPT-4 ~128k, Claude 3 ~200k, Gemini 1.5 ~1M.
- Custos variam; verifique no OpenRouter.

### Número de Queries (`num_queries`)

Controla quantas queries de busca o modelo gera por pergunta.

```bash
# Padrão: 3 queries
python run.py --num_queries 5  # Mais queries = mais contexto, mas mais lento
```

**Recomendação**: 3-5 para equilíbrio entre qualidade e velocidade.

### Modo de Tratamento de Contexto (`modo_contexto`)

Quando o contexto excede limites de tokens, escolha a estratégia:

- **`truncar`** (padrão): Reduz regressivamente (700k → 100k → 50k → 28k chars).
- **`resumir`**: Gera resumo com Gemini 2.5 Flash, preservando essência.

```bash
# Truncamento regressivo
python run.py --modo_contexto truncar

# Resumo inteligente
python run.py --modo_contexto resumir
```

**Quando usar**:
- `truncar`: Rápido, preserva original.
- `resumir`: Melhor para contextos muito grandes, mas usa tokens extras.

### System Prompts Personalizados

Personalize comportamento dos modelos:

```bash
# Via arquivo
python run.py --system_queries_file meu_prompt_queries.txt --system_resposta_file meu_prompt_resposta.txt

# Ou diretamente (use com aspas)
python run.py --system_queries "Você é um especialista jurídico..."
```

### Ground Truths

Forneça respostas ideais para métricas mais precisas:

```bash
python run.py --perguntas "O que é LGPD?" --ground_truth "Lei Geral de Proteção de Dados (Lei nº 13.709/2018)"
```

Sem ground truth, o sistema gera automaticamente (aproximado).

## 📊 Métricas Explicadas

O sistema avalia respostas com métricas RAGAS + textuais:

### Métricas RAGAS (Avaliam Qualidade RAG)
- **Faithfulness (Fidelidade)**: Resposta consistente com contexto? (0-1, alto = fiel).
- **Answer Relevancy (Relevância)**: Resposta relevante para pergunta? (0-1, alto = relevante).
- **Context Precision (Precisão do Contexto)**: Contextos recuperados são relevantes/úteis? (0-1, alto = precisos).

### Métricas Textuais (Comparação com Ground Truth)
- **ROUGE-1/2**: Similaridade n-gram (0-1, alto = similar).
- **BERTScore**: Similaridade semântica via embeddings (0-1, alto = próximo).

### Interpretação
- **Alto em tudo**: Resposta excelente, bem fundamentada.
- **Baixo Faithfulness**: Modelo "inventou" info.
- **Baixo Relevancy**: Resposta off-topic.
- **Baixo Context Precision**: Busca ruim, contextos irrelevantes.

## 🌐 Interface Web Detalhada

Execute `python launcher.py` na pasta `web_interface`.

### Funcionalidades
- **Seleção de Modelos**: Escolha de lista pré-definida ou customizada.
- **Perguntas**: Texto livre ou upload CSV.
- **Configurações**: num_queries, modo_contexto, system prompts.
- **Resultados**: Tabela comparativa, issues identificados, downloads.

### Issues Identificados
A interface mostra problemas como:
- "Queries JSON malformado"
- "Nenhum contexto recuperado"
- "Resposta vazia"

Ajuda depurar execuções.

## 📁 Estrutura de Arquivos

```
EvalAItoNomartiveConsults/
├── main.py              # Pipeline principal
├── models.py            # Geração de queries/respostas
├── metrics.py           # Avaliação de métricas
├── retriever.py         # Busca de contextos LexML
├── report.py            # Geração de relatórios
├── run.py               # CLI
├── web_interface/       # Interface Streamlit
│   ├── app.py
│   └── launcher.py
├── results/             # Saídas (JSON, CSV)
├── requirements.txt
├── .env                 # Configurações (não versionado)
└── README.md
```

## 🔧 Solução de Problemas

### Inicialização Lenta
- **Causa**: Carregamento de embeddings na primeira avaliação.
- **Solução**: Aguarde; próximas execuções são rápidas (cache).

### Erro de API
- Verifique `OPENAI_API_KEY` no `.env`.
- Créditos insuficientes? Recarregue no OpenRouter.

### Contextos Vazios
- Queries ruins? Verifique issues.
- Rede? Teste conectividade com LexML.

### Modelo Não Responde
- Limite de tokens? Use `modo_contexto truncar`.
- Erro de parsing? Sistema tem fallbacks.

### Cache de Modelos
- Delete `HF_Cache/` para forçar re-download se corrompido.

## 📈 Exemplos de Uso

### Comparação Básica
```bash
python run.py --quick_eval --modelos meta-llama/llama-3.3-70b-instruct openai/gpt-3.5-turbo
```

### Avaliação Jurídica Detalhada
```bash
python run.py \
  --perguntas "Quais são os direitos trabalhistas no Brasil?" \
  --ground_truth "CLT prevê jornada de 8h, férias, etc." \
  --num_queries 5 \
  --modo_contexto resumir \
  --modelos anthropic/claude-3.5-sonnet
```

### Relatório Final
Após execução, veja `results/`:
- `resultados.json`: Dados brutos.
- `comparacao_modelos.json`: Rankings e médias.
- `resultados.csv`: Planilha.

## 🤝 Contribuição

Issues e PRs bem-vindos! Para mudanças grandes, abra issue primeiro.

## 📄 Licença

MIT License - veja LICENSE para detalhes.

---

**Dúvidas?** Abra issue no GitHub ou consulte a documentação do OpenRouter.
