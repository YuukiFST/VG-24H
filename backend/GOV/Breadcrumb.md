Vou te mandar um codigo de referencia do Breadcrumb de acordo com o Design System do GOV:

HTML:

<nav class="br-breadcrumb" aria-label="Breadcrumbs">
  <ol class="crumb-list" role="list">
    <li class="crumb home"><a class="br-button circle" href="javascript:void(0)"><span class="sr-only">Página inicial</span><i class="fas fa-home"></i></a></li>
    <li class="crumb"><i class="icon fas fa-chevron-right"></i><a href="javascript:void(0)">Página Ancestral 01</a>
    </li>
    <li class="crumb"><i class="icon fas fa-chevron-right"></i><a href="javascript:void(0)">Página Ancestral 02</a>
    </li>
    <li class="crumb"><i class="icon fas fa-chevron-right"></i><a href="javascript:void(0)">Página Ancestral 03</a>
    </li>
    <li class="crumb"><i class="icon fas fa-chevron-right"></i><a href="javascript:void(0)">Página Ancestral Com Título Grande</a>
      <div class="br-tooltip" role="tooltip" info="info" place="top"><span class="text" role="tooltip">Página Ancestral Com Título Grande</span>
      </div>
    </li>
    <li class="crumb" data-active="active"><i class="icon fas fa-chevron-right"></i><span tabindex="0" aria-current="page">Página atual</span>
    </li>
  </ol>
</nav>

CSS:
.br-breadcrumb {
display: inline-grid;
font-size: var(--font-size-scale-down-01);
font-weight: var(--font-weight-medium);
min-height: var(--spacing-scale-7x);
position: relative;
}
.br-breadcrumb .crumb-list {
align-items: center;
border: 0;
display: flex;
list-style: none;
margin: 0;
overflow-x: auto;
overflow-y: hidden;
padding: 0 0 0 var(--spacing-scale-base);
}
.br-breadcrumb .crumb {
align-items: center;
display: flex;
height: var(--spacing-scale-5x);
}
.br-breadcrumb .crumb .icon {
color: var(--border-color);
font-size: var(--icon-size-sm);
margin-right: -6px;
}
.br-breadcrumb .crumb a {
max-width: 180px;
overflow: hidden;
text-decoration: none;
text-overflow: ellipsis;
white-space: nowrap;
}
.br-breadcrumb .crumb:last-child span {
font-weight: var(--font-weight-medium);
margin: 0 var(--spacing-scale-2x) 0 var(--spacing-scale-base);
white-space: nowrap;
}
.br-breadcrumb .crumb[data-active=active] span:focus:focus, .br-breadcrumb .crumb[data-active=active] span:focus-visible:focus, .br-breadcrumb .crumb[data-active=active] span.focus-visible:focus {
outline: none;
}
.br-breadcrumb .crumb[data-active=active] span:focus.focus-visible, .br-breadcrumb .crumb[data-active=active] span:focus:focus-visible, .br-breadcrumb .crumb[data-active=active] span:focus-visible.focus-visible, .br-breadcrumb .crumb[data-active=active] span:focus-visible:focus-visible, .br-breadcrumb .crumb[data-active=active] span.focus-visible.focus-visible, .br-breadcrumb .crumb[data-active=active] span.focus-visible:focus-visible {
outline-color: var(--focus);
outline-offset: var(--focus-offset);
outline-style: var(--focus-style);
outline-width: var(--focus-width);
}
.br-breadcrumb .crumb a:not(.br-button) {
margin: 0 var(--spacing-scale-base);
}
.br-breadcrumb .home,
.br-breadcrumb .menu-mobil {
--focus-offset: calc(var(--spacing-scale-half) \* -1);
margin: 0 var(--spacing-scale-base) 0 0;
}
@media (max-width: 991px) {
.br-breadcrumb .crumb a:not(.br-button) {
display: block;
max-width: 180px;
overflow: hidden;
text-overflow: ellipsis;
white-space: nowrap;
}
.br-breadcrumb .menu-mobil,
.br-breadcrumb .menu-mobil + .crumb,
.br-breadcrumb .home + .crumb {
display: flex;
}
}
.br-breadcrumb .br-card {
left: var(--spacing-scale-9x);
min-width: fit-content;
position: absolute;
top: var(--spacing-scale-7x);
z-index: var(--z-index-layer-1);
}
.br-breadcrumb .br-item {
color: var(--color);
cursor: pointer;
padding: 0;
}
.br-breadcrumb .br-item:not(:last-child) {
border-bottom: 1px solid var(--border-color);
}
.br-breadcrumb .br-item a {
--interactive: var(--color);
--interactive-rgb: var(--color-rgb);
display: block;
padding: var(--spacing-scale-2x);
}
@media (max-width: 575px) {
.br-breadcrumb .menu-mobil > .icon {
display: none;
}
.br-breadcrumb .br-card {
left: var(--spacing-scale-base);
width: 250px;
}
}

/_# sourceMappingURL=breadcrumb.css.map_/
