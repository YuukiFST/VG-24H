> URL oficial (visão geral): https://www.gov.br/ds/fundamentos-visuais/grid?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/fundamentos-visuais/grid?tab=codigos

## Utilitários CSS de Grid

São classes CSS para aplicar o Fundamento Visual *Grid*.

### Como usar

O *Container* ajusta o conteúdo conforme a tela. Use *Row* e *Col* só quando houver necessidade.

Os utilitários de *Grid* são dividos em ***Container***, ***Row*** e ***Col*** (coluna):

### *Container*

*Container* ajusta o conteúdo conforme o tamanho da tela, ou seja, aplica a responsividade. Ele pode ser **fixo** ou **flexível**.

> **Atenção!** *Row* e *Col* só funcionam quando estão dentro do *Container*.

### *Row*

*Row* é um agrupador de colunas. Dependendo da quantidade de colunas por tamanho de tela, *Row* pode ocupar várias linhas.

> Embora *Row* seja feito para dividir em colunas, ele também serve para ajustar um conteúdo à largura de uma coluna.

### *Col*

A Grid é dividida em 12 colunas ao total.

A largura da coluna depende do tamanho da tela, ou seja, uma coluna de tamanho 4 terá largura diferente em *Tablet Portrait* e *Desktop*.

> Veja em [Visão Geral](/ds/fundamentos-visuais/grid?tab=visao-geral#tipos-de-grid) a quantidade recomendada de colunas para cada tela.

Os tipos de colunas são os seguintes:

- **Proporcional**: a coluna se divide proporcionalmente até o limite de 12 por linha;

- **Predefinido**: são 12 tamanhos calculados de acordo com a fórmula `(tamanho / 12) * 100%`;

- **Automático**: a coluna mantém a largura original do conteúdo.

### Larguras

O *container* fixo ou flexível definirá a largura máxima do conteúdo.

A tabela a seguir mostra os tipos de *Containers* e seus comportamentos para cada resolução de tela.

| Classe do *Container* | *Smartphone Portrait* | *Smartphone Landscape*<br>*Tablet Portrait* | *Tablet Landscape* | *Desktop* | TV     |
| --------------------- | --------------------- | ------------------------------------------- | ------------------ | --------- | ------ |
| `.container`          | 100%                  | 536px                                       | 912px              | 1200px    | 1520px |
| `.container-sm`       | 100%                  | 536px                                       | 912px              | 1200px    | 1520px |
| `.container-md`       | 100%                  | 100%                                        | 912px              | 1200px    | 1520px |
| `.container-lg`       | 100%                  | 100%                                        | 100%               | 1200px    | 1520px |
| `.container-xl`       | 100%                  | 100%                                        | 100%               | 100%      | 1520px |
| `.container-fluid`    | 100%                  | 100%                                        | 100%               | 100%      | 100%   |

Nas colunas, o tipo proporcional, predefinido ou automático definirá a largura da coluna.

A tabela a seguir mostra os tipos de colunas e seus comportamentos para cada resolução de tela.

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
