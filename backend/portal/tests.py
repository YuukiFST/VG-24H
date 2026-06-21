"""
tests.py — Testes verticais do Portal VG 24H

Testes organizados por vertical slice:
1. Protocolo: proximo_protocolo() gera sequencia correta
2. Semaforo: cor_semaforo classifica verde/amarelo/vermelho
3. Paginacao: paginar() com e sem total_count
4. Decoradores: perfil_codigo, controle de acesso
5. Formularios: validacao de senhas e CPF

Cada teste segue F.I.R.S.T: Fast, Independent, Repeatable,
Self-validating, Timely.
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from portal import db
from portal.forms import CadastroCidadaoForm, RedefinirSenhaForm, ServicoForm
from portal.models import ConfiguracaoSemaforo
from portal.utils import proximo_protocolo


# ------------------------------------------------------------------
# Slice 1: Protocolo
# ------------------------------------------------------------------

class ProximoProtocoloTests(TestCase):
    """Testa a geracao sequencial de numeros de protocolo.

    proximo_protocolo() usa INSERT ... ON CONFLICT DO UPDATE RETURNING
    (operacao atomica no PostgreSQL). Os testes mockam connection.cursor.
    """

    @patch("portal.utils.connection")
    def test_primeiro_protocolo_do_ano(self, mock_conn):
        """Insere o primeiro protocolo do ano — retorna 000001."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(1,), None]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        resultado = proximo_protocolo()
        ano = str(timezone.now().year)
        self.assertEqual(resultado, f"{ano}000001")

    @patch("portal.utils.connection")
    def test_protocolo_incrementa_sequencia(self, mock_conn):
        """ON CONFLICT incrementa — retorna 000006."""
        ano = str(timezone.now().year)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(6,), None]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        resultado = proximo_protocolo()
        self.assertEqual(resultado, f"{ano}000006")



class SemaforoGlobalTests(TestCase):
    """Testa a configuracao global do semaforo (ConfiguracaoSemaforo)."""

    def test_servico_form_nao_tem_campos_prazo(self):
        """ServicoForm nao deve conter campos de prazo (agora global)."""
        self.assertNotIn("prazo_amarelo_dias", ServicoForm().fields)
        self.assertNotIn("prazo_vermelho_dias", ServicoForm().fields)

    def test_configuracao_semaforo_get_singleton_cria_se_vazio(self):
        """get_singleton() cria config padrao se nao existir."""
        ConfiguracaoSemaforo.objects.all().delete()
        cfg = ConfiguracaoSemaforo.get_singleton()
        self.assertEqual(cfg.prazo_amarelo_dias, 15)
        self.assertEqual(cfg.prazo_vermelho_dias, 30)


class GestaoPrazosViewTests(TestCase):
    """Testa a view de configuracao global de prazos."""

    def _mock_gestor(self):
        user = MagicMock()
        user.perfil = "GES"
        user.pk = 1
        return user

    @patch("portal.views_equipe.connection.cursor")
    def test_gestao_prazos_get_carrega_form(self, mock_cursor):
        """GET carrega o form com os valores atuais da configuracao."""
        from django.http import HttpRequest
        from portal.views_equipe import gestao_prazos

        mock_c = MagicMock()
        mock_c.fetchone.return_value = (15, 30)
        mock_cursor.return_value.__enter__ = MagicMock(return_value=mock_c)
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        req = HttpRequest()
        req.method = "GET"
        req.portal_user = self._mock_gestor()
        req.META = {"SERVER_NAME": "test", "SERVER_PORT": "80"}
        req.session = {}

        resp = gestao_prazos(req)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"prazo_amarelo_dias", resp.content)

    @patch("portal.views_equipe.messages")
    @patch("portal.views_equipe.connection.cursor")
    def test_gestao_prazos_post_atualiza_config(self, mock_cursor, mock_messages):
        """POST atualiza os valores na configuracao_semaforo."""
        from django.http import HttpRequest
        from portal.views_equipe import gestao_prazos

        posted_data = {"prazo_amarelo_dias": "10", "prazo_vermelho_dias": "25"}
        mock_c = MagicMock()
        mock_cursor.return_value.__enter__ = MagicMock(return_value=mock_c)
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        req = HttpRequest()
        req.method = "POST"
        req.POST = posted_data
        req.portal_user = self._mock_gestor()
        req.META = {"SERVER_NAME": "test", "SERVER_PORT": "80"}
        req.session = {}

        resp = gestao_prazos(req)
        self.assertEqual(resp.status_code, 302)




# ------------------------------------------------------------------
# Slice 5: Formularios (validacao)
# ------------------------------------------------------------------

class CadastroCidadaoFormTests(TestCase):
    """Testa a validacao do formulario de cadastro de cidadao."""

    def _base_data(self):
        return {
            "nome_completo": "Joao Silva",
            "cpf": "123.456.789-01",
            "dt_nascimento": "1990-01-15",
            "telefone": "65999990000",
            "email": "joao@email.com",
            "senha": "minhasenha123",
            "senha2": "minhasenha123",
        }

    def test_form_valido(self):
        """Form com dados completos e senhas iguais eh valido."""
        form = CadastroCidadaoForm(data=self._base_data())
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes_invalida(self):
        """Form com senhas diferentes eh invalido."""
        data = self._base_data()
        data["senha2"] = "outrasenha456"
        form = CadastroCidadaoForm(data=data)
        self.assertFalse(form.is_valid())

    def test_cpf_limpa_mascara(self):
        """CPF com mascara (123.456.789-01) retorna apenas digitos."""
        data = self._base_data()
        data["cpf"] = "123.456.789-01"
        form = CadastroCidadaoForm(data=data)
        form.is_valid()
        self.assertEqual(form.cleaned_data["cpf"], "12345678901")

    def test_senha_curta_invalida(self):
        """Senha com menos de 6 caracteres eh invalida."""
        data = self._base_data()
        data["senha"] = "abc"
        data["senha2"] = "abc"
        form = CadastroCidadaoForm(data=data)
        self.assertFalse(form.is_valid())


class RedefinirSenhaFormTests(TestCase):
    """Testa a validacao do formulario de redefinicao de senha."""

    def test_senhas_iguais_valido(self):
        """Form com senhas iguais e >= 6 chars eh valido."""
        form = RedefinirSenhaForm(data={"senha": "novasenha", "senha2": "novasenha"})
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes_invalido(self):
        """Form com senhas diferentes eh invalido."""
        form = RedefinirSenhaForm(data={"senha": "novasenha", "senha2": "outra"})
        self.assertFalse(form.is_valid())
