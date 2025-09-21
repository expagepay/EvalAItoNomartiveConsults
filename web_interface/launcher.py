#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
from pathlib import Path

def is_venv():
    """Verifica se estamos em um ambiente virtual."""
    return sys.prefix != sys.base_prefix

def create_venv(venv_path):
    """Cria um ambiente virtual na raiz do projeto."""
    print("Criando ambiente virtual na raiz do projeto...")
    venv.create(venv_path, with_pip=True)
    print("Ambiente virtual criado.")

def install_dependencies(venv_path):
    """Instala dependências no venv usando requirements.txt da raiz."""
    pip_path = os.path.join(venv_path, 'Scripts', 'pip') if os.name == 'nt' else os.path.join(venv_path, 'bin', 'pip')
    # Caminho para requirements.txt na raiz do projeto (dois níveis acima de web_interface)
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / 'requirements.txt'

    print("Instalando dependências...")
    subprocess.check_call([pip_path, 'install', '-r', str(requirements_path)])
    print("Dependências instaladas.")

def run_streamlit(venv_path):
    """Executa o Streamlit no venv."""
    python_path = os.path.join(venv_path, 'Scripts', 'python') if os.name == 'nt' else os.path.join(venv_path, 'bin', 'python')
    app_path = os.path.join(os.path.dirname(__file__), 'app.py')

    print("Iniciando interface web...")
    subprocess.run([python_path, '-m', 'streamlit', 'run', app_path])

def main():
    # Venv na raiz do projeto
    project_root = Path(__file__).parent.parent
    venv_path = project_root / 'venv'

    if not is_venv():
        if not venv_path.exists():
            create_venv(str(venv_path))
            install_dependencies(str(venv_path))
        else:
            print("Ambiente virtual encontrado na raiz.")

        # Ativar venv e executar
        if os.name == 'nt':
            python_exe = venv_path / 'Scripts' / 'python.exe'
            subprocess.run([str(python_exe), __file__])
        else:
            python_exe = venv_path / 'bin' / 'python'
            subprocess.run([str(python_exe), __file__])
    else:
        run_streamlit(str(venv_path))

if __name__ == "__main__":
    main()