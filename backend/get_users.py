import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from portal.models import Servidor, Cidadao

print("\n=== SERVIDORES (Gestores/Colaboradores) ===")
for s in Servidor.objects.all():
    print(f"EMAIL: {s.email} | NOME: {s.nome_completo} | PERFIL: {s.perfil}")

print("\n=== CIDADÃOS ===")
for c in Cidadao.objects.all():
    print(f"EMAIL: {c.email} | NOME: {c.nome_completo}")
