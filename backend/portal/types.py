from dataclasses import dataclass
from datetime import datetime


@dataclass
class ServicoRef:
    id_servico: int
    pk: int
    nome: str
    descricao: str


@dataclass
class CategoriaRef:
    nome: str


@dataclass
class ServicoCategoriaRef:
    id_servico: int
    pk: int
    nome: str
    descricao: str
    id_categoria: CategoriaRef | None = None


@dataclass
class BairroRef:
    id_bairro: int
    pk: int
    nome_bairro: str


@dataclass
class StatusRef:
    id_status: int
    pk: int
    sigla: str
    descricao: str


@dataclass
class CidadaoRef:
    id_cidadao: int
    pk: int
    nome_completo: str
    email: str
    telefone: str


@dataclass
class ServidorRef:
    nome_completo: str


@dataclass
class ChamadoDTO:
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
    status_atual: StatusRef | None = None
    sigla_status: str = ""
    cor_semaforo: str = "verde"


@dataclass
class HistoricoDTO:
    id_historico_chamado: int
    pk: int
    dt_alteracao: datetime
    observacao: str | None
    id_servidor_id: int | None
    id_servidor: ServidorRef | None
    id_status: StatusRef


@dataclass
class FotoDTO:
    id_foto: int
    pk: int
    url_foto: str
    dt_upload: datetime
