"""
models.py — Mapeamento ORM (Object-Relational Mapping) do Portal VG 24H

Este arquivo define as CLASSES PYTHON que representam as TABELAS DO BANCO DE DADOS.
Cada classe = uma tabela. Cada atributo = uma coluna.

O Django ORM traduz automaticamente operacoes Python em SQL:
  - Cidadao.objects.get(pk=5)          → SELECT * FROM cidadao WHERE id_cidadao = 5
  - Cidadao.objects.filter(ativo=True) → SELECT * FROM cidadao WHERE ativo = true
  - Cidadao.objects.create(...)        → INSERT INTO cidadao (...) VALUES (...)
  - obj.save()                         → UPDATE cidadao SET ... WHERE id_cidadao = X
  - obj.delete()                       → DELETE FROM cidadao WHERE id_cidadao = X

IMPORTANTE: Todas as classes usam 'managed = False' no Meta.
Isso significa que o Django NAO cria nem altera as tabelas automaticamente.
As tabelas foram criadas manualmente via scripts SQL (pasta database/).
O Django apenas LE e ESCREVE nos registros.

Relacionamentos (FOREIGN KEYS) sao mapeados com models.ForeignKey(),
que equivalem a REFERENCES no SQL. O Django usa isso para fazer JOINs
automaticamente quando usamos select_related() ou acessamos obj.id_servico.nome.

[!] Propriedades-chave da classe Chamado:
    - status_atual      → retorna o objeto StatusChamado do ULTIMO historico
    - sigla_status      → retorna a sigla (string) do status atual
    - ultima_atualizacao → retorna dt_alteracao do ultimo historico
    - cor_semaforo      → retorna 'verde', 'amarelo' ou 'vermelho' conforme prazos
"""

from django.db import models
from django.utils import timezone


# ============================================================
# TABELA: status_chamado
# Armazena os 5 status possíveis de um chamado:
# AB (Aberto), EA (Em Atendimento), EE (Em Execução), CO (Concluído), CA (Cancelado)
# ============================================================
class StatusChamado(models.Model):
    """
    Mapeamento da tabela status_chamado.
    Catalogo com 5 registros fixos: AB (Aberto), EA (Em Atendimento),
    EE (Em Execucao), CO (Concluido), CA (Cancelado).
    """
    id_status = models.AutoField(primary_key=True)      # SERIAL PRIMARY KEY
    descricao = models.CharField(max_length=200, blank=True, null=True)
    sigla = models.CharField(max_length=2, unique=True) # UNIQUE + CHECK no SQL (AB, EA, EE, CO, CA)

    class Meta:
        managed = False          # Django NAO gerencia (tabela criada via SQL)
        db_table = "status_chamado"

    def __str__(self):
        return self.descricao or self.sigla


class Secretaria(models.Model):
    """
    Mapeamento da tabela secretaria.
    Orgaos municipais. FK apontada por: Servidor, CategoriaServico.
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
    """
    Mapeamento da tabela categoria_servico.
    Agrupa servicos por area (ex: Infraestrutura, Mobilidade).
    FK → Secretaria. FK apontada por: Servico.
    """
    id_categoria = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    id_secretaria = models.ForeignKey(
        Secretaria,
        models.DO_NOTHING,       # Nao faz CASCADE no Django (gerenciado pelo banco)
        db_column="id_secretaria",
    )

    class Meta:
        managed = False
        db_table = "categoria_servico"

    def __str__(self):
        return self.nome


class Servico(models.Model):
    """
    Mapeamento da tabela servico.
    Tipos de servico com prazos para o semaforo (amarelo/vermelho).
    FK → CategoriaServico. FK apontada por: Chamado.
    [!] Os prazos (prazo_amarelo_dias, prazo_vermelho_dias) sao usados
        pela property cor_semaforo para classificar a urgencia.
    """
    id_servico = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    prazo_amarelo_dias = models.IntegerField(default=15)    # Dias ate "amarelo"
    prazo_vermelho_dias = models.IntegerField(default=30)   # Dias ate "vermelho"
    ativo = models.BooleanField(default=True)
    id_categoria = models.ForeignKey(
        CategoriaServico,
        models.DO_NOTHING,
        db_column="id_categoria",
        related_name="servicos",     # cat.servicos.all() — acesso reverso
    )

    class Meta:
        managed = False
        db_table = "servico"

    def __str__(self):
        return self.nome


class Bairro(models.Model):
    """
    Mapeamento da tabela bairro.
    Bairros de Varzea Grande/MT. FK apontada por: Chamado.id_bairro.
    """
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
    """
    Mapeamento da tabela cidadao.
    Usuarios do portal (autenticacao propria — NAO usa django.contrib.auth).
    [!] A senha e armazenada como HASH (NUNCA em texto puro).
    Perfil: 'CID' = Cidadao padrao. FK apontada por: Chamado.id_cidadao.
    """
    id_cidadao = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)          # CPF sem mascara (11 digitos)
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)
    senha_hash = models.CharField(max_length=255)               # Hash bcrypt (ex: pbkdf2_sha256$...)
    senha_temporaria = models.CharField(max_length=200, blank=True, null=True)
    perfil = models.CharField(max_length=3, default="CID")      # 'CID' ou 'VER'
    rua = models.CharField(max_length=100, blank=True, null=True)
    num_endereco = models.CharField(max_length=10, blank=True, null=True)
    complemento_endereco = models.CharField(max_length=200, blank=True, null=True)
    bairro_endereco = models.CharField(max_length=200, blank=True, null=True)
    cep_endereco = models.CharField(max_length=8, blank=True, null=True)
    dt_cadastro = models.DateTimeField()
    ativo = models.BooleanField(default=True)                   # Soft delete

    class Meta:
        managed = False
        db_table = "cidadao"

    def __str__(self):
        return self.nome_completo


class Servidor(models.Model):
    """
    Mapeamento da tabela servidor.
    Colaboradores e gestores da prefeitura.

    [!] Perfis (campo 'perfil'):
        'GES' = Gestor (acesso total a todas as funcionalidades)
        'COL' = Colaborador (acesso parcial — atende chamados)

    FK → Secretaria (qual secretaria ele pertence).
    FK apontada por: HistoricoChamado.id_servidor (quem alterou o status).
    """
    id_servidor = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)
    dt_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    email = models.CharField(max_length=255, unique=True)
    senha_hash = models.CharField(max_length=255)
    senha_temporaria = models.CharField(max_length=200, blank=True, null=True)
    perfil = models.CharField(max_length=3)                     # 'GES' ou 'COL'
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
    """
    Mapeamento da tabela chamado (TABELA CENTRAL do sistema).

    [!] NAO possui campo id_status. O status e determinado pelo ULTIMO
        registro de HistoricoChamado (fonte da verdade).

    Properties principais:
      - status_atual        → objeto StatusChamado do ultimo historico
      - sigla_status        → sigla do status (ex: 'AB', 'CO') como string
      - ultima_atualizacao  → data/hora do ultimo historico
      - cor_semaforo        → 'verde' / 'amarelo' / 'vermelho' conforme prazos
    """
    id_chamado = models.AutoField(primary_key=True)
    num_protocolo = models.CharField(max_length=20, unique=True)   # Ex: '2026000001'
    prioridade = models.IntegerField(default=0)                    # 0 a 5 (CHECK no banco)
    ponto_de_referencia = models.CharField(max_length=100, blank=True, null=True)
    descricao = models.CharField(max_length=500)
    resolucao = models.CharField(max_length=600, blank=True, null=True)
    nota_avaliacao = models.IntegerField(blank=True, null=True)    # 1 a 5
    comentario_avaliacao = models.CharField(max_length=500, blank=True, null=True)
    dt_abertura = models.DateTimeField()
    dt_conclusao = models.DateTimeField(blank=True, null=True)     # Atualizado pelo Trigger 2B
    dt_avaliacao = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField()                         # Atualizado pelo Trigger 2A
    # FOREIGN KEYS (equivalem a REFERENCES no SQL)
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
        related_name="chamados",         # cidadao.chamados.all() — acesso reverso
    )

    class Meta:
        managed = False
        db_table = "chamado"

    # ========================================================================
    # PROPERTIES — logica de negocio que consulta o historico
    # ========================================================================

    @property
    def _ultimo_historico(self):
        """
        Retorna o objeto HistoricoChamado mais recente.
        [!] Usa cache: se o related_name 'historicos' foi prefetchado
            via prefetch_related(), evita queries extras.
        """
        try:
            historicos = list(self.historicos.all())
            if not historicos:
                return None
            # Encontra o registro com a maior dt_alteracao
            return max(historicos, key=lambda h: h.dt_alteracao)
        except (ValueError, AttributeError):
            return None

    @property
    def status_atual(self):
        """
        [!] DESTAQUE: Retorna o objeto StatusChamado do ultimo historico.
        Equivalente funcional do antigo campo id_status (que foi removido).
        """
        ultimo = self._ultimo_historico
        return ultimo.id_status if ultimo else None

    @property
    def sigla_status(self):
        """
        Retorna a sigla do status atual como string (ex: 'AB', 'CO').
        Usada em templates e views para comparacao direta.
        """
        st = self.status_atual
        return (st.sigla or "").strip() if st else ""

    @property
    def ultima_atualizacao(self):
        """
        Retorna a data/hora da ultima alteracao de status.
        Se nao houver historico, retorna a data de abertura.
        """
        ultimo = self._ultimo_historico
        return ultimo.dt_alteracao if ultimo else self.dt_abertura

    @property
    def cor_semaforo(self):
        """
        [!] Classifica o chamado por urgencia usando os prazos do servico:
          - 'verde':    dentro do prazo amarelo
          - 'amarelo':  entre prazo amarelo e vermelho
          - 'vermelho': alem do prazo vermelho
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
        """
        Metodo de classe: calcula estatisticas de semaforo para um queryset.
        Uso: Chamado.calcular_stats(Chamado.objects.all())
        Retorna dict: {'no_prazo': N, 'atencao': N, 'critico': N}
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


# ============================================================
# TABELA: foto_chamado
# Fotos anexadas aos chamados. URLs armazenadas (Cloudinary).
# FOREIGN KEY para chamado.
# ============================================================
class FotoChamado(models.Model):
    """
    Mapeamento da tabela foto_chamado.
    Fotos anexadas aos chamados. URLs armazenadas (Cloudinary ou local).
    [!] Trigger de integridade: bloqueia INSERT se chamado estiver CO/CA.
    """
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
    """
    Mapeamento da tabela historico_chamado — FONTE DA VERDADE para status.

    [!] Cada inserção nesta tabela:
      1. Trigger 2B atualiza dt_conclusao em chamado (se CO/CA)
      2. Trigger 2B gera notificacao automatica

    FKs: id_chamado → Chamado, id_servidor → Servidor (quem alterou),
         id_status → StatusChamado.
    related_name="historicos": permite fazer chamado.historicos.all()
    """
    id_historico_chamado = models.AutoField(primary_key=True)
    dt_alteracao = models.DateTimeField()
    observacao = models.CharField(max_length=500, blank=True, null=True)
    id_chamado = models.ForeignKey(
        Chamado,
        models.DO_NOTHING,
        db_column="id_chamado",
        related_name="historicos",    # chamado.historicos.all() — todo o historico
    )
    id_servidor = models.ForeignKey(
        Servidor,
        models.DO_NOTHING,
        db_column="id_servidor",
        blank=True,
        null=True,                    # NULL quando criado pelo sistema (ex: abertura)
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
    """
    Mapeamento da tabela notificacao.
    [!] Geradas AUTOMATICAMENTE pelo Trigger 2B ao inserir historico.
    Avisos ao cidadao sobre mudancas de status nos seus chamados.
    """
    id_notificacao = models.AutoField(primary_key=True)
    mensagem = models.CharField(max_length=200)               # Ex: "Chamado 20260001: status alterado..."
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
    """
    Mapeamento da tabela banner_publicacao (NAO esta no DER original).
    Banners da pagina inicial (carrossel de noticias/destaques).
    Tabela adicional fora das 11 entidades principais.
    """
    id_banner = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descricao = models.CharField(max_length=300, blank=True, null=True)
    url_imagem = models.CharField(max_length=500)
    link = models.CharField(max_length=500, blank=True, null=True)
    ordem = models.IntegerField(default=0)                    # Ordem de exibicao
    ativo = models.BooleanField(default=True)
    dt_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "banner_publicacao"
        ordering = ["ordem", "-dt_criacao"]                   # Ordena por ordem, depois data

    def __str__(self):
        return self.titulo

