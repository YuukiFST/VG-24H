> URL oficial (visão geral): https://www.gov.br/ds/fundamentos-visuais/superficie?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/fundamentos-visuais/superficie?tab=codigos

## Utilitários CSS de Superfície

São classes CSS para aplicar o Fundamento Visual Superfície.

### Como usar

Modifique **bordas**, **arredondamentos**, **display** e outras características da superfície.

> **Atenção!** Para modificar sombras e camadas, veja os [utilitários de elevação](/ds/fundamentos-visuais/elevacao?tab=codigos).

#### Bordas

Aplique bordas com estilos e espessuras diferentes.

Use o prefixo `border-` seguido do estilo e espessura.

**Estilo sólido:**

- `border-solid-none` → remove a borda;
- `border-solid-sm` → espessura pequena;
- `border-solid-md` → espessura média;
- `border-solid-lg` → espessura grande.

**Estilo tracejado:**

- `border-dashed-none` → remove a borda;
- `border-dashed-sm` → espessura pequena;
- `border-dashed-md` → espessura média;
- `border-dashed-lg` → espessura grande.

> **Atenção!** Para modificar a cor da borda, use os [utilitários de cores](/ds/fundamentos-visuais/cores?tab=codigos).

#### Arredondamento de cantos

Aplique arredondamento nos cantos do elemento.

Use a classe `rounder-` seguida do tamanho desejado:

- `rounder-none` → sem arredondamento;
- `rounder-sm` → arredondamento pequeno;
- `rounder-md` → arredondamento médio;
- `rounder-lg` → arredondamento grande;
- `rounder-pill` → formato de pílula.

#### Opacidade

Modifique o nível de transparência do elemento.

Use a classe `opacity-` seguida do nível desejado:

- `opacity-none` → 0% de transparência (opaco);
- `opacity-xs` → 16% de transparência;
- `opacity-sm` → 30% de transparência;
- `opacity-md` → 45% de transparência;
- `opacity-lg` → 65% de transparência;
- `opacity-xl` → 85% de transparência;
- `opacity-default` → 100% de transparência (invisível).

#### Overflow

Controle como o conteúdo excedente é tratado.

Use a classe correspondente ao comportamento desejado:

- `overflow-auto` → cria barra de rolagem;
- `overflow-hidden` → esconde conteúdo excedente.

> **Com breakpoints:** `overflow-sm-auto`, `overflow-lg-hidden`

#### Display

Modifique o tipo de exibição do elemento.

Use a classe correspondente ao display desejado:

- `d-none` → oculta elemento;
- `d-block` → exibição em bloco;
- `d-inline` → exibição inline;
- `d-inline-block` → exibição inline-block;
- `d-flex` → exibição flexbox;
- `d-inline-flex` → exibição inline-flex.

> **Com breakpoints:** `d-sm-none`, `d-lg-block`

---

## Flexbox

O `d-flex` aplica o ***Flexbox***. Ele possui algumas configurações extras dividas entre *flexbox parent* e *flexbox children*.

> Saiba mais sobre *Flexbox* em [Conceitos básicos de flexbox](https://developer.mozilla.org/pt-BR/docs/Web/CSS/Guides/Flexible_box_layout/Basic_concepts) da *Mozilla*.

### Flexbox parent

**Direction**:

- `flex-row`
- `flex-row-reverse`
- `flex-column`
- `flex-column-reverse`

> **Com breakpoints:** `flex-sm-column`, `flex-lg-row`

**Justify content**:

- `justify-content-start`
- `justify-content-end`
- `justify-content-center`
- `justify-content-between`
- `justify-content-around`
- `justify-content-evenly`

> **Com breakpoints:** `justify-content-sm-center`, `justify-content-lg-start`.

**Align items**:

- `align-items-start`
- `align-items-end`
- `align-items-center`
- `align-items-baseline`
- `align-items-stretch`

> **Com breakpoints:** `align-items-sm-center`, `align-items-lg-start`.

**Align content**:

- `align-content-start`
- `align-content-end`
- `align-content-center`
- `align-content-around`
- `align-content-evenly`
- `align-content-stretch`

> **Com breakpoints:** `align-content-sm-center`, `align-content-lg-start`.

**Wrap**:

- `flex-wrap`
- `flex-nowrap`
- `flex-wrap-reverse`

> **Com breakpoints:** `flex-sm-wrap`, `flex-lg-nowrap`.

### Flexbox children

**Align self**:

- `align-self-start`
- `align-self-end`
- `align-self-center`
- `align-self-baseline`
- `align-self-stretch`

> **Com breakpoints:** `align-self-sm-center`, `align-self-lg-start`.

**Fill**, **Grow** e **Shrink**:

- `flex-fill`
- `flex-grow-1`
- `flex-grow-0`
- `flex-shrink-1`
- `flex-shrink-0`

> **Com breakpoints:** `flex-sm-fill`, `flex-lg-grow-1`.

**Order**:

- `order-0`
- `order-1`
- `order-2`
- `order-3`
- `order-4`
- `order-5`
- `order-6`
- `order-7`
- `order-8`
- `order-9`
- `order-10`
- `order-11`
- `order-12`

> **Com breakpoints:** `order-sm-1`, `order-lg-12`.
