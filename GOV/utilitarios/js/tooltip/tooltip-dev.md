## Como usar

### Atributos no Tooltip Texto

#### Obrigatórios

| Atributo                               | Tipo     | Descrição                         |
| -------------------------------------- | -------- | --------------------------------- |
| `data-tooltip-text="texto do tooltip"` | atributo | Texto que vai aparecer no tooltip |

### Atributo no Tooltip com elemento

#### Obrigatórios

| Atributo                               | Tipo     | Descrição                                                      |
| -------------------------------------- | -------- | -------------------------------------------------------------- |
| `data-tooltip-target="id do elemento"` | atributo | Indica qual id do elemento em que vai ser instaciado o tooltip |
| `br-tooltip`                           | classe   | Indica qual o tooltip em que vai gerar o tooltip               |

### JavaScript

Exemplo de ativar tooltip usando classes js em que procuta elemento com atributo `data-tooltip-text` e instancia o Tooltip

```javascript
window.document.querySelectorAll('[data-tooltip-text]').forEach((TooltipExample) => {
  const texttooltip = TooltipExample.getAttribute('data-tooltip-text')
  const config = {
    activator: TooltipExample,
    place: 'top',
    textTooltip: texttooltip,
  }

  TooltipExampleList.push(new core.Tooltip(config))
})
```

#### Objeto de configuração

| Propriedade   | Tipo    | Descrição                                                                       |
| ------------- | ------- | ------------------------------------------------------------------------------- |
| `activator`   | Object  | Referência ao elemento (DOM) acionador                                          |
| `place`       | String  | Local aonde vai ser mostado o tooltip(top, right, left, bottom)                 |
| `textTooltip` | String  | Texto do tooltip (Opcional)                                                     |
| `type`        | String  | Tipo de tooltip(info, warning, error, success)                                  |
| `timer`       | String  | Tempo em que o tooltip fica aberto em milisegundos(Opcional)                    |
| `onActivator` | Boolean | Insere elemento do tooltip ativo dentro do acionador ao invés da body(Opcional) |
| `component`   | String  | Define elemento dom customizado do tooltip(Opcional)                            |
