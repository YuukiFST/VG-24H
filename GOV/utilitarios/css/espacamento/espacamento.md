As classes de espaçamento foram criadas de acordo com o [Fundamento Espaçamento](fundamentos-visuais/espacamento).

- Para aplicar **padding** use a letra **p**.
- Para aplicar **margin** use a letra **m**

## Breakpoints

- Independente do tamanho ou direção você poderá informar o breakpoint de aplicação
- Você pode modificar o tamanho ou direção para cada breakpoint

| Classe              | *Smartphone Portrait*                        | *Smartphone Landscape*<br>*Tablet Portrait*  | *Tablet Landscape*                           | *Desktop*                                    | TV                                           |
| ------------------- | -------------------------------------------- | -------------------------------------------- | -------------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| `.p-*` `.m-*`       | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> |
| `.p-sm-*` `.m-sm-*` | ignora <i class="text-danger fas fa-times">  | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> |
| `.p-md-*` `.m-md-*` | ignora <i class="text-danger fas fa-times">  | ignora <i class="text-danger fas fa-times">  | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> |
| `.p-lg-*` `.m-lg-*` | ignora <i class="text-danger fas fa-times">  | ignora <i class="text-danger fas fa-times">  | ignora <i class="text-danger fas fa-times">  | aplica <i class="text-success fas fa-check"> | aplica <i class="text-success fas fa-check"> |
| `.p-xl-*` `.m-xl-*` | ignora <i class="text-danger fas fa-times">  | ignora <i class="text-danger fas fa-times">  | ignora <i class="text-danger fas fa-times">  | ignora <i class="text-danger fas fa-times">  | aplica <i class="text-success fas fa-check"> |

## Tamanhos

O valor do espaçamento é aplicado usando o formato:

- `.p-tamanho` ou `.p-breakpoint-tamanho` para padding
- `.m-tamanho` ou `.m-breakpoint-tamanho` para margin

Em **margin**, no lugar do tamanho pode ser aplicado também o valor **auto**. Neste caso a regra de uso permanece a mesma dos tamanhos, direção ou sentido. Exemplo: `.m-auto` ou `.m-lg-auto`

| Tamanho       | Valor |
| ------------- | ----- |
| `0`           | 0px   |
| `half` ou `1` | 4px   |
| `base` ou `2` | 8px   |
| `baseh`       | 12px  |
| `2x` ou `3`   | 16px  |
| `2xh`         | 20px  |
| `3x` ou `4`   | 24px  |
| `3xh`         | 28px  |
| `4x` ou `5`   | 32px  |
| `4xh`         | 36px  |
| `5x` ou `6`   | 40px  |
| `5xh`         | 44px  |
| `6x`          | 48px  |
| `6xh`         | 52px  |
| `7x`          | 56px  |
| `7xh`         | 60px  |
| `8x`          | 64px  |
| `8xh`         | 68px  |
| `9x`          | 72px  |
| `9xh`         | 76px  |
| `10x`         | 80px  |
| `10xh`        | 84px  |

## Direção

A aplicação é feita nas seguintes opções:

- Todas as direções
- Direção específica
- Sentido

Você poderá modificar tanto a direção quanto o sentido de acordo com o breakpoint.

### Todas as direções

É aplicado quando não é informado uma direção específica ou sentido de aplicação.

```html
<!-- padding sempre terá tamanho 10x -->
<div class="p-10x">Conteúdo</div>
<!-- padding muda conforme breakpoint -->
<div class="p-2x p-sm-4x p-lg-10x">Conteúdo</div>
```

### Direção específica

1. **Cima** (top) usar a letra **t**
2. **Direita** (right) usar a letra **r**
3. **Baixo** (bottom) usar a letra **b**
4. **Esquerda** (left) usar a letra **l**

- `.p[direção][-breakpoint]-tamanho` para padding
- `.m[direção][-breakpoint]-tamanho` para margin

```html
<!-- padding bottom sempre terá tamanho 10x -->
<div class="pb-10x">Conteúdo</div>
<!-- direção do padding muda conforme breakpoint -->
<div class="pb-2x pb-sm-0 pt-sm-4x pt-lg-0 pl-lg-10x">Conteúdo</div>
```

### Sentido

1. **Horizontal** (base x) usar a letra **x**
2. **Vertical** (base y) usar a letra **y**

- `.p[sentido][-breakpoint]-tamanho` para padding
- `.m[sentido][-breakpoint]-tamanho` para margin

```html
<!-- padding cima e baixo sempre terá tamanho 10x -->
<div class="py-10x">Conteúdo</div>
<!-- sentido do padding muda conforme breakpoint -->
<div class="py-2x py-sm-0 px-sm-4x px-lg-0 py-lg-10x">Conteúdo</div>
```
