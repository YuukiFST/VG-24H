# FAQ de Código e Arquitetura — Portal VG 24H

Este documento reúne perguntas frequentes sobre "Onde acontece tal coisa no código?" para orientar a apresentação e facilitar o entendimento logico de como as requisições se comunicam com o banco de dados.

---

## 1. Onde é feita a busca (SELECT) no banco de dados para o login?

> **Arquivo:** `backend/portal/views_auth.py` (função `login_view`)

Quando o usuário digita e-mail e senha e clica em "Entrar", os dados são enviados para a `login_view`. O Django não utiliza SQL "cru" nessas validações de leitura, ele utiliza uma camada de abstração (ORM). Como existem as tabelas separadas `Cidadao` e `Servidor`, ocorre uma **busca dual**:

```python
try:
    user = Cidadao.objects.get(email__iexact=email, ativo=True)
    tipo = "cidadao"
except Cidadao.DoesNotExist:
    try:
        user = Servidor.objects.get(email__iexact=email, ativo=True)
        tipo = "servidor"
    except Servidor.DoesNotExist:
        pass
```
*Tradução para o Banco de Dados:* Isso funciona como `SELECT * FROM cidadao WHERE email = 'X' AND ativo = true`. Se voltar vazio, ele tenta fazer `SELECT * FROM servidor WHERE email = 'X' AND ativo = true`.

## 2. Como e onde é tratado se os dados de acesso estiverem errados?

> **Arquivo:** `backend/portal/views_auth.py` (função `login_view`)

Se a variável `user` continuar sendo `None` ao final do `try/except`, quer dizer que não achou no banco. Se achou, precisamos verificar se a senha está certa batendo ela contra o "Hash" criptografado.

```python
if user is None:
    # A conta simplesmente não existe
    messages.error(request, "E-mail ou senha incorretos.")
elif check_password(senha, user.senha_hash):
    # Dá certo e libera acesso, veja resposta 3 abaixo...
else:
    # A conta existe, mas a senha falhou
    messages.error(request, "E-mail ou senha incorretos.")
```
> **Por segurança:** Nunca retornamos erros diferenciais como "Email não encontrado" ou "Senha incorreta". Em ambos os casos a resposta falha de forma genérica para blindar as contas.

## 3. Quando o login deu certo, o que o sistema memoriza?

> **Arquivo:** `backend/portal/views_auth.py` (função `login_view`)

Se o usuário é achado e `check_password(senha, user.senha_hash)` retornou verdadeiro, ocorre a gravação no banco de sessões do Django (armazenamento back-end):

```python
elif check_password(senha, user.senha_hash):
    # Sistema memoriza a ID local e se a conta é Cidadão ou Servidor
    request.session["usuario_id"] = user.pk
    request.session["usuario_tipo"] = tipo
    
    if (user.senha_temporaria or "").strip():
        # Verificação do 1º acesso
        request.session["forcar_troca_senha"] = True
        return redirect("portal:troca_senha_obrigatoria")
        
    messages.success(request, f"Olá, {user.nome_completo}.")
    return redirect("portal:root")
```

## 4. Onde ocorre a separação de telas de acordo com o perfil?

A divisão do código por perfil (CID, COL, GES) acontece interceptando acessos em três camadas:

1. **Camada de Rotas (Views)**: Ocorre no arquivo `backend/portal/decorators.py` com o uso das funções `@perfis`. Antes de carregar uma página (`views_gestao.py` por exemplo), ele exige `@perfis("GES")`. Se um cidadão (CID) tentar contornar navegando pela aba da URL, a tela o barra e redireciona de volta mandando erro.
2. **Camada de Botões Visual (Templates HTML)**: O modelo base `backend/templates/portal/base.html` verifica `{% if nav_perfil == "GES" %}` para mostrar o link da administração do menu ou mostrar tela do "Cidadão".
3. **Camada de Segurança do Banco (PostgreSQL)**: Todas as "Rules e Triggers" no SQL dependem do nível de acesso. Exemplo, a Rule R4 verifica se `current_setting('portal.perfil')` é 'COL' ou 'GES' para deixar um chamado ser atualizado para Concluído. 

---

# Mais Perguntas Técnicas Similares

## 5. Como as senhas são criptografadas antes de ir para o banco?
> **Arquivos:** `views_auth.py` e `views_gestao.py` 

O armazenamento de senhas cruas (ex: "123456") é quebrado com a função `make_password()` nativa do pacote de hashes do Django.
No momento do cadastro (`views_auth.py`) ou da criação de um Colaborador pela gestão (`gestao_colaborador_toggle` no `views_gestao.py`), acontece:
`u.senha_hash = make_password(form.cleaned_data["senha"])`
No BD caem *hashes* parecidos com: `pbkdf2_sha256$260000$....`. 

## 6. Como o sistema identifica o usuário a cada vez que ele troca de página?
> **Arquivo:** `backend/portal/middleware.py`

Quando o usuário efetua login, ganha apenas a sessão salva (visto na pergunta 3). Cada vez que ele acessa uma rota como `/cidadao/chamados`, o `PortalUserMiddleware` é acionado **antes de mostrar a tela (Request)**. Ele executa a rotina nativa `_usuario_da_sessao` que puxa toda a ficha baseada em sua ID em background. Isso é convertido na variável `request.portal_user` disponibilizando informações para toda a regra Python. 

## 7. Como as Rules/Triggers do banco sabem que eu sou Gestor ou um Cidadão se estão fora do Django?
> **Arquivo:** `backend/portal/middleware.py`

Toda vez que a `request` do usuário é recebida, o mesmo middleware que faz a conexão entre usuário e a tela também é programado para criar uma **conversa oculta entre o App e o PostgreSQL**:
```python
def _postgres_sessao(perfil, id_acao):
    with connection.cursor() as c:
        c.execute("SELECT set_config('portal.perfil', %s, true)", [perfil])
        c.execute("SELECT set_config('portal.id_usuario_acao', %s, true)", [id_acao])
```
É isso que torna inteligente as Triggers de Integridade que verificam se ele está burlando a página ou acessando a tela pelo `pgAdmin` em nome dele.

## 8. Como a cor do semáforo do prazo é feita? 
> **Arquivo:** `backend/portal/utils.py` com o painel chamando em `views_equipe.py`

Criou-se a função reutilizável `cor_semaforo(chamado)`:
```python
def cor_semaforo(chamado):
    s = chamado.id_servico
    dias = (timezone.now() - chamado.dt_abertura).days
    
    if dias >= s.prazo_vermelho_dias: return "vermelho"
    if dias >= s.prazo_amarelo_dias: return "amarelo"
    return "verde"
```
Isso varre dinamicamente a data exata daquele minuto subtraindo pela data de abertura que o usuário anexou, tudo sem salvar essas contagens pesadas diretamente no BD. Isso é renderizado na tela mandando as variáveis ao template HTML.

## 9. O que ocorre se um usuário for muito esperto e alterar via DevTools para "concluir chamado" em que só equipe visualiza?
> **Arquivos:** `views_cidadao.py` além do BD (Triggers/Rules)

O backend ignora o que não é submetido das Views para o qual foi programado. Além disso:
- Toda e qualquer visualização submete as informações a testes, validando que status a ação pretende atingir.
- Em *Último Recurso*, se ele por exemplo burlasse via POST para colocar observação no chamado já concluído, o TRIGGER 2 (Integridade DB) iria parar o INSERT emitindo a exceção severa: `RAISE EXCEPTION: Chamado encerrado (CO/CA): não é permitido adicionar fotos.` e reverteria as transações automaticamente.
