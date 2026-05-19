#!/usr/bin/env python3
"""Inicia o dashboard interativo do knowledge graph do projeto.

Requer: Node.js >= 22, pnpm >= 10
O plugin understand-anything deve estar instalado em ~/.understand-anything-plugin
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
GRAPH_FILE = PROJECT_DIR / ".understand-anything" / "knowledge-graph.json"
PLUGIN_DIR = Path.home() / ".understand-anything-plugin"
DASHBOARD_DIR = PLUGIN_DIR / "packages" / "dashboard"


def main():
    if not GRAPH_FILE.exists():
        print(f"❌  Nenhum knowledge graph encontrado em {GRAPH_FILE}")
        print("    Execute /understand primeiro para analisar o projeto.")
        sys.exit(1)

    if not DASHBOARD_DIR.is_dir():
        print(f"❌  Dashboard não encontrado em {DASHBOARD_DIR}")
        print("    Instale o plugin understand-anything primeiro.")
        sys.exit(1)

    # Garantir que o core está buildado
    print("🔨  Verificando build do core...")
    subprocess.run(
        ["pnpm", "--filter", "@understand-anything/core", "build"],
        cwd=PLUGIN_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Instalar deps do dashboard se necessário
    if not (DASHBOARD_DIR / "node_modules").is_dir():
        print("📦  Instalando dependências do dashboard...")
        subprocess.run(
            ["pnpm", "install"],
            cwd=DASHBOARD_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Iniciar o Vite
    env = os.environ.copy()
    env["GRAPH_DIR"] = str(PROJECT_DIR)

    print("🚀  Iniciando dashboard...")
    print("    Abra o link com ?token= que aparecer abaixo no navegador.")
    print("    Pressione Ctrl+C para parar.\n")

    subprocess.run(
        ["npx", "vite", "--host", "127.0.0.1"],
        cwd=DASHBOARD_DIR,
        env=env,
    )


if __name__ == "__main__":
    main()
