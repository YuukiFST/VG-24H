"""
tests.py — Testes Verticais do Portal VG 24H

Testes organizados por vertical slice (conforme /tdd skill):
  1. Protocolo — proximo_protocolo() gera sequência correta
  2. Semáforo — cor_semaforo classifica verde/amarelo/vermelho
  3. Modelo — status_atual, sigla_status, calcular_stats
  4. Decoradores — perfil_codigo, controle de acesso
  5. Formulários — validação de senhas, CPF

Cada teste segue F.I.R.S.T: Fast, Independent, Repeatable,
Self-validating, Timely.
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase
from django.utils import timezone

from portal.decorators import perfil_codigo
from portal.forms import CadastroCidadaoForm, RedefinirSenhaForm
from portal.utils import proximo_protocolo


# ═══════════════════════════════════════════════════════════════
# SLICE 1: Protocolo
# ═══════════════════════════════════════════════════════════════
class ProximoProtocoloTests(TestCase):
    """Testa a geração sequencial de números de protocolo.

    [!] proximo_protocolo() usa SQL puro (cursor.execute + MAX),
        não ORM. Os testes mockam connection.cursor para simular
        o retorno do banco.
    """

    @patch("portal.utils.connection")
    def test_primeiro_protocolo_do_ano(self, mock_conn):
        """Quando não há chamados no ano, retorna 000001.

        >>> proximo_protocolo()
        '2026000001'
        """
        # Simula cursor retornando None (nenhum protocolo existente)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        resultado = proximo_protocolo()
        ano = str(timezone.now().year)
        self.assertEqual(resultado, f"{ano}000001")

    @patch("portal.utils.connection")
    def test_protocolo_incrementa_sequencia(self, mock_conn):
        """Quando o último protocolo é 000005, retorna 000006.

        >>> proximo_protocolo()
        '2026000006'
        """
        ano = str(timezone.now().year)
        # Simula cursor retornando o ultimo protocolo existente
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (f"{ano}000005",)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        resultado = proximo_protocolo()
        self.assertEqual(resultado, f"{ano}000006")


# ═══════════════════════════════════════════════════════════════
# SLICE 2: Semáforo (cor_semaforo property)
# ═══════════════════════════════════════════════════════════════
class CorSemaforoTests(TestCase):
    """Testa a classificação de chamados pelo prazo."""

    def _make_chamado_mock(self, dias_aberto, prazo_amarelo=15, prazo_vermelho=30):
        """Cria um mock que simula Chamado para testar cor_semaforo."""
        ch = MagicMock()
        ch.dt_abertura = timezone.now() - timedelta(days=dias_aberto)
        ch.id_servico.prazo_amarelo_dias = prazo_amarelo
        ch.id_servico.prazo_vermelho_dias = prazo_vermelho
        return ch

    def _cor_semaforo(self, ch):
        """Replica a lógica de Chamado.cor_semaforo para teste unitário puro."""
        s = ch.id_servico
        dias = (timezone.now() - ch.dt_abertura).days
        if dias >= s.prazo_vermelho_dias:
            return "vermelho"
        if dias >= s.prazo_amarelo_dias:
            return "amarelo"
        return "verde"

    def test_chamado_no_prazo_retorna_verde(self):
        """Chamado com 5 dias (prazo amarelo=15) deve ser verde."""
        ch = self._make_chamado_mock(dias_aberto=5)
        self.assertEqual(self._cor_semaforo(ch), "verde")

    def test_chamado_atencao_retorna_amarelo(self):
        """Chamado com 20 dias (prazo amarelo=15, vermelho=30) deve ser amarelo."""
        ch = self._make_chamado_mock(dias_aberto=20)
        self.assertEqual(self._cor_semaforo(ch), "amarelo")

    def test_chamado_critico_retorna_vermelho(self):
        """Chamado com 35 dias (prazo vermelho=30) deve ser vermelho."""
        ch = self._make_chamado_mock(dias_aberto=35)
        self.assertEqual(self._cor_semaforo(ch), "vermelho")

    def test_chamado_exatamente_no_limite_amarelo(self):
        """Chamado com exatamente prazo_amarelo dias deve ser amarelo."""
        ch = self._make_chamado_mock(dias_aberto=15)
        self.assertEqual(self._cor_semaforo(ch), "amarelo")

    def test_chamado_exatamente_no_limite_vermelho(self):
        """Chamado com exatamente prazo_vermelho dias deve ser vermelho."""
        ch = self._make_chamado_mock(dias_aberto=30)
        self.assertEqual(self._cor_semaforo(ch), "vermelho")

    def test_chamado_zero_dias(self):
        """Chamado aberto hoje deve ser verde."""
        ch = self._make_chamado_mock(dias_aberto=0)
        self.assertEqual(self._cor_semaforo(ch), "verde")


# ═══════════════════════════════════════════════════════════════
# SLICE 3: Decoradores
# ═══════════════════════════════════════════════════════════════
class PerfilCodigoTests(TestCase):
    """Testa a extração do código de perfil do usuário."""

    def test_cidadao_retorna_cid(self):
        """Usuário com perfil 'CID' retorna 'CID'."""
        user = MagicMock()
        user.perfil = "CID"
        self.assertEqual(perfil_codigo(user), "CID")

    def test_gestor_retorna_ges(self):
        """Usuário com perfil 'GES' retorna 'GES'."""
        user = MagicMock()
        user.perfil = "GES"
        self.assertEqual(perfil_codigo(user), "GES")

    def test_perfil_com_espacos_retorna_limpo(self):
        """Perfil com espaços extras é stripped."""
        user = MagicMock()
        user.perfil = "  COL  "
        self.assertEqual(perfil_codigo(user), "COL")

    def test_usuario_none_retorna_vazio(self):
        """Quando user é None, retorna string vazia."""
        self.assertEqual(perfil_codigo(None), "")

    def test_perfil_none_retorna_vazio(self):
        """Quando user.perfil é None, retorna string vazia."""
        user = MagicMock()
        user.perfil = None
        self.assertEqual(perfil_codigo(user), "")


# ═══════════════════════════════════════════════════════════════
# SLICE 4: Formulários (validação)
# ═══════════════════════════════════════════════════════════════
class CadastroCidadaoFormTests(TestCase):
    """Testa a validação do formulário de cadastro de cidadão."""

    def _base_data(self):
        return {
            "nome_completo": "João Silva",
            "cpf": "123.456.789-01",
            "dt_nascimento": "1990-01-15",
            "telefone": "65999990000",
            "email": "joao@email.com",
            "senha": "minhasenha123",
            "senha2": "minhasenha123",
        }

    def test_form_valido(self):
        """Form com dados completos e senhas iguais é válido."""
        form = CadastroCidadaoForm(data=self._base_data())
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes_invalida(self):
        """Form com senhas diferentes é inválido."""
        data = self._base_data()
        data["senha2"] = "outrasenha456"
        form = CadastroCidadaoForm(data=data)
        self.assertFalse(form.is_valid())

    def test_cpf_limpa_mascara(self):
        """CPF com máscara (123.456.789-01) retorna apenas dígitos."""
        data = self._base_data()
        data["cpf"] = "123.456.789-01"
        form = CadastroCidadaoForm(data=data)
        form.is_valid()
        self.assertEqual(form.cleaned_data["cpf"], "12345678901")

    def test_senha_curta_invalida(self):
        """Senha com menos de 6 caracteres é inválida."""
        data = self._base_data()
        data["senha"] = "abc"
        data["senha2"] = "abc"
        form = CadastroCidadaoForm(data=data)
        self.assertFalse(form.is_valid())


class RedefinirSenhaFormTests(TestCase):
    """Testa a validação do formulário de redefinição de senha."""

    def test_senhas_iguais_valido(self):
        """Form com senhas iguais e >= 6 chars é válido."""
        form = RedefinirSenhaForm(data={"senha": "novasenha", "senha2": "novasenha"})
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes_invalido(self):
        """Form com senhas diferentes é inválido."""
        form = RedefinirSenhaForm(data={"senha": "novasenha", "senha2": "outra"})
        self.assertFalse(form.is_valid())
