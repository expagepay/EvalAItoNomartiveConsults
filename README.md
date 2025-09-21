# EvalAItoNomartiveConsults

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1i2NHH48N4ZOdk9Mt8jYa9ffSLSfnQHMh?usp=sharing)

Uma ferramenta para avaliação comparativa de modelos de IA em consultas jurídicas brasileiras. O sistema gera queries de busca, coleta contextos legais, produz respostas e avalia métricas como faithfulness, relevância e similaridade textual.

## Pré-requisitos

- **Python 3.8+** instalado no sistema.
- Chave de API válida para [OpenRouter](https://openrouter.ai/) (para acesso aos modelos de IA).

## Instalação

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/expagepay/EvalAItoNomartiveConsults.git
   cd EvalAItoNomartiveConsults
   ```

2. **Configure o ambiente virtual**:
   - Execute o launcher da interface web (ele cria o venv automaticamente):
     ```bash
     cd web_interface
     python launcher.py
     ```
     Isso cria um venv na raiz do projeto e instala as dependências de `requirements.txt`.

3. **Configure a API**:
   - Crie um arquivo `.env` na raiz do projeto com:
     ```
     OPENAI_API_KEY=sk-or-v1-sua-chave-aqui
     ```
   - Obtenha a chave em [OpenRouter Keys](https://openrouter.ai/keys).

## Uso

### Interface Web (Recomendado para Iniciantes)

Execute o launcher para iniciar a interface Streamlit:
```bash
cd web_interface
python launcher.py
```
Acesse `http://localhost:8501` no navegador para configurar perguntas, modelos e executar avaliações de forma interativa.

### CLI (Linha de Comando)

Use `run.py` para execuções programáticas:

```bash
python run.py --perguntas "Quais são os direitos do consumidor no Brasil?" --ground_truth "Resposta ideal aqui" --num_queries 3 --modelos meta-llama/llama-3.3-70b-instruct mistralai/mistral-7b-instruct
```

#### Argumentos Principais
- `--perguntas`: Lista de perguntas (ex: `--perguntas "Pergunta 1" "Pergunta 2"`).
- `--ground_truth`: Resposta ideal opcional para avaliação.
- `--num_queries`: Número de queries por modelo (padrão: 3).
- `--system_queries`: Prompt para geração de queries.
- `--system_resposta`: Prompt para geração de respostas.
- `--modelos`: Modelos a comparar (ex: `meta-llama/llama-3.3-70b-instruct`).

Exemplo completo:
```bash
python run.py --perguntas "O que é a LGPD?" --num_queries 2 --modelos mistralai/mistral-7b-instruct
```

### Resultados

Os resultados são salvos em `results/`:
- `resultados.json`: Dados brutos detalhados.
- `comparacao_modelos.json`: Relatório de comparação com rankings.
- `resultados.csv`: Tabela para análise em planilhas.

## Métricas Avaliadas

O sistema calcula métricas para comparar a qualidade das respostas:

- **Faithfulness**: Verifica se a resposta é fiel aos contextos fornecidos (usando RAGAS).
- **Answer Relevancy**: Avalia se a resposta é relevante à pergunta (usando RAGAS).
- **ROUGE-1/2 F1**: Mede similaridade textual com ground truth (precisão e recall).
- **BERTScore F1**: Similaridade semântica baseada em embeddings BERT.

Scores variam de 0.0 a 1.0 (maior = melhor). Métricas = 0.0 indicam falhas (ex: contextos vazios).

## Guia Geral

1. **Pipeline de Execução**:
   - Geração de queries de busca jurídica.
   - Coleta de contextos via API do LexML.
   - Geração de respostas com base nos contextos.
   - Avaliação automática das métricas.

2. **Modelos Suportados**:
   - Qualquer modelo via OpenRouter (ex: Llama, Mistral, Gemini).
   - Recomendado: `meta-llama/llama-3.3-70b-instruct`, `mistralai/mistral-7b-instruct`.

3. **Limitações**:
   - Dependente de conectividade com OpenRouter.
   - Contextos limitados a 25k caracteres (resumidos se maior).
   - Avaliações em português para legislação brasileira.

4. **Dicas**:
   - Use perguntas específicas para melhores contextos.
   - Monitore logs para erros (ex: rate limits, encoding).
   - Para Colab: Abra o notebook e siga as células.
