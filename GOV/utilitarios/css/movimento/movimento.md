As classes de textos foram criadas baseadas no [Fundamento Movimento](fundamentos-visuais/movimento).

### Easing

Easing é o atributo que define a aceleração e a desaceleração do movimento de um objeto ao longo do tempo. Os valores do easing determinam o quanto natural ou artificial o movimento parecerá.

| Classe        | Movimento                        |
| ------------- | -------------------------------- |
| `ease`        | cubic-bezier(0.25, 0.1, 0.25, 1) |
| `ease-in`     | cubic-bezier(0.42, 0, 1, 1)      |
| `ease-out`    | cubic-bezier(0, 0, 0.58, 1)      |
| `ease-in-out` | cubic-bezier(0.42, 0, 0.58, 1)   |
| `ease-linear` | cubic-bezier(0, 0, 1, 1)         |

### Duração

Duração é o parâmetro que considera o tempo que o movimento ocorre.

| Classe      | Tempo (s) |
| ----------- | --------- |
| `very-fast` | 0,10      |
| `fast`      | 0,30      |
| `moderate`  | 0,50      |
| `slow`      | 0,80      |
| `very-slow` | 1,0       |
