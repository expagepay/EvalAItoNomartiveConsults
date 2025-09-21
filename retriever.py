import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import logging

logger = logging.getLogger(__name__)


# =====================================================
# 🔍 FUNÇÃO DE BUSCA NO LEXML
# =====================================================
BASE_URL = "https://www.lexml.gov.br/busca/search"


def buscar_lexml(termo: str, pagina_inicial: int = 0, quantidade: int = 10, resultados_por_pagina: int = 10, autoridade: str = None):
    resultados = []
    pagina_inicial = pagina_inicial
    total_coletados = 0
    print(f"Buscando '{termo}' (max {quantidade} resultados)")
    termo_encoded = urllib.parse.quote(str(termo))

    logger.info(f"Buscando '{termo}' (max {quantidade} resultados)")

    while total_coletados < quantidade:
        pagina_inicial += 1
        start_doc = 1 + (pagina_inicial- 1) * resultados_por_pagina

        # Construir URL com filtro opcional de autoridade
        url = f"{BASE_URL}?keyword={termo_encoded}"
        
        # Adicionar filtro de autoridade se especificado
        if autoridade and autoridade in ['Estadual', 'Federal', 'Municipal', 'Distrital']:
            url += f";f1-autoridade={autoridade}"

        url += f";startDoc={start_doc}"

        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser') 
            
            results_div = soup.find('div', class_='results')
            if not results_div:
                print(f"Estrutura 'results' não encontrada na página {pagina_inicial}")
                break

            doc_hits = results_div.find_all('div', class_='docHit')

            if not doc_hits:
                break

            for doc_hit in doc_hits:
                if total_coletados >= quantidade:
                    break

            all_tables = soup.find_all('table')
            autoridade_global = None
            localidade_global = None
            
            
            for i, table in enumerate(all_tables):
                rows = table.find_all('tr')
                
                for j, row in enumerate(rows):
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        key_cell = cols[1]
                        value_cell = cols[2]
                        
                        key_tag = key_cell.find('b')
                        if key_tag:
                            key_text = key_tag.get_text().strip().lower()
                            key = ''.join(c for c in key_text if c.isalpha())
                            value = value_cell.get_text(strip=True)
                            
                            if key == 'autoridade' and not autoridade_global:
                                autoridade_global = value
                            elif key == 'localidade' and not localidade_global:
                                localidade_global = value
            
            # processar cada documento individual
            for doc_hit in doc_hits:
                dados = {
                    "titulo": "Título não disponível",
                    "ementa": "Ementa não disponível",
                    "link": "Link não disponível",
                    "autor": "Autor não informado",
                    "autoridade": "Autor não informado",
                    "data": "Data não informada",
                    "localidade": "Localidade não informada",
                    "subtitulo": ""
                }
                
                # Usar valores globais como padrão
                if autoridade_global:
                    dados['autoridade'] = autoridade_global
                if localidade_global:
                    dados['localidade'] = localidade_global

                table = doc_hit.find('table')
                if not table:
                    continue
                    
                rows = table.find_all('tr')

                last_field = None

                # Processar linhas da tabela
                for row in rows:
                    key_tag = row.find('b')
                    key = None
                    if key_tag:
                        key_text = key_tag.get_text()
                        key = ''.join(c.lower() for c in key_text if c.isalpha())

                    value_tag = row.find_all('td')
                    if len(value_tag) < 3:
                        continue
                    
                    value = value_tag[2].get_text(strip=True)

                    if key:
                        if key == 'título':
                            dados['titulo'] = value
                            link_tag = value_tag[2].find('a')
                            if link_tag and link_tag.get('href'):
                                href = link_tag.get('href').lstrip('/')
                                dados["link"] = "https://www.lexml.gov.br/" + href
                        elif key == 'autor':
                            dados['autor'] = value
                        elif key == 'autoridade':
                            dados['autoridade'] = value
                        elif key == 'localidade':
                            dados['localidade'] = value
                        elif key == 'data':
                            dados['data'] = value
                        elif key == 'ementa':
                            dados['ementa'] = value
                        elif key == 'assuntos':
                            dados['assuntos'] = value
                        
                        last_field = key

                if dados["titulo"] != "Título não disponível" and total_coletados < quantidade:
                    resultados.append(dados)
                    total_coletados += 1

            # Verificar "Próxima"
            next_link = soup.find('a', string='Próxima')
            if not next_link:
                break

        except Exception as e:
            print(f"ERRO na página {pagina_inicial}: {e}")
            break

    logger.info(f"Busca concluída: {total_coletados} resultados, {pagina_inicial} páginas")
    print(f"Coletados: {total_coletados} resultados")
    return resultados