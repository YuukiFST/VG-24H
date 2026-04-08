# Roteiro de Apresentação — Bruno Dias

## 🎯 Responsabilidade: Autenticação, Módulo do Cidadão e Página Inicial

Bruno é responsável por toda a **experiência do cidadão** no portal: desde o cadastro e login até a abertura, acompanhamento e avaliação de chamados, além da página inicial pública.

---

## 📌 O que você apresenta

### 1. Sistema de Autenticação (Plano §3.1 — Autenticação)

> A autenticação é **dual**: o sistema busca primeiro na tabela `cidadao`, depois na tabela `servidor`. A variável de sessão `usuario_tipo` guarda se é `"cidadao"` ou `"servidor"`.

- **Login** — função `login_view` em `views_auth.py`:
  - Recebe e-mail e senha
  - Busca em `Cidadao` (se não encontra, busca em `Servidor`)
  - Compara senha via `check_password` (Django) contra `senha_hash`
  - Se `senha_temporaria` está preenchida → redireciona para troca obrigatória
  - Grava na sessão: `usuario_id`, `usuario_tipo`

- **Cadastro** — função `cadastro_view` em `views_auth.py`:
  - Usa o formulário `CadastroCidadaoForm` (wizard de 3 etapas no template)
  - Valida CPF e e-mail únicos na tabela `cidadao`
  - Cria registro com `perfil='CID'` e `senha_hash` via `make_password`
  - Campos de endereço são opcionais (rua, num_endereco, complemento, bairro, cep)

- **Recuperação de senha** — função `recuperar_senha_view`:
  - Gera token assinado com `django.core.signing` (validade 3 dias)
  - Envia link por e-mail com `send_mail`
  - Só funciona para Cidadão (busca na tabela `cidadao`)

- **Redefinição de senha** — função `redefinir_senha_view`:
  - Valida o token, localiza o cidadão e atualiza `senha_hash`

- **Troca obrigatória** — função `troca_senha_obrigatoria_view`:
  - Ativada quando `forcar_troca_senha` está na sessão
  - Atualiza `senha_hash` e limpa `senha_temporaria = None`
  - Usada no 1º acesso de Colaboradores criados pelo Gestor

- **Logout** — função `logout_view`:
  - Executa `request.session.flush()`

### 2. Templates de Autenticação

| Template | O que faz |
|---|---|
| `auth/login.html` | Formulário e-mail + senha, link "Esqueci minha senha", link para cadastro |
| `auth/cadastro.html` | Wizard 3 etapas: Dados Pessoais → Endereço → Segurança. Tem dicas de exemplo e sidebar |
| `auth/recuperar_senha.html` | Formulário com campo de e-mail |
| `auth/redefinir_senha.html` | Formulário nova senha + confirmação |
| `auth/troca_senha_obrigatoria.html` | Tela para 1º acesso de colaborador |

### 3. Módulo do Cidadão (Plano §3.1 — Módulo do Cidadão)

> Todas as views do cidadão usam o decorator `@perfis("CID")`. O **status do chamado NÃO é um campo direto** — ele vem do **último registro de `historico_chamado`** via a property `ch.status_atual` / `ch.sigla_status`.

**Siglas de status:**
- `AB` = Aberto, `EA` = Em Análise, `EE` = Em Execução, `CO` = Concluído, `CA` = Cancelado

- **Dashboard / Lista de chamados** — função `cidadao_chamados_lista` em `views_cidadao.py`:
  - Filtra `Chamado.objects.filter(id_cidadao=request.portal_user)`
  - Usa `prefetch_related("historicos__id_status")` para carregar o histórico junto
  - Filtro de status usa `Subquery` para pegar o último histórico
  - Calcula semáforo (verde/amarelo/vermelho) usando prazos do serviço
  - Renderiza `cidadao/dashboard.html`

- **Abertura de chamado** — função `cidadao_chamado_novo`:
  - Usa `ChamadoNovoForm` + `Prefetch` para categorias com serviços vinculados
  - Upload de foto via `salvar_foto_upload()` (Cloudinary ou local)
  - Gera protocolo numérico via `proximo_protocolo()` — formato `20260001`
  - **NÃO define `id_status`** no chamado — o Trigger 1 insere automaticamente em `historico_chamado` com status AB
  - Cria `Chamado` + `FotoChamado` dentro de `transaction.atomic()`

- **Detalhe do chamado** — função `cidadao_chamado_detalhe`:
  - Obtém status via `sigla_status(ch)` (que usa `ch.sigla_status` → último histórico)
  - Verifica `ch.id_cidadao_id == request.portal_user.pk` (privacidade)
  - **4 ações POST possíveis** (campo `acao`):
    - `"obs"` → insere em `historico_chamado` com `id_servidor=None` e `id_status=ch.status_atual`
    - `"foto"` → insere foto em `foto_chamado`
    - `"cancelar"` → insere em `historico_chamado` com status CA + salva `resolucao` no chamado (só se AB ou EA)
    - `"avaliar"` → salva `nota_avaliacao` + `comentario_avaliacao` + `dt_avaliacao` (só se CO e nunca avaliado)
  - Triggers no BD impedem foto/observação em chamados CO/CA (`RAISE EXCEPTION`)

- **Notificações** — função `cidadao_notificacoes`:
  - Busca notificações vinculadas aos chamados do cidadão (`arquivada=False`)
  - Permite exclusão de notificações individuais

### 4. Página Inicial (Homepage)

- **Root view** — função `root_view` em `views_root.py`:
  - Calcula `total_resolvidos` via `Subquery` no último histórico com sigla CO
  - Carrega servicos ativos (top 5), estatísticas e banners
  - Renderiza `root.html`

- **Catálogo de Serviços** — função `catalogo_servicos`:
  - Lista categorias e serviços com busca por nome
  - Renderiza `public/catalogo_servicos.html`

### 5. Formulários do Cidadão — `forms.py`

| Formulário | Campos | Onde usa |
|---|---|---|
| `CadastroCidadaoForm` | nome, cpf, nascimento, telefone, email, senha + endereço | Cadastro |
| `RecuperarSenhaForm` | email | Recuperar senha |
| `RedefinirSenhaForm` | senha + confirmação | Redefinir senha |
| `TrocaSenhaObrigatoriaForm` | senha + confirmação (herda RedefinirSenhaForm) | Troca obrigatória |
| `ChamadoNovoForm` | id_servico, id_bairro, descricao, ponto_referencia, foto | Novo chamado |
| `ObservacaoForm` | texto (máx 500) | Observação no chamado |
| `AvaliacaoForm` | nota (1-5) + comentário | Avaliação pós-conclusão |
| `CancelarChamadoForm` | motivo | Cancelamento |
| `FotoForm` | foto (ImageField) | Upload de foto |

---

## 📁 Arquivos que você DEVE saber explicar

### Python (Backend) — caminho real no projeto

| Arquivo | Caminho | Conteúdo |
|---|---|---|
| `views_auth.py` | `backend/portal/views_auth.py` | Login dual, cadastro, recuperação, troca de senha, logout |
| `views_cidadao.py` | `backend/portal/views_cidadao.py` | Dashboard, novo chamado, detalhe (obs/foto/cancelar/avaliar), notificações |
| `views_root.py` | `backend/portal/views_root.py` | Homepage + catálogo de serviços |
| `forms.py` | `backend/portal/forms.py` | Todos os formulários de validação do cidadão |
| `urls.py` | `backend/portal/urls.py` | Suas rotas: `accounts/*`, `cidadao/*`, raiz (`""`, `servicos/`) |

### Templates (Frontend) — caminho real no projeto

| Arquivo | Caminho |
|---|---|
| `login.html` | `backend/templates/portal/auth/login.html` |
| `cadastro.html` | `backend/templates/portal/auth/cadastro.html` |
| `recuperar_senha.html` | `backend/templates/portal/auth/recuperar_senha.html` |
| `redefinir_senha.html` | `backend/templates/portal/auth/redefinir_senha.html` |
| `troca_senha_obrigatoria.html` | `backend/templates/portal/auth/troca_senha_obrigatoria.html` |
| `dashboard.html` | `backend/templates/portal/cidadao/dashboard.html` |
| `novo_chamado.html` | `backend/templates/portal/cidadao/novo_chamado.html` |
| `chamados_lista.html` | `backend/templates/portal/cidadao/chamados_lista.html` |
| `chamado_detalhe.html` | `backend/templates/portal/cidadao/chamado_detalhe.html` |
| `notificacoes.html` | `backend/templates/portal/cidadao/notificacoes.html` |
| `inicio.html` | `backend/templates/portal/cidadao/inicio.html` |
| `chamado_form.html` | `backend/templates/portal/cidadao/chamado_form.html` |
| `root.html` | `backend/templates/portal/root.html` |
| `catalogo_servicos.html` | `backend/templates/portal/public/catalogo_servicos.html` |
| `landing.html` | `backend/templates/portal/public/landing.html` |

### Suas rotas em `urls.py`

| Rota | View | Name |
|---|---|---|
| `""` | `views_root.root_view` | `root` |
| `servicos/` | `views_root.catalogo_servicos` | `catalogo_servicos` |
| `accounts/login/` | `views_auth.login_view` | `login` |
| `accounts/logout/` | `views_auth.logout_view` | `logout` |
| `accounts/cadastro/` | `views_auth.cadastro_view` | `cadastro` |
| `accounts/recuperar-senha/` | `views_auth.recuperar_senha_view` | `recuperar_senha` |
| `accounts/redefinir-senha/<token>/` | `views_auth.redefinir_senha_view` | `redefinir_senha` |
| `accounts/trocar-senha/` | `views_auth.troca_senha_obrigatoria_view` | `troca_senha_obrigatoria` |
| `cidadao/chamados/` | `views_cidadao.cidadao_chamados_lista` | `cidadao_chamados` |
| `cidadao/chamados/novo/` | `views_cidadao.cidadao_chamado_novo` | `cidadao_chamado_novo` |
| `cidadao/chamados/<pk>/` | `views_cidadao.cidadao_chamado_detalhe` | `cidadao_chamado` |
| `cidadao/notificacoes/` | `views_cidadao.cidadao_notificacoes` | `cidadao_notificacoes` |

---

## 🗣️ Pontos-chave para a apresentação

1. **Explique a autenticação dual**: busca em `Cidadao` → `Servidor`, sessão guarda `usuario_tipo`
2. **Explique que o status NÃO está no chamado**: vem do último `historico_chamado` via property `status_atual`
3. **Faça o fluxo ao vivo**: Cadastro → Login → Abrir chamado → Ver protocolo → Acompanhar → Avaliar
4. **Mostre o wizard de cadastro** (3 passos)
5. **Abra um chamado**: categoria → serviço → bairro → descrição → foto
6. **Mostre o protocolo** gerado e explique `proximo_protocolo()` em `utils.py`
7. **Tente cancelar** um chamado em EE → sistema impede na view
8. **Tente adicionar observação** em chamado CO → trigger `RAISE EXCEPTION`
9. **Avalie um chamado** CO, depois tente alterar → trigger `trg_avaliacao_imutavel` impede
10. **Mostre notificações** geradas automaticamente pelo Trigger 2B

---

## 📚 Mapeamento por Etapa da Disciplina

| Etapa | O que Bruno apresenta |
|---|---|
| **Etapa 1** (Plano de Trabalho) | Seções 1, 2 e 3 — O que fazer, justificativa, funcionalidades do Cidadão |
| **Etapa 2** (Modelagem + Criação BD) | Entidades `cidadao`, `chamado`, `foto_chamado`, `notificacao` |
| **Etapa 3** (Layout das telas) | Print: Login, Homepage, Cadastro (wizard), Dashboard Cidadão, Abertura de Chamado |
| **Etapa 4** (Conexão + Login) | Login (`login.html` + `views_auth.py`) funcionando |
| **Etapa 5** (Cadastro piloto) | Cadastro de Cidadão: INSERT, SELECT, UPDATE, DELETE lógico (`ativo=False`) |
| **Etapa 6** (Demais telas) | Todas as telas listadas abaixo |

### ⚠️ Ponto Crítico — Etapa 6

> **Telas desenvolvidas por Bruno Dias:**
>
> 1. Login (`auth/login.html`)
> 2. Cadastro (`auth/cadastro.html`) — wizard 3 etapas
> 3. Recuperação de Senha (`auth/recuperar_senha.html` + `auth/redefinir_senha.html`)
> 4. Dashboard Cidadão (`cidadao/dashboard.html`)
> 5. Abertura de Chamado (`cidadao/novo_chamado.html`)
> 6. Lista de Chamados (`cidadao/chamados_lista.html`)
> 7. Detalhe do Chamado (`cidadao/chamado_detalhe.html`)
> 8. Notificações (`cidadao/notificacoes.html`)
> 9. Homepage (`root.html`)
> 10. Catálogo de Serviços (`public/catalogo_servicos.html`)

### 📄 Checklist para o Seminário Final

- [ ] Print do `views_auth.py` — login dual e cadastro
- [ ] Print do `views_cidadao.py` — dashboard, novo chamado, detalhe
- [ ] Print do cadastro com wizard (3 passos)
- [ ] Print do dashboard com semáforo
- [ ] Print da abertura de chamado com upload de foto
- [ ] Print do detalhe com histórico + avaliação
- [ ] Print das notificações
- [ ] Demonstração ao vivo do fluxo completo
