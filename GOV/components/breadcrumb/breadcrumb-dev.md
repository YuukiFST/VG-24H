> URL oficial (visão geral): https://www.gov.br/ds/components/breadcrumb?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/breadcrumb?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão      | Descrição                |
| -------- | ------ | ----------------- | ------------------------ |
| class    | string | **br-breadcrumb** | Container do componente. |
| class    | string | **crumb-list**    | Lista interna de links.  |
| class    | string | **crumb**         | Cada item da lista.      |
| class    | string | **home**          | Primeiro link da lista.  |
| class    | string | **icon**          | Cada separador da lista. |

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

## JavaScript

Usar o seguinte código JavaScript para instanciar a classe `BRBreadcrumb`, passando os seguintes parâmetros:

- Nome da classe (br-breadcrumb)
- Objeto referenciando a raiz do componente DOM

```javascript
const breadcrumbList = []
for (const brBreadcrumb of window.document.querySelectorAll('.br-breadcrumb')) {
  breadcrumbList.push(new core.BRBreadcrumb('br-breadcrumb', brBreadcrumb))
}
```

## Dependências

- [Button](/ds/components/button)
- [Card](/ds/components/card)
- [Item](/ds/components/item)
- [Tooltip](/ds/util/tooltip)
