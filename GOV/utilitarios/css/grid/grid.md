As classes criadas de acordo com o [Fundamento Sistema de Grid](fundamentos-visuais/grid).

Utilize as classes de Grid quando houver necessidade de organizar seu conteúdo em colunas. Elas servem também para delimitar a largura de um conteúdo de acordo com o breakpoint.

A Grid é formada pelos seguintes elementos:

- Container
- Linha
- Coluna

Usar a Grid de forma errada significa quebra de layout, portanto fique atento!

| Elemento      | Uso correto <i class="text-success fas fa-check">            | Uso errado <i class="text-danger fas fa-times">     |
| ------------- | ------------------------------------------------------------ | --------------------------------------------------- |
| **Container** |                                                              | Container dentro de container                       |
| **Linha**     | Linhas dentro de um container<br>Linhas dentro de uma coluna | Linha fora de um container<br>Linha dentro de linha |
| **Coluna**    | Colunas dentro de uma linha                                  | Coluna fora de uma Linha<br>Coluna dentro de coluna |

<!--
A tabela a seguir mostra a relação de tokens, breakpoints e valor padrão:

| Token                  | Breakpoint                                 | Valor padrão |
| ---------------------- | ------------------------------------------ | ------------ |
| `--grid-breakpoint-xs` | _Smartphone Portrait_                      | 0            |
| `--grid-breakpoint-sm` | _Smartphone Landscape_ / _Tablet Portrait_ | 576px        |
| `--grid-breakpoint-md` | _Tablet Landscape_                         | 992px        |
| `--grid-breakpoint-lg` | _Desktop_                                  | 1280px       |
| `--grid-breakpoint-xl` | TV                                         | 1600px       |
-->

## Container

O container é responsável por deixar seu sistema ou site responsivo de acordo com as mudanças de breakpoint. Ele pode se comportar de forma fixa ou fluida de acordo com a classe usada.

<!--
A tabela a seguir mostra a relação de tokens, breakpoints e valor padrão:

| Token                            | Breakpoint                                 | Valor padrão |
| -------------------------------- | ------------------------------------------ | ------------ |
| `--grid-breakpoint-xs-max-width` | _Smartphone Portrait_                      | 100%         |
| `--grid-breakpoint-sm-max-width` | _Smartphone Landscape_ / _Tablet Portrait_ | 536px        |
| `--grid-breakpoint-md-max-width` | _Tablet Landscape_                         | 952px        |
| `--grid-breakpoint-lg-max-width` | _Desktop_                                  | 1200px       |
| `--grid-breakpoint-xl-max-width` | TV                                         | 1560px       |

Com exceção do token `--grid-breakpoint-xs-max-width`, os tokens de largura máxima pode ser modificados de acordo com o [Fundamento Sistema de Grid](fundamentos-visuais/grid).

O container "fluido" sempre ocupa 100% de tela enquanto que o "fixo" limita a largura de acordo com o breakpoint usado. Em ambos os casos a margem lateral é respeitada:

- **8px**: _Smartphone Portrait_
- **40px**: _Smartphone Landscape_ / _Tablet Portrait_, _Tablet Landscape_, _Desktop_ e TV
-->

A tabela abaixo representa a **largura máxima** para cada classe de container de acordo com os valores padrão.

| Nome do container  | *Smartphone Portrait* | *Smartphone Landscape*<br>*Tablet Portrait* | *Tablet Landscape* | *Desktop* | TV     |
| ------------------ | --------------------- | ------------------------------------------- | ------------------ | --------- | ------ |
| `.container`       | 100%                  | 536px                                       | 912px              | 1200px    | 1520px |
| `.container-sm`    | 100%                  | 536px                                       | 912px              | 1200px    | 1520px |
| `.container-md`    | 100%                  | 100%                                        | 912px              | 1200px    | 1520px |
| `.container-lg`    | 100%                  | 100%                                        | 100%               | 1200px    | 1520px |
| `.container-xl`    | 100%                  | 100%                                        | 100%               | 100%      | 1520px |
| `.container-fluid` | 100%                  | 100%                                        | 100%               | 100%      | 100%   |

**Atenção**! Caso você use o [Template Base](templates/base), não há necessidade de criar um novo container, pois ele já possui um no local destinado ao conteúdo. O mesmo vale para os componentes [Header](components/header) e [Footer](components/footer). O container do Template Base, Header e Footer pode ser alterado.

### Uso correto

Containers separados para cada bloco de conteúdo

```html
<div class="bg-support-01">
  <div class="container-lg">Bloco A</div>
</div>
<div class="bg-support-02">
  <div class="container-lg">Bloco B</div>
</div>
<div class="bg-support-03">
  <div class="container-lg">
    <div>Bloco C</div>
    <div>Bloco D</div>
  </div>
</div>
```

### Uso errado

Container dentro de container

```html
<div class="container-lg">
  Bloco A
  <div class="container">Bloco B</div>
</div>
```

O conteúdo do "Bloco B" terá largura interna diferente do previsto.

---

## Linha

Crie uma linha para dividir seu conteúdo em colunas ou para delimitar um conteúdo ao tamanho de uma coluna.

**Atenção**! Considere que os exemplos a seguir estejam dentro de um container qualquer.

### Uso correto

Dividir conteúdo em colunas

```html
<div class="row">
  <div class="col">Coluna 1</div>
  <div class="col">Coluna 2</div>
</div>
```

Limitar conteúdo dentro de uma coluna

```html
<!-- Input terá a largura de uma coluna 4 -->
<div class="row">
  <div class="col-4">
    <div class="br-input">...</div>
  </div>
</div>
<!-- Input terá a largura total -->
<div class="br-input">...</div>
```

### Evitar

Criar linhas para coluna com largura total

```html
<div class="row">
  <div class="col">Coluna</div>
</div>
<div class="row">
  <div class="col-12">Coluna</div>
</div>
```

Neste caso não há necessidade de criar linha/coluna.

### Uso errado

Linha dentro de linha

```html
<div class="row">
  <div class="row">
    <div class="col">Coluna</div>
    <div class="col">Coluna</div>
  </div>
  <div class="col">Coluna</div>
</div>
```

No exemplo acima o layout ficará quebrado.

Você poderá criar linhas dentro de colunas sem quebra de layout. Segue a correção para o problema acima:

```html
<div class="row">
  <div class="col">
    <div class="row">
      <div class="col">Coluna</div>
      <div class="col">Coluna</div>
    </div>
  </div>
  <div class="col">Coluna</div>
</div>
```

---

## Coluna

A Grid é dividida em 12 colunas ao total.

As colunas possuem largura proporcional ao breakpoint informado. Significa que uma coluna de tamanho 4 terá largura diferente em *Tablet Portrait* e *Desktop*.

Veja no Fundamento [Sistema de Grid](fundamentos-visuais/grid) a quantidade recomendada de colunas para cada breakpoint.

As larguras da coluna podem ser configuradas da seguinte forma:

- Proporcional
- Tamanho predefinido
- Tamanho do conteúdo

A tabela lista a classe e como ela é aplicada em cada breakpoints:

| Nome do container            | *Smartphone Portrait* | *Smartphone Landscape*<br>*Tablet Portrait* | *Tablet Landscape*  | *Desktop*           | TV                  |
| ---------------------------- | --------------------- | ------------------------------------------- | ------------------- | ------------------- | ------------------- |
| `.col`                       | Proporcional          | Proporcional                                | Proporcional        | Proporcional        | Proporcional        |
| `.col-1` até `.col-12`       | Tamanho predefinido   | Tamanho predefinido                         | Tamanho predefinido | Tamanho predefinido | Tamanho predefinido |
| `.col-sm`                    | 100%                  | Proporcional                                | Proporcional        | Proporcional        | Proporcional        |
| `.col-sm-1` até `.col-sm-12` | 100%                  | Tamanho predefinido                         | Tamanho predefinido | Tamanho predefinido | Tamanho predefinido |
| `.col-md`                    | 100%                  | 100%                                        | Proporcional        | Proporcional        | Proporcional        |
| `.col-md-1` até `.col-md-12` | 100%                  | 100%                                        | Tamanho predefinido | Tamanho predefinido | Tamanho predefinido |
| `.col-lg`                    | 100%                  | 100%                                        | 100%                | Proporcional        | Proporcional        |
| `.col-lg-1` até `.col-lg-12` | 100%                  | 100%                                        | 100%                | Tamanho predefinido | Tamanho predefinido |
| `.col-xl`                    | 100%                  | 100%                                        | 100%                | 100%                | Proporcional        |
| `.col-xl-1` até `.col-xl-12` | 100%                  | 100%                                        | 100%                | 100%                | Tamanho predefinido |
| `.col-auto`                  | Tamanho do conteúdo   | Tamanho do conteúdo                         | Tamanho do conteúdo | Tamanho do conteúdo | Tamanho do conteúdo |
| `.col-auto-sm`               | 100%                  | Tamanho do conteúdo                         | Tamanho do conteúdo | Tamanho do conteúdo | Tamanho do conteúdo |
| `.col-auto-md`               | 100%                  | 100%                                        | Tamanho do conteúdo | Tamanho do conteúdo | Tamanho do conteúdo |
| `.col-auto-lg`               | 100%                  | 100%                                        | 100%                | Tamanho do conteúdo | Tamanho do conteúdo |
| `.col-auto-xl`               | 100%                  | 100%                                        | 100%                | 100%                | Tamanho do conteúdo |

Nas 3 configurações é possivel informar o breakpoint da coluna, sendo assim a mesma coluna pode se comportar diferente para cada breakpoint de acordo com a classe informada.

### Proporcional

As colunas ficam divididas proporcionalmente com a quantidade por linha. Caso haja uma 13º coluna ela será deslocada automaticamente para baixo proporcionalmente ao tamanho da "nova linha".

Esta configuração também serve para colunas que precisem usar o epaço restante da linha.

```html
<div class="row">
  <div class="col-sm">Coluna</div>
  <div class="col-sm">Coluna</div>
  <div class="col-sm">Coluna</div>
</div>
```

### Tamanho predefinido

Você poderá especificar um valor de 1 até 12 para a largura da coluna. Este valor é calculado em porcentagem de forma predefinida segundo a fórmula: `(coluna / 12) * 100%`

Os exemplos abaixo produzem o mesmo efeito.

```html
<!-- Tamanhos predefinidos nas 2 colunas -->
<div class="row">
  <div class="col-6 col-sm-4 col-lg-3 col-xl-2">Coluna</div>
  <div class="col-6 col-sm-8 col-lg-9 col-xl-10">Coluna</div>
</div>

<!-- Tamanhos predefinidos somente na primeira coluna -->
<div class="row">
  <div class="col-6 col-sm-4 col-lg-3 col-xl-2">Coluna</div>
  <div class="col">Coluna</div>
</div>
```

### Tamanho do conteúdo

Neste caso a coluna terá a largura no tamanho do conteúdo, ignorando a proporcionalidade.

```html
<div class="row">
  <div class="col-auto col-lg-3">Coluna</div>
</div>
<div class="row">
  <div class="col">Coluna</div>
</div>
```

No exemplo acima a primeira coluna terá sempre a largura total do conteúdo até chegar no breakpoint *Desktop* onde terá o tamanho 3.

A segunda coluna terá a largura "restante" até completar 12.

Caso fosse usado `.col` ao invés de `.col-auto` a primeira coluna teria sempre a mesma largura da segunda coluna.
