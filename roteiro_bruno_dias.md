# Roteiro de Apresentação — Bruno Dias

## 🎯 Responsabilidade: Autenticação, Módulo do Cidadão e Página Inicial

Bruno é responsável por toda a **experiência do cidadão** no portal: desde o cadastro e login até a abertura, acompanhamento e avaliação de chamados.

---

## 📌 O que você apresenta

### 1. Sistema de Autenticação (Plano §3.1 — Autenticação)

- **Login** (`views_auth.py` → `login_view`): autenticação dual — identifica automaticamente se é cidadão ou servidor pelo e-mail
- **Cadastro** (`views_auth.py` → `cadastro_view`): registro de cidadão com validação de CPF e e-mail únicos
- **Recuperação de senha** (`views_auth.py` → `recuperar_senha_view`): fluxo de envio de token por e-mail
- **Troca obrigatória** (`views_auth.py` → `troca_senha_obrigatoria_view`): força colaboradores a trocar senha temporária no 1º acesso
- **Logout**: encerramento da sessão

### 2. Templates de Autenticação

- **Login** (`login.html`): formulário com e-mail/senha, botão de "Esqueci minha senha" e link para cadastro
- **Cadastro** (`cadastro.html`): wizard de 3 etapas (Dados Pessoais, Endereço, Segurança) com:
  - Dicas de exemplo abaixo de cada campo (Ex: Maria da Silva Oliveira)
  - Sidebar "Informações Importantes" com campos obrigatórios e opcionais
- **Recuperar senha** (`recuperar_senha.html`): formulário de e-mail
- **Redefinir senha** (`redefinir_senha.html`): formulário com nova senha + confirmação
- **Troca obrigatória** (`troca_senha_obrigatoria.html`): tela para 1º acesso de colaborador

### 3. Módulo do Cidadão (Plano §3.1 — Módulo do Cidadão)

- **Dashboard do Cidadão** (`views_cidadao.py` → `cidadao_dashboard`): painel com resumo de chamados por status
- **Abertura de chamado** (`views_cidadao.py` → `cidadao_chamado_novo`): formulário com seleção de categoria, serviço, bairro, descrição (máx 500), upload de foto obrigatório
- **Lista de chamados** (`views_cidadao.py` → `cidadao_chamados`): todos os chamados do cidadão logado
- **Detalhe do chamado** (`views_cidadao.py` → `cidadao_chamado_detalhe`): histórico de status, fotos, avaliação
- **Cancelamento** de chamado: permitido apenas nos status AB e AN
- **Avaliação** do chamado: nota (1-5) + comentário, somente após conclusão, preenchida uma única vez
- **Notificações** (`views_cidadao.py` → `cidadao_notificacoes`): listagem e exclusão de notificações

### 4. Página Inicial (Homepage)

- **Root view** (`views_root.py`): carrega banners e serviços para a homepage
- **Template** (`root.html`): carousel de banners, quick actions, cards de serviço, "Como funciona", estatísticas
- **Formulários** (`forms.py`): classes de formulário Django para validação de dados do cidadão

### 5. Rotas do Cidadão

- Explicar as rotas em `urls.py` referentes às funcionalidades do cidadão e autenticação

---

## 📁 Arquivos que você deve saber explicar

### Python (Backend)

| Arquivo                                                                                           | Conteúdo                                                                              |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [views_auth.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/views_auth.py)       | Login, cadastro, recuperação de senha, logout                                         |
| [views_cidadao.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/views_cidadao.py) | Dashboard, abertura de chamado, lista, detalhe, avaliação, cancelamento, notificações |
| [views_root.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/views_root.py)       | Página inicial — carrega banners e serviços                                           |
| [forms.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/forms.py)                 | Formulários Django para validação                                                     |
| [urls.py](file:///e:/Projects/PersonalProjects/VG_Smart/backend/portal/urls.py)                   | Rotas de autenticação e cidadão (sua metade)                                          |

### Templates (Frontend)

| Arquivo                                                                                                                                  | Conteúdo                                    |
| ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| [login.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/auth/login.html)                                     | Tela de login                               |
| [cadastro.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/auth/cadastro.html)                               | Wizard de cadastro com hints e sidebar      |
| [recuperar_senha.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/auth/recuperar_senha.html)                 | Tela de recuperação de senha                |
| [redefinir_senha.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/auth/redefinir_senha.html)                 | Tela de redefinição de senha                |
| [troca_senha_obrigatoria.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/auth/troca_senha_obrigatoria.html) | Troca obrigatória no 1º acesso              |
| [dashboard.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/cidadao/dashboard.html)                          | Painel do cidadão com resumo                |
| [novo_chamado.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/cidadao/novo_chamado.html)                    | Formulário de abertura de chamado           |
| [chamados_lista.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/cidadao/chamados_lista.html)                | Lista de chamados do cidadão                |
| [chamado_detalhe.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/cidadao/chamado_detalhe.html)              | Detalhes do chamado + histórico + avaliação |
| [notificacoes.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/cidadao/notificacoes.html)                    | Listagem de notificações                    |
| [root.html](file:///e:/Projects/PersonalProjects/VG_Smart/backend/templates/portal/root.html)                                            | Homepage (carousel, serviços, estatísticas) |

---

## 🗣️ Pontos-chave para a apresentação

1. **Faça o fluxo completo ao vivo**: Cadastro → Login → Abrir chamado → Ver protocolo → Acompanhar → Receber notificação → Avaliar
2. **Mostre o wizard de cadastro** com os 3 passos e destaque os hints de exemplo e a sidebar de campos obrigatórios
3. **Abra um chamado** mostrando: seleção de categoria → serviço → bairro → descrição → upload de foto
4. **Mostre o protocolo** gerado (formato 20260001) e explique como é construído
5. **Tente cancelar** um chamado em status EX para mostrar que o sistema impede
6. **Avalie um chamado** concluído e mostre que não permite editar depois
7. **Mostre as notificações** chegando automaticamente quando o status é alterado

---

## 📚 Mapeamento por Etapa da Disciplina

A professora avalia o projeto por etapas. Abaixo está o que você é responsável em cada uma:

| Etapa                                            | O que Bruno apresenta                                                                                                                                                                         |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Etapa 1** (Plano de Trabalho)                  | Seções 1, 2 e 3 — O que fazer, justificativa e funcionalidades do Cidadão                                                                                                                     |
| **Etapa 2** (Modelagem + Criação BD)             | Entidades `cidadao`, `chamado`, `foto_chamado`, `notificacao` — explicar campos e constraints                                                                                                 |
| **Etapa 3** (Layout das telas)                   | Print do layout das telas: Login, Homepage, Cadastro (wizard com 3 etapas), Dashboard do Cidadão, Abertura de Chamado                                                                         |
| **Etapa 4** (Conexão + Login)                    | Tela de Login (`login.html` + `views_auth.py`) em execução — print do código e da tela funcionando                                                                                            |
| **Etapa 5** (Cadastro piloto + Recurso avançado) | Cadastro de Cidadão como tela piloto — demonstrar as 4 operações (INSERT no cadastro, SELECT na listagem, UPDATE no perfil, DELETE lógico)                                                    |
| **Etapa 6** (Demais telas)                       | **Telas que Bruno desenvolveu:** Login, Cadastro, Recuperação de Senha, Dashboard Cidadão, Abertura de Chamado, Lista de Chamados, Detalhe do Chamado (com avaliação), Notificações, Homepage |

### ⚠️ Ponto Crítico — Etapa 6

A professora exige que **cada aluno relate quais telas foram eleitas para desenvolvimento**. Bruno deve listar:

> **Telas desenvolvidas por Bruno Dias:**
>
> 1. Tela de Login (`login.html`)
> 2. Tela de Cadastro do Cidadão (`cadastro.html`) — wizard de 3 etapas
> 3. Tela de Recuperação de Senha (`recuperar_senha.html` + `redefinir_senha.html`)
> 4. Dashboard do Cidadão (`dashboard.html`) — resumo por status
> 5. Tela de Abertura de Chamado (`novo_chamado.html`) — com upload de foto
> 6. Lista de Chamados do Cidadão (`chamados_lista.html`)
> 7. Detalhe do Chamado (`chamado_detalhe.html`) — histórico + avaliação
> 8. Notificações (`notificacoes.html`)
> 9. Página Inicial / Homepage (`root.html`)

### 📄 Checklist para o Seminário Final

- [ ] Print do código `views_auth.py` — funções de login e cadastro
- [ ] Print do código `views_cidadao.py` — dashboard, abertura e detalhe de chamado
- [ ] Print da tela de Login em execução
- [ ] Print do Cadastro em execução (mostrando os 3 passos do wizard)
- [ ] Print do Dashboard do Cidadão com os cards de status
- [ ] Print da abertura de chamado com seleção de categoria → serviço → bairro → foto
- [ ] Print do detalhe do chamado com histórico de status
- [ ] Print da avaliação do chamado (nota + comentário)
- [ ] Print das notificações recebidas automaticamente
- [ ] Demonstração ao vivo do fluxo completo: Cadastro → Login → Abrir chamado → Acompanhar → Avaliar
