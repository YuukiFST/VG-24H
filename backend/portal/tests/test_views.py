"""Testes de views — connection e messages mockados, sem banco."""
from unittest.mock import MagicMock, patch

from django.http import HttpRequest
from django.test import TestCase


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
