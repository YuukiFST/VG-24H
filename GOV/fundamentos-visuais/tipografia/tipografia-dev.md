> URL oficial (visão geral): https://www.gov.br/ds/fundamentos-visuais/tipografia?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/fundamentos-visuais/tipografia?tab=codigos

## Utilitários CSS de Tipografia

São classes CSS para aplicar o **Fundamento Visual Tipografia**.

### Como usar

Modifique **estilos**, **tamanhos**, **pesos**, **alinhamento** e outras características dos textos.

#### Estilos tipográficos

Aplique estilos de texto, independente da tag HTML.

Use a classe correspondente ao estilo desejado:

- `h1` → Título H1;
- `h2` → Título H2;
- `h3` → Título H3;
- `h4` → Título H4;
- `h5` → Título H5;
- `h6` → Título H6;
- `label` → Rótulo;
- `input` → Campo de entrada;
- `placeholder` → Descrição em campo;
- `legend` → Legenda;
- `code` → Bloco de código;
- `mark` → Marcação de texto.

**Exemplo:** `<p class="h1">Texto com estilo de H1</p>`

#### Tamanho da fonte

Modifique o tamanho da fonte do texto.

Use o prefixo `text-` seguido do tamanho desejado.

**Exemplo:** `text-base`, `text-up-04`, `text-down-01`

> Veja todos os tamanhos disponíveis em [Visão Geral](/ds/fundamentos-visuais/tipografia?tab=visao-geral#escala-tipografica).

#### Peso da fonte

Modifique o peso (*font-weight*) do texto.

Use o prefixo `text-weight-` seguido do peso desejado.

**Exemplo:** `text-weight-regular`, `text-weight-medium`, `text-weight-bold`

> Veja todos os pesos disponíveis em [Visão Geral](/ds/fundamentos-visuais/tipografia?tab=visao-geral#peso-da-fonte-font-weight).

#### Transformação de texto

Modifique a capitalização do texto.

Use a classe correspondente à transformação desejada:

- `text-lowercase` → todas as letras minúsculas;
- `text-uppercase` → todas as letras maiúsculas;
- `text-capitalize` → primeira letra de cada palavra em maiúscula.

**Exemplo:** `<p class="text-uppercase">texto em maiúsculas</p>`

#### Alinhamento de texto

Modifique o alinhamento horizontal do texto.

Use a classe correspondente ao alinhamento desejado:

- `text-left` → alinha à esquerda;
- `text-center` → centraliza;
- `text-right` → alinha à direita;
- `text-justify` → justifica.

**Exemplo:** `<p class="text-center">Texto centralizado</p>`

> **Atenção!** O elemento precisa ter display "block" ou "inline-block". Veja os [utilitários de superfície](/ds/fundamentos-visuais/superficie?tab=codigos) para modificar o display.

#### Quebra de linha

Controle o comportamento da quebra de linha do texto.

Use a classe correspondente ao comportamento desejado:

- `text-wrap` → quebra linha em espaços ou hífens;
- `text-nowrap` → nunca quebra linha;
- `text-truncate` → oculta excedente e adiciona reticências;
- `text-break` → quebra linha forçadamente.

**Exemplo:** `<p class="text-truncate">Texto longo...</p>`

> **Atenção!** O elemento precisa ter display "block" ou "inline-block". Veja os [utilitários de superfície](/ds/fundamentos-visuais/superficie?tab=codigos) para modificar o display.
