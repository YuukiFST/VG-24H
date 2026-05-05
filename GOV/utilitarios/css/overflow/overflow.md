Use o utilitário de overflow para definir como o conteúdo que ultrapassa a área do elemento atual seja tratado.

É possível modificar o comportamento de acordo com o breakpoint.

- `overflow[-breakpoint]-auto`: cria barra de rolagemm
- `overflow[-breakpoint]-hidden`: esconde conteúdo excedente

Exemplo de uso:

```html
<!-- Irá criar barra de rolagem -->
<p class="overflow-auto" style="width: 300px">
  Texto com conteúdo muito grande. Texto com conteúdo muito grande. Texto com conteúdo muito grande
</p>

<!-- Irá criar barra de rolagem em desktop -->
<p class="overflow-lg-auto" style="width: 300px">
  Texto com conteúdo muito grande. Texto com conteúdo muito grande. Texto com conteúdo muito grande
</p>

<!-- Irá esconder o conteúdo em excesso -->
<p class="overflow-hidden" style="width: 300px">
  Texto com conteúdo muito grande. Texto com conteúdo muito grande. Texto com conteúdo muito grande
</p>

<!-- Irá esconder o conteúdo em excesso no celular e mostrar barra de rolagem em desktop -->
<p class="overflow-hidden overflow-lg-auto" style="width: 300px">
  Texto com conteúdo muito grande. Texto com conteúdo muito grande. Texto com conteúdo muito grande
</p>
```
