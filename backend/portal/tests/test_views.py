# aqui testo a view de prazos (semaforo) chamando a funcao direto, sem subir
# servidor nem banco: mocko a connection.cursor pra fingir o que vem do banco e
# o messages pra nao reclamar de framework de mensagens.
"""Testes de views — connection e messages mockados, sem banco."""
from unittest.mock import MagicMock, patch

from django.http import HttpRequest
from django.test import TestCase


class GestaoPrazosViewTests(TestCase):
    """Testa a view de configuracao global de prazos (so gestor pode mexer)."""

    def _mock_gestor(self):
        # usuario fake com perfil GES (gestor) pra passar o controle de acesso
        user = MagicMock()
        user.perfil = "GES"
        user.pk = 1
        return user

    @patch("portal.views_equipe.connection.cursor")
    def test_gestao_prazos_get_carrega_form(self, mock_cursor):
        """No GET, a view deve carregar o form ja com os valores atuais do banco."""
        from portal.views_equipe import gestao_prazos

        mock_c = MagicMock()
        # finjo que o banco devolve prazo amarelo=15 e vermelho=30
        mock_c.fetchone.return_value = (15, 30)
        # mesmo truque do context manager do "with cursor() as c"
        mock_cursor.return_value.__enter__ = MagicMock(return_value=mock_c)
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        # monto a request de GET com o gestor logado e META minimo pra view nao quebrar
        req = HttpRequest()
        req.method = "GET"
        req.portal_user = self._mock_gestor()
        req.META = {"SERVER_NAME": "test", "SERVER_PORT": "80"}
        req.session = {}

        resp = gestao_prazos(req)
        # espero 200 e que o html renderizado tenha o campo do form
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"prazo_amarelo_dias", resp.content)

    @patch("portal.views_equipe.messages")
    @patch("portal.views_equipe.connection.cursor")
    def test_gestao_prazos_post_atualiza_config(self, mock_cursor, mock_messages):
        """No POST valido, a view salva os novos prazos e redireciona (302)."""
        from portal.views_equipe import gestao_prazos

        # dados que o gestor "enviou" no form
        posted_data = {"prazo_amarelo_dias": "10", "prazo_vermelho_dias": "25"}
        mock_c = MagicMock()
        # aqui nao preciso de fetchone, so deixo o cursor fake aceitar o UPDATE
        mock_cursor.return_value.__enter__ = MagicMock(return_value=mock_c)
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        req = HttpRequest()
        req.method = "POST"
        req.POST = posted_data
        req.portal_user = self._mock_gestor()
        req.META = {"SERVER_NAME": "test", "SERVER_PORT": "80"}
        req.session = {}

        resp = gestao_prazos(req)
        # depois de salvar tem que redirecionar -> 302 (padrao POST-redirect-GET)
        self.assertEqual(resp.status_code, 302)
