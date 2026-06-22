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
        req = HttpRequest()
        req.session = {"login_attempts": list(attempts)}
        return req

    @patch("portal.views_auth.time")
    def test_poda_tentativas_expiradas(self, mock_time):
        mock_time.time.return_value = 10_000.0
        req = self._req([0.0, 1.0, 2.0])  # todas alem da janela
        self.assertFalse(_check_login_rate_limit(req))
        self.assertEqual(req.session["login_attempts"], [])

    @patch("portal.views_auth.time")
    def test_bloqueia_apos_max_na_janela(self, mock_time):
        now = 10_000.0
        mock_time.time.return_value = now
        recentes = [now - 1 for _ in range(MAX_LOGIN_ATTEMPTS)]
        self.assertTrue(_check_login_rate_limit(self._req(recentes)))

    @patch("portal.views_auth.time")
    def test_record_poda_antes_de_adicionar(self, mock_time):
        now = 10_000.0
        mock_time.time.return_value = now
        antigas = [now - LOGIN_TIMEOUT - 1 for _ in range(4)]
        req = self._req(antigas)
        _record_login_attempt(req)
        # as 4 antigas foram podadas; sobra apenas a recem registrada
        self.assertEqual(req.session["login_attempts"], [now])

    @patch("portal.views_auth.time")
    def test_libera_apos_janela_expirar(self, mock_time):
        now = 10_000.0
        mock_time.time.return_value = now
        expiradas = [now - LOGIN_TIMEOUT - 1 for _ in range(MAX_LOGIN_ATTEMPTS)]
        self.assertFalse(_check_login_rate_limit(self._req(expiradas)))
