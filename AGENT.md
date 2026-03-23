## Regras Específicas do GOVBR-DS

### Acessibilidade (WCAG 2.1)

- **Sempre** incluir atributos ARIA apropriados.
- **Sempre** garantir navegação por teclado.
- Usar elementos semânticos HTML5.
- Garantir contraste de cores adequado.

### Nomenclatura de Classes CSS

- Seguir padrão BEM do GOVBR-DS: `br-componente`, `br-componente__elemento`, `br-componente--modificador`.
- Classes principais sempre com prefixo `br-`.

### Ícones

- Usar Font Awesome 5.x via componente `Icon` de `@/common/Icon`.
- Formato: `<Icon icon="nome-do-icone" />`.

### Propriedades de Espaçamento (IMtProps)

Componentes suportam props de margem/espaçamento:

- `m`, `mt`, `mr`, `mb`, `ml`, `mx`, `my` (margin)
- `p`, `pt`, `pr`, `pb`, `pl`, `px`, `py` (padding)

## Criando Novos Componentes

**Use o gerador Plop:**

```bash
npm run generate
# Informe: BrNomeDoComponente
```

Isso cria automaticamente:

- `src/components/BrNomeDoComponente/index.tsx`
- `src/components/BrNomeDoComponente/stories.tsx`
- `src/components/BrNomeDoComponente/BrNomeDoComponente.test.tsx`

**Após criar:**

1. Implementar o componente seguindo os padrões acima.
2. Adicionar testes unitários.
3. Documentar no Storybook.
4. Exportar em `src/index.ts`.

## Git

- Executar operações do Git **apenas** com solicitação explícita.
- Usar Conventional Commits: `feat:`, `fix:`, `docs:`, etc.
- Executar `npm run commit` para commit interativo.
- Consultar [Wiki do GOVBR-DS](https://gov.br/ds/wiki/) para padrões detalhados.

## Referências

- [Documentação GOVBR-DS](https://www.gov.br/ds)
- [Storybook do Projeto](https://govbr-ds.gitlab.io/bibliotecas/react-components/)
- [React Docs](https://react.dev/)
- [TypeScript Docs](https://www.typescriptlang.org/)

## Dicas para Agentes de IA

1. **Sempre** verificar componentes similares existentes antes de criar novos.
2. **Sempre** manter consistência com padrões do GOVBR-DS.
3. **Nunca** remover código de teste sem solicitação explícita.
4. **Nunca** adicionar testes automaticamente - apenas quando solicitado.
5. Priorizar acessibilidade e semântica HTML.
6. Usar português para comentários e documentação.
7. Consultar `@govbr-ds/core` para classes CSS disponíveis.
8. Ao modificar componentes, manter retrocompatibilidade quando possível.

## Contexto Institucional

Este é um projeto **open-source governamental** com múltiplos contribuidores. Mudanças devem:

- Seguir padrões estabelecidos.
- Ser bem documentadas.
- Manter compatibilidade com especificações do Padrão Digital de Governo.
- Considerar impacto em sistemas governamentais que usam a biblioteca.
