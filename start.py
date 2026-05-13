import os
import sys
import subprocess
import time
import webbrowser
import socket
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
ENV_FILE = os.path.join(BACKEND_DIR, ".env")
VENV_DIR = os.path.join(BACKEND_DIR, ".venv")
PORT = os.environ.get("PORT", "8000")

if sys.platform == "win32":
    _BIN = "Scripts"
    _EXE = ".exe"
else:
    _BIN = "bin"
    _EXE = ""

PYTHON_EXE = os.path.join(VENV_DIR, _BIN, f"python{_EXE}")
UV_EXE = "uv"

BANNER = """
========================================
  VG 24H - Portal de Servicos Publicos
========================================
"""

ENV_TEMPLATE = """SECRET_KEY='django-insecure-=4go(b5(k7+p04r7n)7sht+ct(t=7+k39u%j11wlv%p3jqm@*#'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=neondb
POSTGRES_USER=neondb_owner
POSTGRES_PASSWORD=npg_HxpBqfrFvW45
POSTGRES_HOST=ep-blue-base-acfyy807.sa-east-1.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_SSL=require

CLOUDINARY_URL=cloudinary://356796922145521:3mbCw6p64k_h3xOAqBJka7P3GJ0@dceazqrtx
"""


def print_banner():
    print(BANNER)


def get_env_from_user():
    print("Cole o conteudo do .env abaixo (Ctrl+Z + Enter para finalizar):")
    print("-" * 60)
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    content = "\n".join(lines).strip()
    if not content:
        print("Nenhum conteudo fornecido. Usando valores padrao.")
        return ENV_TEMPLATE.strip()
    return content


def save_env(content):
    os.makedirs(BACKEND_DIR, exist_ok=True)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")
    print(f".env salvo em {ENV_FILE}")


def ensure_venv():
    if os.path.isdir(VENV_DIR):
        print("Virtual environment encontrado.")
        return True
    print("Criando virtual environment com uv...")
    result = subprocess.run(
        [UV_EXE, "venv", VENV_DIR],
        capture_output=True, text=True, cwd=BACKEND_DIR
    )
    if result.returncode != 0:
        print(f"Erro ao criar venv: {result.stderr}")
        return False
    print("Virtual environment criado com sucesso.")
    return True


def install_requirements():
    req_file = os.path.join(BACKEND_DIR, "requirements.txt")
    if not os.path.isfile(req_file):
        print("requirements.txt nao encontrado.")
        return False
    print("Instalando dependencias com uv...")
    result = subprocess.run(
        [UV_EXE, "pip", "install", "-r", req_file],
        capture_output=True, text=True, cwd=BACKEND_DIR
    )
    if result.returncode != 0:
        print(f"Erro ao instalar dependencias: {result.stderr}")
        return False
    print("Dependencias instaladas.")
    return True


def kill_process_on_port(port):
    if sys.platform != "win32":
        return
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line:
                match = re.search(r"\s+(\d+)$", line)
                if match:
                    pid = match.group(1)
                    try:
                        subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            capture_output=True, text=True
                        )
                    except Exception:
                        pass
    except Exception:
        pass


def find_free_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", int(port))) != 0:
            return port
    for p in range(int(port), int(port) + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return str(p)
    return port


def get_lan_ip():
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if "IPv4" in line and "192.168" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        return parts[1].strip()
        else:
            result = subprocess.run(
                ["hostname", "-I"], capture_output=True, text=True
            )
            ips = result.stdout.strip().split()
            for ip in ips:
                if ip.startswith("192.168"):
                    return ip
    except Exception:
        pass
    return None


def start_server(port):
    kill_process_on_port(port)
    port = find_free_port(port)
    print(f"\nIniciando servidor na porta {port}...")

    log_file = os.path.join(BASE_DIR, "server.log")
    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"--- Servidor iniciado em {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    process = subprocess.Popen(
        [PYTHON_EXE, "-u", "manage.py", "runserver", f"0.0.0.0:{port}", "--noreload"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    print("Aguardando servidor iniciar", end="", flush=True)
    timeout = 30
    started = False

    with open(log_file, "a", encoding="utf-8") as log:
        while timeout > 0:
            line = process.stdout.readline()
            if line:
                log.write(line)
                log.flush()
                if "Starting development server" in line:
                    started = True
                    print(" OK!")
                    break
            print(".", end="", flush=True)
            time.sleep(1)
            timeout -= 1

    if not started:
        remaining = process.stdout.read()
        if remaining:
            with open(log_file, "a", encoding="utf-8") as log:
                log.write(remaining)
        print(" TIMEOUT")
        print(f"Verifique o log: {log_file}")
        process.terminate()
        return False

    print()
    print("========================================")
    print("  Servidor VG 24H iniciado!")
    print("========================================")
    print()
    print(f"  Local:   http://127.0.0.1:{port}/")

    lan_ip = get_lan_ip()
    if lan_ip:
        print(f"  Rede:    http://{lan_ip}:{port}/")

    print()
    print(f"  Log:     {log_file}")
    print()

    print("  Navegador aberto automaticamente.")
    webbrowser.open(f"http://127.0.0.1:{port}/")

    print()
    print("Para parar o servidor, pressione Ctrl+C")
    print()

    try:
        while True:
            time.sleep(1)
            if process.poll() is not None:
                print("Servidor encerrado.")
                break
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        process.terminate()
        process.wait(timeout=5)
        print("Servidor encerrado.")

    return True


def main():
    print_banner()

    if not os.path.isfile(ENV_FILE):
        content = get_env_from_user()
        save_env(content)
    else:
        resp = input(".env ja existe. Deseja substituir? (s/N): ").strip().lower()
        if resp == "s":
            content = get_env_from_user()
            save_env(content)
        else:
            print("Usando .env existente.")

    if not ensure_venv():
        input("\nErro ao configurar venv. Pressione Enter para sair...")
        return

    if not install_requirements():
        input("\nErro ao instalar dependencias. Pressione Enter para sair...")
        return

    if not start_server(PORT):
        input("\nErro ao iniciar servidor. Pressione Enter para sair...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        input("Pressione Enter para sair...")
