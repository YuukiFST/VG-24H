# dataclass pra eu nao ter que escrever __init__ na mao em cada classe dessas
from dataclasses import dataclass
from datetime import datetime

# uso esses DTOs/Refs pra montar na mao os objetos vindos do SQL puro
# (como nao uso o ORM, sou eu quem preenche cada campo)


@dataclass
class ServicoRef:
    # referencia enxuta de servico que eu grudo dentro do chamado
    id_servico: int
    pk: int
    nome: str
    descricao: str


@dataclass
class BairroRef:
    # referencia enxuta de bairro que eu grudo dentro do chamado
    id_bairro: int
    pk: int
    nome_bairro: str


@dataclass
class StatusRef:
    # referencia de status (sigla tipo "AB" + descricao por extenso)
    id_status: int
    pk: int
    sigla: str
    descricao: str


@dataclass
class ServidorRef:
    # so o nome do servidor, e o que eu mostro no historico
    nome_completo: str


@dataclass
class ChamadoDTO:
    # o objeto cheio do chamado que eu monto com varios joins do SQL
    id_chamado: int
    pk: int
    num_protocolo: str
    prioridade: int
    ponto_de_referencia: str | None
    descricao: str
    resolucao: str | None
    nota_avaliacao: int | None
    comentario_avaliacao: str | None
    dt_abertura: datetime
    dt_conclusao: datetime | None
    dt_avaliacao: datetime | None
    atualizado_em: datetime
    id_cidadao_id: int
    id_servico: ServicoRef
    id_bairro: BairroRef
    # esses ultimos tem default porque nem sempre eu preencho na hora de montar
    status_atual: StatusRef | None = None
    sigla_status: str = ""
    cor_semaforo: str = "verde"  # verde/amarelo/vermelho do semaforo na tela


@dataclass
class HistoricoDTO:
    # cada linha do historico de mudancas de status de um chamado
    id_historico_chamado: int
    pk: int
    dt_alteracao: datetime
    observacao: str | None
    id_servidor_id: int | None  # pode ser None quando foi acao do proprio cidadao
    id_servidor: ServidorRef | None
    id_status: StatusRef


@dataclass
class FotoDTO:
    # cada foto anexada num chamado
    id_foto: int
    pk: int
    url_foto: str
    dt_upload: datetime
