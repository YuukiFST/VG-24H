> URL oficial (visão geral): https://www.gov.br/ds/fundamentos-visuais/elevacao?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/fundamentos-visuais/elevacao?tab=codigos

## Utilitários CSS de Elevação

São classes CSS para aplicar o Fundamento Visual Elevação.

### Como usar

Modifique as **sombras** e a **camada** (*z-index*) da superfície.

> **Atenção!** Para modificar bordas, arredondamentos, *display*, etc veja os [utilitários de superficie](/ds/fundamentos-visuais/superficie?tab=codigos).

#### Sombras

Aplique sombras externas ou internas ao elemento.

Use a classe `shadow-` seguida do tamanho e tipo.

**Sombra externa:**

- `shadow-none` → remove a sombra;
- `shadow-sm` → sombra pequena;
- `shadow-md` → sombra média;
- `shadow-lg` → sombra grande;
- `shadow-xl` → sombra muito grande.

**Sombra interna:**

- `shadow-sm-inset` → sombra interna pequena;
- `shadow-md-inset` → sombra interna média;
- `shadow-lg-inset` → sombra interna grande;
- `shadow-xl-inset` → sombra interna muito grande.

#### Camadas (*z-index*)

Controle a ordem de empilhamento do elemento.

Use a classe `layer-` seguida do número da camada:

- `layer-0` → camada 0;
- `layer-1` → camada 1;
- `layer-2` → camada 2;
- `layer-3` → camada 3;
- `layer-4` → camada 4.

> **Atenção!** O *z-index* só funciona com ***position*** *relative*, *absolute* ou *fixed*.
