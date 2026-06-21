"""Testes de funcoes puras — sem dependencia de banco ou mocks."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from portal import db
from portal.decorators import perfil_codigo


class CorSemaforoTests(TestCase):
    """Testa a classificacao de chamados por urgencia (verde/amarelo/vermelho)."""

    def test_chamado_no_prazo_retorna_verde(self):
        agora = timezone.now()
        dt = agora - timedelta(days=5)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "verde")

    def test_chamado_atencao_retorna_amarelo(self):
        agora = timezone.now()
        dt = agora - timedelta(days=20)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "amarelo")

    def test_chamado_critico_retorna_vermelho(self):
        agora = timezone.now()
        dt = agora - timedelta(days=35)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "vermelho")

    def test_chamado_exatamente_no_limite_amarelo(self):
        agora = timezone.now()
        dt = agora - timedelta(days=15)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "amarelo")

    def test_chamado_exatamente_no_limite_vermelho(self):
        agora = timezone.now()
        dt = agora - timedelta(days=30)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "vermelho")

    def test_chamado_zero_dias(self):
        agora = timezone.now()
        self.assertEqual(db.cor_semaforo(agora, 15, 30), "verde")


class PaginarTests(TestCase):
    """Testa a paginacao manual implementada em db.py."""

    def test_pagina_1_sem_total_count(self):
        itens = list(range(30))
        page_obj, total = db.paginar(itens, pagina=1, por_pagina=15)
        self.assertEqual(total, 30)
        self.assertEqual(list(page_obj.object_list), list(range(15)))

    def test_pagina_2_sem_total_count(self):
        itens = list(range(30))
        page_obj, total = db.paginar(itens, pagina=2, por_pagina=15)
        self.assertEqual(total, 30)
        self.assertEqual(list(page_obj.object_list), list(range(15, 30)))

    def test_pagina_2_com_total_count(self):
        itens = list(range(15))
        page_obj, total = db.paginar(itens, pagina=2, por_pagina=15, total_count=30)
        self.assertEqual(total, 30)
        self.assertEqual(list(page_obj.object_list), list(range(15)))

    def test_pagina_invalida_cai_para_1(self):
        itens = list(range(30))
        page_obj, _ = db.paginar(itens, pagina="abc", por_pagina=15)
        self.assertEqual(page_obj.number, 1)

    def test_ultima_pagina_incompleta(self):
        itens = list(range(25))
        page_obj, total = db.paginar(itens, pagina=2, por_pagina=15)
        self.assertEqual(total, 25)
        self.assertEqual(list(page_obj.object_list), list(range(15, 25)))
        self.assertFalse(page_obj.has_next)


class PerfilCodigoTests(TestCase):
    """Testa a extracao do codigo de perfil do usuario."""

    def test_cidadao_retorna_cid(self):
        self.assertEqual(perfil_codigo(Mock(perfil="CID")), "CID")

    def test_gestor_retorna_ges(self):
        self.assertEqual(perfil_codigo(Mock(perfil="GES")), "GES")

    def test_perfil_com_espacos_retorna_limpo(self):
        self.assertEqual(perfil_codigo(Mock(perfil="  COL  ")), "COL")

    def test_usuario_none_retorna_vazio(self):
        self.assertEqual(perfil_codigo(None), "")

    def test_perfil_none_retorna_vazio(self):
        self.assertEqual(perfil_codigo(Mock(perfil=None)), "")


class ValidarTabelaTests(TestCase):
    """Testes para _validar_tabela — whitelist SQL injection protection."""

    def test_tabela_valida_cidadao_ok(self):
        from portal.db import _validar_tabela
        _validar_tabela("cidadao")  # nao levanta

    def test_tabela_valida_servidor_ok(self):
        from portal.db import _validar_tabela
        _validar_tabela("servidor")

    def test_tabela_invalida_levanta_value_error(self):
        from portal.db import _validar_tabela
        with self.assertRaises(ValueError):
            _validar_tabela("tabela_inexistente")

    def test_tabela_injetada_levanta_value_error(self):
        from portal.db import _validar_tabela
        with self.assertRaises(ValueError):
            _validar_tabela("servidor; DROP TABLE chamado")


class SqlLateralUltimoStatusTests(TestCase):
    """Testes para sql_lateral_ultimo_status — whitelist SQL injection protection."""

    def test_colunas_validas_ok(self):
        from portal.db import sql_lateral_ultimo_status
        result = sql_lateral_ultimo_status()
        self.assertIn("JOIN LATERAL", result)
        self.assertIn("sc.sigla", result)

    def test_coluna_sigla_ok(self):
        from portal.db import sql_lateral_ultimo_status
        result = sql_lateral_ultimo_status(colunas="sc.sigla")
        self.assertIn("sc.sigla", result)

    def test_coluna_invalida_levanta_value_error(self):
        from portal.db import sql_lateral_ultimo_status
        with self.assertRaises(ValueError):
            sql_lateral_ultimo_status(colunas="1; DROP TABLE chamado")

    def test_alias_invalido_levanta_value_error(self):
        from portal.db import sql_lateral_ultimo_status
        with self.assertRaises(ValueError):
            sql_lateral_ultimo_status(alias="x")


class Mock:
    """Minimo mock para teste de funcao pura."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
