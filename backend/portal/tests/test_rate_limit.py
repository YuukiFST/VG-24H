# aqui testo o rate limit do login. Como ele depende do tempo (janela de X seg),
# eu mocko o time.time() pra travar o "agora" e controlar quais tentativas estao
# dentro ou fora da janela. As tentativas ficam guardadas na session, sem banco.
"""Testes do rate limit de login (views_auth) — time mockado, sem banco."""
from unittest.mock import patch

from django.http import HttpRequest
from django.test import TestCase

from portal.views_auth import (
    LOGIN_TIMEOUT,
    MAX_LOGIN_ATTEMPTS,
    _check_login_rate_limit,
    _record_login_attempt,
)


class LoginRateLimitTests(TestCase):
    def _req(self, attempts):
        # request fake so com a session preenchida com a lista de timestamps
        # de tentativas que eu quero testar
        req = HttpRequest()
        req.session = {"login_attempts": list(attempts)}
        return req

    @patch("portal.views_auth.time")
    def test_poda_tentativas_expiradas(self, mock_time):
        # finjo que agora sao 10_000s; as tentativas la em 0/1/2s estao MUITO
        # velhas, entao devem ser podadas e o check nao deve bloquear (False)
        mock_time.time.return_value = 10_000.0
        req = self._req([0.0, 1.0, 2.0])  # todas alem da janela
        self.assertFalse(_check_login_rate_limit(req))
        # confiro tambem que a lista ficou limpa depois da poda
        self.assertEqual(req.session["login_attempts"], [])

    @patch("portal.views_auth.time")
    def test_bloqueia_apos_max_na_janela(self, mock_time):
        now = 10_000.0
        mock_time.time.return_value = now
        # encho a lista com o maximo de tentativas, todas 1s atras (dentro da janela)
        recentes = [now - 1 for _ in range(MAX_LOGIN_ATTEMPTS)]
        # bateu no limite dentro da janela -> tem que bloquear (True)
        self.assertTrue(_check_login_rate_limit(self._req(recentes)))

    @patch("portal.views_auth.time")
    def test_record_poda_antes_de_adicionar(self, mock_time):
        now = 10_000.0
        mock_time.time.return_value = now
        # 4 tentativas ja expiradas (mais velhas que o timeout)
        antigas = [now - LOGIN_TIMEOUT - 1 for _ in range(4)]
        req = self._req(antigas)
        # registrar uma nova tentativa deve primeiro limpar as velhas e so depois add
        _record_login_attempt(req)
        # as 4 antigas foram podadas; sobra apenas a recem registrada (now)
        self.assertEqual(req.session["login_attempts"], [now])

    @patch("portal.views_auth.time")
    def test_libera_apos_janela_expirar(self, mock_time):
        now = 10_000.0
        mock_time.time.return_value = now
        # mesmo tendo batido no MAX, todas estao expiradas -> nao bloqueia mais (False)
        expiradas = [now - LOGIN_TIMEOUT - 1 for _ in range(MAX_LOGIN_ATTEMPTS)]
        self.assertFalse(_check_login_rate_limit(self._req(expiradas)))
