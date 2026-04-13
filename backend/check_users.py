import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from portal.models import Cidadao, Servidor

cidados = Cidadao.objects.all()
servidores = Servidor.objects.all()

print("=== CIDADÃOS ===")
for c in cidados:
    print(f"Email: {c.email} | CPF: {c.cpf} | SenhaTemp: {c.senha_temporaria or 'Nenhuma'}")
if not cidados:
    print("Nenhum cidadão cadastrado.")

print("\n=== SERVIDORES (GESTOR / COLABORADOR) ===")
for s in servidores:
    print(f"Email: {s.email} | CPF: {s.cpf} | Perfil: {s.perfil} | SenhaTemp: {s.senha_temporaria or 'Nenhuma'}")
if not servidores:
    print("Nenhum servidor cadastrado.")
