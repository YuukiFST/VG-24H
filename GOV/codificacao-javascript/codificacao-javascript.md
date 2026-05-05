Esse documento descreve o padrão de codificação para a linguagem **JavaScript** utilizado no Design System de Governo.

## ECMAScript

[ECMAScript][1] é uma especificação de linguagem de programação baseada em scripts, padronizada pela [ECMA International][2] na especificação [ECMA-262][3] e [ISO/IEC 16262][4]. A especificação é usada em tecnologias para Internet para a criação de scripts executados no cliente, sendo criada para padronizar a linguagem JavaScript, além permitir outras implementações independentes.

## JavaScript no Design System GOV.BR

O Design System de Governo utiliza o JavaScript na versão 6 (ES6) para a construção do código JavaScript de seus componentes.

> É importante que o programador esteja familiarizado com os conceitos da linguagem JavaScript envolvidos nessa versão, tais como: escopo de variáveis declarados com const, var ou let, higher-order functions, closure, arrow functions, etc, pois o padrão de codificação utiliza-se desses conceitos.

## Padrão de codificação JavaScript

O padrão de codificação JavaScript utiliza-se de um **modelo base para a escrita das classes** relacionadas a um determinado componente ou template e um conjunto de [regras validadas pelo ESLint][5]

### Modelo base para a escrita das classes

O nome das classes começa com o prefixo **BR** em maiúsculo, seguida do nome do componente ou template com a primeira letra em maiúsculo.

```js
class BRInput {}
```

#### Escrita do construtor

O construtor deve receber os parâmetros necessários para o correto funcionamento do componente ou template. Atualmente é adotado duas formas de se declarar os parâmetros do construtor:

- Declarando os parâmetros diretamente
- Declarando os parâmetros dentro de uma notação de objeto, usado para *destructuring*

##### Declarando os parâmetros diretamente

Nesse caso adotou-se dois parâmetros obrigatórios: `name` e `component` e, caso o construtor precise receber mais parâmetros, estes devem ser inseridos após esses dois parâmetros obrigatórios.

- `name`: **string** com o nome do componente ou template na nomenclatura de classe
- `component`: **objeto** contendo a referência ao elemento DOM que representa a raiz do componente ou template.

Esses parâmetros passados no construtor devem ser atribuídos às propriedades do objeto, por meio do **this**, que contém a referência ao objeto instanciado.

```js
class BRInput {
  constructor(name, component) {
    this.name = name
    this.component = component
  }
}
```

##### Declarando os parâmetros para destructuring

Quando houver muitos argumentos opcionais ou uma longa lista de parâmetros, pode-se se utilizar a passagem de argumentos para métodos ou funções por meio do recurso da linguagem chamado *desctructuring assingment* ou *atribuição por desmembramento*.

O *destructuring assignment* é um recurso da liguagem JavaScript que permite atribuir valores às variáveis usando uma sintaxe que imita a sintaxe de array ou objeto literal.

```js
let [x, y] = [1, 2] // É o mesmo que x = 1, y = 2
let { x, y } = { x: 1, y: 2 } // É o mesmo que x = 1, y = 2
```

Esse recurso pode ser usado na declaração de métodos ou funções e na passagem de argumentos para esses métodos ou funções ao invocá-los. Para isso, deve-se declarar o método ou função usando a sintaxe que imita um array ou objeto literal e deve-se invocá-lo passando um objeto, contendo as propriedades declaradas, como argumento. Segue uma parte do código do BRCookiebar com exemplo.

```js
export default class BRCookiebar {
  constructor({ name, component, json, lang, mode = 'default', callback }) {
    this.name = name
    this.component = component
    this.data = new CookiebarData(json, lang)
    this.templates = new CookiebarTemplates(this.data)
    this.mode = mode
    this.callback = callback
    this._setUp()
  }
}
```

#### Instanciação

Para instanciar o objeto, usa-se o **new**, seguido do nome da classe e os argumentos entre parênteses, que serão passados aos parâmetros do construtor.

Contudo, é necessário garantir que replicações do mesmo componente ou template funcionem dentro de seu próprio scopo, ou seja, de forma isolada.

Logo, é necessário "varrer" a página procurando todas as réplicas dos componentes ou templates e, para cada uma delas, instanciar seu respectivo objeto. Mais ainda, é necessário guardar essas referências para poder usá-las depois.

```js
const inputList = []
for (const brInput of window.document.querySelectorAll('.br-input')) {
  inputList.push(new BRInput('br-input', brInput))
}
```

> Esse código de instanciação acima, não faz parte do componente ou template. Ele serve, como a própria descrição diz, para instanciar a classe que representa o componente ou template.

Caso o construtor da classe tenha sido declarado usando-se a sintaxe para *destructuring*, deve-se passar um objeto um objeto contendo as propriedades declaradas. Por exemplo, para instanciar a classe BRCookiebar acima, usa-se:

```js
const cookiebarList = []
for (const brCookiebar of window.document.querySelectorAll('.br-cookiebar')) {
    const params = {
        name: 'br-cookiebar',
        component: brCookiebar,
        lang: 'pt-br',
        mode: 'default',
        json: jsonData,
        callback: () => {},
    }
    cookiebarList.push(new BRCookiebar(params))
```

#### Métodos privados e públicos

A linguagem JavaScript não possui um mecanismo para garantir que um método é de uso privado. Todos os métodos declarados em uma classe é de uso público. Porém, adota-se como boa prática usar o **underline (\_)** no começo do identificador para simbolizar que aquele método é de uso privado. Isso não garante que serão privados, mas é uma prática adotada na linguagem JavaScript.

```js
_changeIcon() {
  ...
}
```

> Para os métodos externos **não usar** o underline (\_)

## Regras Validadas pelo ESLint

As seguintes regras são utilizadas na validação do código JavaScript pelo validador ESLint. Essas regras estão configuradas no arquivo `.eslintrc.json`

## Uso da Ferramenta JSDOC

A documentação do código JavaScript usa a ferramenta [JSDOC 3](https://jsdoc.app/), que é uma API que gera uma documentação em HTML para os códigos JavaScript documentados seguindo uma sintaxe específica no comentário do código.

### Adicionando Comentários de Documentação no Código

Os comentários reconhecidos pela JSDOC devem ser colocados imediatamente antes do código sendo comentado. Eles devem começar com a sequência `/**` para serem reconhecidos pelo analisador (parser) da JSDOC. Comentários começados com uma sequência diferente dessa são ignorados.

A JSDOC possui tags especiais que dão mais informações sobre o que está sendo documentado. A JSDOC usa essas tags para gerar a documentação em HTML e apresentá-la de forma adequada.

```js
/**
 * Represents a book.
 * @constructor
 * @param {string} title - The title of the book.
 * @param {string} author - The author of the book.
 */
function Book(title, author) {}
```

> A lista completa das tags suportadas pode ser encontrada na [home page](https://jsdoc.app/index.html#block-tags) da JSDOC 3.

### Gerando a Documentação JavaScript

A JSDOC 3 gera uma página HTML a partir dos códigos fontes comentados. Por padrão a JSDOC usa um template default para gerar a página HTML, mas esse template pode ser customizado.

#### Rodando o Gerador de Documentação

A documentação é gerada usando-se a seguinte linha de comando

```sh
jsdoc <arquivo.js>
```

Alternativamente, pode-se usar um arquivo de configuração contendo as opções para a execução do programa jsdoc. O DSGOV utiliza um arquivo de configuração chamado `jsdoc.json` e é executado usando o seguinte script no Node:

```sh
npm run docs:js
```

### Regras para possíveis erros

#### [no-console](https://eslint.org/docs/rules/no-console)

Esta regra não permite chamadas para métodos do objeto console, exceto warn e error.

```json
"no-console": ["error", {
  "allow": ["warn", "error"]
}]
```

#### [no-debugger](https://eslint.org/docs/rules/no-debugger)

Esta regra não permite instruções de debugger.

```json
"no-debugger": "error"
```

#### [no-dupe-args](https://eslint.org/docs/rules/no-dupe-args)

Esta regra não permite nomes de parâmetros duplicados em declarações ou expressões de função. Não se aplica a arrow functions ou métodos de classe, porque o parser relata o erro.

```json
"no-dupe-args": "error"
```

#### [no-dupe-else-if](https://eslint.org/docs/rules/no-dupe-else-if)

Esta regra não permite condições duplicadas na mesma cadeia if-else-if.

```json
"no-dupe-else-if": "error"
```

#### [no-dupe-keys](https://eslint.org/docs/rules/no-dupe-keys)

Esta regra não permite keys duplicadas em literais de objeto.

```json
"no-dupe-keys": "error"
```

#### [no-duplicate-case](https://eslint.org/docs/rules/no-duplicate-case)

Esta regra não permite expressões de teste duplicadas nas cláusulas case das instruções do switch.

```json
"no-duplicate-case": "error"
```

#### [no-empty](https://eslint.org/docs/rules/no-empty)

Esta regra não permite instruções de bloco vazias. Essa regra ignora as instruções de bloco que contêm um comentário.

```json
"no-empty": "error"
```

#### [no-ex-assign](https://eslint.org/docs/rules/no-ex-assign)

Esta regra não permite reatribuir exceções nas cláusulas catch.

```json
"no-ex-assign": "error"
```

#### [no-extra-semi](https://eslint.org/docs/rules/no-extra-semi)

Esta regra não permite ponto e vírgula desnecessários.

```json
"no-extra-semi": "error"
```

#### [no-func-assign](https://eslint.org/docs/rules/no-func-assign)

Esta regra não permite reatribuir declarações de função.

```json
"no-func-assign": "error"
```

#### [no-import-assign](https://eslint.org/docs/rules/no-import-assign)

Esta regra alerta para atribuições, incrementos e decrementos de variáveis delacaras no import.

```json
"no-import-assign": "error"
```

#### [no-template-curly-in-string](https://eslint.org/docs/rules/no-template-curly-in-string)

Esta regra tem como objetivo avisar quando uma string regular contiver o que parece ser uma sintaxe de template literal (\${something}) que use "ou' para as aspas.

```json
"no-template-curly-in-string": "error"
```

#### [no-unexpected-multiline](https://eslint.org/docs/rules/no-unexpected-multiline)

Esta regra não permite expressões de múltiplas linhas confusas onde uma nova linha parece estar finalizando uma instrução, mas não está.

```json
"no-unexpected-multiline": "error"
```

#### [no-unreachable](https://eslint.org/docs/rules/no-unreachable)

Essa regra não permite código inacessível após instruções de return, throw, continue e break.

```json
"no-unreachable": "error"
```

#### [no-unsafe-finally](https://eslint.org/docs/rules/no-unsafe-finally)

Essa regra não permite instruções de return, throw, break e continue dentro de blocos finaly. Permite usos indiretos, como nas definições de função ou classe.

```json
"no-unsafe-finally": "error"
```

#### [use-isnan](https://eslint.org/docs/rules/use-isnan)

Esta regra não permite comparações com 'NaN'.

```json
"use-isnan": ["error", {
  "enforceForSwitchCase": true,
  "enforceForIndexOf": true
}]
```

#### [valid-typeof](https://eslint.org/docs/rules/valid-typeof)

Esta regra aplica a comparação de expressões typeof com literais de string válidos.

```json
"valid-typeof": ["error", {
  "requireStringLiterals": true
}]
```

---

### Regras para melhores práticas

#### [block-scoped-var](https://eslint.org/docs/rules/block-scoped-var)

Esta regra visa reduzir o uso de variáveis fora do seu contexto de ligação e emular o escopo de bloco tradicional de outras linguagems. Isso é para ajudar os recém-chegados à linguagem a evitar erros difíceis com o variable hoisting.

```json
"block-scoped-var": "error"
```

#### [class-methods-use-this](https://eslint.org/docs/rules/class-methods-use-this)

Esta regra tem como objetivo sinalizar métodos de classe que não usam this.

```json
"class-methods-use-this": "error"
```

#### [complexity](https://eslint.org/docs/rules/complexity)

Essa regra visa reduzir a complexidade do código limitando a quantidade de complexidade ciclomática permitida em um programa. Como tal, ele avisa quando a complexidade ciclomática cruza o limite configurado (o padrão é 20).

```json
"complexity": ["error", {
  "max": 20
}]
```

#### [default-case](https://eslint.org/docs/rules/default-case)

Esta regra visa exigir o default nas instruções do switch. Opcionalmente, você pode incluir um "// no default" após o último caso, se não houver um caso padrão.

```json
"default-case": ["error", {
  "commentPattern": "^no\\sdefault"
}]
```

#### [default-case-last](https://eslint.org/docs/rules/default-case-last)

Esta regra impõe que as cláusulas default nas instruções do switch sejam as últimas.

```json
"default-case-last": "error"
```

#### [default-param-last](https://eslint.org/docs/rules/default-param-last)

Esta regra impõe que os parâmetros padrão sejam o último dos parâmetros.

```json
"default-param-last": ["error"]
```

#### [dot-location](https://eslint.org/docs/rules/dot-location)

Esta regra visa impor consistência de nova linha em member expressions. Essa regra impede o uso de novas linhas mistas ao redor do ponto em uma member expression.

```json
"dot-location": ["error", "property"]
```

#### [no-alert](https://eslint.org/docs/rules/no-alert)

Essa regra tem como objetivo detectar alert usado como debug ou como elementos de popup visuais que devem ser substituídos por interfaces personalizadas menos invasivas. Como tal, ele avisa quando encontra alerts, prompts e confirms que não estão shadowed.

```json
"no-alert": "error"
```

#### [no-caller](https://eslint.org/docs/rules/no-caller)

Essa regra tem como objetivo desencorajar o uso de código deprecated e subotimizado, proibindo o uso de `arguments.caler` e `arguments.callee`. Como tal, ele avisa quando forem usados.

```json
"no-caller": "error"
```

#### [no-constructor-return](https://eslint.org/docs/rules/no-constructor-return)

Esta regra não permite instruções return no construtor de uma classe. Observe que é permitido return em instruções de controle de fluxo.

```json
"no-constructor-return": "error"
```

#### [no-else-return](https://eslint.org/docs/rules/no-else-return)

Esta regra tem como objetivo destacar um bloco de código desnecessário após um if contendo uma instrução de return. Como tal, ele avisará quando encontrar um else seguindo uma cadeia de ifs, todos eles contendo uma instrução de return.

```json
"no-else-return": ["error", {
  "allowElseIf": true
}]
```

#### [no-empty-function](https://eslint.org/docs/rules/no-empty-function)

Esta regra visa eliminar funções vazias. Uma função não será considerada um problema se contiver um comentário.

```json
"no-empty-function": "error"
```

#### [no-empty-pattern](https://eslint.org/docs/rules/no-empty-pattern)

Essa regra tem como objetivo sinalizar quaisquer padrões vazios em destructuring de objetos e matrizes e, como tal, reportará um problema sempre que um for encontrado.

```json
"no-empty-pattern": "error"
```

#### [no-eq-null](https://eslint.org/docs/rules/no-eq-null)

A regra no-eq-null visa reduzir possíveis erros e comportamentos indesejados, garantindo que as comparações com null correspondam apenas a null e não undefined. Como tal, sinalizará comparações para null ao usar == e !=.

```json
"no-eq-null": "error"
```

#### [no-eval](https://eslint.org/docs/rules/no-eval)

Essa regra visa impedir o código potencialmente perigoso, desnecessário e lento, impedindo o uso da função eval(). Como tal, ele avisa sempre que a função eval() é usada.

```json
"no-eval": ["error", {
  "allowIndirect": false
}]
```

#### [no-extra-label](https://eslint.org/docs/rules/no-extra-label)

Esta regra visa eliminar labels desnecessárias.

```json
"no-extra-label": "error"
```

#### [no-fallthrough](https://eslint.org/docs/rules/no-fallthrough)

Essa regra visa eliminar o fallthrough não intencional de um case para outro no switch. Como tal, sinaliza quaisquer cenários de avanço que não são marcados por um comentário.

```json
"no-fallthrough": ["error", {
  "commentPattern": "break[\\s\\w]*omitted"
}]
```

#### [no-floating-decimal](https://eslint.org/docs/rules/no-floating-decimal)

Essa regra visa eliminar pontos decimais flutuantes e avisa sempre que um valor numérico tem um ponto decimal, mas está faltando um número antes ou depois dele.

```json
"no-floating-decimal": "error"
```

#### [no-global-assign](https://eslint.org/docs/rules/no-global-assign)

Esta regra não permite modificações em variáveis globais de somente leitura.

```json
"no-global-assign": "error"
```

#### [no-implied-eval](https://eslint.org/docs/rules/no-implied-eval)

Esta regra visa eliminar eval() implícita através do uso de setTimeout(), setInterval() ou execScript(). Como tal, ele avisará quando uma das funções for usada com uma string como o primeiro argumento.

```json
"no-implied-eval": "error"
```

#### [no-iterator](https://eslint.org/docs/rules/no-iterator)

Esta regra visa impedir erros que possam surgir ao usar a propriedade `__iterator__`, que não é implementada em vários navegadores. Como tal, ele avisará sempre que encontrar a propriedade `__iterator__`.

```json
"no-iterator": "error"
```

#### [no-lone-blocks](https://eslint.org/docs/rules/no-lone-blocks)

Essa regra visa eliminar blocos desnecessários e potencialmente confusos no nível superior de um *script* ou dentro de outros blocos.

```json
"no-lone-blocks": "error"
```

#### [no-loop-func](https://eslint.org/docs/rules/no-loop-func)

Esta regra não permite qualquer função dentro de um loop que contenha referências não seguras (por exemplo, para variáveis modificadas do escopo externo).

```json
"no-loop-func": "error"
```

#### [no-multi-spaces](https://eslint.org/docs/rules/no-multi-spaces)

Essa regra visa proibir vários espaços em branco em torno de expressões lógicas, expressões condicionais, declarações, elementos de matriz, propriedades de objetos, sequências e parâmetros de função.

```json
"no-multi-spaces": ["error", {
  "ignoreEOLComments": true
}]
```

#### [no-new](https://eslint.org/docs/rules/no-new)

Essa regra visa manter a consistência e a convenção, impedindo chamadas de construtor usando `new` que não atribui o objeto resultante a uma variável.

```json
"no-new": "error"
```

#### [no-param-reassign](https://eslint.org/docs/rules/no-param-reassign)

Esta regra tem como objetivo evitar comportamento não intencional causado por modificação ou reatribuição de parâmetros de função.

```json
"no-param-reassign": ["error", {
  "props": false
}]
```

#### [no-proto](https://eslint.org/docs/rules/no-proto)

A propriedade `__proto__` foi descontinuada a partir do ECMAScript 3.1 e não deve ser usada no código. Use `Object.getPrototypeOf` e `Object.setPrototypeOf`.

```json
"no-proto": "error"
```

#### [no-redeclare](https://eslint.org/docs/rules/no-redeclare)

Esta regra tem como objetivo eliminar variáveis que possuem várias declarações no mesmo escopo.

```json
"no-redeclare": "error"
```

#### [no-self-assign](https://eslint.org/docs/rules/no-self-assign)

Esta regra visa eliminar auto-atribuições.

```json
"no-self-assign": ["error", {"props": true}]
```

#### [no-self-compare](https://eslint.org/docs/rules/no-self-compare)

Comparar uma variável com ela mesma geralmente é um erro, um erro de digitação ou refatoração. É confuso para o leitor e pode potencialmente introduzir um erro de tempo de execução.

```json
"no-self-compare": "error"
```

#### [no-unused-expressions](https://eslint.org/docs/rules/no-unused-expressions)

Esta regra visa eliminar expressões não utilizadas que não afetam o estado do programa.

```json
"no-unused-expressions": ["error", {
  "allowShortCircuit": false,
  "allowTernary": false,
  "allowTaggedTemplates": false
}]
```

#### [no-unused-labels](https://eslint.org/docs/rules/no-unused-labels)

Esta regra visa eliminar labels não utilizadas.

```json
"no-unused-labels": "error"
```

#### [no-useless-concat](https://eslint.org/docs/rules/no-useless-concat)

Esta regra visa sinalizar a concatenação de 2 literais quando eles podem ser combinados em um único literal. Os literais podem ser cadeias de caracteres ou *template literals*.

```json
"no-useless-concat": "error"
```

#### [no-useless-catch](https://eslint.org/docs/rules/no-useless-catch)

Esta regra reporta *catchs* que lançam apenas o erro capturado.

```json
"no-useless-catch": "error"
```

#### [no-useless-escape](https://eslint.org/docs/rules/no-useless-escape)

Esta regra sinaliza escapes que podem ser removidos com segurança sem alterar o comportamento.

```json
"no-useless-escape": "error"
```

#### [no-useless-return](https://eslint.org/docs/rules/no-useless-return)

Esta regra tem como objetivo relatar declarações de retorno redundantes.

```json
"no-useless-return": "error"
```

#### [no-with](https://eslint.org/docs/rules/no-with)

Esta regra não permite *with statements*.

```json
"no-with": "error"
```

#### [vars-on-top](https://eslint.org/docs/rules/vars-on-top)

Esta regra visa manter todas as declarações de variáveis nas principais linhas de instruções. Permitir múltiplas declarações ajuda a promover a manutenção e, portanto, é permitido.

```json
"vars-on-top": "error"
```

---

### Regras para variáveis

#### [no-delete-var](https://eslint.org/docs/rules/no-delete-var)

Esta regra não permite o uso do operador delete em variáveis.

```json
"no-delete-var": "error"
```

#### [no-label-var](https://eslint.org/docs/rules/no-label-var)

Essa regra visa criar um código mais claro, proibindo a prática incorreta de criar uma label que compartilhe um nome com uma variável que esteja no escopo.

```json
"no-label-var": "error"
```

#### [no-shadow-restricted-names](https://eslint.org/docs/rules/no-shadow-restricted-names)

Definir restricted words para significar outra coisa pode ter consequências não intencionais e confundir outras pessoas que leem o código.

```json
"no-shadow-restricted-names": "error"
```

#### [no-undef-init](https://eslint.org/docs/rules/no-undef-init)

Esta regra visa eliminar declarações de variáveis que são inicializadas com undefined.

```json
"no-undef-init": "error"
```

#### [no-undefined](https://eslint.org/docs/rules/no-undefined)

Esta regra tem como objetivo eliminar o uso de undefined e, como tal, gera um aviso sempre que é usado.

```json
"no-undefined": "error"
```

#### [no-use-before-define](https://eslint.org/docs/rules/no-use-before-define)

Esta regra avisará quando encontrar uma referência a um identificador que ainda não foi declarado.

```json
"no-use-before-define": ["error", {
  "functions": false,
  "classes": true,
  "variables": true
}]
```

---

### Regras para estilo

#### [array-bracket-spacing](https://eslint.org/docs/rules/array-bracket-spacing)

Essa regra impõe espaçamento consistente entre colchetes da matriz.

```json
"array-bracket-spacing": ["error", "never"]
```

#### [block-spacing](https://eslint.org/docs/rules/block-spacing)

Essa regra aplica espaçamento consistente dentro de um token de abertura de bloco e o próximo token na mesma linha. Essa regra também aplica espaçamento consistente dentro de um token de fechamento de bloco e um token anterior na mesma linha.

```json
"block-spacing": "error"
```

#### [brace-style](https://eslint.org/docs/rules/brace-style)

Esta regra aplica estilo de chaves consistente para blocos.

```json
"brace-style": ["error", "1tbs", {
  "allowSingleLine": false
}]
```

#### [camelcase](https://eslint.org/docs/rules/camelcase)

Esta regra procura por underscores (\_) localizados no código-fonte. Ele ignora os underscores iniciais e finais e apenas verifica aqueles no meio do nome de uma variável. Se o ESLint decidir que a variável é uma constante (todas em maiúsculas), nenhum aviso será lançado. Caso contrário, um aviso será lançado. Esta regra sinaliza apenas definições e atribuições, mas não chamadas de função. No caso de instruções de import do ES6, esta regra visa apenas o nome da variável que será importada para o escopo do módulo local.

```json
"camelcase": ["error", {
  "properties": "always",
  "ignoreDestructuring": false,
  "ignoreImports": false
}]
```

#### [comma-dangle](https://eslint.org/docs/rules/comma-dangle)

Essa regra impõe o uso consistente de vírgulas finais nos literais de objeto e matriz.

```json
"comma-dangle": ["error", "never"]
```

#### [comma-spacing](https://eslint.org/docs/rules/comma-spacing)

Essa regra aplica espaçamento consistente antes e depois de vírgulas nas declarações de variáveis, literais de matriz, literais de objeto, parâmetros de função e seqüências.

```json
"comma-spacing": ["error", {
  "before": false,
  "after": true
}]
```

#### [comma-style](https://eslint.org/docs/rules/comma-style)

Essa regra aplica estilo de vírgula consistente em literais de matriz, literais de objeto e declarações de variáveis.

```json
"comma-style": ["error", "last"]
```

#### [computed-property-spacing](https://eslint.org/docs/rules/computed-property-spacing)

Esta regra impõe espaçamento consistente entre colchetes de propriedades computadas.

```json
"computed-property-spacing": ["error", "never", {
  "enforceForClassMembers": true
}]
```

#### [eol-last](https://eslint.org/docs/rules/eol-last)

Esta regra exige pelo menos uma nova linha (ou ausência dela) no final de arquivos não vazios.

```json
"eol-last": ["error", "always"]
```

#### [func-call-spacing](https://eslint.org/docs/rules/func-call-spacing)

Essa regra não permite espaços entre o nome da função e o parêntese de abertura que a chama.

```json
"func-call-spacing": ["error", "never"]
```

#### [implicit-arrow-linebreak](https://eslint.org/docs/rules/implicit-arrow-linebreak)

Esta regra visa impor um local consistente para uma *arrow function* que contém um returno implícito.

```json
"implicit-arrow-linebreak": ["error", "beside"]
```

#### [indent](https://eslint.org/docs/rules/indent)

Esta regra impõe um estilo de identação consistente.

```json
"indent": ["error", 2, {
  "SwitchCase": 1,
  "VariableDeclarator": "first",
  "outerIIFEBody": "off",
  "MemberExpression": 1,
  "FunctionDeclaration": {
    "parameters": 1,
    "body": 1
  },
  "FunctionExpression": {
    "parameters": 1,
    "body": 1
  },
  "CallExpression": {
    "arguments": 1
  },
  "ArrayExpression": 1,
  "ObjectExpression": 1,
  "ImportDeclaration": 1,
  "flatTernaryExpressions": false,
  "offsetTernaryExpressions": false,
  "ignoreComments": false
}]
```

#### [key-spacing](https://eslint.org/docs/rules/key-spacing)

Esta regra impõe espaçamento consistente entre chaves e valores nas propriedades literais do objeto. No caso de linhas longas, é aceitável adicionar uma nova linha sempre que um espaço em branco for permitido.

```json
"key-spacing": ["error", {
  "beforeColon": false,
  "afterColon": true,
  "mode": "strict"
}]
```

#### [keyword-spacing](https://eslint.org/docs/rules/keyword-spacing)

Essa regra aplica espaçamento consistente em torno de palavras-chave e tokens semelhantes a palavras-chave: as (em declarações de módulo), *assync* (de funções assíncronas), *await* (de expressões de espera), *break, case, catch, class, const, continue, debugger, default, delete, do, else, export, extends, finally, for, from* (nas declarações do módulo), *function, get* (de getters), *if, import, in, instanceof, let, new, of* (de sentenças for-of), *return, set* (de setters), *static, super, switch, this, throw, try, typeof, var, void, while, with e yield*. Essa regra foi projetada com cuidado para não entrar em conflito com outras regras de espaçamento: não se aplica ao espaçamento onde outras regras relatam problemas.

```json
"keyword-spacing": ["error", {
  "before": true,
  "after": true
}]
```

#### [lines-between-class-members](https://eslint.org/docs/rules/lines-between-class-members)

Esta regra melhora a legibilidade exigindo linhas entre os membros da classe. Ele não verifica linhas vazias antes do primeiro membro e depois do último membro, já que isso já é resolvido pela regra de espaços entre os blocos.

```json
"ines-between-class-members": ["error", "always", {
  "exceptAfterSingleLine": false
}]
```

#### [new-parens](https://eslint.org/docs/rules/new-parens)

Essa regra pode impõe parênteses ao chamar um construtor sem argumentos usando *new*.

```json
"new-parens": ["error", "always"]
```

#### [no-lonely-if](https://eslint.org/docs/rules/no-lonely-if)

Esta regra não permite if como a única declaração em blocos else.

```json
"no-lonely-if": "error"
```

#### [no-mixed-spaces-and-tabs](https://eslint.org/docs/rules/no-mixed-spaces-and-tabs)

Esta regra não permite espaços e tabulações misturados para recuo.

```json
"no-mixed-spaces-and-tabs": "error"
```

#### [no-multiple-empty-lines](https://eslint.org/docs/rules/no-multiple-empty-lines)

Esta regra visa reduzir a rolagem necessária ao ler seu código. Ele avisará quando a quantidade máxima de linhas vazias for excedida no final do arquivo.

```json
"no-multiple-empty-lines": ["error", {
  "maxEOF": 1
}]
```

#### [no-tabs](https://eslint.org/docs/rules/no-tabs)

Esta regra procura tabs em qualquer lugar dentro de um arquivo: código, comentários ou qualquer outra coisa.

```json
"no-tabs": ["error", {
  "allowIndentationTabs": false
}]
```

#### [no-trailing-spaces](https://eslint.org/docs/rules/no-trailing-spaces)

Esta regra não permite espaços em branco à direita (espaços, guias e outros caracteres de espaço em branco Unicode) no final das linhas.

```json
"no-trailing-spaces": ["error", {
  "skipBlankLines": false,
  "ignoreComments": true
}]
```

#### [no-whitespace-before-property](https://eslint.org/docs/rules/no-whitespace-before-property)

Essa regra não permite espaços em branco ao redor do ponto ou antes do colchete de abertura antes das propriedades dos objetos se eles estiverem na mesma linha. Essa regra permite espaços em branco quando o objeto e a propriedade estão em linhas separadas, pois é comum adicionar novas linhas a cadeias mais longas de propriedades

```json
"no-whitespace-before-property": "error"
```

#### [object-curly-spacing](https://eslint.org/docs/rules/object-curly-spacing)

Esta regra impõe espaçamento consistente entre chaves de literais de objetos, atribuições de destructuring e especificadores de importação / exportação.

```json
"object-curly-spacing": ["error", "never", {
  "arraysInObjects": false,
  "objectsInObjects": false
}]
```

#### [operator-assignment](https://eslint.org/docs/rules/operator-assignment)

Esta regra requer ou desabilita a abreviação do operador de atribuição, sempre que possível.

```json
"operator-assignment": ["error", "always"]
```

#### [operator-linebreak](https://eslint.org/docs/rules/operator-linebreak)

Esta regra impõe um estilo consistente de quebra de linha para os operadores.

```json
"operator-linebreak": ["error", "after"]
```

#### [padded-blocks](https://eslint.org/docs/rules/padded-blocks)

Esta regra aplica uso de linha vazia consistente dentro de blocos.

```json
"padded-blocks": ["error", {
  "blocks": "never",
  "classes": "always",
  "switches": "never",
  "allowSingleLineBlocks": false
}]
```

#### [semi](https://eslint.org/docs/rules/semi)

Esta regra impõe o uso consistente de ponto e vírgula.

```json
"semi": ["error", "always", {
  "omitLastInOneLineBlock": false
}]
```

#### [semi-spacing](https://eslint.org/docs/rules/semi-spacing)

Essa regra visa impor o espaçamento em torno de um ponto e vírgula. Essa regra impede o uso de espaços antes de um ponto e vírgula nas expressões.

```json
"semi-spacing": ["error", {
  "before": false,
  "after": true
}]
```

#### [semi-style](https://eslint.org/docs/rules/semi-style)

Esta regra reporta terminadores de linha em ponto e vírgula.

```json
"semi-style": ["error", "last"],
```

#### [sort-keys](https://eslint.org/docs/rules/sort-keys)

Essa regra checa todas as definições de propriedades das expressões de objetos e verifica se todas elas estão ordenadas alfabeticamente.

```json
"sort-keys": ["error", "asc", {
  "caseSensitive": true,
  "natural": true,
  "minKeys": 2
}]
```

#### [space-before-blocks](https://eslint.org/docs/rules/space-before-blocks)

Esta regra reforçará a consistência do espaçamento antes dos blocos. É aplicado apenas em blocos que não começam em uma nova linha.

```json
"space-before-blocks": ["error", "always"]
```

#### [space-before-function-paren](https://eslint.org/docs/rules/space-before-function-paren)

Essa regra visa impor um espaçamento consistente antes dos parênteses da função e, como tal, avisa sempre que o espaço em branco não corresponder às preferências especificadas.

```json
"space-before-function-paren": ["error", {
  "anonymous": "always",
  "named": "never",
  "asyncArrow": "always"
}]
```

#### [space-in-parens](https://eslint.org/docs/rules/space-in-parens)

Essa regra aplicará espaçamento consistente diretamente entre parênteses, impedindo ou exigindo um ou mais espaços à direita de ( e à esquerda de ).

```json
"space-in-parens": ["error", "never"]
```

#### [space-infix-ops](https://eslint.org/docs/rules/space-infix-ops)

Essa regra visa garantir a existência de espaços ao redor dos operadores infixos.

```json
"space-infix-ops": ["error", {
  "int32Hint": false
}]
```

#### [space-unary-ops](https://eslint.org/docs/rules/space-unary-ops)

Esta regra impõe consistência em relação aos espaços antes de depois de operadores unários, tanto operadores com palavras ou com símbolos.

```json
"space-unary-ops": ["error", {
  "words": true,
  "nonwords": false
}]
```

#### [switch-colon-spacing](https://eslint.org/docs/rules/switch-colon-spacing)

Essa regra controla o espaçamento entre os dois pontos dos cases instruções de *switch*. Esta regra verifica apenas se os tokens consecutivos existem na mesma linha.

```json
"switch-colon-spacing": ["error", {
  "after": true,
  "before": false
}]
```

---

### Regra relacionadas ao ECMAScript 6

#### [arrow-body-style](https://eslint.org/docs/rules/arrow-body-style)

Esta regra pode impor ou proibir o uso de chaves ao redor do corpo da *arrow function*.

```json
"arrow-body-style": ["error", "as-needed", {
  "requireReturnForObjectLiteral": false
}]
```

#### [arrow-parens](https://eslint.org/docs/rules/arrow-parens)

Esta regra impõe o uso consistente de parênteses nas *arrow functions*.

```json
"arrow-parens": ["error", "always"]
```

#### [arrow-spacing](https://eslint.org/docs/rules/arrow-spacing)

Esta regra normaliza o estilo do espaçamento antes/depois da seta de uma *arrow function* (=>).

```json
"arrow-spacing": ["error", {
  "before": true,
  "after": true
}]
```

#### [constructor-super](https://eslint.org/docs/rules/constructor-super)

Esta regra tem como objetivo sinalizar chamadas *super()* inválidas/ausentes.

```json
"constructor-super": "error"
```

#### [no-class-assign](https://eslint.org/docs/rules/no-class-assign)

Esta regra tem como objetivo sinalizar variáveis modificadoras de declarações de classe.

```json
"no-class-assign": "error"
```

#### [no-confusing-arrow](https://eslint.org/docs/rules/no-confusing-arrow)

Esta regra adverte contra o uso da sintaxe da *arrow function* em locais onde ela pode ser confundida com um operador de comparação.

```json
"no-confusing-arrow": ["error", {
  "allowParens": true
}]
```

#### [no-const-assign](https://eslint.org/docs/rules/no-const-assign)

Esta regra tem como objetivo sinalizar a modificação de variáveis declaradas usando a palavra-chave *const*.

```json
"no-const-assign": "error"
```

#### [no-dupe-class-members](https://eslint.org/docs/rules/no-dupe-class-members)

Esta regra tem como objetivo sinalizar o uso de nomes duplicados nas classes.

```json
"no-dupe-class-members": "error"
```

#### [no-duplicate-imports](https://eslint.org/docs/rules/no-duplicate-imports)

Esta regra exige que todas as importações de um único módulo existam em uma única instrução de importação.

```json
"no-duplicate-imports": ["error", {
  "includeExports": true
}]
```

#### [no-this-before-super](https://eslint.org/docs/rules/no-this-before-super)

Esta regra tem como objetivo sinalizar as palavras-chave *this/super* antes de chamadas a *super()*.

```json
"no-this-before-super": "error"
```

#### [no-useless-computed-key](https://eslint.org/docs/rules/no-useless-computed-key)

Esta regra não permite o uso desnecessário de *property keys* computadas.

```json
"no-useless-computed-key": ["error", {
  "enforceForClassMembers": true
}]
```

#### [no-useless-constructor](https://eslint.org/docs/rules/no-useless-constructor)

Essa regra sinaliza construtores de classe que podem ser removidos com segurança sem alterar o funcionamento da classe.

```json
"no-useless-constructor": "error"
```

#### [no-useless-rename](https://eslint.org/docs/rules/no-useless-rename)

Essa regra não permite renomear atribuições de *import*, *export* e *destructuring* para o mesmo nome.

```json
"no-useless-rename": ["error", {
    "ignoreDestructuring": false,
    "ignoreImport": false,
    "ignoreExport": false
}]
```

#### [prefer-arrow-callback](https://eslint.org/docs/rules/prefer-arrow-callback)

Esta regra localiza *function expressions* usadas como retornos de chamada ou argumentos de função. Um erro será produzido para qualquer um que possa ser substituído por uma *arrow function* sem alterar o resultado.

```json
"prefer-arrow-callback": [ "error", {
  "allowNamedFunctions": false,
  "allowUnboundThis": true
}]
```

#### [no-var](https://eslint.org/docs/rules/no-var)

Essa regra visa desestimular o uso de var e incentivar o uso de *const* ou *let*.

```json
"no-var": "error"
```

#### [prefer-const](https://eslint.org/docs/rules/prefer-const)

Essa regra tem como objetivo sinalizar variáveis declaradas usando a palavra-chave *let*, mas nunca reatribuídas após a atribuição inicial.

```json
"prefer-const": ["error", {
  "destructuring": "any",
  "ignoreReadBeforeAssign": false
}]
```

#### [prefer-destructuring](https://eslint.org/docs/rules/prefer-destructuring)

Esta regra impõe o uso de *destructuring* em vez de acessar uma propriedade por meio de uma *member expression*.

```json
"prefer-destructuring": ["error", {
  "VariableDeclarator": {
    "array": true,
    "object": true
  },
  "AssignmentExpression": {
    "array": true,
    "object": true
  }
}, {
  "enforceForRenamedProperties": false
}]
```

#### [prefer-rest-params](https://eslint.org/docs/rules/prefer-rest-params)

Esta regra tem como objetivo sinalizar o uso de variáveis de argumentos.

```json
"prefer-rest-params": "error"
```

#### [prefer-spread](https://eslint.org/docs/rules/prefer-spread)

Esta regra tem como objetivo sinalizar o uso de *Function.prototype.apply()* em situações em que a sintaxe de propagação poderia ser usada.

```json
"prefer-spread": "error"
```

#### [prefer-template](https://eslint.org/docs/rules/prefer-template)

Essa regra tem como objetivo sinalizar o uso do operadores + com string. No caso ela está impedindo o uso do operador + para concatenação, obrigando o uso de template literals.

```json
"prefer-template": "error"
```

#### [rest-spread-spacing](https://eslint.org/docs/rules/rest-spread-spacing)

Esta regra visa impor um espaçamento consistente entre operadores de *rest* e *spread* e suas expressões.

```json
"rest-spread-spacing": ["error", "never"]
```

#### [sort-imports](https://eslint.org/docs/rules/sort-imports)

Esta regra verifica se todas as importações são classificadas em ordem alfabética tanto pelo nome do módulo quanto pelos seus membros declarados. Ela está tratando "case sensitive" e impõe uma ordem para a importação dos membros, conforme especificado abaixo.

```json
"sort-imports": ["error", {
  "ignoreCase": false,
  "ignoreDeclarationSort": false,
  "ignoreMemberSort": false,
  "memberSyntaxSortOrder": ["none", "all", "multiple", "single"]
}]
```

#### [template-curly-spacing](https://eslint.org/docs/rules/template-curly-spacing)

Esta regra visa manter a consistência em torno do espaçamento dentro das *template literals*

```json
"template-curly-spacing": ["error", "never"]
```

## Referências

- [ECMAScript - WikipédiA][1]
- [ECMA Internacional][2]
- [ECMA-262][3]
- [ISO/IEC 16262][4]
- [ESLint Rules][5]

[1]: https://pt.wikipedia.org/wiki/ECMAScript
[2]: http://www.ecma-international.org/
[3]: http://www.ecma-international.org/publications/standards/Ecma-262.htm
[4]: https://www.iso.org/standard/55755.html
[5]: https://eslint.org/docs/rules/
