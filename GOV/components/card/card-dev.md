> URL oficial (visão geral): https://www.gov.br/ds/components/card?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/card?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão     | Descrição               |
| -------- | ------ | ---------------- | ----------------------- |
| class    | string | **br-card**      | Container do componente |
| class    | string | **card-content** | Conteúdo do Card        |

### Propriedades Adicionais

| Atributo | Tipo   | Valor Padrão    | Descrição                                     |
| -------- | ------ | --------------- | --------------------------------------------- |
| class    | string | **card-header** | Área de cabeçalho                             |
| class    | string | **card-footer** | Área de rodapé                                |
| class    | string | **hover**       | Habilita o estado hover                       |
| class    | string | **h-fixed**     | Habilita altura fixa e ativa barra de rolagem |

## Estados

| Estado     | atributo   | Valores |
| ---------- | ---------- | ------- |
| Desativado | `disabled` |         |

## Informações adicionais

### Card desativado

Para manter a acessibilidade do componente adicione o atributo `aria-disabled="true"` ao componente.

### Card com collapse

Veja exemplo de instanciação do collapse na aba "JavaScript" na sessão **Código compartilhado entre exemplos**.

### Card com altura fixa

A altura do conteúdo do card é controlado pelo token `--card-height-fixed` no CSS.
