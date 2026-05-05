Sugerimos a leitura dos [Princípios do Design System](/ds/introducao/principios), eles são a base para construção de todos os artefatos disponibilizados e devem ser aplicados também aos produtos que adotem o Padrão Digital de Governo.

#### Designer

Se você é um designer e está começando a adotar o Design System, indicamos a leitura dos [Fundamentos Visuais](/ds/fundamentos-visuais/cores). Eles auxiliam na tomada de decisões, melhoram a assertividade de seu produto e garante que a solução criada esteja aderente aos padrões existentes.

Disponibilizamos alguns materiais para ajudar a projetar sua interface:

[Downloads](/ds/downloads/assets)

Caso tenha dúvida em como aplicar os padrões a um serviço, temos alguns protótipos já aderentes, que podem ser utilizados como referência ou mesmo não ter que iniciar seu trabalho do zero. Dessa forma, você poderá direcionar seu esforço para estratégias de negócio e/ou ux. Confira na área de downloads na [**aba Modelos**](/ds/downloads/assets).

<!-- Temos uma novidade que acabamos de disponibilizar para download: Protótipos de um caso de uso. Neles exemplificamos como podem ser aplicados os padrões do design system em soluções web, mobile responsivo e aplicativos nativos IOS e Android sem ferir os padrões de cada plataforma, para que entendam as diferenças entre as aplicações. [Confira na área de downloads na **aba Designer**](/ds/downloads/assets). -->

Para saber mais sobre como utilizar os UIKITs, acesse [**Prototipando com o Design System GOV.BR**](/ds/como-comecar/prototipando)

## Instalação

### Requisitos

O projeto requer a versão mínima do [node](https://nodejs.org/) >= v18.13.0

Serão criados automaticamente os seguintes arquivos em seu projeto:

- **package.json**: configurações do seu projeto
- **node_modules/@govbr-ds/core**: pasta com os módulos necessários para o funcionamento do Design System

### Instalação com npm

**Confira sempre a versão referência ao baixar o pacote @govbr-ds/core**.

1. Execute o comando **npm install @govbr-ds/core**, exemplo:

   ```bash
   npm install @govbr-ds/core
   ```

## Template Inicial

A seguir temos um exemplo de um template inicial para utilização do Design System GOV.BR. Copie o template para um arquivo html e confira se os caminhos dos arquivos **rawline.css** e **core.min.css** estão corretos. Antes de **`</body>`** temos a chamada para o arquivo **core.min.js**, confira se o caminho está correto de acordo com as pastas do seu projeto.

```html
<!doctype html>
<html lang="pt-br">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta http-equiv="X-UA-Compatible" content="ie=edge" />
    <!-- Font Rawline-->
    <link
      rel="stylesheet"
      href="https://cdngovbr-ds.estaleiro.serpro.gov.br/design-system/fonts/rawline/css/rawline.css"
    />
    <!-- Font Raleway-->
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Raleway:300,400,500,600,700,800,900&amp;display=swap"
    />
    <!-- Design System GOV.BR CSS-->
    <link rel="stylesheet" href="node_modules/@govbr-ds/core/dist/core.min.css" />
    <!-- Fontawesome-->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.11.2/css/all.min.css" />
    <title>Padrão Digital de Governo</title>
  </head>

  <body>
    <!-- Conteúdo-->

    <!-- Scripts de componentes -->
    <script type="module" src="<node_modules></node_modules>/@govbr-ds/core/dist/core.min.js"></script>
  </body>
</html>
```

**core.js** deve ser importado como módulo. Não são criadas instâncias para componentes. Procure criar e referenciar instâncias para utilização na DOM. Esse procedimento não é necessário se utilizar babel ou webpack. Nesse caso, é possível ser importado diretamente do seu script.

> **Atenção!** Certifique-se que as referências ao `css` e `js` estejam corretas e inseridas devidamentes na pasta do projeto, caso contrário ocorrerá quebra no layout. Muitas vezes, em ambiente de desenvolvimento, pode não haver os arquivos minificados, ou seja, com o posfixo `.min`.

## Versão "lite" da folha de estilo

Você poderá usar uma versão "lite" do CSS no lugar da versão completa. No código usado em Template Inicial basta trocar a linha de carregamento do Design System GOV.BR pelo exemplo a seguir:

```html
<!-- Design System GOV.BR CSS-->
<link rel="stylesheet" href="node_modules\@govbr-ds\core\dist\core-lite.css" />
```

Visite [Design System GOV.BR lite](/ds/como-comecar/versao-lite) para saber as diferenças.

## Template Base

Um bom ponto de partida para usar o Design System GOV.BR é usar um template já com elementos básicos estruturantes da página como Cabeçalho, Menu e Rodapé. [Visite o Template Base](/ds/templates/base) na visão **Desenvolvedor** para acessar o código de referência.

## Servidor CDN

Em **Template Inicial** temos uma importação do arquivo **rawline.css** via CDN:

```html
<link rel="stylesheet" href="https://cdngovbr-ds.estaleiro.serpro.gov.br/design-system/fonts/rawline/css/rawline.css" />
```

<div class="br-message warning" role="alert">
    <div class="icon" aria-label="Componente Obsoleto">
        <i class="fas fa-exclamation-triangle fa-lg" aria-hidden="true"></i>
    </div>
    <div class="content">
        <p><strong>No momento o Servidor CDN possui capacidade suficiente para suprir apenas o desenvolvimento do projeto, não possuindo garantia de estabilidade suficiente para projetos em produção.</strong></p>
        <p></p>
    </div>
</div>

Para ambiente em produção:

- Faça o [download dos Assets](/ds/downloads/assets) Na Aba **Desenvolvedor > Assets** para usar os assets de fonte e imagens em produção. Ele está disponível na seção Downloads
- Troque as referências de CDN para os arquivos locais de CSS e JS

## Documentação

Para informações mais detalhadas sobre [Cores](/ds/fundamentos-visuais/cores), [Tipografia](/ds/fundamentos-visuais/tipografia), etc acesse o item **Fundamentos Visuais** na navegação principal.

Para uso dos estilos ou criação de novos componentes acesse o item **Guias** na navegação principal:

- No menu **Utilitários CSS** há utilitários para não precisar reescrever CSS em seu código
- Em [Construção de Componentes](/ds/guias/construcao-de-componentes) é apresentado um passo a passo de como criar um componente.

## Componentes

Acesse a seção **Componentes** no menu principal e veja a lista de componentes disponíveis.

Cada componente possui sua documentação, código fonte e preview.

### Exemplo de uso da instância do componente

```javascript
const breadcrumbList = []
for (const brBreadcrumb of window.document.querySelectorAll('.br-breadcrumb')) {
  breadcrumbList.push(new core.BRBreadcrumb('br-breadcrumb', brBreadcrumb))
}
```

## Utilitários JS

São classes JavaScript para auxiliar os componentes. Para seu uso, deve-se importar a classe js correspondente ao utilitário que fica na pasta **@govbr-ds/dist/partial/behavior**, e instanciá-la no seu script, com os atributos de configuração, conforme exemplo abaixo:

### Exemplo de uso de utilitário

```javascript
element = window.document.querySelectorAll('.collapse-example')
element.querySelectorAll('[data-toggle="accordion"]').forEach((trigger) => {
  const config = {
    iconToHide: 'fa-chevron-up',
    iconToShow: 'fa-chevron-down',
    trigger,
    useIcons: true,
  }
  const accordion = new core.Accordion(config)
  accordion.setBehavior()
})
```

> Nesse exemplo precisa indicar **element** como elemento dom
> Os utilitários não são automaticamente inicializados precisando de uma classe JavaScript para inicializá-los

Acesse a seção **Utilitários** no menu principal e veja a lista de componentes disponíveis.

## Release Notes

Ao final de cada release, disponibilizamos um resumo do que foi alterado desde a última release.
