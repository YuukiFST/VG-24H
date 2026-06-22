from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
    id_categoria: Optional[CategoriaRef] = None


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
    ponto_de_referencia: Optional[str]
    descricao: str
    resolucao: Optional[str]
    nota_avaliacao: Optional[int]
    comentario_avaliacao: Optional[str]
    dt_abertura: datetime
    dt_conclusao: Optional[datetime]
    dt_avaliacao: Optional[datetime]
    atualizado_em: datetime
    id_cidadao_id: int
    id_servico: ServicoRef
    id_bairro: BairroRef
    status_atual: Optional[StatusRef] = None
    sigla_status: str = ""
    cor_semaforo: str = "verde"


@dataclass
class HistoricoDTO:
    id_historico_chamado: int
    pk: int
    dt_alteracao: datetime
    observacao: Optional[str]
    id_servidor_id: Optional[int]
    id_servidor: Optional[ServidorRef]
    id_status: StatusRef


@dataclass
class FotoDTO:
    id_foto: int
    pk: int
    url_foto: str
    dt_upload: datetime
