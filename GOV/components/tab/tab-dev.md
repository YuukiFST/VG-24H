> URL oficial (visão geral): https://www.gov.br/ds/components/tab?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/tab?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor padrão    | Descrição               |
| -------- | ------ | --------------- | ----------------------- |
| class    | string | **br-tab**      | Container do componente |
| class    | string | **tab-nav**     | Container das abas      |
| class    | string | **tab-item**    | Rótulo de cada aba      |
| class    | string | **tab-content** | Container dos conteúdos |
| class    | string | **tab-panel**   | Conteúdo de cada aba    |

### Propriedades Adicionais

| Atributo     | Tipo    | Valor padrão           | Descrição                        |
| ------------ | ------- | ---------------------- | -------------------------------- |
| data-counter | boolean | **true**               | Versão com contadores            |
| class        | string  | **small** ou **large** | Modifica a densidade             |
| class        | string  | **dark-mode**          | Aplica cores para fundos escuros |

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

### JavaScript

Usar o seguinte código JavaScript para instanciar a classe `BRTab`, passando os seguintes parâmetros:

- Nome da classe (br-tab)
- Objeto referenciando a raiz do componente DOM

```javascript
const abasList = []
for (const brTab of window.document.querySelectorAll('.br-tab')) {
  abasList.push(new core.BRTab('br-tab', brTab))
}
```
