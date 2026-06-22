"""
models.py — Mapeamento ORM do Portal VG 24H

Aqui eu defino as classes Python que espelham as tabelas do banco. Cada
classe eh uma tabela e cada atributo eh uma coluna.

PONTO MAIS IMPORTANTE pra eu nao esquecer: TODAS as classes tem
managed = False no Meta. Isso quer dizer que o Django NAO cria nem mexe na
estrutura das tabelas. Quem cria as tabelas sou eu, com os scripts SQL la
da pasta database/. O Django so le e escreve os registros.

Entao pra que servem esses models? Pra tres coisas:
- Forms: o ModelChoiceField usa o queryset do ORM pra validar as FKs.
- Properties uteis: Chamado.status_atual, Chamado.cor_semaforo.
- Metodos de classe: Chamado.calcular_stats().

E de novo: as views fazem tudo em SQL puro (INSERT, UPDATE, SELECT, DELETE).
"""

# models do ORM e timezone pra trabalhar com datas "aware"
from django.db import models
from django.utils import timezone


class StatusChamado(models.Model):
    """Catalogo com os 5 status possiveis de um chamado.

    AB = Aberto, EA = Em Atendimento, EE = Em Execucao,
    CO = Concluido, CA = Cancelado. Sao registros fixos, ninguem cria nem
    apaga pela tela.
    """
    id_status = models.AutoField(primary_key=True)  # PK auto-incremento
    descricao = models.CharField(max_length=200, blank=True, null=True)  # texto amigavel
    sigla = models.CharField(max_length=2, unique=True)  # AB/EA/EE/CO/CA, unica

    class Meta:
        managed = False  # quem cria a tabela eh o meu SQL, nao o Django
        db_table = "status_chamado"  # nome exato da tabela no banco

    def __str__(self):
        # mostro a descricao; se nao tiver, caio pra sigla
        return self.descricao or self.sigla


class Secretaria(models.Model):
    """Orgao municipal. Por enquanto so tem uma (a VG 24H).

    Quem aponta FK pra ca: Servidor.id_secretaria e CategoriaServico.id_secretaria.
    """
    id_secretaria = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    gestor_responsavel = models.CharField(max_length=100)
    cpf = models.CharField(max_length=11, unique=True)  # CPF do gestor, unico
    email = models.CharField(max_length=255, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = False  # tabela vem do meu SQL
        db_table = "secretaria"

    def __str__(self):
        return self.nome


class CategoriaServico(models.Model):
    """Agrupa os servicos por area (ex: Infraestrutura, Mobilidade Urbana).

    Tem FK pra Secretaria. Uma categoria pode ter varios servicos.
    """
    id_categoria = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)  # nome da categoria, unico
    descricao = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    # FK pra secretaria. DO_NOTHING porque quem cuida do ON DELETE eh o banco,
    # nao o Django. db_column fixa o nome da coluna real
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


class ConfiguracaoSemaforo(models.Model):
    """Prazos globais do semaforo de urgencia. Eh um singleton (so 1 linha).

    No banco tem um CHECK id = 1 garantindo que so existe esse 1 registro.
    Eu uso ela no Chamado.cor_semaforo e em todo calculo de semaforo.
    """
    id = models.IntegerField(primary_key=True, default=1)  # sempre 1
    prazo_amarelo_dias = models.IntegerField(default=15)  # apos X dias -> amarelo
    prazo_vermelho_dias = models.IntegerField(default=30)  # apos X dias -> vermelho

    class Meta:
        managed = False
        db_table = "configuracao_semaforo"

    @classmethod
    def get_singleton(cls):
        # pego o unico registro; se por algum motivo nao existir, eu crio
        # ja com os prazos padrao pra nunca retornar None
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create(id=1, prazo_amarelo_dias=15, prazo_vermelho_dias=30)
        return obj


class Servico(models.Model):
    """Tipos de servico que o cidadao pode pedir."""
    id_servico = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)  # uso esse flag pra filtrar no form
    # FK pra categoria. related_name="servicos" me deixa fazer categoria.servicos
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
    """Bairros de Varzea Grande/MT. Uso como endereco do chamado.

    O regiao aceita valores predefinidos (Central, Norte, Sul, etc.) pra
    evitar gente digitando regiao de qualquer jeito e baguncar o filtro.
    """
    id_bairro = models.AutoField(primary_key=True)
    nome_bairro = models.CharField(max_length=100, unique=True)  # nome unico
    cep = models.CharField(max_length=8, blank=True, null=True)  # so os 8 digitos
    regiao = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)  # filtro bairro ativo no form

    class Meta:
        managed = False
        db_table = "bairro"

    def __str__(self):
        return self.nome_bairro


class Cidadao(models.Model):
    """Usuarios do portal. Tenho autenticacao propria, NAO uso o django.contrib.auth.

    A senha vai sempre como hash bcrypt no senha_hash, jamais em texto puro.
    O perfil diz o tipo: 'CID' = cidadao padrao.
    """
    id_cidadao = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)  # so digitos, unico
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)  # login eh por email, unico
    senha_hash = models.CharField(max_length=255)  # bcrypt aqui
    senha_temporaria = models.CharField(max_length=200, blank=True, null=True)  # marca primeiro acesso
    perfil = models.CharField(max_length=3, default="CID")
    # campos de endereco, todos opcionais (o cidadao pode preencher depois)
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
    """Colaboradores e gestores da prefeitura (o pessoal interno).

    Perfis: 'GES' = gestor (acesso total), 'COL' = colaborador (acesso parcial).
    O senha_temporaria indica que eh primeiro acesso e tem que trocar a senha.
    """
    id_servidor = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)
    senha_hash = models.CharField(max_length=255)  # bcrypt, igual ao cidadao
    senha_temporaria = models.CharField(max_length=200, blank=True, null=True)  # primeiro acesso
    perfil = models.CharField(max_length=3)  # GES ou COL
    dt_cadastro = models.DateTimeField()
    ativo = models.BooleanField(default=True)
    # FK pra secretaria onde o servidor trabalha
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
    """Tabela central do sistema: guarda as solicitacoes dos cidadaos.

    Sacada importante: NAO existe campo id_status aqui. O status atual eh
    sempre o do ULTIMO registro de HistoricoChamado. Isso eh event sourcing:
    o estado vem do historico de eventos, nao de uma coluna fixa.

    Minhas properties principais:
    - status_atual: o objeto StatusChamado do ultimo historico
    - sigla_status: a sigla em texto (ex: 'AB', 'CO')
    - cor_semaforo: 'verde', 'amarelo' ou 'vermelho' conforme os prazos
    - ultima_atualizacao: data/hora do ultimo historico
    """
    id_chamado = models.AutoField(primary_key=True)
    num_protocolo = models.CharField(max_length=20, unique=True)  # protocolo unico
    prioridade = models.IntegerField(default=0)  # 0..5, a equipe ajusta
    ponto_de_referencia = models.CharField(max_length=100, blank=True, null=True)
    descricao = models.CharField(max_length=500)  # o que o cidadao relatou
    resolucao = models.CharField(max_length=600, blank=True, null=True)  # preenchida ao concluir/cancelar
    nota_avaliacao = models.IntegerField(blank=True, null=True)  # 1..5 depois de concluir
    comentario_avaliacao = models.CharField(max_length=500, blank=True, null=True)
    dt_abertura = models.DateTimeField()  # uso ela pra contar os dias do semaforo
    dt_conclusao = models.DateTimeField(blank=True, null=True)  # o trigger 2B preenche
    dt_avaliacao = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField()  # o trigger 2A atualiza
    # FKs do chamado: servico, bairro e o cidadao dono
    id_servico = models.ForeignKey(Servico, models.DO_NOTHING, db_column="id_servico")
    id_bairro = models.ForeignKey(Bairro, models.DO_NOTHING, db_column="id_bairro")
    # related_name="chamados" -> consigo fazer cidadao.chamados
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
        # helper privado: acha o historico mais recente desse chamado.
        # uso list(self.historicos.all()) de proposito pra aproveitar o cache
        # do prefetch_related quando a view ja trouxe os historicos juntos
        try:
            historicos = list(self.historicos.all())
            if not historicos:
                return None
            # o mais novo eh o de maior dt_alteracao
            return max(historicos, key=lambda h: h.dt_alteracao)
        except (ValueError, AttributeError):
            # se der ruim (sem historico/sem relacao) eu so devolvo None
            return None

    @property
    def status_atual(self):
        # status atual = o status do ultimo historico (a tal fonte da verdade)
        ultimo = self._ultimo_historico
        return ultimo.id_status if ultimo else None

    @property
    def sigla_status(self):
        # mesma coisa, mas ja devolvendo a sigla limpa em string (ex: 'AB')
        st = self.status_atual
        return (st.sigla or "").strip() if st else ""

    @property
    def ultima_atualizacao(self):
        # data da ultima mudanca; se nao tiver historico, caio pra dt_abertura
        ultimo = self._ultimo_historico
        return ultimo.dt_alteracao if ultimo else self.dt_abertura

    @property
    def cor_semaforo(self):
        """Classifica o chamado por urgencia usando os prazos globais.

        Devolve 'verde' (no prazo), 'amarelo' (atencao) ou 'vermelho' (critico).
        """
        config = ConfiguracaoSemaforo.get_singleton()  # pego os prazos globais
        dias = (timezone.now() - self.dt_abertura).days  # ha quantos dias ta aberto
        # ordem importa: testo o vermelho (maior prazo) primeiro
        if dias >= config.prazo_vermelho_dias:
            return "vermelho"
        if dias >= config.prazo_amarelo_dias:
            return "amarelo"
        return "verde"

    @classmethod
    def calcular_stats(cls, queryset):
        """Conta os chamados por cor do semaforo pra um queryset.

        Devolve um dict: {'no_prazo': N, 'atencao': N, 'critico': N}.
        Faco em Python pra reaproveitar a mesma regra de dias do cor_semaforo.
        """
        config = ConfiguracaoSemaforo.get_singleton()
        stats = {"no_prazo": 0, "atencao": 0, "critico": 0}
        now = timezone.now()  # pego o agora uma vez so, fora do loop
        # select_related pra nao tomar N+1 ao acessar o servico
        for ch in queryset.select_related("id_servico"):
            dias = (now - ch.dt_abertura).days
            # mesma logica de faixas do cor_semaforo, so que somando contadores
            if dias >= config.prazo_vermelho_dias:
                stats["critico"] += 1
            elif dias >= config.prazo_amarelo_dias:
                stats["atencao"] += 1
            else:
                stats["no_prazo"] += 1
        return stats


class FotoChamado(models.Model):
    """Fotos anexadas aos chamados. Guardo so a URL (Cloudinary ou local).

    Tem um trigger de integridade no banco que BLOQUEIA o INSERT de foto
    se o chamado ja estiver concluido ou cancelado. Ou seja, nao da pra
    adicionar foto em chamado fechado.
    """
    id_foto = models.AutoField(primary_key=True)
    url_foto = models.CharField(max_length=200)  # so a URL, nao o arquivo
    dt_upload = models.DateTimeField()
    id_chamado = models.ForeignKey(Chamado, models.DO_NOTHING, db_column="id_chamado")

    class Meta:
        managed = False
        db_table = "foto_chamado"


class HistoricoChamado(models.Model):
    """Historico de mudancas de status — eh a fonte da verdade do status.

    Cada INSERT aqui pode disparar dois triggers la no banco:
    - Trigger 2A: atualiza o atualizado_em la na tabela chamado.
    - Trigger 2B: se o novo status for CO ou CA, seta dt_conclusao = NOW()
      e ainda cria uma notificacao automatica pro cidadao.

    O id_servidor pode ser NULL quando o registro foi criado automaticamente
    (ex: na abertura do chamado, quem cria o historico eh o Trigger 1).
    """
    id_historico_chamado = models.AutoField(primary_key=True)
    dt_alteracao = models.DateTimeField()  # uso pra achar o ultimo historico
    observacao = models.CharField(max_length=500, blank=True, null=True)
    # related_name="historicos" -> casa com o self.historicos la no Chamado
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
        related_name="historicos",
    )
    # servidor pode ser nulo (historico criado por trigger nao tem servidor)
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
    """Notificacoes que o Trigger 2B cria sozinho.

    Toda vez que o status muda, o banco gera uma notificacao avisando o
    cidadao dono do chamado sobre a nova situacao.
    """
    id_notificacao = models.AutoField(primary_key=True)
    mensagem = models.CharField(max_length=200)
    lida = models.BooleanField(default=False)  # cidadao ja viu?
    arquivada = models.BooleanField(default=False)
    dt_envio = models.DateTimeField()
    # id_chamado pode ser nulo (notificacao avulsa, nao ligada a um chamado)
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
    """Banners da home (o carrossel de noticias/destaques).

    Essa tabela eh um extra, fora das 11 entidades principais do DER. O campo
    ordem manda na posicao do banner no carrossel, e quem gerencia eh o gestor
    pelo painel admin.
    """
    id_banner = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descricao = models.CharField(max_length=300, blank=True, null=True)
    url_imagem = models.CharField(max_length=500)
    link = models.CharField(max_length=500, blank=True, null=True)  # link opcional ao clicar
    ordem = models.IntegerField(default=0)  # posicao no carrossel
    ativo = models.BooleanField(default=True)
    dt_criacao = models.DateTimeField(auto_now_add=True)  # auto na criacao

    class Meta:
        managed = False
        db_table = "banner_publicacao"
        # ordena por ordem e, em empate, mostra o mais recente primeiro
        ordering = ["ordem", "-dt_criacao"]

    def __str__(self):
        return self.titulo
