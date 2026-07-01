# patches_legado — correcoes pontuais para bancos JA existentes

Scripts de uso **unico**, aplicaveis apenas em bancos criados por uma versao
antiga do schema. Instalacoes novas (`00_install_all.sql` ou `aplicar_no_neon.sql`)
ja nascem corretas e **NAO** precisam destes patches.

| Arquivo | O que corrige | Ainda necessario? |
|---|---|---|
| `fix_rules_to_triggers.sql` | Converte as Rules condicionais antigas (R1/R2/R3) em Triggers BEFORE. Ja incorporado em `04_rules.sql`. | So em bancos anteriores a conversao Rule->Trigger. |
| `fix_status_descricoes.sql` | Remove o prefixo da sigla das descricoes de status ("AB — Aberto" -> "Aberto"). Ja incorporado em `02_seed.sql`. | So em bancos com descricoes prefixadas antigas. |

Aplicar apenas se o diagnostico indicar que o banco esta no estado antigo.
