> URL oficial (visão geral): https://www.gov.br/ds/fundamentos-visuais/espacamento?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/fundamentos-visuais/espacamento?tab=codigos

## Utilitários CSS de Espaçamento

São classes CSS para aplicar o Fundamento Visual Espaçamento.

### Como usar

Modifique ***margin*** e ***padding***.

Informe o espaçamento seguido do tamanho.

- `m-*` → margin;
- `p-*` → padding.
- `base`, `half`, `2x`, `3x` → tamanhos.

Exemplos: `m-base`, `p-3x`, `m-half`

> Veja todos os tamanhos disponíveis em [Visão Geral](/ds/fundamentos-visuais/espacamento?tab=visao-geral#layout).

### Direções

Inclua a **sigla** da direção após o prefixo e antes do tamanho.

- `t` = top (superior) → `mt-3x`
- `b` = bottom (inferior) → `pb-base`
- `l` = left (esquerda) → `ml-half`
- `r` = right (direita) → `pr-2x`
- `x` = horizontal (esq + dir) → `px-2x`
- `y` = vertical (top + bottom) → `my-half`

### *Breakpoints*

Informe o *breakpoint* após o prefixo e antes do tamanho.

- `m-*` / `p-*` → funcionam em todos os dispositivos;
- `m-sm-*` / `p-sm-*` → a partir de ***smartphone* em modo paisagem** e ***tablet* em modo retrato**;
- `m-md-*` / `p-md-*` → a partir de ***tablet* em modo paisagem**;
- `m-lg-*` / `p-lg-*` → a partir de ***desktop***;
- `m-xl-*` / `p-xl-*` → apenas em **TVs**.

### Dicas

- Use `m-*` e `p-*` para espaçamentos globais.
- Combine direções (`mt`, `px`, `my`) para ajustes finos.
- Adapte com *breakpoints* (`sm`, `md`, `lg`, `xl`) para responsividade.
