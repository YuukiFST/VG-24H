> URL oficial (visão geral): https://www.gov.br/ds/components/magicbutton?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/magicbutton?tab=codigos

## Como usar

### Uso de texto

```html
<div class="br-magic-button">
  <button class="br-button" type="button">Label</button>
</div>
```

### Uso de ícone

```html
<div class="br-magic-button">
  <button class="br-button circle" type="button" aria-label="Adicionar">
    <i class="fas fa-cart-plus" aria-hidden="true"></i>
  </button>
</div>
```

### Propriedades obrigatórias

| Atributo | Valor padrão    | Descrição               |
| -------- | --------------- | ----------------------- |
| class    | br-magic-button | Container do componente |

### Propriedades Adicionais

| Atributo | Valor padrão | Descrição                       |
| -------- | ------------ | ------------------------------- |
| class    | large        | Aplica densidade baixa          |
| class    | medium       | Aplica densidade média (padrão) |
| class    | small        | Aplica densidade alta           |

## Acessibilidade

- Use `aria-label="descrição da ação"` nos botões que tenham somente ícone como conteúdo.

## Dependências

- [Button](/ds/components/button)
