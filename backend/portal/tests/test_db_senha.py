# aqui eu testo a parte de senha do db sem precisar de banco de verdade:
# mocko a connection inteira e so olho o SQL que minha funcao mandaria rodar.
"""Testes da camada de senha (db.senha) — connection mockada, sem banco."""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from portal import db


class AtualizarSenhaUsuarioTests(TestCase):
    """Garanto que toda troca de senha limpa a flag senha_temporaria.

    Esse bug me mordeu antes: se eu troco a senha mas esqueco de zerar a flag,
    o usuario cai num loop de "tem que trocar a senha" todo login. Aqui travo
    isso pra nao acontecer de novo.
    """

    def _exec_sql(self, tabela, pk):
        # helper meu: roda a atualizacao com a connection mockada e me devolve
        # o primeiro arg do execute (a string SQL) pra eu inspecionar.
        with patch("portal.db.senha.connection") as mock_conn:
            mock_cursor = MagicMock()
            # finjo o context manager do "with connection.cursor() as cur":
            # __enter__ devolve meu cursor fake, __exit__ nao engole excecao.
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            db.atualizar_senha_usuario(tabela, pk, "NovaSenha1!")
            # pego o SQL que foi montado: call_args[0][0] = primeiro posicional do execute
            return mock_cursor.execute.call_args[0][0]

    def test_servidor_limpa_flag_temporaria(self):
        # caso servidor: o SQL tem que zerar a flag e mexer na pk certa (id_servidor)
        sql = self._exec_sql("servidor", 7)
        self.assertIn("senha_temporaria = NULL", sql)
        self.assertIn("id_servidor", sql)

    def test_cidadao_limpa_flag_temporaria(self):
        # mesma coisa pro cidadao, so muda a tabela e a pk (id_cidadao)
        sql = self._exec_sql("cidadao", 3)
        self.assertIn("senha_temporaria = NULL", sql)
        self.assertIn("id_cidadao", sql)

    def test_tabela_invalida_rejeitada(self):
        # se alguem passar lixo/injection no nome da tabela, tem que estourar
        # ValueError (whitelist) antes de chegar perto do banco
        with self.assertRaises(ValueError):
            db.atualizar_senha_usuario("servidor; DROP TABLE chamado", 1, "x")
