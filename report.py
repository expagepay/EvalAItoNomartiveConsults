# report.py
import json
import csv
from fpdf import FPDF

def salvar_resultados(resultados):
    print(f"💾 [REPORT] Salvando {len(resultados)} resultados...")
    
    # 1. Salvar JSON
    print(f"📄 [REPORT] Salvando resultados.json...")
    try:
        with open("resultados.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        print(f"✅ [REPORT] JSON salvo com sucesso")
    except Exception as e:
        print(f"❌ [REPORT] Erro ao salvar JSON: {e}")
    
    # 2. Salvar CSV
    print(f"📊 [REPORT] Salvando resultados.csv...")
    try:
        with open("resultados.csv", "w", newline="", encoding="utf-8") as f:
            if resultados:
                writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
                writer.writeheader()
                writer.writerows(resultados)
        print(f"✅ [REPORT] CSV salvo com sucesso")
    except Exception as e:
        print(f"❌ [REPORT] Erro ao salvar CSV: {e}")
    
    # 3. Salvar PDF
    print(f"📋 [REPORT] Gerando relatório PDF...")
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Usar fonte padrão Arial
        pdf.set_font('Arial', '', 12)
        
        pdf.cell(0, 10, "Relatorio de Avaliacao de Modelos", ln=True, align="C")
        pdf.ln(10)
        
        for i, resultado in enumerate(resultados, 1):
            pdf.cell(0, 8, f"Resultado {i}:", ln=True)
            # Remover caracteres especiais para evitar erros de encoding
            pergunta_clean = resultado['pergunta'].encode('latin-1', 'ignore').decode('latin-1')[:80]
            modelo_clean = resultado['modelo'].encode('latin-1', 'ignore').decode('latin-1')
            
            pdf.cell(0, 6, f"Pergunta: {pergunta_clean}...", ln=True)
            pdf.cell(0, 6, f"Modelo: {modelo_clean}", ln=True)
            pdf.cell(0, 6, f"Faithfulness: {resultado['faithfulness']:.3f}", ln=True)
            pdf.cell(0, 6, f"Answer Relevancy: {resultado['answer_relevancy']:.3f}", ln=True)
            pdf.cell(0, 6, f"Contextos: {resultado['num_contextos']}", ln=True)
            pdf.ln(5)
        
        pdf.output("resultados.pdf")
        print(f"✅ [REPORT] PDF salvo com sucesso")
    except Exception as e:
        print(f"❌ [REPORT] Erro ao salvar PDF: {e}")
    
    print(f"🎉 [REPORT] Todos os arquivos salvos!")


def gerar_relatorio_pdf(resultados, nome_arquivo="relatorio_avaliacao.pdf"):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    
    print(f"📄 [REPORT] Gerando relatório PDF: {nome_arquivo}")
    
    doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center
        fontName='Arial'
    )
    story.append(Paragraph("Relatorio de Avaliacao de IA para Consultas Normativas".encode('latin-1', 'ignore').decode('latin-1'), title_style))
    story.append(Spacer(1, 12))
    
    # System Prompts utilizados
    if resultados and len(resultados) > 0 and 'system_prompts' in resultados[0]:
        story.append(Paragraph("System Prompts Utilizados", styles['Heading2']))
        
        system_prompts = resultados[0]['system_prompts']
        
        # System Prompt para Queries
        story.append(Paragraph("System Prompt para Geracao de Queries:", styles['Heading3']))
        queries_prompt = system_prompts.get('queries', 'Nao definido')
        story.append(Paragraph(queries_prompt.encode('latin-1', 'ignore').decode('latin-1'), styles['Normal']))
        story.append(Spacer(1, 12))
        
        # System Prompt para Respostas
        story.append(Paragraph("System Prompt para Geracao de Respostas:", styles['Heading3']))
        resposta_prompt = system_prompts.get('resposta', 'Nao definido')
        story.append(Paragraph(resposta_prompt.encode('latin-1', 'ignore').decode('latin-1'), styles['Normal']))
        story.append(Spacer(1, 24))
    
    # Resumo Executivo
    story.append(Paragraph("Resumo Executivo", styles['Heading2']))
    
    total_perguntas = len(set(r['pergunta'] for r in resultados))
    total_modelos = len(set(r['modelo'] for r in resultados))
    
    resumo_text = f"""
    Este relatorio apresenta a avaliacao de {total_modelos} modelos de IA em {total_perguntas} perguntas sobre consultas normativas.
    Os modelos foram avaliados usando metricas de fidelidade (faithfulness) e relevancia da resposta (answer_relevancy).
    """
    story.append(Paragraph(resumo_text.encode('latin-1', 'ignore').decode('latin-1'), styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Tabela de Resultados
    story.append(Paragraph("Resultados Detalhados", styles['Heading2']))
    
    # Cabeçalho da tabela
    data = [['Pergunta', 'Modelo', 'Faithfulness', 'Answer Relevancy']]
    
    for resultado in resultados:
        pergunta = resultado['pergunta'][:50] + "..." if len(resultado['pergunta']) > 50 else resultado['pergunta']
        modelo = resultado['modelo'].split('/')[-1] if '/' in resultado['modelo'] else resultado['modelo']
        
        # Extrair métricas
        metricas = resultado.get('metricas', {})
        faithfulness = f"{metricas.get('faithfulness', 0.0):.3f}"
        answer_relevancy = f"{metricas.get('answer_relevancy', 0.0):.3f}"
        
        data.append([
            pergunta.encode('latin-1', 'ignore').decode('latin-1'),
            modelo.encode('latin-1', 'ignore').decode('latin-1'),
            faithfulness,
            answer_relevancy
        ])
    
    table = Table(data, colWidths=[3*inch, 1.5*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Arial'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 12))
    
    # Análise por Modelo
    story.append(Paragraph("Analise por Modelo", styles['Heading2']))
    
    modelos_stats = {}
    for resultado in resultados:
        modelo = resultado['modelo']
        if modelo not in modelos_stats:
            modelos_stats[modelo] = {'faithfulness': [], 'answer_relevancy': []}
        
        metricas = resultado.get('metricas', {})
        modelos_stats[modelo]['faithfulness'].append(metricas.get('faithfulness', 0.0))
        modelos_stats[modelo]['answer_relevancy'].append(metricas.get('answer_relevancy', 0.0))
    
    for modelo, stats in modelos_stats.items():
        modelo_nome = modelo.split('/')[-1] if '/' in modelo else modelo
        avg_faith = sum(stats['faithfulness']) / len(stats['faithfulness']) if stats['faithfulness'] else 0
        avg_relevancy = sum(stats['answer_relevancy']) / len(stats['answer_relevancy']) if stats['answer_relevancy'] else 0
        
        modelo_text = f"""
        Modelo: {modelo_nome}
        - Faithfulness media: {avg_faith:.3f}
        - Answer Relevancy media: {avg_relevancy:.3f}
        - Total de avaliacoes: {len(stats['faithfulness'])}
        """
        story.append(Paragraph(modelo_text.encode('latin-1', 'ignore').decode('latin-1'), styles['Normal']))
        story.append(Spacer(1, 8))
    
    try:
        doc.build(story)
        print(f"✅ [REPORT] Relatório PDF gerado com sucesso: {nome_arquivo}")
    except Exception as e:
        print(f"❌ [REPORT] Erro ao gerar PDF: {e}")
