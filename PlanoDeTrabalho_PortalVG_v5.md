**INSTITUTO FEDERAL DE MATO GROSSO**

Programação de Banco de Dados — 2026/1

Docente: Juliana Saragiotto Silva

**PROPOSTA DE PLANO DE TRABALHO**

**VG 24H**

*Developer*(s):Bruno Dias, Fausto Yuuki, Rafael Pereira 

*Product Owner*: Yuri Batista

# **1\. O que fazer?**

O projeto consiste no desenvolvimento de uma aplicação *web* para a Prefeitura de Várzea Grande, inspirada no aplicativo "Cuiabá *Smart*", porém executada exclusivamente como um portal responsivo, em conformidade com o *Design System* do Governo Federal (Gov.br).

O sistema tem como objetivo centralizar o recebimento de solicitações de serviços públicos, permitindo que o cidadão reporte problemas urbanos como buracos, falhas na iluminação pública, problemas de saneamento e acompanhar o andamento dos chamados pelo número de protocolo, sem a necessidade de instalação de aplicativos móveis.

O sistema será projetado pensando na acessibilidade e facilidade de uso para todos os públicos, incluindo pessoas idosas — por isso o número de protocolo é composto exclusivamente por números e reinicia a cada ano (ex: 20260001, 20260002...), facilitando a anotação e consulta.

O banco de dados em PostgreSQL será responsável por armazenar e integrar os dados, garantindo integridade e rastreabilidade por meio de *Triggers* e *Rules* implementados diretamente no banco.

# **2\. Justificativa**

## **2.1 Importância para a área proposta**

A digitalização dos serviços públicos é essencial para a modernização da gestão municipal. Um portal web facilita o acesso dos cidadãos, democratiza a informação e permite que a prefeitura mapeie problemas recorrentes por meio de dados estatísticos, otimizando recursos e aumentando a transparência na gestão pública.

## **2.2 Importância para o curso**

O projeto possibilita a aplicação prática dos principais conteúdos da disciplina e do curso, incluindo:

* Modelagem de dados relacional com entidades bem definidas: usuários, chamados, serviços, histórico e notificações.

* Controle de acesso por perfil de usuário, diferenciando as permissões de Cidadão, Colaborador e Administrador.

* Desenvolvimento *full-stack* com *Django* e PostgreSQL.

* Utilização de recursos avançados de banco de dados: *Triggers*, *Rules* e *Views*, previstos no plano de ensino da disciplina.

## **2.3 Justificativa pessoal**

O grupo tem como objetivo desenvolver uma solução que contribua para a modernização dos serviços municipais de Várzea Grande, atendendo à demanda por canais digitais de comunicação entre o cidadão e a administração pública. A escolha do projeto visa consolidar competências em desenvolvimento *web*, modelagem de dados e engenharia de *software*.

# **3\. Funcionalidades e Requisitos**

## **3.1 Funcionalidades principais**

**Autenticação e controle de acesso**

* Tela de *login* padronizada (Gov.br) para Cidadão, Colaborador e Administrador.

* O Cidadão faz o seu cadastro pela plataforma.

* Contas de Colaborador são criadas exclusivamente pelo Administrador.

* O Cidadão pode recuperar sua senha pela opção "Esqueci minha senha" — o sistema envia um link com *token* temporário para o e-mail cadastrado, permitindo a criação de uma nova senha.

* O Administrador pode gerar uma senha temporária para um Colaborador. No primeiro acesso com essa senha temporária, o sistema obriga o Colaborador a definir uma nova senha.

**Módulo do Cidadão**

* Abertura de chamados: seleção de categoria e serviço específico, descrição objetiva (máximo 500 caracteres), *upload* de foto obrigatório, endereço estruturado com seleção de bairro.

* O número do endereço é obrigatório — caso o local não possua número, o cidadão deve informar 0\.

* Adição de novas fotos e observações em chamados abertos (bloqueado em chamado CO ou CA).

* Cancelamento do próprio chamado, permitido apenas nos *status* AB e AN.

* Acompanhamento de chamados via protocolo numérico, com visualização do histórico de status.

* Avaliação do atendimento (nota de 1 a 5 e comentário opcional de até 500 caracteres) somente após conclusão, permitida uma única vez e não alterável.

* Visualização e exclusão de notificações recebidas na plataforma.

**Módulo do Colaborador**

* *Dashboard* (Semáforo) com listagem de todos os chamados, filtráveis por bairro, *status* e data .

* Alteração de *status* dos chamados livremente — exceto reabrir chamados CO ou CA.

* Todo encerramento (CO ou CA) exige preenchimento obrigatório do campo de resolução — descrevendo a solução aplicada ou o motivo da não solução.

* Adição de observações visíveis ao cidadão.

* Adição de fotos ao chamado como comprovação do serviço realizado.

**Módulo do Administrador**

* Todas as funcionalidades do Colaborador.

* Pode alterar o *status* de qualquer chamado, independente do *status*, incluindo CO e CA.

* Pode invalidar chamados incorretos, usando o *status* CA, com o motivo preenchido no campo de resolução.

* Gerenciamento de usuários (criação de contas de Colaborador), categorias de serviço, serviços e bairros.

* Acesso exclusivo ao painel de estatísticas consolidadas.

## **3.2 Requisitos técnicos e de banco de dados**

* Chaves primárias (*SERIAL*), estrangeiras e restrições de integridade (*NOT NULL, UNIQUE, CHECK*).

* Protocolo numérico gerado pela aplicação, reiniciando a cada ano (ex: 20260001).

* Registros inativados com campo ativo — nenhum registro é excluído do banco de dados, exceto notificações.

* Fotos armazenadas e gerenciadas pelo *Cloudinary*, com compressão e otimização automática no momento do *upload*. O custo do serviço é de responsabilidade da Prefeitura de Várzea Grande.

* Carga inicial: 2 categorias, 5 serviços, 5 *status* e bairros de Várzea Grande.

  **Categorias:** Infraestrutura e Via Pública; Mobilidade e Cidadania.

  **Serviços:** Iluminação Pública (Infraestrutura e Via Pública); Pavimentação e Vias (Infraestrutura e Via Pública); Saneamento e Drenagem (Infraestrutura e Via Pública); Trânsito e Sinalização (Mobilidade e Cidadania); Saúde e Bem-estar (Mobilidade e Cidadania).

  **tipo_status:** AB — Chamado aberto pelo cidadão; AN — Em análise pela equipe responsável; EX — Em execução no campo; CO — Serviço concluído; CA — Chamado cancelado.

## **3.3 Recursos avançados de banco de dados**

**Triggers**

* ***Trigger 1 — AFTER INSERT*** **em chamado:** insere automaticamente o primeiro registro em historico\_chamado com *status* AB, garantindo que todo chamado nasça com ao menos um histórico.

* ***Trigger 2 — AFTER UPDATE*** **em chamado:** quando o campo id\_status é alterado, executa automaticamente quatro ações:

1. Insere registro em historico\_chamado com o *status* aplicado, responsável e data.

2. Insere aviso em notificacao para o cidadão dono do chamado com mensagem gerada automaticamente.

3. Preenche dt\_conclusao caso o novo *status* seja CO.

4. Atualiza o campo atualizado\_em do chamado.

**Rules**

* ***Rule 1*** **— em foto\_chamado:** impede *INSERT* se o chamado estiver com *status* CO ou CA.

* ***Rule 2*** **— em observacao\_chamado:** impede *INSERT* se o chamado estiver com *status* CO ou CA.

* ***Rule 3*** **— em chamado:** impede *UPDATE* nos campos nota\_avaliacao e comentario\_avaliacao se já estiverem preenchidos.

* ***Rule 4*** **— em chamado:** controla as alterações de *status* permitidas por perfil. Para o perfil CID: impede qualquer alteração de *status* quando o chamado já está CO ou CA, e impede também a alteração para CA quando o chamado estiver em EX. Para o perfil COL: impede qualquer *UPDATE* de *status* em chamados CO ou CA. O perfil ADM fica isento de todas essas restrições.

* ***Rule 5*** **— em qualquer chamado:** impede *UPDATE* e *DELETE* em chamados já enviados, para todos os perfis.

* ***Rule 6*** **— em chamado:** impede *UPDATE* do *status* para CO ou CA se o campo resolução estiver *NULL* ou vazio — válida para todos os perfis.

**View**

* Consolidação de estatísticas de chamados agrupados por categoria, bairro e status — acessível exclusivamente pelo Administrador.

## **3.4 Funcionalidades futuras (caso haja tempo após a entrega do essencial)**

* Implementação de regras automáticas no banco baseadas nos campos prazo\_amarelo\_dias e prazo\_vermelho\_dias — como alertas automáticos para chamados que ultrapassaram o prazo estimado de atendimento.

# **4\. Restrições do Projeto**

| Restrição | Descrição |
| ----- | ----- |
| Linguagem e *framework* | *Backend* desenvolvido exclusivamente em *Python* com o *framework Django*. |
| Banco de dados | *PostgreSQL* obrigatório. |
| Interface visual | O *frontend* deve seguir o *Design System* Gov.br. |
| Plataforma | Sistema exclusivamente *web* e responsivo; não será desenvolvido aplicativo móvel nativo. |
| Gerenciador de ambiente | O ambiente *Python* é gerenciado com *uv*, ferramenta moderna que substitui o *pip*. |
| Armazenamento de fotos | *Cloudinary* — armazenamento, compressão e otimização automática de imagens. Custo de responsabilidade da Prefeitura de Várzea Grande. |
| Hospedagem | *Render* — plataforma de hospedagem da aplicação *web*. Custo de responsabilidade da Prefeitura de Várzea Grande. |
| Envio de e-mail | Serviço de envio de e-mail transacional para recuperação de senha do Cidadão. Custo de responsabilidade da Prefeitura de Várzea Grande. |
| Privacidade | O cidadão só visualiza os próprios chamados — consulta por protocolo exige autenticação e valida o vínculo com o usuário. |
| Integridade dos registros | Chamados, históricos e observações nunca são apagados do banco de dados. Apenas notificações podem ser excluídas pelo cidadão. |
| Foco inicial | Desenvolvimento do fluxo básico (cadastro → chamado → acompanhamento) antes dos recursos avançados. |

# 

# **5\. Modelo de Dados**

## **5.1 Entidades e Atributos**

**Entidade 1: usuario**

*Armazena os dados de cidadãos, colaboradores e administradores. O campo perfil diferencia os tipos: CID (Cidadão), COL (Colaborador) e ADM (Administrador).*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_usuario | PK, SERIAL | Identificador único do usuário |
| nome\_completo | VARCHAR(200), NOT NULL | Nome completo do usuário |
| cpf | VARCHAR(14), UNIQUE, NOT NULL | CPF do usuário, único no sistema |
| dt\_nascimento | DATE, NOT NULL | Data de nascimento, usada para fins estatísticos e serviços futuros |
| telefone | VARCHAR(20), NOT NULL | Telefone de contato |
| email | VARCHAR(255), UNIQUE, NOT NULL | E-mail de acesso e recuperação de senha |
| senha\_hash | VARCHAR(255), NOT NULL | Senha armazenada em formato criptografado |
| senha\_temporaria | VARCHAR(255), NULL | Senha temporária gerada pelo Admin para Colaborador; NULL indica que não há senha temporária ativa |
| perfil | CHAR(3), NOT NULL, CHECK IN ('CID', 'COL', 'ADM') | Tipo de acesso: CID (Cidadão), COL (Colaborador), ADM (Administrador) |
| rua | VARCHAR(200), NULL | Rua do endereço residencial do usuário |
| numero\_endereco | VARCHAR(10), NULL | Número do endereço residencial |
| complemento\_endereco | VARCHAR(200), NULL | Complemento do endereço residencial |
| bairro\_endereco | VARCHAR(200), NULL | Bairro do endereço residencial |
| cep\_endereco | CHAR(8), NULL | CEP do endereço residencial |
| ativo | BOOLEAN, DEFAULT TRUE | Indica se o usuário está ativo; registros nunca são excluídos |
| dt\_cadastro | TIMESTAMP, DEFAULT CURRENT\_TIMESTAMP | Data e hora do cadastro |

**Entidade 2: status\_chamado**

*Tabela de domínio com os status possíveis de um chamado. Siglas: AB (Aberto), AN (Em Análise), EX (Em Execução), CO (Concluído), CA (Cancelado).*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_status | PK, SERIAL | Identificador único do status |
| tipo\_status | CHAR(2), NOT NULL, UNIQUE | Sigla do status: AB, AN, EX, CO ou CA |
| descricao | VARCHAR(200) | Descrição legível do status |

**Valores iniciais:**

| tipo\_status | descricao |
| ----- | ----- |
| AB | Chamado aberto pelo cidadão |
| AN | Em análise pela equipe responsável |
| EX | Em execução no campo |
| CO | Serviço concluído |
| CA | Chamado cancelado |

**Entidade 3: categoria\_servico**

*Agrupa os tipos de serviços oferecidos pela prefeitura.*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_categoria | PK, SERIAL | Identificador único da categoria |
| nome | VARCHAR(200), NOT NULL, UNIQUE | Nome da categoria |
| descricao | VARCHAR(200) | Descrição da categoria |
| ativo | BOOLEAN, DEFAULT TRUE | Indica se a categoria está ativa; registros nunca são excluídos |

**Valores iniciais:**

| nome | descricao |
| ----- | ----- |
| Infraestrutura e Via Pública | Problemas que afetam a locomoção e segurança imediata. |
| Mobilidade e Cidadania | Serviços de organização, saúde e segurança. |

**Entidade 4: servico**

*Detalha cada serviço específico dentro de uma categoria.*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_servico | PK, SERIAL | Identificador único do serviço |
| nome | VARCHAR(200), NOT NULL | Nome do serviço |
| descricao | VARCHAR(200) | Descrição do serviço |
| prazo\_amarelo\_dias | INTEGER, NOT NULL, DEFAULT 15 | Número de dias sem resolução para o semáforo indicar amarelo; alterável apenas por ateste do Secretário Municipal |
| prazo\_vermelho\_dias | INTEGER, NOT NULL, DEFAULT 30 | Número de dias sem resolução para o semáforo indicar vermelho; alterável apenas por ateste do Secretário Municipal |
| ativo | BOOLEAN, DEFAULT TRUE | Indica se o serviço está ativo; registros nunca são excluídos |

**Valores iniciais:**

| categoria | nome |
| ----- | ----- |
| Infraestrutura e Via Pública | Iluminação Pública |
| Infraestrutura e Via Pública | Pavimentação e Vias |
| Infraestrutura e Via Pública | Saneamento e Drenagem |
| Mobilidade e Cidadania | Trânsito e Sinalização |
| Mobilidade e Cidadania | Saúde e Bem-estar |

**Entidade 5: bairro\_regiao**

*Normaliza a localização para uso em filtros e relatórios. Os bairros de Várzea Grande serão inseridos via script SQL na criação do banco.*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_bairro | PK, SERIAL | Identificador único do bairro |
| nome | VARCHAR(200), NOT NULL | Nome do bairro |
| cep | CHAR(8), NOT NULL | CEP referente ao bairro |
| regiao\_administrativa | VARCHAR(200), NULL | Região administrativa à qual o bairro pertence (preenchimento opcional) |
| ativo | BOOLEAN, DEFAULT TRUE | Indica se o bairro está ativo; registros nunca são excluídos |

**Entidade 6: chamado**

*Registra as solicitações de serviço abertas pelos cidadãos. Entidade central do sistema.*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_chamado | PK, SERIAL | Identificador único do chamado |
| protocolo | VARCHAR(20), UNIQUE, NOT NULL | Código numérico único gerado automaticamente para acompanhamento pelo cidadão |
| prioridade | SMALLINT, CHECK (0 a 5), NOT NULL, DEFAULT 0 | Nível de prioridade de 0 a 5, classificado pelo Colaborador ao receber o chamado |
| numero | VARCHAR(10), NOT NULL, DEFAULT '0' | Número do endereço do local do problema; informar 0 caso não haja número |
| complemento | VARCHAR(200), NULL | Informação adicional do endereço do local do problema |
| ponto\_referencia | VARCHAR(200), NULL | Referência para facilitar a localização do local no campo |
| descricao | VARCHAR(500), NOT NULL | Relato do problema pelo cidadão, com no máximo 500 caracteres |
| resolucao | VARCHAR(500), NULL | Descrição da solução aplicada ou motivo do cancelamento; obrigatório no encerramento |
| nota\_avaliacao | SMALLINT, CHECK (1 a 5), NULL | Nota de 1 a 5 atribuída pelo cidadão após conclusão; preenchida uma única vez |
| comentario\_avaliacao | VARCHAR(500), NULL | Comentário opcional do cidadão sobre o atendimento recebido |
| dt\_abertura | TIMESTAMP, DEFAULT CURRENT\_TIMESTAMP | Data e hora de abertura do chamado |
| dt\_conclusao | TIMESTAMP, NULL | Data e hora de encerramento do chamado |
| dt\_avaliacao | TIMESTAMP, NULL | Data e hora em que a avaliação foi registrada |
| atualizado\_em | TIMESTAMP, DEFAULT CURRENT\_TIMESTAMP | Data e hora da última atualização do registro |

**Entidade 7: foto\_chamado**

*Armazena as fotos do chamado. Tanto Cidadão quanto Colaborador podem adicionar fotos. A *Rule* 1 impede *uploads* em chamados CO ou CA. Exibição em ordem cronológica de *upload*.*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_foto | PK, SERIAL | Identificador único da foto |
| url\_foto | VARCHAR(200), NOT NULL | Endereço da foto armazenada no *Cloudinary* |
| dt\_upload | TIMESTAMP, DEFAULT CURRENT\_TIMESTAMP | Data e hora do envio da foto |

**Entidade 8: historico\_chamado**

*Registra todas as mudanças de status. Populado automaticamente pelos Triggers 1 e 2\.*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_historico | PK, SERIAL | Identificador único do registro de histórico |
| tipo\_status | CHAR(2), NOT NULL | Status aplicado no momento do registro (AB, AN, EX, CO ou CA) |
| dt\_alteracao | TIMESTAMP, DEFAULT CURRENT\_TIMESTAMP | Data e hora da alteração de status |
| observacao | VARCHAR(500) | Observação opcional registrada no momento da alteração |

**Entidade 9: observacao\_chamado**

*Troca de mensagens entre Cidadão e Colaborador. Funciona como um chat — ordem cronológica crescente, sem edição ou exclusão. *Rules* 2 e 5 protegem a integridade dos registros.*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_observacao | PK, SERIAL | Identificador único da observação |
| texto\_observacao | VARCHAR(500), NOT NULL | Conteúdo da mensagem enviada pelo Cidadão ou Colaborador |
| criado\_em | TIMESTAMP, DEFAULT CURRENT\_TIMESTAMP | Data e hora do envio da observação |

**Entidade 10: notificacao**

*Avisos exibidos na plataforma para o cidadão quando seu chamado é atualizado. Populada automaticamente pelo Trigger 2. Notificações não são excluídas — após 30 dias são arquivadas automaticamente via job agendado, deixando de aparecer na interface do cidadão mas permanecendo no banco.*

| Atributo | Tipo / Restrição | Descrição |
| :---- | :---- | :---- |
| id\_notificacao | PK, SERIAL | Identificador único da notificação |
| mensagem | VARCHAR(200), NOT NULL | Texto da notificação gerado automaticamente pelo sistema |
| lida | BOOLEAN, DEFAULT FALSE | Indica se o cidadão visualizou a notificação |
| arquivada | BOOLEAN, DEFAULT FALSE | Indica se a notificação foi arquivada após 30 dias; arquivadas não aparecem na interface |
| dt\_envio | TIMESTAMP, DEFAULT CURRENT\_TIMESTAMP | Data e hora do envio da notificação |

## **5.2 Relacionamentos com Cardinalidades**

> **Nota:** Foi identificado nas anotações de aula um relacionamento N:N que ainda não foi expresso no DER. Este ponto deve ser verificado e esclarecido com a turma antes da entrega da modelagem.

| Relacionamento | Cardinalidade | Descrição |
| ----- | ----- | ----- |
| usuario → chamado | 1:N | Um usuário abre zero ou vários chamados; cada chamado pertence a um único usuário identificado. O relacionamento foi mantido como 1:N pois o chamado anônimo foi descartado do escopo — todo chamado exige autenticação, garantindo rastreabilidade e privacidade. |
| categoria\_servico → servico | 1:N (mín. 1\) | Uma categoria agrupa um ou vários serviços; cada serviço pertence a uma única categoria. |
| servico → chamado | 1:N | Um serviço é referenciado em zero ou vários chamados; cada chamado tem um único serviço. |
| status\_chamado → chamado | 1:N | Um status se aplica a zero ou vários chamados; cada chamado possui um único status atual. |
| bairro\_regiao → chamado | 1:N | Um bairro tem zero ou vários chamados; cada chamado está em um único bairro. |
| chamado → foto\_chamado | 1:N (mín. 1\) | Um chamado tem uma ou várias fotos (obrigatória na abertura); cada foto pertence a um chamado. |
| chamado → historico\_chamado | 1:N (mín. 1\) | Todo chamado tem ao menos um histórico (inserido pelo *Trigger* 1); cada histórico pertence a um chamado. |
| usuario → historico\_chamado | 1:N | Um usuário aparece em zero ou vários históricos; cada histórico tem um único responsável. |
| status\_chamado → historico\_chamado | 1:N | Um status aparece em vários registros de histórico; cada registro guarda o status aplicado naquele momento. |
| chamado → observacao\_chamado | 1:N (mín. 0\) | Um chamado pode ter zero ou várias observações; cada observação pertence a um chamado. |
| usuario → observacao\_chamado | 1:N | Um usuário pode registrar zero ou várias observações; cada observação tem um único autor. |
| usuario → notificacao | 1:N | Um usuário recebe zero ou várias notificações; cada notificação pertence a um único usuário. |
| chamado → notificacao | 1:N (mín. 0\) | Um chamado pode gerar zero ou várias notificações; uma notificação pode ou não estar ligada a um chamado. |

# **6\. Público-Alvo**

| Perfil | Descrição |
| ----- | ----- |
| Cidadão | Moradores de Várzea Grande que desejam registrar problemas urbanos e acompanhar o andamento dos chamados. O sistema foi projetado para ser acessível a todos os públicos, incluindo pessoas idosas. |
| Colaborador | Servidores da prefeitura responsáveis pela triagem, gerenciamento e resposta às solicitações. Conta criada exclusivamente pelo Administrador. |
| Administrador | Responsável pela gestão de usuários, categorias, serviços e bairros. Possui acesso total ao sistema, incluindo o painel de estatísticas e a capacidade de alterar qualquer chamado independente do status. |

# **7\. Ferramentas**

| Ferramenta | Função no Projeto | Justificativa |
| ----- | ----- | ----- |
| *Python* / *Django* | Linguagem e *framework* do *backend* | *Framework* maduro, amplamente adotado no setor público e com suporte nativo ao PostgreSQL. |
| PostgreSQL | Banco de dados relacional | — |
| BrModelo | Criação do DER Conceitual e Lógico | — |
| *pgAdmin* 4 | Administração do banco de dados | — |
| *uv* | Gerenciador de pacotes *Python* | Substitui o *pip* por ser mais rápido, garantir reprodutibilidade e resolver conflitos de versão automaticamente. |
| *Design System* Gov.br | Padrão visual do *frontend* | — |
| *Git* / *GitHub* | Controle de versão | — |
| *Neon* | Hospedagem do banco de dados PostgreSQL | Plataforma gerenciada de PostgreSQL sem cobrança de IPv4 e sem pausa por inatividade, compatível com a hospedagem no *Render*. |
| *Cloudinary* | Armazenamento e gestão de fotos | Serviço de armazenamento com compressão e otimização automática de imagens. Custo de responsabilidade da Prefeitura de Várzea Grande. |
| *Render* | Hospedagem da aplicação *web* | Plataforma de hospedagem compatível com *Django*. Custo de responsabilidade da Prefeitura de Várzea Grande. |

# 

# **8\. Cronograma**

## **1º Bimestre (12/03 a 14/04) — Projeto do BD \[30% da nota\]**

| Etapa | Descrição | Entregável |
| ----- | ----- | ----- |
| Etapa 1 — Planejamento | Levantamento de requisitos, definição de escopo e elaboração da proposta. | Proposta aprovada |
| Etapa 2 — Modelagem | Criação do DER Conceitual e Lógico utilizando o BrModelo. | DER validado pela professora |
| Etapa 3 — Implementação do BD | Geração do script SQL, criação das tabelas, *constraints* e carga inicial (2 categorias, 5 serviços, 5 *status* e bairros). | Banco criado com tabelas no PostgreSQL |

## **2º Bimestre (15/04 a 07/07) — Recursos Avançados e Integração \[70% da nota\]**

| Etapa | Descrição | Entregável |
| ----- | ----- | ----- |
| Etapa 4 — Conexão e *Login* | Configuração do *Django* com *uv*, conexão com PostgreSQL e tela de *login*. | Tela de *login* funcional |
| Etapa 5 — Recursos Avançados | Implementação dos 2 *Triggers*, 6 *Rules* e *View* no PostgreSQL. | Recursos avançados funcionando |
| Etapa 6 — Módulo do Cidadão | Abertura de chamado, *upload* de foto, observações, acompanhamento e avaliação. | Fluxo do cidadão operacional |
| Etapa 7 — Módulo Colaborador/*Admin* | *Dashboard*, filtros, alteração de *status*, resolução e painel de estatísticas. | Módulos Colaborador e *Admin* funcionais |
| Etapa 8 — Finalização | Testes finais, ajustes e documentação. | Versão final entregável |
