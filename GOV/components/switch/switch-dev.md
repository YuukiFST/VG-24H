> URL oficial (visão geral): https://www.gov.br/ds/components/switch?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/switch?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor padrão  | Descrição               |
| -------- | ------ | ------------- | ----------------------- |
| class    | string | **br-switch** | Container do componente |

### Propriedades Adicionais

| Atributo | Tipo   | Valor Padrão                        | Descrição                                              |
| -------- | ------ | ----------------------------------- | ------------------------------------------------------ |
| class    | string | **right** ou **top**                | Modifica alinhamento do label                          |
| class    | string | **icon**                            | Adiciona ícone na chave de alternância (switch toggle) |
| class    | string | **small**, **medium**, ou **large** | Modifica densidade do componente                       |

## Estados

| Estado     | atributo | Valores      |
| ---------- | -------- | ------------ |
| Desativado | class    | **disabled** |

## Informações adicionais

### Switch com rótulos adicionais

Para o rótulo adiciona use a classe `switch-data`. Os textos de ligado e desligado devem ficar em atributos data-\*:

- **data-enabled**: é mostrado quando o componente está "ligado"
- **data-disabled**: é mostrado quando o componente está "desligado"
