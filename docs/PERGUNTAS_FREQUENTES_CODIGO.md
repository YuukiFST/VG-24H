# FAQ de Código e Arquitetura — Portal VG 24H

Este documento reúne perguntas frequentes sobre "Onde acontece tal coisa no código?" para orientar a apresentação e facilitar o entendimento lógico de como as requisições se comunicam com o banco de dados.

---

## 1. Onde é feita a busca (SELECT) no banco de dados para o login?

> **Arquivo:** `backend/portal/views_auth.py` (função `login_view`)

Quando o usuário digita e-mail e senha e clica em "Entrar", os dados são enviados para a `login_view`. Para atender a exigência da disciplina, o sistema utiliza **SQL puro** (via `connection.cursor()`) em todas as operações de banco de dados. Como existem as tabelas separadas `Cidadao` e `Servidor`, ocorre uma **busca dual**:

```python
with connection.cursor() as cursor:
    # SELECT na tabela 'cidadao' — busca pelo email informado
    cursor.execute(
        "SELECT id_cidadao, nome_completo, senha_hash, perfil, senha_temporaria "
        "FROM cidadao "
        "WHERE LOWER(email) = %s AND ativo = TRUE",
        [email],
    )
    row = cursor.fetchone()
    # Se não encontrar, faz um SELECT na tabela 'servidor'...
```
*Exatamente como escrito no código:* A consulta é feita usando `SELECT` explícito para a tabela `cidadao`. Se não retornar nada, uma nova consulta `SELECT` é feita na tabela `servidor`.

---

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

---

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

---

## 4. Onde ocorre a separação de telas de acordo com o perfil?

A divisão do código por perfil (CID, COL, GES) acontece interceptando acessos em três camadas:

1. **Camada de Rotas (Views)**: Ocorre no arquivo `backend/portal/decorators.py` com o uso das funções `@perfis`. Antes de carregar uma página (`views_gestao.py` por exemplo), ele exige `@perfis("GES")`. Se um cidadão (CID) tentar contornar navegando pela aba da URL, a tela o barra e redireciona de volta mandando erro.
2. **Camada de Botões Visual (Templates HTML)**: O modelo base `backend/templates/portal/base.html` verifica `{% if nav_perfil == "GES" %}` para mostrar o link da administração do menu ou mostrar tela do "Cidadão".
3. **Camada de Segurança do Banco (PostgreSQL)**: As Triggers de integridade no SQL dependem do nível de acesso. Exemplo, a Trigger de Rule 1 verifica se o chamado está encerrado antes de deixar adicionar fotos, protegendo mesmo se alguém burlar a interface.

---

# Mais Perguntas Técnicas Similares

## 5. Como as senhas são criptografadas antes de ir para o banco?

> **Arquivos:** `views_auth.py` e `views_gestao.py`

O armazenamento de senhas cruas (ex: "123456") é quebrado com a função `make_password()` nativa do pacote de hashes do Django.
No momento do cadastro (`views_auth.py`) ou da criação de um Colaborador pela gestão (`gestao_colaboradores` no `views_gestao.py`), acontece:

```python
# views_auth.py — cadastro de cidadão
senha_hash=make_password(d["senha"])

# views_gestao.py — criação de colaborador
senha_hash=make_password(d["senha_provisoria"])
```

No BD caem *hashes* parecidos com: `pbkdf2_sha256$720000$....`. A senha real **nunca** é gravada.

---

## 6. Como o sistema identifica o usuário a cada vez que ele troca de página?

> **Arquivo:** `backend/portal/middleware.py`

Quando o usuário efetua login, ganha apenas a sessão salva (visto na pergunta 3). Cada vez que ele acessa uma rota como `/cidadao/chamados`, o `PortalUserMiddleware` é acionado **antes de mostrar a tela (Request)**. Ele executa a rotina `_usuario_da_sessao` que puxa toda a ficha baseada em sua ID em background.

```python
def _usuario_da_sessao(request):
    uid = request.session.get("usuario_id")       # ID salvo no login
    tipo = request.session.get("usuario_tipo")     # 'cidadao' ou 'servidor'
    if not uid or not tipo:
        return None  # não está logado
    if tipo == "servidor":
        # SQL: SELECT * FROM servidor WHERE id_servidor = uid AND ativo = true
        with connection.cursor() as cursor:
            cursor.execute("SELECT ... FROM servidor WHERE id_servidor = %s AND ativo = TRUE", [uid])
            # ... monta e retorna o objeto Servidor
    else:
        # SQL: SELECT * FROM cidadao WHERE id_cidadao = uid AND ativo = true
        with connection.cursor() as cursor:
            cursor.execute("SELECT ... FROM cidadao WHERE id_cidadao = %s AND ativo = TRUE", [uid])
            # ... monta e retorna o objeto Cidadao
```

Isso é convertido na variável `request.portal_user` disponibilizando informações para toda a regra Python.

---

## 7. Como as Triggers do banco sabem que eu sou Gestor ou Cidadão, se estão fora do Django?

> **Arquivo:** `backend/portal/middleware.py`

Toda vez que a `request` do usuário é recebida, o mesmo middleware que faz a conexão entre usuário e a tela também é programado para criar uma **conversa oculta entre o App e o PostgreSQL**:

```python
def _postgres_sessao(perfil, id_acao):
    with connection.cursor() as c:
        c.execute("SELECT set_config('portal.perfil', %s, true)", [perfil])
        c.execute("SELECT set_config('portal.id_usuario_acao', %s, true)", [id_acao])
```

É isso que torna inteligente as Triggers de Integridade que verificam se ele está burlando a página ou acessando o banco diretamente.

---

## 8. Como a cor do semáforo do prazo é calculada?

> **Arquivo:** `backend/portal/models.py` (propriedade `cor_semaforo` na classe `Chamado`)

Criou-se a propriedade reutilizável `cor_semaforo` dentro do model `Chamado`:

```python
@property
def cor_semaforo(self):
    s = self.id_servico                          # Faz JOIN com tabela servico
    dias = (timezone.now() - self.dt_abertura).days
    if dias >= s.prazo_vermelho_dias: return "vermelho"
    if dias >= s.prazo_amarelo_dias:  return "amarelo"
    return "verde"
```

Isso varre dinamicamente a data exata daquele minuto subtraindo pela data de abertura, tudo sem salvar essas contagens no BD. A view `equipe_chamados_lista` em `views_equipe.py` chama `ch.cor_semaforo` e passa para o template HTML.

---

## 9. O que ocorre se um usuário alterar via DevTools para "concluir chamado" em que só a equipe visualiza?

> **Arquivos:** `views_cidadao.py` + banco (Triggers)

O backend ignora o que não é submetido das Views para o qual foi programado. Além disso:

- O `@perfis("CID")` no decorador rejeita qualquer acesso direto a rotas da equipe.
- Na view `cidadao_chamado_detalhe`, antes de processar qualquer POST, o código verifica: `pode_obs_foto = ts not in ("CO", "CA")` e `pode_cancelar = ts in ("AB", "EA")`. Se a condição falha, a ação é simplesmente ignorada.
- Em **último recurso**, se ele burlasse via POST para adicionar foto em chamado concluído, a Trigger no banco (`fn_rule_foto_chamado_encerrado` no `04_rules.sql`) iria parar o INSERT: `RAISE EXCEPTION: 'Chamado encerrado (CO/CA): não é permitido adicionar fotos.'` e reverteria as transações automaticamente.

---

## 10. O que são os Triggers do banco e quais existem no projeto?

> **Arquivo:** `database/03_functions_triggers.sql` e `database/04_rules.sql`

Triggers são funções que o PostgreSQL executa **automaticamente** quando ocorre INSERT, UPDATE ou DELETE em uma tabela. No projeto existem:

| Trigger | Tabela | Evento | O que faz |
|---|---|---|---|
| `trg_chamado_after_insert_historico_ab` | `chamado` | AFTER INSERT | Insere o 1º histórico com status "AB" (Aberto) automaticamente |
| `trg_chamado_before_update_metadados` | `chamado` | BEFORE UPDATE | Atualiza o campo `atualizado_em` com a data/hora atual |
| `trg_historico_after_insert_status` | `historico_chamado` | AFTER INSERT | Atualiza `dt_conclusao` no chamado + cria notificação |
| `trg_foto_chamado_encerrado` | `foto_chamado` | BEFORE INSERT | Bloqueia foto se chamado está CO/CA |
| `trg_historico_obs_encerrado` | `historico_chamado` | BEFORE INSERT | Bloqueia observação se chamado está CO/CA |
| `trg_avaliacao_imutavel` | `chamado` | BEFORE UPDATE | Impede alterar avaliação já registrada |

**Exemplo prático:** Quando o cidadão abre um chamado (INSERT INTO chamado), o Trigger 1 automaticamente insere `INSERT INTO historico_chamado (..., sigla='AB')` — o desenvolvedor não precisa fazer isso manualmente no Python.

---

## 11. O que são as Rules do banco e qual a diferença para Triggers?

> **Arquivo:** `database/04_rules.sql`

Rules são regras que o PostgreSQL aplica para **reescrever** comandos SQL antes de executá-los. A diferença prática:
- **Trigger** = executa uma função antes/depois do evento (pode fazer lógica complexa)
- **Rule** = substitui o comando inteiro (ex: transforma DELETE em "faça nada")

No projeto existem 3 Rules ativas:

```sql
-- Impede UPDATE no histórico (preserva o registro original)
CREATE RULE r05_historico_sem_update AS ON UPDATE TO historico_chamado
DO INSTEAD NOTHING;

-- Impede DELETE no histórico (nunca se apaga um histórico)
CREATE RULE r05_historico_sem_delete AS ON DELETE TO historico_chamado
DO INSTEAD NOTHING;

-- Impede DELETE em chamado (integridade referencial)
CREATE RULE rx_chamado_sem_delete AS ON DELETE TO chamado
DO INSTEAD NOTHING;
```

**Na prática:** Se alguém acessar o pgAdmin e tentar `DELETE FROM historico_chamado WHERE id = 5`, o PostgreSQL simplesmente ignora o comando e não apaga nada.

---

## 12. O que é a View SQL `vw_estatisticas_chamados` e onde ela é usada?

> **Arquivos:** `database/05_views.sql` + `backend/portal/views_gestao.py`

Uma View SQL é uma "tabela virtual" — ela não armazena dados, apenas salva uma consulta complexa com um nome amigável. No projeto:

```sql
CREATE VIEW vw_estatisticas_chamados AS
SELECT
    cat.nome AS categoria,  b.nome_bairro AS bairro,
    s.sigla  AS sigla_status, COUNT(*)::BIGINT AS total_chamados
FROM chamado ch
JOIN servico srv ON srv.id_servico = ch.id_servico
JOIN categoria_servico cat ON cat.id_categoria = srv.id_categoria
JOIN bairro b ON b.id_bairro = ch.id_bairro
JOIN LATERAL (...) -- pega o último status de cada chamado
GROUP BY cat.nome, b.nome_bairro, s.sigla, s.descricao;
```

No Python (`views_gestao.py`), a consulta é feita com SQL direto:
```python
c.execute("SELECT * FROM vw_estatisticas_chamados ORDER BY categoria, bairro")
```

O gestor vê esses dados na tela `/gestao/estatisticas/`.

---

## 13. Como é gerado o número de protocolo de um chamado?

> **Arquivo:** `backend/portal/utils.py` (função `proximo_protocolo`)

O número de protocolo segue o formato `ANO + SEQUENCIAL` (ex: `2026000001`, `2026000002`):

```python
def proximo_protocolo():
    y = timezone.now().year              # Ex: 2026
    prefix = str(y)                      # "2026"
    # SQL: SELECT MAX(num_protocolo) FROM chamado WHERE num_protocolo LIKE '2026%'
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT MAX(num_protocolo) FROM chamado "
            "WHERE num_protocolo LIKE %s",
            [f"{prefix}%"]
        )
        row = cursor.fetchone()
        ultimo = row[0] if row else None
    if not ultimo:
        n = 1                            # Primeiro do ano
    else:
        n = int(ultimo[len(prefix):]) + 1  # Pega o número e soma 1
    return f"{prefix}{n:06d}"            # "2026000001"
```

**Na prática:** Se o último protocolo do ano é `2026000042`, o próximo será `2026000043`.

---

## 14. Como funciona o sistema de notificações automáticas?

> **Arquivos:** `database/03_functions_triggers.sql` (Trigger 2B) + `backend/portal/views_cidadao.py` + `backend/portal/context_processors.py`

A notificação funciona em 3 etapas:

**1. Criação automática (Trigger no banco):** Toda vez que um novo registro é inserido no `historico_chamado`, o Trigger `trg_historico_after_insert_status` cria automaticamente uma notificação:
```sql
INSERT INTO notificacao (id_chamado, mensagem)
VALUES (NEW.id_chamado, 'Chamado 2026000001: status alterado para Concluído');
```

**2. Contagem no menu (Context Processor):** O arquivo `context_processors.py` conta notificações não lidas a cada página:
```python
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT COUNT(*) FROM notificacao n "
        "WHERE n.arquivada = FALSE AND n.lida = FALSE "
        "AND n.id_chamado IN ("
        "    SELECT c.id_chamado FROM chamado c WHERE c.id_cidadao = %s"
        ")", [u.pk]
    )
    notif_count = cursor.fetchone()[0]
```

**3. Visualização (View):** O cidadão vê suas notificações em `/cidadao/notificacoes/` via `views_cidadao.py`.

---

## 15. Como o `managed = False` no models.py afeta o projeto?

> **Arquivo:** `backend/portal/models.py`

Todas as classes de modelo possuem `managed = False` no `Meta`:

```python
class Chamado(models.Model):
    class Meta:
        managed = False          # Django NÃO gerencia esta tabela
        db_table = "chamado"     # Nome exato da tabela no PostgreSQL
```

**O que isso significa:**
- O Django **NÃO** cria nem altera as tabelas automaticamente (`makemigrations`/`migrate` não tocam nelas).
- As tabelas foram criadas **manualmente** via scripts SQL da pasta `database/` (01_schema.sql → 02_seed.sql → ...).
- Nós usamos **SQL puro (`cursor.execute`)** nas views para ler e escrever dados, ignorando as facilidades de consulta do ORM do Django.

**Por que fizemos assim:** Porque a disciplina é de **Banco de Dados** — a professora exige que as tabelas, triggers e rules sejam criadas com SQL puro, não geradas automaticamente pelo framework.

---

## 16. O que é `transaction.atomic()` e onde é usado?

> **Arquivo:** `backend/portal/views_cidadao.py` (função `cidadao_chamado_novo`)

Ao abrir um novo chamado, precisamos inserir em **duas tabelas** (chamado + foto). Se a foto falhar, o chamado não pode ficar registrado sem foto. O `transaction.atomic()` garante que ambos os INSERTs funcionem ou nenhum funcione:

```python
# O código do INSERT na view faz algo como:
with connection.cursor() as cursor:
    cursor.execute(
        "INSERT INTO chamado (num_protocolo, ...) VALUES (%s, ...) RETURNING id_chamado",
        [...]
    )
    chamado_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO foto_chamado (id_chamado, url_foto, ...) VALUES (%s, %s, ...)",
        [chamado_id, url, ...]
    )
```

**Tradução SQL:** O banco garante que ambos os INSERTs funcionem ou nenhum funcione; se falhar na foto, executa `ROLLBACK`.

---

## 17. Para que servem os Índices (CREATE INDEX) no schema?

> **Arquivo:** `database/01_schema.sql`

Os índices aceleram as buscas (SELECT) em colunas muito consultadas. Sem índice, o banco lê a tabela inteira (*Full Table Scan*). Com índice, vai direto ao registro.

```sql
CREATE INDEX ix_chamado_cidadao    ON chamado (id_cidadao);
CREATE INDEX ix_chamado_bairro     ON chamado (id_bairro);
CREATE INDEX ix_chamado_servico    ON chamado (id_servico);
CREATE INDEX ix_foto_chamado       ON foto_chamado (id_chamado);
CREATE INDEX ix_historico_chamado   ON historico_chamado (id_chamado);
CREATE INDEX ix_notificacao_chamado ON notificacao (id_chamado);
```

**Exemplo prático:** Quando o cidadão acessa `/cidadao/chamados/`, o Django faz `SELECT * FROM chamado WHERE id_cidadao = 5 ORDER BY dt_abertura DESC`. Sem o índice `ix_chamado_cidadao`, o banco varreria TODOS os chamados. Com o índice, vai direto nos chamados do cidadão 5.

**Desvantagem:** Índices ocupam espaço e deixam INSERT/UPDATE um pouco mais lentos, por isso indexamos apenas as colunas de chave estrangeira (FK) mais consultadas.

---

## 18. Como é feito o JOIN para pegar os dados relacionados de um chamado?

No sistema, usamos SQL puro para trazer dados de múltiplas tabelas em uma única consulta:

```python
# views_equipe.py — Dashboard da equipe
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT c.id_chamado, c.num_protocolo, "
        "s.nome AS servico_nome, b.nome_bairro "
        "FROM chamado c "
        "JOIN servico s ON c.id_servico = s.id_servico "
        "JOIN bairro b ON c.id_bairro = b.id_bairro "
        "WHERE TRUE "
        "ORDER BY c.dt_abertura DESC"
    )
```

**Por que fazemos o JOIN manualmente?** Como usamos apenas SQL puro, em vez de fazer várias consultas separadas (`SELECT` na tabela servico e bairro para cada chamado), montamos um único `SELECT` com `JOIN` para evitar lentidão e múltiplas idas ao banco.

---

## 19. Como funciona o fluxo completo de abertura de um chamado no banco?

> **Arquivos:** `views_cidadao.py` → `03_functions_triggers.sql`

Quando o cidadão preenche o formulário e clica "Abrir Chamado", acontecem **5 operações no banco** em sequência:

1. **INSERT chamado** → `cursor.execute("INSERT INTO chamado ...")` — cria o registro principal
2. **Trigger 1 dispara** → `trg_chamado_after_insert_historico_ab` insere automaticamente `INSERT INTO historico_chamado (sigla='AB')` — primeiro histórico
3. **Trigger 2B dispara** → `trg_historico_after_insert_status` cria `INSERT INTO notificacao (mensagem='Chamado aberto')` — notifica o cidadão
4. **INSERT foto** → `cursor.execute("INSERT INTO foto_chamado ...")` — salva a foto obrigatória
5. **COMMIT** → `transaction.atomic()` confirma tudo de uma vez

Se qualquer etapa falhar, o `ROLLBACK` desfaz tudo (atomicidade).

---

## 20. Como o gestor exclui um chamado se existe Rule impedindo DELETE?

> **Arquivo:** `backend/portal/views_equipe.py` (função `gestao_chamado_excluir`)

A Rule `rx_chamado_sem_delete` impede DELETE via ORM (`chamado.delete()`). Porém, o gestor precisa poder excluir chamados. A solução é usar **SQL direto** que contorna a Rule:

```python
@perfis("GES")
def gestao_chamado_excluir(request, pk):
    # 1. Exige justificativa obrigatória
    if not justificativa:
        messages.error(request, "É obrigatório informar uma justificativa...")
    
    # 2. Grava LOG de auditoria ANTES de apagar
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO historico_chamado (id_chamado, observacao, dt_alteracao) "
            "VALUES (%s, %s, %s)",
            [pk, f"[EXCLUSÃO] Justificativa: {justificativa}", timezone.now()]
        )
    
    # 3. Apaga registros filhos primeiro, depois o chamado
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM foto_chamado WHERE id_chamado = %s", [pk])
        cursor.execute("DELETE FROM historico_chamado WHERE id_chamado = %s", [pk])
        cursor.execute("DELETE FROM notificacao WHERE id_chamado = %s", [pk])
        cursor.execute("DELETE FROM chamado WHERE id_chamado = %s", [pk])
```

**Importante:** Apaga os registros filhos (foto, histórico, notificação) **antes** do chamado pai, para respeitar as FOREIGN KEYs.
