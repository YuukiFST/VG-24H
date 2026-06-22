"""Regressao: a rota /trocar-senha/ (views_root.trocar_senha) renderiza o
template portal/senha/trocar_senha.html. Esse template faltava e o GET
quebrava com TemplateDoesNotExist (500)."""
from unittest.mock import MagicMock, patch

from django.http import HttpRequest
from django.test import TestCase


class TrocarSenhaViewTests(TestCase):
    def _req(self, method="GET"):
        # monto uma request fake do jeito que os outros testes de view fazem,
        # sem subir banco — so preciso de um usuario logado pro @autenticado passar
        req = HttpRequest()
        req.method = method
        req.portal_user = MagicMock(pk=1)  # usuario logado qualquer
        req.session = {}
        req.META = {"SERVER_NAME": "test", "SERVER_PORT": "80"}
        return req

    def test_get_renderiza_template(self):
        # se o template some de novo, esse GET volta a estourar 500
        from portal.views_root import trocar_senha

        resp = trocar_senha(self._req("GET"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"nova_senha", resp.content)

    @patch("portal.views_root.db")
    @patch("portal.views_root.messages")
    def test_post_valido_atualiza_senha(self, mock_messages, mock_db):
        # POST com senha forte: chama o updater de senha e redireciona pra home
        from portal.views_root import trocar_senha

        req = self._req("POST")
        req.POST = {"nova_senha": "Minhasenha123!"}
        req.session = MagicMock()  # a view seta session.modified = True
        # portal_user sem id_servidor -> cai no ramo cidadao
        req.portal_user = MagicMock(spec=["pk"], pk=7)

        resp = trocar_senha(req)
        self.assertEqual(resp.status_code, 302)
        mock_db.atualizar_senha_usuario.assert_called_once_with("cidadao", 7, "Minhasenha123!")
