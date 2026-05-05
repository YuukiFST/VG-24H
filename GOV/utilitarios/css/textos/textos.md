As classes de textos foram criadas baseadas no [Fundamento Tipografia](fundamentos-visuais/tipografia).

Todos os utilitários de texto começam com o prefixo `text-` e podem ser modificados por breakpoint.

Podem ser modificadas as seguintes propriedades:

- alinhamento
- wrap e overflow
- transformação
- peso
- tamanho

Exemplo de uso:

```html
<p class="text-up-01 text-lg-up-06 text-center text-lg-left">Texto de tamanho e alinhamento variável por breakpoint</p>
```

## Alinhamento

**Atenção**! O elemento precisa ser "block" ou "inline-block".

- `text-center`: centraliza
- `text-justify`: justifica
- `text-left`: alinha à esquerda
- `text-right`: alinha à direita

## Wrap e overflow

**Atenção**! O elemento precisa ser "block" ou "inline-block".

- `text-wrap`: quebra linha caso haja espaço em branco ou hífen entre as palavras
- `text-nowrap`: nunca quebra linha
- `text-truncate`: oculta palavras que ultrapassem a largura do elemento e adiciona reticências
- `text-break`: quebra linha independente de espaço em branco ou hífen

## Transformação

- `text-lowercase`: força todas as letras minúsculas
- `text-uppercase`: força todas as letras maiúsculas
- `text-capitalize`: Primeira letra de cada palavra em maiúsculo

## Peso

Aplica os tokens de peso de texto.

| Classe                    | Peso | Token                     |
| ------------------------- | ---- | ------------------------- |
| `text-weight-thin`        | 100  | --font-weight-thin        |
| `text-weight-extra-light` | 200  | --font-weight-extra-light |
| `text-weight-light`       | 300  | --font-weight-light       |
| `text-weight-regular`     | 400  | --font-weight-regular     |
| `text-weight-medium`      | 500  | --font-weight-medium      |
| `text-weight-semi-bold`   | 600  | --font-weight-semi-bold   |
| `text-weight-bold`        | 700  | --font-weight-bold        |
| `text-weight-extra-bold`  | 800  | --font-weight-extra-bold  |
| `text-weight-black`       | 900  | --font-weight-black       |

## Tamanho

Aplica os tokens de tamanho de texto.

| Classe         | Tamanho (px) | Token                     |
| -------------- | ------------ | ------------------------- |
| `text-up-07`   | 50.16        | --font-size-scale-up-07   |
| `text-up-06`   | 41.8         | --font-size-scale-up-06   |
| `text-up-05`   | 34.84        | --font-size-scale-up-05   |
| `text-up-04`   | 29.03        | --font-size-scale-up-04   |
| `text-up-03`   | 24.19        | --font-size-scale-up-03   |
| `text-up-02`   | 20.16        | --font-size-scale-up-02   |
| `text-up-01`   | 16.8         | --font-size-scale-up-01   |
| `text-base`    | 14           | --font-size-scale-base    |
| `text-down-01` | 11.67        | --font-size-scale-down-01 |
| `text-down-02` | 9.72         | --font-size-scale-down-02 |
| `text-down-03` | 8.10         | --font-size-scale-down-03 |
