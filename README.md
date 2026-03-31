# 🏙️ VG-24h - Sistema de Gestão de Infraestrutura Urbana

O **VG-24h** é um projeto de plataforma digital concebido para otimizar a zeladoria urbana em Várzea Grande (MT).
O sistema foca no registro e monitoramento de incidentes como iluminação pública, pavimentação e saneamento, servindo como uma ponte direta entre o cidadão e a gestão municipal.

---

## 🎓 Contexto Acadêmico e Cronograma

Este projeto é um trabalho original desenvolvido para a disciplina de **Programação de Banco de Dados** do 4º Semestre de **TSI (Tecnologia em Sistemas Para Internet)**.

- **Início do Desenvolvimento:** 19 de março de 2026
- **Status Atual:** Protótipo em fase de implementação (MVP Acadêmico)
- **Padrão Visual:** Baseado no Design System Padrão Digital GOV.BR, conforme sugestão técnica apresentada em 11/03/2026 para alinhamento com padrões de mercado.

---

## ✍️ Autoria e Implementação Técnica

A execução técnica, incluindo a arquitetura de sistemas, modelagem de dados (NeonDB), lógica de back-end (Django) e integração de interface, foi realizada integralmente pelos desenvolvedores:

- **Bruno Dias Fonteles**
- **Fausto Yuuki Tadano Araújo Freire**
- **Rafael Pereira Marques**

---

## 🛡️ Propriedade Intelectual e Direitos

> ### ⚠️ AVISO LEGAL IMPORTANTE
>
> Embora o plano de trabalho conte com a colaboração de **Yuri Batista de Almeida** na definição inicial de requisitos e sugestão de referências (Product Owner - PO),
> a **propriedade intelectual do código-fonte, arquitetura e implementação técnica** pertence exclusivamente aos desenvolvedores supracitados.
>
> Este software é um **protótipo estritamente acadêmico**. Até a presente data, **não possui qualquer termo de cessão de direitos**, licença de uso comercial ou autorização de transferência de tecnologia para órgãos públicos ou empresas privadas.
> Este software é distribuído sob GPL-3.0. A propriedade intelectual e os créditos de autoria pertencem aos desenvolvedores. Uso comercial sem os termos da GPL-3.0 ou sem acordo formal com os autores não é autorizado (Lei 9.609/98 e Lei 9.610/98).

---

## 📄 Licença

Este repositório está protegido sob a licença **GNU General Public License v3.0 (GPL-3.0)**. Esta licença garante que o código permaneça aberto para fins de estudo e que os créditos de autoria original sejam permanentemente preservados e vinculados ao projeto.

---

## 🛠️ Guia de Inicialização (Como Rodar o Projeto)

Para rodar o projeto localmente no Windows, siga os passos abaixo:

### 1. Requisitos

- **Python 3.12** instalado.
- O projeto usa um **Ambiente Virtual (venv)** para isolar o Django e as bibliotecas.

### 2. Passo Automático (Recomendado)

Se você tiver o `uv` instalado, basta rodar na pasta raiz:

```powershell
uv run --project backend python manage.py runserver
```

### 3. Passo Manual (Padrão)

Se preferir o modo tradicional, no seu terminal:

1. **Entre na pasta do código**:
   ```powershell
   cd backend
   ```
2. **Ative o Ambiente Virtual** (Isso "liga" o Django do projeto):
   ```powershell
   .\.venv\Scripts\activate
   ```
3. **Inicie o Servidor**:
   ```powershell
   python manage.py runserver
   ```

### 🌐 Acesso

Após iniciar, abra seu navegador em: **[http://localhost:8000/](http://localhost:8000/)**

---

## 📋 Credenciais de Teste

Para testar as diferentes visões do portal, consulte os arquivos de roteiro na raiz:

---

## 👥 Guia para Novos Desenvolvedores (Clone)

Se você acabou de baixar o projeto do GitHub, o seu código virá sem a "caixinha" de ferramentas (`.venv`) e sem as configurações de banco (`.env`) por segurança. Siga este passo-a-passo:

1. **Abra o terminal na pasta raiz**.
2. **Crie seu Ambiente Virtual**:
   ```powershell
   python -m venv backend\.venv
   ```
3. **Instale as bibliotecas**:
   ```powershell
   .\backend\.venv\Scripts\pip install -r backend\requirements.txt
   ```
4. **Configure o Banco de Dados**:
   - Copie o arquivo `backend\.env.example` e renomeie para `backend\.env`.
   - Peça as **credenciais do banco (Neon)** para o dono do projeto e preencha no arquivo `.env`.
5. **Rode o projeto**: (veja o _Guia de Inicialização_ acima).
