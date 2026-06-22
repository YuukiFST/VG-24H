# aqui testo a geracao do numero de protocolo. Como o contador real fica no
# banco, eu mocko a connection e mando o fetchone devolver o numero que eu quero,
# ai so confiro se a string final ficou no formato ANO + 6 digitos.
"""Testes da geracao de protocolo — connection mockada, sem banco."""
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from portal.utils import proximo_protocolo


class ProximoProtocoloTests(TestCase):
    """Confiro que o protocolo sai sequencial e formatado certinho.

    Por baixo o proximo_protocolo() usa INSERT ... ON CONFLICT DO UPDATE
    RETURNING (atomico no Postgres pra nao gerar numero repetido). Como nao
    quero subir banco, eu mocko o connection.cursor e simulo o retorno.
    """

    @patch("portal.utils.connection")
    def test_primeiro_protocolo_do_ano(self, mock_conn):
        """Primeiro protocolo do ano: contador volta 1, espero ANO+000001."""
        mock_cursor = MagicMock()
        # finjo dois fetchone: o 1o devolve o contador (1,), o 2o None (fim)
        mock_cursor.fetchone.side_effect = [(1,), None]
        # mesmo truque do context manager do "with connection.cursor() as cur"
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        resultado = proximo_protocolo()
        # uso o ano de agora pra montar o esperado e nao quebrar virada de ano
        ano = str(timezone.now().year)
        self.assertEqual(resultado, f"{ano}000001")

    @patch("portal.utils.connection")
    def test_protocolo_incrementa_sequencia(self, mock_conn):
        """Se ja existe contador, o ON CONFLICT incrementa: simulo 6 -> ANO+000006."""
        ano = str(timezone.now().year)
        mock_cursor = MagicMock()
        # agora finjo que o banco devolveu 6, entao o numero tem que sair 000006
        mock_cursor.fetchone.side_effect = [(6,), None]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        resultado = proximo_protocolo()
        self.assertEqual(resultado, f"{ano}000006")
