from django.db import models


class StatusChamado(models.Model):
    id_status = models.AutoField(primary_key=True)
    tipo_status = models.CharField(max_length=2, unique=True)
    descricao = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "status_chamado"


class CategoriaServico(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200, unique=True)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "categoria_servico"


class Servico(models.Model):
    id_servico = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(
        CategoriaServico,
        models.DO_NOTHING,
        db_column="id_categoria",
    )
    nome = models.CharField(max_length=200)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    prazo_amarelo_dias = models.IntegerField()
    prazo_vermelho_dias = models.IntegerField()
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "servico"


class BairroRegiao(models.Model):
    id_bairro = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200, unique=True)
    cep = models.CharField(max_length=8)
    regiao_administrativa = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "bairro_regiao"


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)
    senha_hash = models.CharField(max_length=255)
    senha_temporaria = models.CharField(max_length=255, blank=True, null=True)
    perfil = models.CharField(max_length=3)
    rua = models.CharField(max_length=200, blank=True, null=True)
    numero_endereco = models.CharField(max_length=10, blank=True, null=True)
    complemento_endereco = models.CharField(max_length=200, blank=True, null=True)
    bairro_endereco = models.CharField(max_length=200, blank=True, null=True)
    cep_endereco = models.CharField(max_length=8, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    dt_cadastro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "usuario"


class Chamado(models.Model):
    id_chamado = models.AutoField(primary_key=True)
    protocolo = models.CharField(max_length=20, unique=True)
    prioridade = models.SmallIntegerField()
    rua = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=200, blank=True, null=True)
    ponto_referencia = models.CharField(max_length=200, blank=True, null=True)
    descricao = models.CharField(max_length=500)
    resolucao = models.CharField(max_length=500, blank=True, null=True)
    nota_avaliacao = models.SmallIntegerField(blank=True, null=True)
    comentario_avaliacao = models.CharField(max_length=500, blank=True, null=True)
    dt_abertura = models.DateTimeField()
    dt_conclusao = models.DateTimeField(blank=True, null=True)
    dt_avaliacao = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField()
    id_usuario = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="id_usuario",
        related_name="chamados",
    )
    id_servico = models.ForeignKey(
        Servico,
        models.DO_NOTHING,
        db_column="id_servico",
    )
    id_status = models.ForeignKey(
        StatusChamado,
        models.DO_NOTHING,
        db_column="id_status",
    )
    id_bairro = models.ForeignKey(
        BairroRegiao,
        models.DO_NOTHING,
        db_column="id_bairro",
    )

    class Meta:
        managed = False
        db_table = "chamado"


class FotoChamado(models.Model):
    id_foto = models.AutoField(primary_key=True)
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
    )
    url_foto = models.CharField(max_length=500)
    dt_upload = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "foto_chamado"


class HistoricoChamado(models.Model):
    id_historico = models.AutoField(primary_key=True)
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
    )
    id_usuario_responsavel = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="id_usuario_responsavel",
        blank=True,
        null=True,
    )
    tipo_status = models.CharField(max_length=2)
    dt_alteracao = models.DateTimeField()
    observacao = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "historico_chamado"


class ObservacaoChamado(models.Model):
    id_observacao = models.AutoField(primary_key=True)
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
    )
    id_usuario_autor = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="id_usuario_autor",
    )
    texto_observacao = models.CharField(max_length=500)
    criado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "observacao_chamado"


class Notificacao(models.Model):
    id_notificacao = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="id_usuario",
        related_name="notificacoes",
    )
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
        blank=True,
        null=True,
    )
    mensagem = models.CharField(max_length=200)
    lida = models.BooleanField(default=False)
    arquivada = models.BooleanField(default=False)
    dt_envio = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "notificacao"
