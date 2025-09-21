# Interface Web para Avaliação de Modelos Jurídicos

Esta interface web permite executar avaliações de modelos de IA para consultas jurídicas brasileiras de forma intuitiva e local.

## Como Usar

1. **Certifique-se de ter Python instalado** (versão 3.7+).

2. **Execute o launcher**:
   ```bash
   python launcher.py
   ```

   O launcher irá:
   - Criar um ambiente virtual (se não existir).
   - Instalar as dependências necessárias.
   - Iniciar a interface web automaticamente.

3. **Acesse a interface**:
   - Abra seu navegador e vá para `http://localhost:8501` (padrão do Streamlit).

4. **Configure e execute**:
   - Insira sua API Key do OpenRouter (obrigatório).
   - Escolha o modo de avaliação.
   - Ajuste parâmetros opcionais.
   - Clique em "Executar Avaliação".

## Funcionalidades

- **Modos de Avaliação**:
  - **Avaliação Rápida**: Usa conjunto padrão de perguntas jurídicas.
  - **Perguntas Customizadas**: Digite suas próprias perguntas.
  - **Arquivo CSV**: Faça upload de um arquivo com perguntas e respostas ideais.

- **Parâmetros Ajustáveis**:
  - Número de queries por pergunta.
  - Seleção de modelos de IA.

- **Progresso em Tempo Real**: Veja logs e progresso da execução.

- **Resultados**: Salvos automaticamente na pasta `results` do projeto pai.

## Estrutura

- `launcher.py`: Script para gerenciar ambiente virtual e iniciar a interface.
- `app.py`: Aplicação Streamlit principal.
- `requirements.txt`: Dependências da interface.
- `README.md`: Este arquivo.

## Requisitos

- Python 3.7+
- Acesso à internet (para API do OpenRouter e downloads de modelos)

## Solução de Problemas

- Se houver erro de permissões, execute como administrador.
- Certifique-se de que a pasta pai contém o código principal do projeto.
- Para Windows, o launcher cria um venv em `web_interface/venv`.

Aproveite a avaliação intuitiva dos seus modelos!