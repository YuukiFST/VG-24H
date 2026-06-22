"""Testes da geracao de protocolo — connection mockada, sem banco."""
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from portal.utils import proximo_protocolo


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
