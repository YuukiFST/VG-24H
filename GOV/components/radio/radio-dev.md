> URL oficial (visão geral): https://www.gov.br/ds/components/radio?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/radio?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão | Descrição               |
| -------- | ------ | ------------ | ----------------------- |
| class    | string | **br-radio** | Container do componente |

## Estados

| Estado     | atributo | Valores      |
| ---------- | -------- | ------------ |
| Desativado | class    | **disabled** |
| Inválido   | class    | **invalid**  |
| Válido     | class    | **valid**    |

## Informações adicionais

### Listagem horizontal

Usar Utilitários CSS [Display](utilitarios/css/display) e [Espaçamento](utilitarios/css/espacamento) para modificar o componente.

### Radio desativado

Além de adicionar a classe "disabled" ao componente, adicione também o atributo "disabled" na tag html `<input>`.
