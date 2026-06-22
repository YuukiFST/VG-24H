"""Testes da camada de senha (db.senha) — connection mockada, sem banco."""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from portal import db


class AtualizarSenhaUsuarioTests(TestCase):
    """atualizar_senha_usuario deve limpar senha_temporaria em toda troca.

    Regressao: trocar a senha sem limpar a flag forcava o usuario a trocar
    de novo no proximo login (loop de troca obrigatoria).
    """

    def _exec_sql(self, tabela, pk):
        with patch("portal.db.senha.connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            db.atualizar_senha_usuario(tabela, pk, "NovaSenha1!")
            return mock_cursor.execute.call_args[0][0]

    def test_servidor_limpa_flag_temporaria(self):
        sql = self._exec_sql("servidor", 7)
        self.assertIn("senha_temporaria = NULL", sql)
        self.assertIn("id_servidor", sql)

    def test_cidadao_limpa_flag_temporaria(self):
        sql = self._exec_sql("cidadao", 3)
        self.assertIn("senha_temporaria = NULL", sql)
        self.assertIn("id_cidadao", sql)

    def test_tabela_invalida_rejeitada(self):
        with self.assertRaises(ValueError):
            db.atualizar_senha_usuario("servidor; DROP TABLE chamado", 1, "x")
