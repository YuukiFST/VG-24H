# aqui testo a geracao do numero de protocolo. A atomicidade e a sequencia
# moram na stored function fn_proximo_protocolo(ano) no banco; o Python so
# chama a funcao e devolve o que ela retornou. Como nao quero subir banco, eu
# mocko a connection e confiro que a chamada e o retorno estao certos.
"""Testes da geracao de protocolo — connection mockada, sem banco."""
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from portal.utils import proximo_protocolo


class ProximoProtocoloTests(TestCase):
    """Confiro que proximo_protocolo() chama a funcao do banco e devolve o valor.

    A regra (INSERT ... ON CONFLICT + unicidade) agora fica na stored function
    fn_proximo_protocolo(ano); o Python virou um wrapper fino. Por isso mocko o
    connection.cursor e simulo o retorno da funcao.
    """

    @patch("portal.utils.connection")
    def test_retorna_protocolo_da_funcao(self, mock_conn):
        """A app chama fn_proximo_protocolo(ano) e devolve o protocolo pronto."""
        ano = timezone.now().year
        mock_cursor = MagicMock()
        # a stored function ja devolve o protocolo montado (ANO + 6 digitos)
        mock_cursor.fetchone.return_value = (f"{ano}000001",)
        # mesmo truque do context manager do "with connection.cursor() as cur"
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        resultado = proximo_protocolo()
        self.assertEqual(resultado, f"{ano}000001")
        # confiro que chamei a funcao do banco passando o ano da aplicacao
        sql, params = mock_cursor.execute.call_args[0]
        self.assertIn("fn_proximo_protocolo", sql)
        self.assertEqual(params, [ano])

    @patch("portal.utils.connection")
    def test_erro_se_funcao_nao_retorna(self, mock_conn):
        """Se a funcao do banco nao devolver linha, e bug grave -> RuntimeError."""
        mock_cursor = MagicMock()
        # fetchone None simula a funcao nao retornando nada (nao deveria acontecer)
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with self.assertRaises(RuntimeError):
            proximo_protocolo()
