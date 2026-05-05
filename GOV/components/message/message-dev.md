> URL oficial (visão geral): https://www.gov.br/ds/components/message?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/message?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão   | Descrição                      |
| -------- | ------ | -------------- | ------------------------------ |
| class    | string | **br-message** | Container para Tipo Padrão     |
| class    | string | **feedback**   | Container para Tipo Contextual |

### Propriedades adicionais

| Atributo | Tipo   | Valor Padrão | Descrição               |
| -------- | ------ | ------------ | ----------------------- |
| class    | string | **danger**   | Mensagens de Erro       |
| class    | string | **success**  | Mensagens de Sucesso    |
| class    | string | **info**     | Mensagens de Informação |
| class    | string | **warning**  | Mensagens de Alerta     |

## Dependências

- [Button](/ds/components/button)

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

## JavaScript

Usar o seguinte código JavaScript para instanciar a classe `BRMessage`, passando os seguintes parâmetros:

- Nome da classe (br-message)
- Objeto referenciando a raiz do componente DOM

```javascript
const alertList = []
for (const brAlert of window.document.querySelectorAll('.br-message')) {
  alertList.push(new core.BRAlert('br-message', brAlert))
}
```
