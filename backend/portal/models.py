"""
models.py — Mapeamento ORM (Object-Relational Mapping) do Portal VG 24H

Este arquivo define as CLASSES PYTHON que representam as TABELAS DO BANCO DE DADOS.
Cada classe = uma tabela. Cada atributo = uma coluna.

O Django ORM traduz automaticamente operações Python em SQL:
  - Cidadao.objects.get(pk=5)          → SELECT * FROM cidadao WHERE id_cidadao = 5
  - Cidadao.objects.filter(ativo=True) → SELECT * FROM cidadao WHERE ativo = true
  - Cidadao.objects.create(...)        → INSERT INTO cidadao (...) VALUES (...)
  - obj.save()                         → UPDATE cidadao SET ... WHERE id_cidadao = X
  - obj.delete()                       → DELETE FROM cidadao WHERE id_cidadao = X

IMPORTANTE: Todas as classes usam 'managed = False' no Meta.
Isso significa que o Django NÃO cria nem altera as tabelas automaticamente.
As tabelas foram criadas manualmente via scripts SQL (pasta database/).
O Django apenas LÊ e ESCREVE nos registros.

Relacionamentos (FOREIGN KEYS) são mapeados com models.ForeignKey(),
que equivalem a REFERENCES no SQL. O Django usa isso para fazer JOINs
automaticamente quando usamos select_related() ou acessamos obj.id_servico.nome.
"""

from django.db import models


# ============================================================
# TABELA: status_chamado
# Armazena os 5 status possíveis de um chamado:
# AB (Aberto), EA (Em Atendimento), EE (Em Execução), CO (Concluído), CA (Cancelado)
# ============================================================
class StatusChamado(models.Model):
    id_status = models.AutoField(primary_key=True)  # SERIAL PRIMARY KEY no SQL
    descricao = models.CharField(max_length=200, blank=True, null=True)
    sigla = models.CharField(max_length=2, unique=True)  # UNIQUE no SQL

    class Meta:
        managed = False      # Django NÃO gerencia esta tabela (criada via SQL)
        db_table = "status_chamado"  # Nome exato da tabela no PostgreSQL

    def __str__(self):
        return self.descricao or self.sigla


class Secretaria(models.Model):
    id_secretaria = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    gestor_responsavel = models.CharField(max_length=100)
    cpf = models.CharField(max_length=11, unique=True)
    email = models.CharField(max_length=255, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "secretaria"

    def __str__(self):
        return self.nome


class CategoriaServico(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    id_secretaria = models.ForeignKey(
        Secretaria,
        models.DO_NOTHING,
        db_column="id_secretaria",
    )

    class Meta:
        managed = False
        db_table = "categoria_servico"

    def __str__(self):
        return self.nome


class Servico(models.Model):
    id_servico = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    prazo_amarelo_dias = models.IntegerField(default=15)
    prazo_vermelho_dias = models.IntegerField(default=30)
    ativo = models.BooleanField(default=True)
    id_categoria = models.ForeignKey(
        CategoriaServico,
        models.DO_NOTHING,
        db_column="id_categoria",
        related_name="servicos",
    )

    class Meta:
        managed = False
        db_table = "servico"

    def __str__(self):
        return self.nome


class Bairro(models.Model):
    id_bairro = models.AutoField(primary_key=True)
    nome_bairro = models.CharField(max_length=100, unique=True)
    cep = models.CharField(max_length=8)
    regiao = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "bairro"

    def __str__(self):
        return self.nome_bairro


# ============================================================
# TABELA: cidadao
# Usuários do portal (login próprio, NÃO usa django.contrib.auth).
# O campo 'perfil' define o tipo: 'CID' = Cidadão.
# 'senha_hash' armazena o hash bcrypt da senha (NUNCA a senha real).
# ============================================================
class Cidadao(models.Model):
    id_cidadao = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)    # CPF único no banco (UNIQUE)
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)  # Email único (UNIQUE)
    senha_hash = models.CharField(max_length=255)  # Hash bcrypt, ex: 'pbkdf2_sha256$720000$...'
    senha_temporaria = models.CharField(max_length=200, blank=True, null=True)
    perfil = models.CharField(max_length=3, default="CID")  # 'CID' = Cidadão
    rua = models.CharField(max_length=100, blank=True, null=True)
    num_endereco = models.CharField(max_length=10, blank=True, null=True)
    complemento_endereco = models.CharField(max_length=200, blank=True, null=True)
    bairro_endereco = models.CharField(max_length=200, blank=True, null=True)
    cep_endereco = models.CharField(max_length=8, blank=True, null=True)
    dt_cadastro = models.DateTimeField()
    ativo = models.BooleanField(default=True)  # Soft delete: false = conta desativada

    class Meta:
        managed = False
        db_table = "cidadao"

    def __str__(self):
        return self.nome_completo


# ============================================================
# TABELA: servidor
# Colaboradores e gestores da prefeitura.
# O campo 'perfil' define o nível de acesso:
#   'GES' = Gestor (acesso total)    'COL' = Colaborador (acesso parcial)
# Possui FOREIGN KEY para secretaria (qual secretaria ele pertence).
# ============================================================
class Servidor(models.Model):
    id_servidor = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)
    senha_hash = models.CharField(max_length=255)
    senha_temporaria = models.CharField(max_length=200, blank=True, null=True)
    perfil = models.CharField(max_length=3)  # 'GES' ou 'COL'
    dt_cadastro = models.DateTimeField()
    ativo = models.BooleanField(default=True)
    # FOREIGN KEY: REFERENCES secretaria(id_secretaria)
    # models.DO_NOTHING = não faz CASCADE no Django (gerenciado pelo banco)
    id_secretaria = models.ForeignKey(
        Secretaria,
        models.DO_NOTHING,
        db_column="id_secretaria",
    )

    class Meta:
        managed = False
        db_table = "servidor"

    def __str__(self):
        return self.nome_completo


# ============================================================
# TABELA: chamado
# Tabela CENTRAL do sistema. Registra as solicitações dos cidadãos.
# Possui 3 FOREIGN KEYS: servico, bairro e cidadao.
#
# Relacionamentos:
#   chamado.id_servico → JOIN com tabela servico
#   chamado.id_bairro  → JOIN com tabela bairro
#   chamado.id_cidadao → JOIN com tabela cidadao (quem abriu)
#
# O Django permite acessar dados relacionados diretamente:
#   ch.id_servico.nome      → nome do serviço (faz JOIN automaticamente)
#   ch.id_cidadao.email     → email do cidadão que abriu
#   ch.historicos.all()     → todos os registros de histórico (related_name)
# ============================================================
class Chamado(models.Model):
    id_chamado = models.AutoField(primary_key=True)
    num_protocolo = models.CharField(max_length=20, unique=True)  # Ex: '2026000001'
    prioridade = models.IntegerField(default=0)  # 0 a 5 (CHECK no banco)
    ponto_de_referencia = models.CharField(max_length=100, blank=True, null=True)
    descricao = models.CharField(max_length=500)
    resolucao = models.CharField(max_length=600, blank=True, null=True)
    nota_avaliacao = models.IntegerField(blank=True, null=True)  # 1 a 5
    comentario_avaliacao = models.CharField(max_length=500, blank=True, null=True)
    dt_abertura = models.DateTimeField()
    dt_conclusao = models.DateTimeField(blank=True, null=True)
    dt_avaliacao = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField()
    # FOREIGN KEYS — equivalem a REFERENCES no SQL
    id_servico = models.ForeignKey(
        Servico,
        models.DO_NOTHING,
        db_column="id_servico",  # Nome exato da coluna no banco
    )
    id_bairro = models.ForeignKey(
        Bairro,
        models.DO_NOTHING,
        db_column="id_bairro",
    )
    id_cidadao = models.ForeignKey(
        Cidadao,
        models.DO_NOTHING,
        db_column="id_cidadao",
        related_name="chamados",  # Permite fazer cidadao.chamados.all()
    )

    class Meta:
        managed = False
        db_table = "chamado"

    @property
    def status_atual(self):
        """
        Retorna o status atual do chamado consultando o último histórico.
        SQL equivalente:
          SELECT s.* FROM historico_chamado h
          JOIN status_chamado s ON h.id_status = s.id_status
          WHERE h.id_chamado = X
          ORDER BY h.dt_alteracao DESC LIMIT 1
        """
        ultimo = (
            self.historicos.select_related("id_status")
            .order_by("-dt_alteracao")
            .first()
        )
        return ultimo.id_status if ultimo else None

    @property
    def sigla_status(self):
        """Retorna a sigla do status atual (ex: 'AB', 'CO')."""
        st = self.status_atual
        return (st.sigla or "").strip() if st else ""

    @property
    def ultima_atualizacao(self):
        """Retorna a data/hora da última alteração de status."""
        ultimo = self.historicos.order_by("-dt_alteracao").first()
        return ultimo.dt_alteracao if ultimo else self.dt_abertura


# ============================================================
# TABELA: foto_chamado
# Fotos anexadas aos chamados. URLs armazenadas (Cloudinary).
# FOREIGN KEY para chamado.
# ============================================================
class FotoChamado(models.Model):
    id_foto = models.AutoField(primary_key=True)
    url_foto = models.CharField(max_length=200)
    dt_upload = models.DateTimeField()
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
    )

    class Meta:
        managed = False
        db_table = "foto_chamado"


# ============================================================
# TABELA: historico_chamado
# Registra CADA mudança de status de um chamado (timeline).
# Exemplo: Aberto → Em Atendimento → Concluído
# FOREIGN KEYS: chamado, servidor (quem alterou), status_chamado
# related_name="historicos" permite fazer chamado.historicos.all()
# ============================================================
class HistoricoChamado(models.Model):
    id_historico_chamado = models.AutoField(primary_key=True)
    dt_alteracao = models.DateTimeField()
    observacao = models.CharField(max_length=500, blank=True, null=True)
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
        related_name="historicos",  # chamado.historicos.all() retorna todo o histórico
    )
    id_servidor = models.ForeignKey(
        Servidor,
        models.DO_NOTHING,
        db_column="id_servidor",
        blank=True,
        null=True,  # NULL quando o sistema cria automaticamente (ex: abertura)
    )
    id_status = models.ForeignKey(
        StatusChamado,
        models.DO_NOTHING,
        db_column="id_status",
    )

    class Meta:
        managed = False
        db_table = "historico_chamado"


class Notificacao(models.Model):
    id_notificacao = models.AutoField(primary_key=True)
    mensagem = models.CharField(max_length=200)
    lida = models.BooleanField(default=False)
    arquivada = models.BooleanField(default=False)
    dt_envio = models.DateTimeField()
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "notificacao"


class BannerPublicacao(models.Model):
    id_banner = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descricao = models.CharField(max_length=300, blank=True, null=True)
    url_imagem = models.CharField(max_length=500)
    link = models.CharField(max_length=500, blank=True, null=True)
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)
    dt_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "banner_publicacao"
        ordering = ["ordem", "-dt_criacao"]

    def __str__(self):
        return self.titulo

