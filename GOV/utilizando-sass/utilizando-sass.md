1. Instalar o GOVBR-DS conforme o [como começar](/ds/como-comecar/instalacao)

2. instalar o dart sass com o comando abaixo

   ```text
   npm install sass
   ```

#### Exemplo consumindo todos os estilos do Design System GOV.BR

1. Crie o arquivo `style.scss` com import do `core.scss` conforme o exemplo abaixo, se atentar a localização da pasta `node_modules` que pode mudar conforme a organização do projeto

   ```text
   @import "node_modules/@govbr-ds/core/src/core.scss"
   ```

1. para compilar o arquivo acima basta rodar o seguinte comando:

   ```text
   npx sass style.scss dist/style.css
   ```

#### Para consumir alguns componentes específicos

1. deverá criar o arquivo `style.scss` onde deverá importar o `core-base.scss` que se encontra na pasta **src/partial/scss** e os componentes desejados, que podem ser encontrados na pasta **src/components** como exemplo abaixo:

   ```text
   @import "../node_modules/@govbr-ds/core/src/partial/scss/core-base.scss";
   @import "../node_modules/@govbr-ds/core/src/components/button/button";
   @import "../node_modules/@govbr-ds/core/src/components/avatar/avatar";
   @import "../node_modules/@govbr-ds/core/src/components/card/card";
   ```

1. Para compilar basta rodar o comando abaixo

   ```text
   npx sass style.scss dist/style.css
   ```

#### É possível gerar uma versão compilada dos arquivos scss a partir do diretório de instalação do Design System GOV.BR, conforme exemplos a seguir

1. Compilando todos os estilos do Design System GOV.BR:

   ```text
   npx sass node_modules/@govbr-ds/core/src/govbr-ds dist/exemplo.css
   ```

1. Compilando um estilo de um arquivo específico:

   ```text
   npx sass src/exemplo.scss dist/exemplo.css
   ```

#### Caso seu projeto esteja configurado para o uso do webpack, deverá instalar o webpack5, sass-loader e o css-loader

1. Inclua a configuração abaixo no webpack.config.js , conforme exemplo de configuração abaixo, dependendo da estrutura de pastas do seu projeto, os paths e expressões regulares deverão ser ajustadas.

   ```text
   const path = require('path');
   const MiniCssExtractPlugin = require('mini-css-extract-plugin')
   const projectRootDir = process.cwd()

   module.exports = {
       entry: {exemplo: ['./src/exemplo.scss']},

       module: {
           rules: [

             {
               test: /\.(scss)$/,
               use: [
                   MiniCssExtractPlugin.loader,
                   'css-loader',
                   {
                     loader: 'sass-loader',
                   },
                 ],
             }
           ]
       },
       plugins: [new MiniCssExtractPlugin()],
       output: {
           filename: 'exemplo.css',
       },

   };
   ```
