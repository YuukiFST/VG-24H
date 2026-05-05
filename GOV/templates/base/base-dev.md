## Como usar

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    ...
  </head>
  <body>
    <div class="template-base">
      <!-- Atalhos de Teclado aqui -->
      <nav id="skip-links">...</nav>
      <!-- Header aqui -->
      <header class="br-header" id="header" data-sticky>...</header>
      <!-- Área de conteúdo -->
      <main id="main" class="d-flex flex-fill">
        <!-- Define a largura da página -->
        <div class="container-lg d-flex">
          <div class="row">
            <!-- Menu aqui -->
            <div class="br-menu pt-md-3" id="main-navigation">...</div>
            <!-- Coluna do conteúdo aqui -->
            <div class="col pt-3 pb-5">
              <!-- Breadcrumbs aqui -->
              <div class="br-breadcrumb">...</div>
              <!-- Conteúdo Principal aqui -->
              <div id="main-content" class="main-content pl-sm-3">...</div>
            </div>
          </div>
        </div>
      </main>
      <!-- Footer aqui -->
      <footer id="footer" class="br-footer">...</footer>
    </div>
  </body>
</html>
```

> **Atenção**! A classe `template-base` aplica os estilos do Template. Ela pode ser usada dentro de algum *wrapper* (como no exemplo acima) ou dentro da tag `<body>`.

### Atalhos de Teclado

Os valores usados em `href` nos Atalhos de teclado precisam apontar para Ids existentes na página. Ajuste de acordo com a sua necessidade.

```html
<div class="skip-links" aria-label="Acesso rápido">
  <a accesskey="1" href="#main-content"> Ir para o Conteúdo<strong class="accesskey">1</strong> </a>
  <a accesskey="2" href="#navigation"> Ir para para Navegação<strong class="accesskey">2</strong> </a>
  <a accesskey="3" href="#main-searchbox"> Ir para para Busca<strong class="accesskey">3</strong> </a>
</div>
```

### Versão com Largura Fluida

A classe `container-lg` força a **Largura Fixa** no *breakpoint desktop*. Altere essa classe para `container-fluid` para usar a **Largura Fluida**. Veja onde é usada:

- Dentro do componente **Header**
- Dentro do bloco **&lt;main&gt;**
- Dentro do componente **Footer**

### Versão com Menu empurrando conteúdo

O template é compatível com as versões de Menu Principal Flutuante (Offcanvas) e Menu Principal deslocando a página (Push).

Adicione a classe `push` ao componente Menu para este efeito. Veja mais informações na [documentação do componente Menu](/ds/components/menu).

> **Atenção**! A condição obrigatória é que ele seja *simbling* imediato da coluna de conteúdo, caso contrário a versão push não irá funcionar.
