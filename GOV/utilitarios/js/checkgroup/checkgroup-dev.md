## Como usar

### Atributos no checkbox pai

#### Obrigatórios

| Atributo                  | Tipo     | Descrição                                                |
| ------------------------- | -------- | -------------------------------------------------------- |
| `data-parent="tag-group"` | atributo | Indica que o checkbox é o pai e a tag identifica o grupo |

#### Opcionais

| Atributo                                 | Tipo     | Descrição                                                |
| ---------------------------------------- | -------- | -------------------------------------------------------- |
| `aria-label="label"`                     | atributo | Informa a label para a acessibilidade                    |
| `data-checked-label="label-checked"`     | atributo | Label para checkbox selecionado. Default: tag `<label>`  |
| `data-unchecked-label="label-unchecked"` | atributo | Label para checkbox desselecionado. Default: tag `label` |
| `checked`                                | atributo | Indica se o checkbox está selecionado                    |
| `indeterminate`                          | atributo | Indica se o checkbox está indeterminado                  |

> Os atributos `data-checked-label` e `data-unchecked-label` só estão disponíveis em um checkbox pai

### Atributo no checkbox filho

#### Obrigatórios

| Atributo                 | Tipo     | Descrição                                                           |
| ------------------------ | -------- | ------------------------------------------------------------------- |
| `data-child="tag-group"` | atributo | Indica que o checkbox é filho e a tag indica o grupo a que pertence |

> Para formar o grupo o valor do `data-child` deve ser o mesmo do `data-parent`

#### Opcionais

| Atributo             | Tipo     | Descrição                             |
| -------------------- | -------- | ------------------------------------- |
| `aria-label="label"` | atributo | Informa a label para a acessibilidade |
| `checked`            | atributo | Indica se o checkbox está selecionado |

### Estado Indeterminado

O estado indeterminado acontece quando alguns checkboxes filhos estão selecionados e outros não.

> Quando o checkbox pai está no estado indeterminado, ele possui os atributos `checked` e `indeterminate`

### Checkgroup em Cadeia

O comportamento checkgroup pode ser usado em cadeia. Isso acontece quando um checkbox filho é também pai de outro grupo.

Para que isso aconteça, deve-se adicionar o atributo `data-parent` no checkbox filho e colocar um outro valor para ele indicando um novo grupo. Os filhos desse checkbox terão esse mesmo valor no atributo `data-child`

```HTML
<div class="br-checkbox">
  <input name="name" type="checkbox" aria-label="label" data-child="tag-group" data-parent="tag-group-2" checked/>
  <label for="name">...</label>
</div>
<div class="br-checkbox">
  <input name="name" type="checkbox" aria-label="label" data-child="tag-group-2" checked/>
  <label for="name">...</label>
</div>
```

### JavaScript

**Para cada checkbox pai (trigger)**, instanciar a classe Checkgroup passando uma referencia ao checkbox pai.

Em seguida chamar o método setBehavior()

```javascript
this.element.querySelectorAll('input[type="checkbox"][data-parent]').forEach((trigger) => {
  const checkgroup = new core.Checkgroup(trigger)
  checkgroup.setBehavior()
})
```

> **this.element**: elemento DOM onde vai ser instanciado o utilitário
