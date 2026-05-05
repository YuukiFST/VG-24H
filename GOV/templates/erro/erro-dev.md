## Como usar

```html
<div class="template-erro">
  <div class="row my-5">
    <div class="col imagem-erro">
      <img
        src="https://cdngovbr-ds.estaleiro.serpro.gov.br/design-system/images/logo-positive.png"
        alt="imagem de erro"
      />
    </div>
    <div class="col erro-text">
      <div class="text-support-03">
        <p class="text-up-06 text-semi-bold my-3">Estamos constrangidos em te ver por aqui</p>
      </div>
      <div class="text-secondary-06">
        <p class="text-up-03 text-medium my-3">
          Mas, podemos ajudá-lo a encontrar o que está procurando de outra forma
        </p>
      </div>
      <p class="my-3">
        Talvez você tenha se equivocado ao digitar o endereço URL ou quem sabe nós tenhamos cometido uma falha por aqui.
        Se possível, relate o erro para que possamos sempre estar melhorando.
      </p>
    </div>
  </div>
  <div class="row my-3">
    <div class="col-sm-12 col-md-12">
      <div class="search">
        <p class="search-text">Aproveite para fazer uma nova busca</p>
        <div class="br-input has-icon">
          <label></label>
          <input class="has-icon" type="text" placeholder="O que você procura?" aria-label="Texto da pesquisa" />
          <button class="br-button crumb circle small" type="button" aria-label="Pesquisar">
            <i class="fas fa-search" aria-hidden="true"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
  <div class="row my-4">
    <div class="col">
      <div class="buttons-auxiliary my-4">
        <button class="br-button crumb" type="button">
          <i class="fas fa-chevron-left" aria-hidden="true"></i><span>Ir para Página Anterior</span>
        </button>
        <button class="br-button crumb" type="button">
          <i class="fas fa-home" aria-hidden="true"></i><span>Ir para Página Principal</span>
        </button>
        <button class="br-button crumb" type="button">
          <i class="fas fa-comment-dots" aria-hidden="true"></i><span>Envie um Feedback</span>
        </button>
      </div>
    </div>
  </div>
</div>
```

### Elementos obrigatórios

O template de erro usa como base o template padrão [Template Base](/ds/templates/base) para construção de sua anatomia. O template base é a parte que engloba o template de erro. Sendo assim, os elementos do `template erro` ficam na parte interna, região onde fica o contéudo no `template base`.

### Elementos opcionais

| Elemento | Tipo | Descrição          |
| -------- | ---- | ------------------ |
| `img`    | tag  | Tag imagem de erro |
| `input`  | tag  | Tag de busca       |

> **Atenção** : Para trocar as cores dos textos nas mensagens de erro, usam-se as classes do [utilitário de texto](utilities-css/cores) presente na aba `Guias` no site do Design System.
