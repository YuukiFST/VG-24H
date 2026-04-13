import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from portal.models import Cidadao, Servidor
from django.contrib.auth.hashers import make_password

print("CONTAS DISPONÍVEIS NO BANCO DE DADOS:")
print("Cidadãos:")
for c in Cidadao.objects.all():
    c.senha_hash = make_password("portal123")
    c.save()
    print(f"- Login (Email): {c.email} | Perfil: {c.perfil}")

print("\nServidores:")
for s in Servidor.objects.all():
    s.senha_hash = make_password("portal123")
    s.save()
    print(f"- Login (Email): {s.email} | Perfil: {s.perfil} | Secretaria: {s.id_secretaria.nome}")

print("\nNota: As senhas de todas as contas acima foram redefinidas para 'portal123' pois o banco usa criptografia unidirecional (hash).")
