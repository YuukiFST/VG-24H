> URL oficial (visão geral): https://www.gov.br/ds/components/tag?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/tag?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão | Descrição               |
| -------- | ------ | ------------ | ----------------------- |
| class    | string | **br-tag**   | container do componente |

### Propriedades adicionais

| Atributo | Tipo   | Valor Padrão                       | Descrição                    |
| -------- | ------ | ---------------------------------- | ---------------------------- |
| class    | string | **interaction**                    | Tag de Interação Dispensável |
| class    | string | **interaction-select**             | Tag de Interação Persistente |
| class    | string | **status**                         | Tag de status                |
| class    | string | **count**                          | Tag de contagem              |
| class    | string | **icon**                           | Tag de ícone                 |
| class    | string | **small**, **medium** ou **large** | Modifica a densidade         |

## Instanciação do Componente

### HTML

Incluir o arquivo `core.min.js` no html.

```html
<script src="node_modules/@govbr-ds/core/dist/core.min.js"></script>
```

> O arquivo core.min.js expõe um objeto chamado `core` contendo as referências para todas as classes exportadas.

### JavaScript

Usar o seguinte código JavaScript para instanciar a classe `BRTag`, passando os seguintes parâmetros:

- Nome da classe (br-tag)
- Objeto referenciando a raiz do componente DOM

```javascript
const tagList = []
for (const brTag of window.document.querySelectorAll('.br-tag')) {
  tagList.push(new core.BRTag('br-tag', brTag))
}
```

## Informações adicionais

### Cores

Usar Utilitário CSS [Cores](ds/utilities-css/cores) para modificar cores de texto e fundo para o componente.

## Dependências

- [Button](/ds/components/button)
