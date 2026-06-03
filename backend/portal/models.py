"""
models.py — Mapeamento ORM do Portal VG 24H

Este arquivo define as classes Python que representam as tabelas do banco
de dados. Cada classe equivale a uma tabela e cada atributo a uma coluna.

Todas as classes usam managed = False no Meta, o que significa que o Django
nao cria nem altera as tabelas automaticamente. As tabelas foram criadas
manualmente via scripts SQL (pasta database/). O Django apenas le e
escreve nos registros.

Os modelos existem para:
- Formularios: ModelChoiceField usa queryset do ORM para validar FKs.
- Propriedades utilitarias: Chamado.status_atual, Chamado.cor_semaforo.
- Metodos de classe: Chamado.calcular_stats().

As views, por sua vez, usam SQL puro para todas as operacoes de
leitura e escrita (INSERT, UPDATE, SELECT, DELETE).
"""

from django.db import models
from django.utils import timezone


class StatusChamado(models.Model):
    """Catalogo dos 5 status possiveis de um chamado.

    AB = Aberto, EA = Em Atendimento, EE = Em Execucao,
    CO = Concluido, CA = Cancelado. Registros fixos, nao devem
    ser criados ou removidos pelo usuario.
    """
    id_status = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    sigla = models.CharField(max_length=2, unique=True)

    class Meta:
        managed = False
        db_table = "status_chamado"

    def __str__(self):
        return self.descricao or self.sigla


class Secretaria(models.Model):
    """Orgaos municipais. Atualmente so existe uma (VG 24H).

    FK apontada por: Servidor.id_secretaria e CategoriaServico.id_secretaria.
    """
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
    """Agrupa servicos por area (ex: Infraestrutura, Mobilidade Urbana).

    FK para Secretaria. Cada categoria pode ter varios servicos.
    """
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
    """Tipos de servico com prazos para o semaforo de urgencia.

    Cada servico pertence a uma Categoria e tem dois prazos:
    - prazo_amarelo_dias: dias ate o chamado ficar amarelo (atencao).
    - prazo_vermelho_dias: dias ate ficar vermelho (critico).
    Esses prazos sao usados pela funcao cor_semaforo() em db.py.
    """
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
    """Bairros de Varzea Grande/MT. Usado como endereco do chamado.

    O campo regiao aceita valores predefinidos (Central, Norte, Sul, etc.)
    para evitar inconsistencias de digitacao.
    """
    id_bairro = models.AutoField(primary_key=True)
    nome_bairro = models.CharField(max_length=100, unique=True)
    cep = models.CharField(max_length=8, blank=True, null=True)
    regiao = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "bairro"

    def __str__(self):
        return self.nome_bairro


class Cidadao(models.Model):
    """Usuarios do portal (autenticacao propria, nao usa django.contrib.auth).

    A senha eh armazenada como hash bcrypt (senha_hash), nunca em texto puro.
    O campo perfil define o tipo: 'CID' = cidadao padrao.
    """
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
    """Colaboradores e gestores da prefeitura.

    Perfis: 'GES' = gestor (acesso total), 'COL' = colaborador (parcial).
    O campo senha_temporaria indica primeiro acesso (deve trocar senha).
    """
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
    """Tabela central do sistema. Registra as solicitacoes dos cidadaos.

    Nao possui campo id_status. O status eh determinado pelo ultimo
    registro de HistoricoChamado (padrao event sourcing).

    Properties principais:
    - status_atual: objeto StatusChamado do ultimo historico
    - sigla_status: sigla do status como string (ex: 'AB', 'CO')
    - cor_semaforo: 'verde', 'amarelo' ou 'vermelho' conforme prazos
    - ultima_atualizacao: data/hora do ultimo historico
    """
    id_chamado = models.AutoField(primary_key=True)
    num_protocolo = models.CharField(max_length=20, unique=True)
    prioridade = models.IntegerField(default=0)
    ponto_de_referencia = models.CharField(max_length=100, blank=True, null=True)
    descricao = models.CharField(max_length=500)
    resolucao = models.CharField(max_length=600, blank=True, null=True)
    nota_avaliacao = models.IntegerField(blank=True, null=True)
    comentario_avaliacao = models.CharField(max_length=500, blank=True, null=True)
    dt_abertura = models.DateTimeField()
    dt_conclusao = models.DateTimeField(blank=True, null=True)
    dt_avaliacao = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField()
    id_servico = models.ForeignKey(Servico, models.DO_NOTHING, db_column="id_servico")
    id_bairro = models.ForeignKey(Bairro, models.DO_NOTHING, db_column="id_bairro")
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
    def _ultimo_historico(self):
        """Retorna o historico mais recente. Usa cache do prefetch_related se disponivel."""
        try:
            historicos = list(self.historicos.all())
            if not historicos:
                return None
            return max(historicos, key=lambda h: h.dt_alteracao)
        except (ValueError, AttributeError):
            return None

    @property
    def status_atual(self):
        """Retorna o objeto StatusChamado do ultimo historico (fonte da verdade)."""
        ultimo = self._ultimo_historico
        return ultimo.id_status if ultimo else None

    @property
    def sigla_status(self):
        """Retorna a sigla do status atual como string (ex: 'AB', 'CO')."""
        st = self.status_atual
        return (st.sigla or "").strip() if st else ""

    @property
    def ultima_atualizacao(self):
        """Retorna a data/hora da ultima alteracao de status."""
        ultimo = self._ultimo_historico
        return ultimo.dt_alteracao if ultimo else self.dt_abertura

    @property
    def cor_semaforo(self):
        """Classifica o chamado por urgencia usando os prazos do servico.

        Retorna 'verde' (dentro do prazo), 'amarelo' (atencao) ou 'vermelho' (critico).
        """
        s = self.id_servico
        dias = (timezone.now() - self.dt_abertura).days
        if dias >= s.prazo_vermelho_dias:
            return "vermelho"
        if dias >= s.prazo_amarelo_dias:
            return "amarelo"
        return "verde"

    @classmethod
    def calcular_stats(cls, queryset):
        """Calcula estatisticas do semaforo para um queryset de chamados.

        Retorna dict: {'no_prazo': N, 'atencao': N, 'critico': N}.
        """
        stats = {"no_prazo": 0, "atencao": 0, "critico": 0}
        now = timezone.now()
        for ch in queryset.select_related("id_servico"):
            dias = (now - ch.dt_abertura).days
            s = ch.id_servico
            if dias >= s.prazo_vermelho_dias:
                stats["critico"] += 1
            elif dias >= s.prazo_amarelo_dias:
                stats["atencao"] += 1
            else:
                stats["no_prazo"] += 1
        return stats


class FotoChamado(models.Model):
    """Fotos anexadas aos chamados. URLs armazenadas (Cloudinary ou local).

    O banco possui um trigger de integridade que bloqueia INSERT
    se o chamado estiver concluido ou cancelado.
    """
    id_foto = models.AutoField(primary_key=True)
    url_foto = models.CharField(max_length=200)
    dt_upload = models.DateTimeField()
    id_chamado = models.ForeignKey(Chamado, models.DO_NOTHING, db_column="id_chamado")

    class Meta:
        managed = False
        db_table = "foto_chamado"


class HistoricoChamado(models.Model):
    """Historico de alteracoes de status — fonte da verdade para status.

    Cada insercao nesta tabela pode disparar dois triggers:
    - Trigger 2A: atualiza atualizado_em na tabela chamado.
    - Trigger 2B: se o novo status eh CO ou CA, seta dt_conclusao = NOW()
      e gera uma notificacao automatica para o cidadao.

    O campo id_servidor pode ser NULL quando o registro foi criado
    automaticamente (ex: abertura de chamado pelo Trigger 1).
    """
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
    id_status = models.ForeignKey(StatusChamado, models.DO_NOTHING, db_column="id_status")

    class Meta:
        managed = False
        db_table = "historico_chamado"


class Notificacao(models.Model):
    """Notificacoes geradas automaticamente pelo Trigger 2B.

    Cada mudanca de status gera uma notificacao para o cidadao
    dono do chamado, informando a nova situacao.
    """
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
    """Banners da pagina inicial (carrossel de noticias/destaques).

    Tabela adicional fora das 11 entidades principais do DER.
    A ordem controla a posicao no carrossel e eh gerenciada
    pelo gestor via painel administrativo.
    """
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
