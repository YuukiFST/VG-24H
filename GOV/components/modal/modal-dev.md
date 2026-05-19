> URL oficial (visão geral): https://www.gov.br/ds/components/modal?tab=visao-geral
> URL oficial (códigos): https://www.gov.br/ds/components/modal?tab=codigos

## Como usar

### Propriedades obrigatórias

| Atributo | Tipo   | Valor Padrão      | Descrição               |
| -------- | ------ | ----------------- | ----------------------- |
| class    | string | **br-modal**      | container do componente |
| class    | string | **br-modal-body** | corpo da modal          |

### Propriedades adicionais

| Atributo | Tipo   | Valor Padrão                                             | Descrição                     |
| -------- | ------ | -------------------------------------------------------- | ----------------------------- |
| class    | string | **br-modal-header**                                      | cabeçalho da modal            |
| class    | string | **br-modal-footer**                                      | rodapé da modal               |
| class    | string | **modal-title**                                          | título com limite de 2 linhas |
| class    | string | **xsmall**, **small**, **medium**, **large** ou **auto** | Modifica a largura da modal   |

## Informações adicionais

### Modal com scroll

O scroll é adicionado automaticamente caso seja definida uma altura para a modal.

## Dependências

- [Button](/ds/components/button)
- [Loading](/ds/components/loading)

## Utilização do utilitário Scrim com o componente modal

Consultar documentação do utilitário JS Scrim [Scrim](/ds/utilitarios/js/scrim).
