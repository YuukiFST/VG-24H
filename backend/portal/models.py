from django.db import models


class StatusChamado(models.Model):
    id_status = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    sigla = models.CharField(max_length=2, unique=True)

    class Meta:
        managed = False
        db_table = "status_chamado"

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


class Cidadao(models.Model):
    id_cidadao = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)
    senha_hash = models.CharField(max_length=255)
    senha_temporaria = models.CharField(max_length=200, blank=True, null=True)
    perfil = models.CharField(max_length=3, default="CID")
    rua = models.CharField(max_length=100, blank=True, null=True)
    num_endereco = models.CharField(max_length=10, blank=True, null=True)
    complemento_endereco = models.CharField(max_length=200, blank=True, null=True)
    bairro_endereco = models.CharField(max_length=200, blank=True, null=True)
    cep_endereco = models.CharField(max_length=8, blank=True, null=True)
    dt_cadastro = models.DateTimeField()
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "cidadao"

    def __str__(self):
        return self.nome_completo


class Servidor(models.Model):
    id_servidor = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)
    senha_hash = models.CharField(max_length=255)
    senha_temporaria = models.CharField(max_length=200, blank=True, null=True)
    perfil = models.CharField(max_length=3)
    dt_cadastro = models.DateTimeField()
    ativo = models.BooleanField(default=True)
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


class Chamado(models.Model):
    id_chamado = models.AutoField(primary_key=True)
    num_protocolo = models.CharField(max_length=20, unique=True)
    prioridade = models.IntegerField(default=0)
    descricao = models.CharField(max_length=500)
    ponto_de_referencia = models.CharField(max_length=100, blank=True, null=True)
    resolucao = models.CharField(max_length=500, blank=True, null=True)
    nota_avaliacao = models.IntegerField(blank=True, null=True)
    comentario_avaliacao = models.CharField(max_length=500, blank=True, null=True)
    dt_abertura = models.DateTimeField()
    dt_conclusao = models.DateTimeField(blank=True, null=True)
    dt_avaliacao = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField()
    id_servico = models.ForeignKey(
        Servico,
        models.DO_NOTHING,
        db_column="id_servico",
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
        related_name="chamados",
    )

    class Meta:
        managed = False
        db_table = "chamado"

    @property
    def status_atual(self):
        """Retorna o StatusChamado atual (último histórico)."""
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
    def atualizado_em(self):
        """Retorna a data/hora da última alteração de status."""
        ultimo = self.historicos.order_by("-dt_alteracao").first()
        return ultimo.dt_alteracao if ultimo else self.dt_abertura


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


class HistoricoChamado(models.Model):
    id_historico_chamado = models.AutoField(primary_key=True)
    dt_alteracao = models.DateTimeField()
    observacao = models.CharField(max_length=500, blank=True, null=True)
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
        related_name="historicos",
    )
    id_servidor = models.ForeignKey(
        Servidor,
        models.DO_NOTHING,
        db_column="id_servidor",
        blank=True,
        null=True,
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

