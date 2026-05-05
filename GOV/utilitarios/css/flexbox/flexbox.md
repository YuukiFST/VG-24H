As classes a seguir funcionam apenas em elementos com display "flex" ou "inline-flex". O [utilitário de display](utilitarios/css/display) informa como transformar o display para essa finalidade.

A linha da Grid `.row` usa display "flex", portanto você poderá usar as classes de flexbox nela também.

Todas as classes de flexbox podem ser modificadas por breakpoint.

## Direction

`flex[-breakpoint]-row`

<div class="d-flex border-solid-sm mb-5 flex-row" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`flex[-breakpoint]-row-reverse`

<div class="d-flex border-solid-sm mb-5 flex-row-reverse" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`flex[-breakpoint]-column`

<div class="d-flex border-solid-sm mb-5 flex-column" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`flex[-breakpoint]-column-reverse`

<div class="d-flex border-solid-sm mb-5 flex-column-reverse" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

## Justify content

`justify-content[-breakpoint]-start`

<div class="mb-5 d-flex border-solid-sm mt-1 justify-content-start" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`justify-content[-breakpoint]-end`

<div class="mb-5 d-flex border-solid-sm mt-1 justify-content-end" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`justify-content[-breakpoint]-center`

<div class="mb-5 d-flex border-solid-sm mt-1 justify-content-center" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`justify-content[-breakpoint]-between`

<div class="mb-5 d-flex border-solid-sm mt-1 justify-content-between" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`justify-content[-breakpoint]-around`

<div class="mb-5 d-flex border-solid-sm mt-1 justify-content-around" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`justify-content[-breakpoint]-evenly`

<div class="mb-5 d-flex border-solid-sm mt-1 justify-content-evenly" style="height: auto;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

## Align items

`align-items[-breakpoint]-start`

<div class="mb-5 d-flex border-solid-sm mt-1 align-items-start" style="height: 120px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`align-items[-breakpoint]-end`

<div class="mb-5 d-flex border-solid-sm mt-1 align-items-end" style="height: 120px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`align-items[-breakpoint]-center`

<div class="mb-5 d-flex border-solid-sm mt-1 align-items-center" style="height: 120px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`align-items[-breakpoint]-baseline`

<div class="mb-5 d-flex border-solid-sm mt-1 align-items-baseline" style="height: 120px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

`align-items[-breakpoint]-stretch`

<div class="mb-5 d-flex border-solid-sm mt-1 align-items-stretch" style="height: 120px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

## Wrap

`flex[-breakpoint]-wrap`

<div class="col-6 col-sm-5 col-md-4 col-lg-3 col-xl-2">
  <div class="d-flex border-solid-sm mb-5 flex-wrap" style="height: auto;">
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 1</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 2</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 3</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 4</div>
  </div>
</div>

`flex[-breakpoint]-nowrap`

<div class="col-6 col-sm-5 col-md-4 col-lg-3 col-xl-2">
  <div class="d-flex border-solid-sm mb-5 flex-nowrap" style="height: auto;">
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 1</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 2</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 3</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 4</div>
  </div>
</div>

`flex[-breakpoint]-wrap-reverse`

<div class="col-6 col-sm-5 col-md-4 col-lg-3 col-xl-2">
  <div class="d-flex border-solid-sm mb-5 flex-wrap-reverse" style="height: auto;">
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 1</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 2</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 3</div>
    <div class="m-half border-dashed-sm p-1 text-nowrap">children 4</div>
  </div>
</div>

## Align self

- `align-self[-breakpoint]-start`
- `align-self[-breakpoint]-end`
- `align-self[-breakpoint]-center`
- `align-self[-breakpoint]-baseline`
- `align-self[-breakpoint]-stretch`

<div class="my-3 d-flex border-solid-sm mt-1 align-self-start" style="height: 100px">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1 align-self-start">
    <code>align-self-start</code>
  </div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

<div class="my-3 d-flex border-solid-sm mt-1 align-self-end" style="height: 100px">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1 align-self-end">
    <code>align-self-end</code>
  </div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

<div class="my-3 d-flex border-solid-sm mt-1 align-self-center" style="height: 100px">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1 align-self-center">
    <code>align-self-center</code>
  </div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

<div class="my-3 d-flex border-solid-sm mt-1 align-self-baseline" style="height: 100px">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1 align-self-baseline">
    <code>align-self-baseline</code>
  </div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

<div class="my-3 d-flex border-solid-sm mt-1 align-self-stretch" style="height: 100px">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1 align-self-stretch">
    <code>align-self-stretch</code>
  </div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
</div>

## Fill, Grow e Shrink

- `flex[-breakpoint]-fill`
- `flex-grow[-breakpoint]-1`
- `flex-grow[-breakpoint]-0`
- `flex-shrink[-breakpoint]-1`
- `flex-shrink[-breakpoint]-0`

<div class="d-flex border-solid-sm mb-5">
  <div class="m-half border-dashed-sm p-1 flex-fill">
    <code>flex-fill</code>
    <p class="mt-3">Children 1</p>
  </div>
  <div class="m-half border-dashed-sm p-1 flex-fill">
    <code>flex-fill</code>
    <p class="mt-3">Children 2</p>
  </div>
  <div class="m-half border-dashed-sm p-1 flex-fill">
    <code>flex-fill</code>
    <p class="mt-3">Children 3</p>
  </div>
</div>

<div class="d-flex border-solid-sm mb-5">
  <div class="m-half border-dashed-sm p-1 flex-grow-1">
    <code>flex-grow-1</code>
    <p class="mt-3">Children 1</p>
  </div>
  <div class="m-half border-dashed-sm p-1 flex-grow-0">
    <code>flex-grow-0</code>
    <p class="mt-3">Children 2</p>
  </div>
  <div class="m-half border-dashed-sm p-1 flex-fill">
    <code>flex-fill</code>
    <p class="mt-3">Children 3</p>
  </div>
</div>

<div class="d-flex border-solid-sm mb-5">
  <div class="m-half border-dashed-sm p-1 flex-shrink-1">
    <code>flex-shrink-1</code>
    <p class="mt-3">Children 1</p>
  </div>
  <div class="m-half border-dashed-sm p-1 flex-shrink-0">
    <code>flex-shrink-0</code>
    <p class="mt-3">Children 2</p>
  </div>
  <div class="m-half border-dashed-sm p-1 flex-fill">
    <code>flex-fill</code>
    <p class="mt-3">Children 3</p>
  </div>
</div>

## Order

- `order[-breakpoint]-0`
- `order[-breakpoint]-1`
- `order[-breakpoint]-2`
- `order[-breakpoint]-3`
- `order[-breakpoint]-4`
- `order[-breakpoint]-5`
- `order[-breakpoint]-6`
- `order[-breakpoint]-7`
- `order[-breakpoint]-8`
- `order[-breakpoint]-9`
- `order[-breakpoint]-10`
- `order[-breakpoint]-11`
- `order[-breakpoint]-12`

<div class="d-flex flex-wrap border-solid-sm mt-1">
  <div class="m-half border-dashed-sm p-1 order-3">
    <code>order-3</code>
    <p class="mt-3">children 1</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-0">
    <code>order-0</code>
    <p class="mt-3">children 2</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-9">
    <code>order-9</code>
    <p class="mt-3">children 3</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-5">
    <code>order-5</code>
    <p class="mt-3">children 4</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-1">
    <code>order-1</code>
    <p class="mt-3">children 5</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-11">
    <code>order-11</code>
    <p class="mt-3">children 6</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-4">
    <code>order-4</code>
    <p class="mt-3">children 7</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-8">
    <code>order-8</code>
    <p class="mt-3">children 8</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-2">
    <code>order-2</code>
    <p class="mt-3">children 9</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-6">
    <code>order-6</code>
    <p class="mt-3">children 10</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-12">
    <code>order-12</code>
    <p class="mt-3">children 11</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-10">
    <code>order-10</code>
    <p class="mt-3">children 12</p>
  </div>
  <div class="m-half border-dashed-sm p-1 order-7">
    <code>order-7</code>
    <p class="mt-3">children 13</p>
  </div>
</div>

## Align content

`align-content-start`

<div class="mb-5 d-flex border-solid-sm mt-1 align-content-start flex-wrap" style="height: 540px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
  <div class="m-half border-dashed-sm p-1">children 4</div>
  <div class="m-half border-dashed-sm p-1">children 5</div>
  <div class="m-half border-dashed-sm p-1">children 6</div>
  <div class="m-half border-dashed-sm p-1">children 7</div>
  <div class="m-half border-dashed-sm p-1">children 8</div>
  <div class="m-half border-dashed-sm p-1">children 9</div>
  <div class="m-half border-dashed-sm p-1">children 10</div>
  <div class="m-half border-dashed-sm p-1">children 11</div>
  <div class="m-half border-dashed-sm p-1">children 12</div>
  <div class="m-half border-dashed-sm p-1">children 13</div>
  <div class="m-half border-dashed-sm p-1">children 14</div>
  <div class="m-half border-dashed-sm p-1">children 15</div>
  <div class="m-half border-dashed-sm p-1">children 16</div>
  <div class="m-half border-dashed-sm p-1">children 17</div>
  <div class="m-half border-dashed-sm p-1">children 18</div>
  <div class="m-half border-dashed-sm p-1">children 19</div>
  <div class="m-half border-dashed-sm p-1">children 20</div>
  <div class="m-half border-dashed-sm p-1">children 21</div>
  <div class="m-half border-dashed-sm p-1">children 22</div>
  <div class="m-half border-dashed-sm p-1">children 23</div>
  <div class="m-half border-dashed-sm p-1">children 24</div>
  <div class="m-half border-dashed-sm p-1">children 25</div>
  <div class="m-half border-dashed-sm p-1">children 26</div>
  <div class="m-half border-dashed-sm p-1">children 27</div>
  <div class="m-half border-dashed-sm p-1">children 28</div>
  <div class="m-half border-dashed-sm p-1">children 29</div>
  <div class="m-half border-dashed-sm p-1">children 30</div>
</div>

`align-content-end`

<div class="mb-5 d-flex border-solid-sm mt-1 align-content-end flex-wrap" style="height: 540px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
  <div class="m-half border-dashed-sm p-1">children 4</div>
  <div class="m-half border-dashed-sm p-1">children 5</div>
  <div class="m-half border-dashed-sm p-1">children 6</div>
  <div class="m-half border-dashed-sm p-1">children 7</div>
  <div class="m-half border-dashed-sm p-1">children 8</div>
  <div class="m-half border-dashed-sm p-1">children 9</div>
  <div class="m-half border-dashed-sm p-1">children 10</div>
  <div class="m-half border-dashed-sm p-1">children 11</div>
  <div class="m-half border-dashed-sm p-1">children 12</div>
  <div class="m-half border-dashed-sm p-1">children 13</div>
  <div class="m-half border-dashed-sm p-1">children 14</div>
  <div class="m-half border-dashed-sm p-1">children 15</div>
  <div class="m-half border-dashed-sm p-1">children 16</div>
  <div class="m-half border-dashed-sm p-1">children 17</div>
  <div class="m-half border-dashed-sm p-1">children 18</div>
  <div class="m-half border-dashed-sm p-1">children 19</div>
  <div class="m-half border-dashed-sm p-1">children 20</div>
  <div class="m-half border-dashed-sm p-1">children 21</div>
  <div class="m-half border-dashed-sm p-1">children 22</div>
  <div class="m-half border-dashed-sm p-1">children 23</div>
  <div class="m-half border-dashed-sm p-1">children 24</div>
  <div class="m-half border-dashed-sm p-1">children 25</div>
  <div class="m-half border-dashed-sm p-1">children 26</div>
  <div class="m-half border-dashed-sm p-1">children 27</div>
  <div class="m-half border-dashed-sm p-1">children 28</div>
  <div class="m-half border-dashed-sm p-1">children 29</div>
  <div class="m-half border-dashed-sm p-1">children 30</div>
</div>

`align-content-center`

<div class="mb-5 d-flex border-solid-sm mt-1 align-content-center flex-wrap" style="height: 540px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
  <div class="m-half border-dashed-sm p-1">children 4</div>
  <div class="m-half border-dashed-sm p-1">children 5</div>
  <div class="m-half border-dashed-sm p-1">children 6</div>
  <div class="m-half border-dashed-sm p-1">children 7</div>
  <div class="m-half border-dashed-sm p-1">children 8</div>
  <div class="m-half border-dashed-sm p-1">children 9</div>
  <div class="m-half border-dashed-sm p-1">children 10</div>
  <div class="m-half border-dashed-sm p-1">children 11</div>
  <div class="m-half border-dashed-sm p-1">children 12</div>
  <div class="m-half border-dashed-sm p-1">children 13</div>
  <div class="m-half border-dashed-sm p-1">children 14</div>
  <div class="m-half border-dashed-sm p-1">children 15</div>
  <div class="m-half border-dashed-sm p-1">children 16</div>
  <div class="m-half border-dashed-sm p-1">children 17</div>
  <div class="m-half border-dashed-sm p-1">children 18</div>
  <div class="m-half border-dashed-sm p-1">children 19</div>
  <div class="m-half border-dashed-sm p-1">children 20</div>
  <div class="m-half border-dashed-sm p-1">children 21</div>
  <div class="m-half border-dashed-sm p-1">children 22</div>
  <div class="m-half border-dashed-sm p-1">children 23</div>
  <div class="m-half border-dashed-sm p-1">children 24</div>
  <div class="m-half border-dashed-sm p-1">children 25</div>
  <div class="m-half border-dashed-sm p-1">children 26</div>
  <div class="m-half border-dashed-sm p-1">children 27</div>
  <div class="m-half border-dashed-sm p-1">children 28</div>
  <div class="m-half border-dashed-sm p-1">children 29</div>
  <div class="m-half border-dashed-sm p-1">children 30</div>
</div>

`align-content-around`

<div class="mb-5 d-flex border-solid-sm mt-1 align-content-around flex-wrap" style="height: 540px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
  <div class="m-half border-dashed-sm p-1">children 4</div>
  <div class="m-half border-dashed-sm p-1">children 5</div>
  <div class="m-half border-dashed-sm p-1">children 6</div>
  <div class="m-half border-dashed-sm p-1">children 7</div>
  <div class="m-half border-dashed-sm p-1">children 8</div>
  <div class="m-half border-dashed-sm p-1">children 9</div>
  <div class="m-half border-dashed-sm p-1">children 10</div>
  <div class="m-half border-dashed-sm p-1">children 11</div>
  <div class="m-half border-dashed-sm p-1">children 12</div>
  <div class="m-half border-dashed-sm p-1">children 13</div>
  <div class="m-half border-dashed-sm p-1">children 14</div>
  <div class="m-half border-dashed-sm p-1">children 15</div>
  <div class="m-half border-dashed-sm p-1">children 16</div>
  <div class="m-half border-dashed-sm p-1">children 17</div>
  <div class="m-half border-dashed-sm p-1">children 18</div>
  <div class="m-half border-dashed-sm p-1">children 19</div>
  <div class="m-half border-dashed-sm p-1">children 20</div>
  <div class="m-half border-dashed-sm p-1">children 21</div>
  <div class="m-half border-dashed-sm p-1">children 22</div>
  <div class="m-half border-dashed-sm p-1">children 23</div>
  <div class="m-half border-dashed-sm p-1">children 24</div>
  <div class="m-half border-dashed-sm p-1">children 25</div>
  <div class="m-half border-dashed-sm p-1">children 26</div>
  <div class="m-half border-dashed-sm p-1">children 27</div>
  <div class="m-half border-dashed-sm p-1">children 28</div>
  <div class="m-half border-dashed-sm p-1">children 29</div>
  <div class="m-half border-dashed-sm p-1">children 30</div>
</div>

`align-content-evenly`

<div class="mb-5 d-flex border-solid-sm mt-1 align-content-evenly flex-wrap" style="height: 540px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
  <div class="m-half border-dashed-sm p-1">children 4</div>
  <div class="m-half border-dashed-sm p-1">children 5</div>
  <div class="m-half border-dashed-sm p-1">children 6</div>
  <div class="m-half border-dashed-sm p-1">children 7</div>
  <div class="m-half border-dashed-sm p-1">children 8</div>
  <div class="m-half border-dashed-sm p-1">children 9</div>
  <div class="m-half border-dashed-sm p-1">children 10</div>
  <div class="m-half border-dashed-sm p-1">children 11</div>
  <div class="m-half border-dashed-sm p-1">children 12</div>
  <div class="m-half border-dashed-sm p-1">children 13</div>
  <div class="m-half border-dashed-sm p-1">children 14</div>
  <div class="m-half border-dashed-sm p-1">children 15</div>
  <div class="m-half border-dashed-sm p-1">children 16</div>
  <div class="m-half border-dashed-sm p-1">children 17</div>
  <div class="m-half border-dashed-sm p-1">children 18</div>
  <div class="m-half border-dashed-sm p-1">children 19</div>
  <div class="m-half border-dashed-sm p-1">children 20</div>
  <div class="m-half border-dashed-sm p-1">children 21</div>
  <div class="m-half border-dashed-sm p-1">children 22</div>
  <div class="m-half border-dashed-sm p-1">children 23</div>
  <div class="m-half border-dashed-sm p-1">children 24</div>
  <div class="m-half border-dashed-sm p-1">children 25</div>
  <div class="m-half border-dashed-sm p-1">children 26</div>
  <div class="m-half border-dashed-sm p-1">children 27</div>
  <div class="m-half border-dashed-sm p-1">children 28</div>
  <div class="m-half border-dashed-sm p-1">children 29</div>
  <div class="m-half border-dashed-sm p-1">children 30</div>
</div>

`align-content-stretch`

<div class="mb-5 d-flex border-solid-sm mt-1 align-content-stretch flex-wrap" style="height: 540px;">
  <div class="m-half border-dashed-sm p-1">children 1</div>
  <div class="m-half border-dashed-sm p-1">children 2</div>
  <div class="m-half border-dashed-sm p-1">children 3</div>
  <div class="m-half border-dashed-sm p-1">children 4</div>
  <div class="m-half border-dashed-sm p-1">children 5</div>
  <div class="m-half border-dashed-sm p-1">children 6</div>
  <div class="m-half border-dashed-sm p-1">children 7</div>
  <div class="m-half border-dashed-sm p-1">children 8</div>
  <div class="m-half border-dashed-sm p-1">children 9</div>
  <div class="m-half border-dashed-sm p-1">children 10</div>
  <div class="m-half border-dashed-sm p-1">children 11</div>
  <div class="m-half border-dashed-sm p-1">children 12</div>
  <div class="m-half border-dashed-sm p-1">children 13</div>
  <div class="m-half border-dashed-sm p-1">children 14</div>
  <div class="m-half border-dashed-sm p-1">children 15</div>
  <div class="m-half border-dashed-sm p-1">children 16</div>
  <div class="m-half border-dashed-sm p-1">children 17</div>
  <div class="m-half border-dashed-sm p-1">children 18</div>
  <div class="m-half border-dashed-sm p-1">children 19</div>
  <div class="m-half border-dashed-sm p-1">children 20</div>
  <div class="m-half border-dashed-sm p-1">children 21</div>
  <div class="m-half border-dashed-sm p-1">children 22</div>
  <div class="m-half border-dashed-sm p-1">children 23</div>
  <div class="m-half border-dashed-sm p-1">children 24</div>
  <div class="m-half border-dashed-sm p-1">children 25</div>
  <div class="m-half border-dashed-sm p-1">children 26</div>
  <div class="m-half border-dashed-sm p-1">children 27</div>
  <div class="m-half border-dashed-sm p-1">children 28</div>
  <div class="m-half border-dashed-sm p-1">children 29</div>
  <div class="m-half border-dashed-sm p-1">children 30</div>
</div>
