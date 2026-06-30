# VG-24h - Sistema de Gestão de Infraestrutura Urbana

O VG-24h é um projeto de plataforma digital concebido para otimizar a zeladoria urbana em Várzea Grande (MT).
O sistema foca no registro e monitoramento de incidentes como iluminação pública, pavimentação e saneamento, servindo como uma ponte direta entre o cidadão e a gestão municipal.

---

## Contexto Acadêmico e Cronograma

Este projeto é um trabalho original desenvolvido para a disciplina de Programação de Banco de Dados do 4º Semestre de TSI (Tecnologia em Sistemas Para Internet).

- Início do Desenvolvimento: 19 de março de 2026
- Status Atual: Protótipo em fase de implementação (MVP Acadêmico)
- Padrão Visual: Baseado no Design System Padrão Digital GOV.BR, conforme sugestão técnica apresentada em 11/03/2026 para alinhamento com padrões de mercado.

---

## Autoria e Implementação Técnica

A execução técnica, incluindo a arquitetura de sistemas, modelagem de dados (NeonDB), lógica de back-end (Django) e integração de interface, foi realizada integralmente pelos desenvolvedores:

- Bruno Dias Fonteles
- Fausto Yuuki
- Rafael Pereira Marques

---

## Propriedade Intelectual e Direitos

> ### AVISO LEGAL IMPORTANTE
>
> Embora o plano de trabalho conte com a colaboração de Yuri Batista de Almeida na definição inicial de requisitos e sugestão de referências (Product Owner - PO),
> a propriedade intelectual do código-fonte, arquitetura e implementação técnica pertence exclusivamente aos desenvolvedores supracitados.
>
> Este software é um protótipo estritamente acadêmico. Até a presente data, não possui qualquer termo de cessão de direitos, licença de uso comercial ou autorização de transferência de tecnologia para órgãos públicos ou empresas privadas.
> Este software é distribuído sob GPL-3.0. A propriedade intelectual e os créditos de autoria pertencem aos desenvolvedores. Uso comercial sem os termos da GPL-3.0 ou sem acordo formal com os autores não é autorizado (Lei 9.609/98 e Lei 9.610/98).

---

## Licença

Este repositório está protegido sob a licença GNU General Public License v3.0 (GPL-3.0). Esta licença garante que o código permaneça aberto para fins de estudo e que os créditos de autoria original sejam permanentemente preservados e vinculados ao projeto.

---

## Guia de Inicialização (Como Rodar o Projeto)

Para rodar o projeto localmente no Windows, siga os passos abaixo:

### 1. Requisitos

- Python 3.12 ou superior instalado.
- Git instalado (para clonar o repositório).

### 2. Como Clonar e Rodar em Outra Máquina

Se você acabou de clonar este repositório, siga estes passos para configurar o ambiente:

1. **Abra o terminal** na pasta onde você clonou o projeto.
2. **Crie o Ambiente Virtual**:
   ```powershell
   python -m venv backend\.venv
   ```
3. **Ative o Ambiente Virtual**:
   ```powershell
   .\backend\.venv\Scripts\activate
   ```
4. **Instale as Dependências**:
   ```powershell
   pip install -r backend\requirements.txt
   ```
5. **Configure as Variáveis de Ambiente**:
   - Localize o arquivo `backend\.env.example` (ou crie um novo arquivo `backend\.env`).
   - Renomeie para `.env` se necessário e preencha as credenciais do banco de dados:
     ```env
     SECRET_KEY='sua_secret_key_aqui'
     DEBUG=True
     ALLOWED_HOSTS=localhost,127.0.0.1
     POSTGRES_DB=nome_do_banco
     POSTGRES_USER=usuario
     POSTGRES_PASSWORD=senha
     POSTGRES_HOST=host_do_banco
     POSTGRES_PORT=5432
     POSTGRES_SSL=require
     ```
6. **Inicie o Servidor**:
   ```powershell
   cd backend
   python manage.py runserver
   ```

### 3. Acesso

Após iniciar, abra seu navegador em: **[http://localhost:8000/](http://localhost:8000/)**

---

## Uso com o Gerenciador UV (Opcional)

Se você tiver o `uv` instalado, o processo é simplificado:

```powershell
uv run --project backend python manage.py runserver
```
