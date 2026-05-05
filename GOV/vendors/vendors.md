Os vendors podem ser carregados de duas formas:

- por Pacote NPM
- por CDN

Em ambientes de produção é recomendado carregar por pacote npm enquanto que em ambientes de desenvolvimento o carregamento por cdn é suficiente.

## Pacote NPM

Para mais informação sobre como criar seu projeto usando pacotes NPM acesse [Como Começar](/ds/como-comecar/instalacao).

```bash
npm i nome-do-vendor --save
```

## CDN

Alguns vendors já possuem seus códigos disponíveis em CDN, neste caso basta seguir as instruções do próprio vendor.

Nos casos em que o próprio vendor nao informe um endereço de CDN é possível que ele esteja disponível em algum dos listados abaixo:

- [CDNJS](https://cdnjs.com/)
- [JSDelivr](https://www.jsdelivr.com/)

## Adicionar no template

Os códigos devem ser carregados sempre antes do Design System GOV.BR.

```html
<!doctype html>
<html lang="pt-br">
  <head>
    <!-- CSS do vendor -->
    <link rel="stylesheet" href="path/vendor.min.css" />
    <!-- Design System GOV.BR CSS -->
    <link rel="stylesheet" href="path/core.min.css" />
  </head>
  <body>
    <!-- Scripts do vendor -->
    <script src="path/.min.js"></script>
    <!-- Design System GOV.BR JS -->
    <script src="path/core.min.js"></script>
  </body>
</html>
```
