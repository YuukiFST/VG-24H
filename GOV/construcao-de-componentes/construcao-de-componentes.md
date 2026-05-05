Faça um fork ou clone do projeto, conforme o exemplo abaixo:

```bash
git clone https://gitlab.com/govbr-ds/ds/dev/govbr-ds-dev-core.git
cd govbr-ds-dev-core
npm install
npm start
```

Algumas dependências com o prefixo @govbr são acessíveis apenas dentro da intranet do serpro. Assim, caso esteja fora, é necessário deletá-las do *package.json* para conseguir executar o comando *npm install* sem erros.

Veja a lista de componentes no endereço <http://localhost:9000/>.

Os códigos foram escritos usando a linguagem de templates Pug - <https://pugjs.org/api/getting-started.html>. Eles são compilados para HTML.

Para os estilos foi usado o SASS - <https://sass-lang.com/>. Eles são compilados para CSS.

## Regras

1. Componentes do Design System DEVEM ter prefixo **br-**
2. Variações deve ser aplicadas por classe, exemplos de variações: tipo, densidade, cor, estado etc
3. Comportamentos devem ser aplicados por atributo, exemplos de comportamentos: ativar dropdown, collapse, modal etc
4. Por motivos de acessibilidade e compatibilidade de navegadores os comportamentos de ação devem ser atribuídos apenas a elementos do tipo botão ou links (tags `<button></button>` e `<a></a>` respectivamente)

## Estrutura de Pastas

Basicamente há 4 (quatro) tipos de extensões de arquivos que formam um componente:

1. `md` - Markdown da documentação
2. `pug` - Código na Linguagem [Pug](https://pugjs.org)
3. `js` - Código na Linguagem [JavaScript](https://developer.mozilla.org/pt-BR/docs/Web/JavaScript)
4. `scss` - Código na Linguagem [Sass](https://sass-lang.com/documentation)

Para exemplificar, vamos supor a criação de um `componente-novo`. O componente deve obedecer a seguinte estrutura:

```text
govbr-ds-dev-core/
├── config.json
├── docs/
│   └── components/
|       └── componente-novo/
|            ├── imagens/
|            ├── componente-novo.md
|            ├── componente-novo-dev.md
|            └── componente-novo-dsg.md
└── src/
    └── components/
        └── componente-novo/
            ├── examples/
            │   └── example-componente-novo.pug
            ├── examples.pug
            ├── componente-novo.js
            ├── componente-novo.pug
            ├── _componente-novo.scss
            └── _mixins.scss
```

- Note que há na estrutura, conforme exemplo, um padrão de nomenclatura e hierarquia de arquivos e pastas.
- Perceba ainda que, para cada tipo, há pelo menos um arquivo específico do componente e outro agregador que o associa aos demais componentes.

### Detalhamento da estrutura para cada extensão

#### MD

```text
govbr-ds-dev-core/
├── config.json (incluir o novo componente na lista de componentes)
└── docs/
    └── components/
        └── componente-novo/
            ├── imagens/
            ├── componente-novo.md
            ├── componente-novo-dev.md
            └── componente-novo-dsg.md
```

1. Dentro de `docs/components/` deve haver uma pasta com o nome do componente
2. Dentro dessa pasta (no caso `docs/components/componente-novo/`) podem existir os arquivos:

   - `componente-novo.md` - Explica os objetivos do componente.
   - `componente-novo-dev.md` - Documentação de desenvolvedor do componente.
   - `componente-novo-dsg.md` - Documentação de design do componente.
   - `imagens/` imagens referenciadas na documentação.

3. Deve ser registrado na lista de componentes no arquivo `govbr-ds-dev-core/config.json`. Exemplificando:

   ```text
   [
     {
       "children": [
         {
           "label": "Novo Componente",
           "filename": "componente-novo"
         }
       ],
       "id": "components",
       "label": "Componentes",
       "type": "component"
     }
   ]
   ```

4. Também deve ser registrado na lista de componentes no arquivo `design-system/webpack/core.entries.js` com os mixins de reuso. Exemplificando:

   ```js
   setComponentPug('componente-novo', ['componente-novo-1', 'componente-novo-2'])
   ```

Após criados os arquivos de documentação e respeitadas as corretas referências da nomenclatura e hierarquia dos arquivos o novo componente já aparecerá no menu do `Site` e sua página carregará os conteúdos de documentação.

#### JS

```text
govbr-ds-dev-core/
└── src/
    └── components/
        └── componente-novo/
            └── componente-novo.js
```

- Partimos da premissa que cada componente distinto deve ser definido pela sua própria classe. Para declarar uma classe, no código JavaScript, deve-se usar a palavra-chave `class` seguida pelo prefixo `BR` e nome da classe.
- Propriedades de instâncias devem ser definidas dentro do método `construtor` da classe, por padrão definimos as propriedades `name` e `component` que são atribuídas ao instanciar o componente.
- Outro método padrão é o `_setBehavior`, onde devem ser definidos as ações e estados padrão dos componentes internos.

Supondo que, seguindo nosso exemplo, o `BRComponenteNovo` contém um botão de ação clicável, teríamos:

```js
class BRComponenteNovo {
  constructor(name, component) {
    this.name = name
    this.component = component
    this.btn_action = component.querySelector('button.action')
    this._setBehavior()
  }
  _setBehavior() {
    if (this.btn_action) {
      this.btn_action.addEventListener('click', () => {
        this._buttonClick()
      })
    }
  }
  _buttonClick() {
    alert('Botão clicado!')
  }
}
export default BRComponenteNovo
```

Ademais, cria-se uma lista de objetos dessa classe repassando as instâncias dos objetos contidos no código HTML da página e identificados pelo seletor específico (no caso `.br-componente-novo`) que deve ser declarada no arquivo `global-class.js` bem como no código padão do componente, da seguinte forma:

```js
const componenteNovoList = []
for (const brComponenteNovo of window.document.querySelectorAll('.br-componente-novo')) {
  componenteNovoList.push(new BRComponenteNovo('componente-novo', brComponenteNovo))
}
```

#### PUG

```text
govbr-ds-dev-core/
└── src/
    └── components/
        └── componente-novo/
            ├── examples/
            │   └── example-componente.pug
            ├── componente-novo.pug
            └── examples.pug
```

- O arquivo `examples.pug` é a view do componente com os códigos reusáveis
- O arquivo `componente-novo.pug` é onde contém os mixins e códigos
- A pasta examples contém os arquivos dos mixin reusáveis separados

#### SCSS

```text
govbr-ds-dev-core/
└── src/
    ├── components/
    |   └── componente-novo/
    │       └── _componente-novo.scss
    └── partial/
        └── scss/
            ├── _components.scss (incluir o novo componente na lista de componentes)
            └── _mixins.scss (Contem os mixins necessários para o componente)
```

- Dentro de `src/components/componente-novo/` deve ser criado os arquivos `_componente-novo.scss` e `_mixins.scss` contendo os estilos a serem aplicados no componente.
- Atente para a nomenclatura do arquivo que, por padrão do sass, usa o underscore(\_) ou sublinhado, antes do nome do componente.
- Incluir o novo componente na lista de componentes em `src/partial/scss/_components.scss`

---

## Exemplo prático

No exemplo a seguir iremos criar um botão simples. Com as seguintes características:

1. Fundo preto e texto branco
1. Letras maiúsculas
1. Quadrado
1. Tamanho padrão e pequeno
1. Ao clicar é exibida a mensagem: "Botão clicado!"

### Código reusável

Escrever o componente de forma reusável facilita a interação dele com outros componentes ou templates. A ideia é criar um **mixin** para ser reusado quando necessário.

**Mixin** pode ser criado tanto no SASS quanto no Pug.

- Veja a documentação de mixin para Pug em <https://pugjs.org/language/mixins.html>
- Veja a documentação de mixin para SASS em <https://sass-lang.com/documentation/at-rules/mixin>

Crie a pasta de `src/components/simple-button/` dentro dela crie o arquivo **simple-button.pug** com o seguinte código:

```pug
//- src/components/simple-buttom/simple-button.pug
mixin simple-button
  button.br-simple-button(type="button")&attributes(attributes)
    if block
      block
```

Inclua o novo componente na listagem de componentes em `src/partial/pug/default.pug` :

```pug
//- src/pug/layouts/default.pug
block components
  include ../components/simple-button/simple-button
```

### View básica

Dentro de `src/components/simple-buttom/` crie o arquivo **examples.pug** com o seguinte código:

```pug
//- src/components/simple-buttom/simple-button.pug
extends ../../partial/pug/component

append vars
  - var title = "Botão simples"

append content
  +simple-button Botão simples
  +simple-button#botao.py-3 Botão com Id e classes
  +simple-button.py-3()(disabled) Botão desativado
```

Dentro de `src/components/simple-buttom/example` crie o arquivo **simple-button.pug** ,para que gere html sem head, com o seguinte código:

```pug
extends ../../../partial/pug/isolate

block dependencies
  include ../simple-button

block content
  +simple-button
```

### Estilo básico

Dentro de `src/components/simple-button/` crie o arquivo **\_simple-button.scss** e **\_mixins.scss**
No arquivo **\_mixins.scss** o seguinte código:

```scss
/// src/scss/components/simple-button/_simple-button.scss
/// @group simple-button
@mixin simple-button {
  @include simple-button-tokens;
  @include simple-button-default;
  @include simple-button-sizes;
}

@mixin simple-button-tokens {
  --simple-button-background: black;
  --simple-button-radius: 0;
  --simple-button-color: white;
  --simple-button-padding: var(--spacing-scale-2x);
  --simple-button-size: var(--simple-button-medium);
  --simple-button-small: 32px;
  --simple-button-medium: 40px;
  --simple-button-large: 44px;
}

@mixin simple-button-default {
  background: var(--simple-button-background);
  border-radius: var(--simple-button-radius);
  color: var(--simple-button-color);
  padding: calc(var(--simple-button-padding) * 0.5) var(--simple-button-padding);
  text-transform: uppercase;
}

@mixin simple-button-sizes {
  @each $size in small, medium, large {
    &.#{$size} {
      --simple-button-size: var(--simple-button-#{$size});
    }
  }
}
```

No arquivo **\_simple-button.scss** adicionar os seguintes código

```scss
@import 'mixins';

.#{$prefix}simple-button {
  @include simple-button;
}
```

Incluir o novo componente na lista de componentes em `src/partial/scss/_components.scss` :

```scss
// src/components/_components.scss
@import '../components/simple-button/simple-button';
```

Atenção! Da mesma forma como foi feito no arquivo Pug, você poderá criar um mixin SASS para reúso de código, neste caso o arquivo deverá ser criado em `src/partial/scss/mixins` e incluído da lista de mixins em `src/partial/scss/_mixins.scss` .

### Comportamento básico

Dentro de `src/components/componente-novo/` crie o arquivo **simple-button.js** com o seguinte código:

```js
class BRSimpleButton {
  constructor(name, component) {
    this.name = name
    this.component = component
    this._setBehavior()
  }

  _setBehavior() {
    this.component.addEventListener('click', () => {
      this._buttonClick()
    }
  }

  _buttonClick() {
    alert('Botão clicado!')
  }
}
export default BRSimpleButton

```

E no arquivo `global-class.js` criar uma lista de instâncias para o botão:

```js
const simpleButtonsList = [];
for (**const** brSimpleButton of window.document.querySelectorAll(
    ".br-simple-button"
)) {
    simpleButtonsList.push(new BRSimpleButton("simple-button", brSimpleButton));
}
```

no arquivo `design-system/webpack/core.entries.js` deve setar o componente e os exemplos

```js
setComponentPug('simple-button', ['componente-novo-1', 'componente-novo-2'])
```
