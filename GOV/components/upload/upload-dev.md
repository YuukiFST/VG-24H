> URL oficial (visão geral): https://www.gov.br/ds/components/upload?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/upload?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão     | Descrição               |
| -------- | ------ | ---------------- | ----------------------- |
| class    | string | **br-upload**    | Container do componente |
| class    | string | **upload-label** | Label do componente     |
| class    | string | **upload-input** | Entrada de arquivo(s)   |

### Propriedades Adicionais

| Atributo | Tipo     | Valor Padrão | Descrição                                               |
| -------- | -------- | ------------ | ------------------------------------------------------- |
| multiple | atributo |              | Incluir múltiplos arquivos. Aplicar em **upload-input** |

### Estados

| Estado     | atributo   | Valores |
| ---------- | ---------- | ------- |
| Desativado | `disabled` |         |

## Dependências

- [Button](/ds/components/button)
- [Item](/ds/components/item)
- [Message](/ds/components/message)
- [Tooltip](/ds/util/tooltip)

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

### JavaScript

Usar o seguinte código JavaScript para instanciar a classe `BRUpload`, passando os seguintes parâmetros:

- Nome da classe (br-upload)
- Objeto referenciando a raiz do componente DOM

```javascript
const uploadList = []

function uploadTimeout() {
  return new Promise((resolve) => {
    // Colocar aqui um upload para o servidor e retirar o timeout
    return setTimeout(resolve, 3000)
  })
}

for (const brUpload of window.document.querySelectorAll('.br-upload')) {
  uploadList.push(new core.BRUpload('br-upload', brUpload, uploadTimeout))
}
```
