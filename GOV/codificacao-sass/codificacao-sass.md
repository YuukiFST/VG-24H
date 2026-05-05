Os estilos em CSS no Design System GOV.BR são criados usando o [Sass](https://sass-lang.com/) no formato **scss**.

## Padronização

O Design System GOV.BR usa o [stylelint](https://stylelint.io/) para manter o padrão de escrita Sass.

Customizações utilizadas:

```json
{
  "extends": ["stylelint-config-sass-guidelines", "stylelint-config-prettier"],
  "defaultSeverity": "warning",
  "rules": {
    "max-nesting-depth": null,
    "order/order": [["custom-properties", "dollar-variables", "declarations", "rules"]],
    "selector-max-compound-selectors": null,
    "selector-no-qualifying-type": null
  }
}
```

Nas situações onde os estilos precisem sobrescrever scss de vendors em conflito com as configurações do govbr-ds, desabilite temporariamente a regra de acordo com a documentação [Ignoring code](https://stylelint.io/user-guide/ignore-code).

## Documentação e comentários

Utilizamos o [SassDoc](http://sassdoc.com/) para documentar functions e mixins reusáveis.

- Usar formato SassDoc (3 barras) para documentação
- Usar formato convencional (2 barras) para dicas ou observações.

Para ver a documentação do SassDoc rode o script `npm run docs:sass` em seguida abra o arquivo **sassdoc/index.html** no browser.

Cada documentação é classificada por grupo específico conforme configurado no arquivo `.sassdocrc.yaml`:

```yaml
dest: ./sassdoc
groups:
  '01': Configurações globais
  '02': Uso genérico
  '03': Utilitários
  '04': Uso específico
  '05': Obsoleto
```

## Functions e Mixins

Ao criar uma nova function ou mixim use os exemplos a seguir.

### function

```scss
/// Retorna o RGB de uma variável em hexadecimal
/// @group 02
/// @param {Variable} $hex - Variável Sass no formato Hexadecimal
/// @example scss - Criar variável Sass no formato RGB
///  $color-primary-default: #1351b4;
///  $rgb-primary-default: get-rgb($color-primary-default);
/// @example scss - Criar tokens no formato RGB
///  @mixin token-color-rgb($map) {
///    @each $key, $value in $map {
///      --#{$key}-rgb: #{get-rgb($value)};
///    }
///  }
@function get-rgb($var) {
  @return red($var), green($var), blue($var);
}
```

### mixin

```scss
/// Aplica o foco padrão (tracejado).
/// @group 02
/// @example scss - Uso prático
///  a {
///    @include focus;
///  }
@mixin focus {
  &:focus {
    outline: none;
  }

  &.focus-visible,
  &:focus-visible {
    outline-color: var(--focus-color);
    outline-offset: var(--focus-offset);
    outline-style: var(--focus-style);
    outline-width: var(--focus-width);
  }
}
```

### Parâmetros utilizados

| Parâmetro | Descrição                                                                                             |
| --------- | ----------------------------------------------------------------------------------------------------- |
| @group    | Grupo a qual pertence o código. ver arquivo `.sassdocrc.yaml`                                         |
| @param    | Deve ser informado o tipo e descrição do parâmentro. Opcionalmente pode ser informado o valor padrão. |
| @example  | Código de exemplo de uso.                                                                             |

- Quando for escrever um exemplo não use a mesma indentação do parâmentro, pois pode gerar erro na documentação.
- O grupo "Uso interno" deve ser usado para functions/mixins criados sem objetivo de reuso

## Componentes

Para agilizar a manutenção dos arquivos Sass dividimos o código em pequenos blocos. Cada bloco é responsável por uma funcionalidade, tipo ou variação, portanto tenha em mente que alguns códigos podem ter mais blocos que outros.

Usamos mixin para cada bloco interno. Eles são escritos em arquivo a parte e são carregados dentro do componente.

Arquivo `_mixins.scss`:

```scss
@mixin component-configs {
  @include component-tokens;
  @include component-default;
  @include component-alternate;
  @include component-sizes;
}
@mixin component-tokens {
  --component-background: var(--background);
  --component-color: var(--color);
  --component-size: var(--component-medium);
  --component-small: 40px;
  --component-medium: 100px;
  --component-large: 160px;
}
@mixin component-default {
  background: var(--component-background);
  color: var(--component-color);
  display: inline-block;
  height: var(--component-size);
}
@mixin component-alternate {
  &.alternate {
    --component-background: var(--background-alternate);
    --component-color: var(--color-alternate);
  }
}
@mixin component-sizes {
  @each $size in small, medium, large {
    &.#{$size} {
      --component-size: var(--component-#{$size});
    }
  }
}
```

Arquivo `_componente.scss`:

```scss
@include 'mixins';

.#{$prefix}component {
  @include component-configs;
}
```

## Bloco configs

Responsável por carregar todos os blocos de código. Propositalmente é a primeira linha, portanto é a parte mais importante.

Nela você terá a noção de quantos blocos o arquivo Sass está dividido e poderá ir direto ao ponto quando precisar ler ou fazer manutenção no código.

```scss
@mixin component-configs {
  @include component-tokens;
  @include component-default;
  @include component-alternate;
  @include component-sizes;
}
```

## Bloco tokens

Alguns componentes podem ter tokens para facilitar modificações. Eles podem consumir tanto os tokens do govbr-ds quanto seus tokens internos.

No exemplo abaixo existem 6 tokens criados para o componente. Os 2 primeiros consomem tokens de tema do govbr-ds enquanto que os restantes são internos do próprio componente.

```scss
@mixin component-tokens {
  --component-background: var(--background);
  --component-color: var(--color);
  --component-size: var(--component-medium);
  --component-small: 40px;
  --component-medium: 100px;
  --component-large: 160px;
}
```

Crie tokens apenas quando houver necessidade de modificação do seu valor caso contrário eles não terão utilidade.

## Bloco default

Coloque somente o código básico neste bloco. Códigos específicos devem ficar em blocos a parte.

No exemplo abaixo foram definidas as cores de superfície e leitura, o tipo de display e altura.

```scss
@mixin component-default {
  background: var(--component-background);
  color: var(--component-color);
  display: inline-block;
  height: var(--component-size);
}
```

## Blocos específicos

No exemplo abaixo a versão alternativa do componente troca as cores de superfície e leitura.

```scss
@mixin component-alternate {
  &.alternate {
    --component-background: var(--background-alternate);
    --component-color: var(--color-alternate);
  }
}
```

No exemplo abaixo são criadas as variações de tamanho.

```scss
@mixin component-sizes {
  @each $size in small, medium, large {
    &.#{$size} {
      --component-size: var(--component-#{$size});
    }
  }
}
```

## Código compilado

```css
.br-component {
  --component-background: var(--background);
  --component-color: var(--color);
  --component-size: var(--component-medium);
  --component-small: 40px;
  --component-medium: 100px;
  --component-large: 160px;
  background: var(--component-background);
  color: var(--component-color);
  display: inline-block;
  height: var(--component-size);
}

.br-component.alternate {
  --component-background: var(--background-alternate);
  --component-color: var(--color-alternate);
}

.br-component.small {
  --component-size: var(--component-small);
}

.br-component.medium {
  --component-size: var(--component-medium);
}

.br-component.large {
  --component-size: var(--component-large);
}
```
