## Como usar

### Atributos no elemento alvo

#### Obrigatórios

| Atributo                  | Tipo     | Descrição                                       |
| ------------------------- | -------- | ----------------------------------------------- |
| `data-scrim="true/false"` | atributo | Indica que o elemento é o scrim                 |
| `aria-modal="true/false"` | atributo | Adiciona semântica para o leitor de tela        |
| `role="dialog"`           | atributo | Indica que tem um dialogo para o leitor de tela |

#### Opcionais

| Atributo                    | Tipo     | Descrição                                                        |
| --------------------------- | -------- | ---------------------------------------------------------------- |
| `data-dismiss="true"`       | atributo | Clicando no elemento com essa propriedade, o Scrim será fechado. |
| `data-visible="true/false"` | atributo | Atributo de controle de visibilidade do Scrim                    |

> Os atributos opcionais do acionador são gerados automaticamente pelo JavaScript.

### JavaScript

\*\*Exemplo de como criar um Scrim passando um objeto de configuração.

```javascript
const buttonActivateModalScrim = window.document.querySelector('#buttonactivatemodal')
const scrscrim = window.document.querySelector('#scrimutilexamplemodal')

const scrimfoco = new Scrim({
  trigger: scrscrim,
  escEnable: true,
  limitTabKey: true,
})
buttonActivateModalScrim.addEventListener('click', (event) => {
  scrimfoco.showScrim()
})
```

\*\*Exemplo de como criar um Scrim com um seletor para os elementos internos que ao clicar fechará o Scrim.

```javascript
    const btnActivateModal = window.document.querySelector('#buttonactivatemodal')
    const modalScrim  = window.document.querySelector('#scrimutilexamplemodal')

    const scrimInstance = new Scrim({
      closeElement: '.clicktoclose'
      trigger: modalScrim ,
      escEnable: true,
      limitTabKey: true
    })
    btnActivateModal.addEventListener('click',(event)=>{
      scrimInstance.showScrim()
    })
```

#### Objeto de configuração

| Propriedade    | Tipo    | Descrição                                                                                     |
| -------------- | ------- | --------------------------------------------------------------------------------------------- |
| `trigger`      | Object  | Referência ao elemento (DOM) Scrim                                                            |
| `closeElement` | String  | Seletor JS id ou classe do (DOM) que ao ser clicado fechará o Scrim                           |
| `limitTabKey`  | boolean | Default é false, ao modificar para true a navegacao via tab ficará presa ao contexto do Scrim |
| `escEnable`    | Boolean | Default é false, ao modificar para true a tecla ESC fechará o Scrim                           |

#### Métodos da instância do comportamento Scrim

| Nome        | Tipo     | Descrição                                              |
| ----------- | -------- | ------------------------------------------------------ |
| `showScrim` | estática | Alterna o estado do comportamento scrim para visível   |
| `hideScrim` | estática | Alterna o estado do comportamento scrim para escondido |
