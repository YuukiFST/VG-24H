#!/usr/bin/env python
"""manage.py — eh por aqui que eu rodo os comandos do Django (runserver, migrate, meus commands...)."""
import os
import sys


def main():
    """Roda a tarefa que eu pedi na linha de comando."""
    # digo qual settings usar antes de qualquer coisa
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        # importo a funcao do Django que entende os comandos
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # se cair aqui geralmente eu esqueci de ativar a venv ou instalar o Django
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # passo os argumentos do terminal (sys.argv) pro Django executar
    execute_from_command_line(sys.argv)


# so roda quando chamo o arquivo direto: python manage.py ...
if __name__ == '__main__':
    main()
