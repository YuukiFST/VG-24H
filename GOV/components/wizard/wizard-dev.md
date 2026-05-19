> URL oficial (visão geral): https://www.gov.br/ds/components/wizard?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/wizard?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão             | Descrição                                  |
| -------- | ------ | ------------------------ | ------------------------------------------ |
| class    | string | **br-wizard**            | Container do componente                    |
| class    | string | **wizard-progress**      | Container das etapas                       |
| class    | string | **wizard-progress-btn**  | Cada etapa                                 |
| class    | string | **wizard-form**          | Container dos conteúdos/barra de navegação |
| class    | string | **wizard-panel**         | Cada painel                                |
| class    | string | **wizard-panel-content** | Container do conteúdo                      |
| class    | string | **wizard-panel-btn**     | Container da barra de navegação            |

### Propriedades adicionais

| Atributo | Tipo    | Valor Padrão | Descrição                            |
| -------- | ------- | ------------ | ------------------------------------ |
| scroll   | boolean |              | Habilita rolagem no painel de etapas |
| class    | string  | **vertical** | Habilita versão vertical             |
| step     | number  | **1**        | Determina qual será o passo inicial  |

## Informações adicionais

### Comportamento em celular/tablet

As etapas mostram apenas os números e a descrição ficará visível após realizar swipe na área.

## Dependências

- [Button](/ds/components/button)

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

### JavaScript

Usar o seguinte código JavaScript para instanciar a classe `BRWizard`, passando os seguintes parâmetros:

- Nome da classe (br-wizard)
- Objeto referenciando a raiz do componente DOM

```javascript
const wizardList = []
for (const brWizard of window.document.querySelectorAll('.br-wizard')) {
  wizardList.push(new core.BRWizard('br-wizard', brWizard))
}
```
