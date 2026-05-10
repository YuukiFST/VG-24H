# Source: https://www.gov.br/ds/padroes/design/dropdown

Design
Ajuda e Comunicação
Densidade
Content Overflow
Dropdown
Formulário
Gráfico
Onboarding
Collapse
Navegação
Empty States
Dropdown (Elemento Flutuante)

O padrão Dropdown ocorre quando uma superfície flutuante surge sobre a tela, de forma temporária, a partir de um elemento acionador. Esta superfície pode conter informações adicionais com características voltadas para coleta de dados, seleção de opções ou apenas texto informativo.


Exemplos de Dropdown - Menu Suspenso, Painel de Notificação e Campo de Seleção

Utilize o padrão Dropdown quando:

existir a necessidade de apresentar informações extras de forma temporária, sem a necessidade de navegar para uma nova tela ou ocupar espaço útil dentro da interface;
houver a necessidade de exibir itens de seleção ou múltipla escolha ao usuário de forma contextual e temporária;

Não utilize o padrão Dropdown:

quando uma lista suspensa possuir apenas duas opções de escolha. Nesse caso, recomenda-se usar botões de opção, switches ou outro componente que permita o usuário selecionar sua opção diretamente na interface;

para exibir informações excessivamente complexas. Neste caso, utilize hiperlinks para outras páginas;

aninhando muitos elementos Dropdown em cascata. Mantenha os elementos flutuantes organizados da forma mais simples possível, dentro do possível.

Anatomia
ID	Nome	Referência	Uso
1	Acionador		Obrigatório
2	Identificador de Estado	Fundamento Iconografia	Obrigatório
3	Superfície Flutuante	Fundamento Superfície	Obrigatório


Anatomia do Dropdown

Detalhamento dos Itens
1. Acionador (Obrigatório)

O Acionador poderá ser qualquer elemento interativo no qual o usuário irá executar a ação de exibir ou ocultar a Superfície Flutuante.

Geralmente o Acionador é utilizado como Button, porém é possível usar outros elementos como acionadores. Por exemplo, superfícies, hiperlinks ou componentes. Veja os exemplos abaixo:


Exemplo de Acionadores - Botões, Componente Avatar, Select e Texto Interativo como Acionador

2. Identificador de Estado (Obrigatório)

O Identificador de Estado é um elemento iconográfico que representa o estado visível/oculto da Superfície Flutuante. Também serve para identificar se determinado elemento possui o padrão Dropdown.


Exemplo de Identificador de Estado

O Identificador de Estado é representado pelos ícones:

A. caret-down;
B. caret-up;
C. caret-right;
D. caret-left.


Ícones do Identificador de Estado

3. Superfície Flutuante (Obrigatório)

A Superfície Flutuante é o elemento que será exibido ou ocultado na interface através do Acionador. Esta deve aparecer flutuando sobre o conteúdo da interface, com ênfase e contraste.

A. Superfície Flutuante;
B. Conteúdo da Tela.


Superfície Flutuante

Observe alguns exemplos de Superfície Flutuante utilizada em alguns Componentes:


Exemplo de Superfície Flutuante no Menu


Exemplo de Superfície Flutuante no Notification


Exemplo de Superfície Flutuante no Select

Comportamentos
1. Ênfase

O elemento Dropdown, por se tratar de um elemento flutuante, precisa se destacar do restante do layout. Para isto, é utilizado o conceito de elevação, que faz uso da sombra em diferentes intensidades de acordo com a elevação em que a Superfície Flutuante se encontra.

Para elementos flutuantes, como Dropdown, usa-se o padrão de Elevação na Camada 2, como demonstrado na figura abaixo.


Exemplo de Sombras em Diferentes Intensidades e Dropdown na Camada 2 de Elevação

OBS: Consulte mais detalhes em Fundamentos > Elevação.

Apesar de se utilizar a sombra como um elemento obrigatório para destaque da Superfície Flutuante, nem sempre seu uso é suficiente para agregar contraste entre a superfície e a tela. Para proporcionar mais ênfase e contraste, é possível utilizar algumas características opcionais provenientes do conceito de Superfície, como Borda, Cor ou Overlay. Veja abaixo:

A. Borda: Outra propriedade opcional da superfície que pode agregar a ideia de elevação;
B. Cor: Também pode-se adicionar a cor para produzir o contraste na superfície;
C. Overlay: Pode-se utilizar outros recursos, caso seja prioritário a atenção do usuário. Como por exemplo, o uso de Overlay em uma camada inferior ao Dropdown.

Importante: Note que esses elementos opcionais devem ser usados juntamente com a sombra.


Exemplos de Ênfase com características opcionais - Borda, Cor e Overlay

Importante: Quando for utilizado o recurso de Overlay com a finalidade de proporcionar contraste ao elemento Dropdown, os elementos interativos abaixo da camada Overlay devem permanecer bloqueados a qualquer tipo de interação pelo usuário, tanto através do mouse como através de navegação por teclado.


Exemplo de Overlay - Elementos interativos abaixo da camada Overlay permanecem bloqueados

2. Responsividade

Os elementos Dropdown não tem a necessidade de seguir as regras da Grid, pois como são elementos flutuantes, não recebem influência desta.


Exemplo de Lista Dropdown sem interferência da Grid


Exemplo de Menu Dropdown sem interferência da Grid

Grid de 4 Colunas

Porém, é comum que em Grid de 4 colunas, os elementos Dropdown ocupem 100% da largura na tela, se adequando à Grid. Observe a seguir.


Exemplo de Select se adequando à Grid de 4 colunas

Atenção: Deve-se estar atento aos Breakpoints, afim de propor soluções diferenciadas para as dimensões da Superfície Flutuante.

3. Posicionamento

A Superfície Flutuante deve ser posicionada próxima ao Acionador ou centralizada na tela, no caso de dispositivos móveis. Por padrão, a Superfície Flutuante aparece logo abaixo do Acionador. Caso não tenha espaço para exibir o elemento Dropdown, este poderá surgir em outras direções (direita, esquerda, acima) opostas ao limite da tela. Observe abaixo.

A. Por padrão, a Superfície Flutuante abre abaixo do Acionador;
B. A Superfície Flutuante abre abaixo e à direita do Acionador próximo ao limite da tela;
C. A Superfície Flutuante abre abaixo e à esquerda do Acionador próximo ao limite da tela;
D. A Superfície Flutuante abre acima do Acionador próximo ao limite da tela;
E. Limite visível da tela.


Limites da Tela e Posição do Dropdown

Importante: o elemento flutuante deve sempre utilizar o espaço útil disponível na tela, não podendo criar espaços extras. Dessa forma, evitamos comportamentos inesperados, como surgimento de uma barra de rolagem por exemplo.

4. Uso do Identificador de Estado

O Identificador de Estado é o elemento iconográfico padrão para representar a abertura ou fechamento da Superfície Flutuante. Ele deve funcionar com o comportamento toggle, alternando a representação do ícone, cada vez que a Superfície Flutuante é exibida ou ocultada.

Forma Iconográfica

Por padrão, a forma iconográfica utilizada é:

A. caret-down quando a Superfície Flutuante está oculta;
B. caret-up quando a Superfície Flutuante está visível;


Comportamento Toggle do Identificador de Estado

Em raras situações é possível abrir o elemento Dropdown horizontalmente. Neste caso se utiliza a seguinte iconografia:

A. caret-right quando a Superfície Flutuante está oculta e vai abrir horizontalmente;

B. caret-left quando a Superfície Flutuante está visível e vai fechar horizontalmente.


Exemplo de Painel Retrátil com Identificador de Estado na Horizontal

Posicionamento
Por padrão, deve-se usar o Identificador de Estado à direita do Acionador e centralizado verticalmente, com o intuito de identificá-lo como elemento Dropdown.


Exemplo de Identificador de Estado

Uso Opcional

Algumas situações desobrigam o uso do Identificador de Estado, quando o Acionador já possui uma representação iconográfica ou semântica forte o suficiente para representar o padrão Dropdown, deixando claro ao usuário esta ideia.


Exemplo de Acionadores sem Identificador de Estado - Já representam fortemente o conceito Dropdown

Mesmo nestas situações, o uso do Identificador de Estado é opcional. Caso haja o desejo de reforçar mais ainda a semântica do Dropdown pode-se utilizar o Identificador de Estado.


Caso haja necessidade, pode-se usar o Identificador de Estado para tornar mais claro o padrão Dropdown

5. Uso do Acionador

É recomendado, sempre que possível, que a área de clique tenha abrangência por toda superfície do Acionador, incluindo o Identificador de Estado.


Área de Clique do Acionador incluindo o Identificador de Estado

Persistência do Estado

Utilize a Persistência de Estado para representar a abertura ou fechamento da Superfície Flutuante.

O importante é que fique claro para o usuário que foi ele quem executou a ação. A melhor forma de indicar isso, é utilizar o estado persistente do momento da interação. Por exemplo, se o usuário acionar com pressed ou com hover, o Acionador deverá manter esses estados enquanto o elemento Dropdown estiver sendo exibido na tela. Veja o exemplo abaixo:


O usuário utilizou o hover para abrir o Dropdown. O Acionador mantém o estado hover até o Dropdown fechar


O usuário utilizou o Clique para abrir o Dropdown. O Acionador mantém o estado pressed até o Dropdown fechar

OBS: A Persistência de Estado é um recurso opcional e também pode ser utilizada juntamente com o Identificador de Estado.

6. Fechamento da Superfície Flutuante

A Superfície Flutuante é um elemento temporário, logo precisa desaparecer da interface, ou seja, precisa ser fechada. Abaixo seguem as formas mais comuns utilizadas para fechamento da Superfície Flutuante:

Acionador: o próprio elemento que acionou a Superfície Flutuante pode ser utilizado para fechá-la. Caso tenha sido acionado por clique ou toque, basta clicar ou tocar novamente no Acionador para fechá-la. Se tiver sido acionado por um hover, retire o ponteiro do mouse sobre o Acionador;


Fechamento pelo Próprio Acionador

Botão Fechar: o Botão Fechar com ícone times (x) é a forma mais comum utilizada. Recomenda-se posicionar o ícone na parte superior direita da Superfície Flutuante;


Fechamento pelo Botão Fechar

Clique fora da superfície: clicando fora da Superfície Flutuante, é outra forma bastante usada para fechar elementos Dropdown, independentemente se está ou não sobre um Overlay;


Fechamento com clique fora da superfície

Concluir objetivo: após a conclusão do objetivo para o qual foi solicitado o elemento Dropdown. Esse objetivo pode ser por uma escolha/seleção, preenchimento de um formulário ou até finalizando o carregamento de algum conteúdo.


Fechamento com conclusão de objetivo

Importante: Os comportamentos acima podem ser utilizados separadamente, mas a recomendação é que eles sejam utilizados em conjunto, desde que façam sentido no contexto da interface.

7. Conteúdos
Em algumas situações, o conteúdo exibido na Superfície Flutuante pode ser relativamente grande, como é o caso de alguns painéis de filtros ou painéis retráteis. Neste caso, a recomendação é ter cautela neste tipo de uso. Se o conteúdo for realmente muito extenso a ponto de criar barra de rolagem na área visível da tela, prefira usar hiperlink para uma nova tela;


Exemplo de Conteúdo em Dropdown


Exemplo de Conteúdo Muito Extenso em Dropdown - Prefira utilizar hiperlinks para um nova página

Recomenda-se utilizar o conteúdo de um Dropdown sempre contido (ou parcialmente contido) dentro da Superfície Flutuante. Caso contrário, poderá gerar confusão por parte do usuário.

O conteúdo deve ser apresentado de forma mais simples e sucinta possível. Sem desvio de atenção.

Pode haver a necessidade de múltiplos elementos Dropdown aninhados em cascata, porém, utilize com muita cautela para que o usuário não se perca dentro de diversos níveis. Como padrão, mantenha no máximo 3 níveis de Dropdown.


Exemplo de Boa Prática - Elementos Dropdown aninhados em cascata


Exemplo de Mau Uso - Elementos Dropdown aninhados em cascata

8. Acessibilidade

O padrão WAI ARIA define algumas regras específicas para cada elemento/conteúdo utilizado. O Dropdown do Design System é um comportamento genérico que pode ser aplicado a uma variedade de situações e estruturas. Por esse motivo, não será especificado regras de atributos ARIA necessários (a não ser nos componentes do Design System que utilizam este comportamento). Os autores terão que incluir por contra própria esses atributos mais específicos, dependo do que for utilizado na sua estrutura Dropdown;

No entanto, é importante permitir a navegação entre os elementos interativos em um Dropdown sejam feitos pela tecla TAB. Neste caso, utilize o estado foco nos elementos durante a navegação;


Exemplo de Uso do Teclado para Navegação em Dropdown - Tecla Tab

e em alguns casos, o uso de Teclas de Navegação (cima, baixo, direta, esquerda);


Exemplo de Uso do Teclado para Navegação em Dropdown - Teclas de Navegação

Em caso de navegação a partir do teclado, o fechamento do Dropdown deve ser feito com uso da tecla ESC;


Exemplo de Uso do Teclado para Navegação em Dropdown - Fechamento com Tecla Esc

Em caso de navegação a partir do teclado, o acionamento pode ser feito com a tecla Enter ou Espaço.


Exemplo de Uso do Teclado para Navegação em Dropdown - Acionamento com Tecla Enter ou Espaço

Especificações
Iconografia
Name	Estado	Ícone	Size	Class (Font Awesome)
Indicador de Estado (Visível)	–		--icon-size-base	.fa-caret-up
Indicador de Estado (Oculto)	–		--icon-size-base	.fa-caret-down
Indicador de Estado (Visível Horizontal)	–		--icon-size-base	.fa-caret-left
Indicador de Estado (Oculto Horizontal)	–		--icon-size-base	.fa-caret-right
Sombra
Camada	Inner Shadow	Offset *	Blur	Color	Color Opacity
2	none	3 ou -3	6	--pure-100	--surface-opacity-xs