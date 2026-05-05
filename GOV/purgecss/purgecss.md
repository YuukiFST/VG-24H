Devido ao grande número de opções de utilitários no Design System GOV.BR o tamanho do arquivo core.css é grande e pode impactar na performance da solução. Sugerimos o uso do [PurgeCSS](https://purgecss.com/) nas soluções que estejam rodando em **produção**.

Ele irá remover todo o CSS não usado e, portanto, diminuir o tamanho do arquivo impactando diretamente na performance da solução.

## Instalação

```bash
npm i --save-dev purgecss
```

### Modo de uso

Use pelo linha de comando ou por arquivo de configuração.

```bash
purgecss --css css/core.css --content ./**/*.html ./**/*.js --output ./css
```

O exemplo acima é uma forma simplificada de uso. Para mais informações e outras opções acesse a documentação oficial em <https://purgecss.com/configuration.html>.
