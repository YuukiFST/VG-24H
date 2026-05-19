> URL oficial (visão geral): https://www.gov.br/ds/components/item?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/item?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor padrão | Descrição                |
| -------- | ------ | ------------ | ------------------------ |
| class    | string | **br-item**  | Container do componente. |

### Propriedades Adicionais

| Atributo | Tipo   | Valor padrão | Descrição                                  |
| -------- | ------ | ------------ | ------------------------------------------ |
| class    | string | **divider**  | Aplica separador na borda inferior do Item |

## Estados

| Estado      | propriedade  | Valores                   |
| ----------- | ------------ | ------------------------- |
| Ativo       | **active**   | Aplica estilo ativo       |
| Selecionado | **selected** | Aplica estilo selecionado |
| Desativado  | **disabled** | Aplica estilo desativado  |

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

### JavaScript

Usar o seguinte código JavaScript para instanciar a classe `BRItem`, passando os seguintes parâmetros:

- Nome da classe (br-item)
- Objeto referenciando a raiz do componente DOM

```javascript
const itemList = []
for (const brItem of window.document.querySelectorAll('.br-item')) {
  itemList.push(new core.BRItem('br-item', brItem))
}
```
