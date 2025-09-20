# run.py
import argparse
import csv
from main import run_pipeline

def main():
    parser = argparse.ArgumentParser(description="Executar pipeline de avaliação de modelos de IA para consultas jurídicas brasileiras.")
    
    # Defaults
    default_perguntas = [
        "Quais são os direitos do consumidor no Brasil?",
        "Como funciona o processo de aposentadoria no INSS?",
        "Quais são as regras para abertura de empresa no Brasil?"
    ]
    default_system_queries = """Você é um especialista em pesquisa jurídica brasileira. Sua tarefa é gerar queries de busca precisas e eficazes para encontrar informações relevantes sobre legislação, jurisprudência e normas brasileiras.

Diretrizes:
- Use termos jurídicos específicos e precisos
- Inclua sinônimos e variações terminológicas
- Considere diferentes níveis de governo (federal, estadual, municipal)
- Foque em aspectos práticos e procedimentais
- Use linguagem formal e técnica apropriada"""
    
    default_system_resposta = """Você é um assistente jurídico especializado em direito brasileiro. Sua função é fornecer respostas claras, precisas e bem fundamentadas sobre questões legais, baseando-se exclusivamente no contexto fornecido.

Diretrizes:
- Base suas respostas APENAS no contexto fornecido
- Cite as fontes legais quando disponíveis (leis, decretos, etc.)
- Use linguagem clara e acessível, mas tecnicamente precisa
- Estruture a resposta de forma lógica e organizada
- Se o contexto for insuficiente, indique claramente essa limitação
- Não invente informações que não estejam no contexto"""
    
    # Mock padrão para avaliação rápida
    mock_perguntas = [
        "Quais são os direitos do consumidor no Brasil?",
        "Como funciona o processo de aposentadoria no INSS?",
        "Quais são as regras para abertura de empresa no Brasil?",
        "O que é a LGPD?",
        "Quem criou a LGPD?",
        "Quais são as penalidades por violação da LGPD?"
    ]
    mock_ground_truths = [
        "Os direitos do consumidor incluem proteção contra práticas abusivas, garantia de produtos e serviços, direito à informação, etc., conforme o Código de Defesa do Consumidor (Lei nº 8.078/1990).",
        "O processo de aposentadoria no INSS envolve contribuição previdenciária por pelo menos 15 anos, idade mínima de 65 anos para homens e 62 para mulheres, ou tempo de contribuição de 35 anos para homens e 30 para mulheres.",
        "Para abertura de empresa no Brasil, é necessário registrar no CNPJ, escolher o regime tributário (Simples Nacional, Lucro Presumido, etc.), obter alvará municipal e estadual, e cumprir obrigações fiscais.",
        "A LGPD é a Lei Geral de Proteção de Dados (Lei nº 13.709/2018), que regula o tratamento de dados pessoais no Brasil, visando proteger a privacidade dos indivíduos.",
        "A LGPD foi criada pelo Congresso Nacional brasileiro e sancionada pelo Presidente da República em 2018.",
        "As penalidades por violação da LGPD incluem multas de até 2% do faturamento da empresa (limitado a R$ 50 milhões por infração), além de outras sanções administrativas e civis."
    ]
    
    # Argumentos
    parser.add_argument('--perguntas', nargs='*', default=default_perguntas, help='Lista de perguntas a serem processadas (use aspas duplas para perguntas com espaços, ex: --perguntas "O que é a lei" "Outra pergunta")')
    parser.add_argument('--ground_truth', nargs='*', default=[], help='Respostas ideais opcionais para avaliação, uma por pergunta (use "" para vazio ou omita para auto-gerar)')
    parser.add_argument('--csv_file', type=str, help='Arquivo CSV com colunas "pergunta" e "ground_truth" (opcional, sobrescreve --perguntas e --ground_truth)')
    parser.add_argument('--quick_eval', action='store_true', help='Usa conjunto padrão de perguntas e ground truths para avaliação rápida (sobrescreve --perguntas e --ground_truth)')
    parser.add_argument('--num_queries', type=int, default=3, help='Número máximo de queries que os modelos podem gerar')
    parser.add_argument('--system_queries', type=str, default=default_system_queries, help='System prompt para geração de queries')
    parser.add_argument('--system_resposta', type=str, default=default_system_resposta, help='System prompt para geração de respostas')
    parser.add_argument('--modelos', nargs='+', default=['mistralai/mistral-7b-instruct', 'meta-llama/llama-3.3-70b-instruct'], help='Lista de modelos a serem comparados')
    
    args = parser.parse_args()
    
    # Prioridade: quick_eval > csv_file > argumentos
    if args.quick_eval:
        perguntas = mock_perguntas
        ground_truths = mock_ground_truths
    elif args.csv_file:
        perguntas = []
        ground_truths = []
        try:
            with open(args.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    perguntas.append(row['pergunta'].strip())
                    gt = row.get('ground_truth', '').strip()
                    ground_truths.append(gt if gt else None)
        except Exception as e:
            print(f"Erro ao ler CSV: {e}")
            return
    else:
        perguntas = args.perguntas
        ground_truths = args.ground_truth
    
    # Construir config
    config = {
        'perguntas': perguntas,
        'ground_truth': ground_truths,
        'num_queries': args.num_queries,
        'system_prompts': {
            'queries': args.system_queries,
            'resposta': args.system_resposta
        },
        'modelos': args.modelos
    }
    
    # Executar pipeline
    run_pipeline(config)

if __name__ == "__main__":
    main()
