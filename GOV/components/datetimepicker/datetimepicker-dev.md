> URL oficial (visão geral): https://www.gov.br/ds/components/datetimepicker?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/datetimepicker?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão          | Descrição               |
| -------- | ------ | --------------------- | ----------------------- |
| class    | string | **br-datetimepicker** | Container do componente |

### Propriedades adicionais

| Atributo   | Tipo    | Valor Padrão                             | Descrição                                                            |
| ---------- | ------- | ---------------------------------------- | -------------------------------------------------------------------- |
| data-mode  | string  | **single** ou **range**                  | Modo do data única ou intervalo de data                              |
| data-type  | string  | **text**, **time** ou **datetime-local** | Tipo datetimepicker, timepicker ou datetimepicker + timepicker       |
| data-input | boolean | **true**                                 | Indica que o input irá receber o valor selecionado no datetimepicker |

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

## JavaScript

Usar o seguinte código JavaScript para instanciar a classe `BRDateTimePicker`, passando os seguintes parâmetros:

- Nome da classe (br-datetimepicker)
- Objeto referenciando a raiz do componente DOM

```javascript
const datetimepickerList = []
for (const brDateTimePicker of window.document.querySelectorAll(
  '.br-datetimepicker'
)) {
  datetimepickerList.push(
    new core.BRDateTimePicker('br-datetimepicker', brDateTimePicker,{minDate: '15/04/2022',maxDate: '20/04/2022'}
  )
}
```

Exemplo código JavaScript para mudar o idioma do datepicker passando parâmetro com objeto de idioma flatpickr.

```javascript
const datetimepickerList = []
for (const brDateTimePicker of window.document.querySelectorAll('.br-datetimepicker')) {
  const Spain = require('flatpickr/dist/l10n/es').default.es
  datetimepickerList.push(new BRDateTimePicker('br-datetimepicker', brDateTimePicker, {}, Spain))
}
```

## Informações adicionais

- O atributo `data-input` deve ser inserido na tag `<input>`.
- O atributo `datetimepicker-config` pode ser usado conforme o [Flatpickr options](https://flatpickr.js.org/options/)
- As variáveis **dateFormat,disableMobile, enableTime, minuteIncrement, node, minuteIncrement, nextArrow, noCalendar, prevArrow, time_24hr e wrap** não estão habilitados para alteração.
- O formato de data e hora é o **dia/mês/ano hora:minuto**

## Dependências

- [Button](/ds/components/button)
- [Input](/ds/components/input)
