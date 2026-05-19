> URL oficial (visão geral): https://www.gov.br/ds/components/textarea?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/textarea?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor padrão    | Descrição               |
| -------- | ------ | --------------- | ----------------------- |
| class    | string | **br-textarea** | Container do componente |

### Propriedades Adicionais

| Atributo | Tipo   | Valor padrão           | Descrição                         |
| -------- | ------ | ---------------------- | --------------------------------- |
| class    | string | **small** ou **large** | Modifica a densidade.             |
| class    | string | **dark-mode**          | Aplica cores para fundos escuros. |

## Estados

| Estado     | atributo | Valores |
| ---------- | -------- | ------- |
| Desativado | disabled |         |
| Erro       | class    | danger  |
| Sucesso    | class    | success |
| Alerta     | class    | warning |
| Informação | class    | info    |

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

### JavaScript

Usar o seguinte código JavaScript para instanciar a classe `brTextArea`, passando os seguintes parâmetros:

- Nome da classe (br-textarea)
- Objeto referenciando a raiz do componente DOM

```javascript
const textareaList = []
for (const brTextArea of window.document.querySelectorAll('.br-textarea')) {
  textareaList.push(new core.BRTextArea('br-textarea', brTextArea))
}
```
