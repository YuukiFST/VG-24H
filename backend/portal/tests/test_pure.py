# estes aqui sao os mais limpos: funcoes puras, entrada -> saida, sem banco e sem
# mock nenhum. Bom pra testar a logica de regra de negocio isolada.
"""Testes de funcoes puras — sem dependencia de banco ou mocks."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from portal import db
from portal.decorators import perfil_codigo


class CorSemaforoTests(TestCase):
    """Testa a regra do semaforo: classificar chamado em verde/amarelo/vermelho
    pela idade dele (quantos dias parado vs os limites amarelo=15 e vermelho=30)."""

    def test_chamado_no_prazo_retorna_verde(self):
        # so 5 dias parado, bem dentro do prazo -> verde
        agora = timezone.now()
        dt = agora - timedelta(days=5)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "verde")

    def test_chamado_atencao_retorna_amarelo(self):
        # 20 dias: passou do amarelo(15) mas nao do vermelho(30) -> amarelo
        agora = timezone.now()
        dt = agora - timedelta(days=20)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "amarelo")

    def test_chamado_critico_retorna_vermelho(self):
        # 35 dias: ja passou do vermelho(30) -> vermelho
        agora = timezone.now()
        dt = agora - timedelta(days=35)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "vermelho")

    def test_chamado_exatamente_no_limite_amarelo(self):
        # teste de borda: bate exatamente em 15 dias -> ja conta como amarelo
        agora = timezone.now()
        dt = agora - timedelta(days=15)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "amarelo")

    def test_chamado_exatamente_no_limite_vermelho(self):
        # outra borda: exatamente 30 dias -> ja conta como vermelho
        agora = timezone.now()
        dt = agora - timedelta(days=30)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "vermelho")

    def test_chamado_zero_dias(self):
        # acabou de abrir (0 dias) -> tem que ser verde
        agora = timezone.now()
        self.assertEqual(db.cor_semaforo(agora, 15, 30), "verde")


class PaginarTests(TestCase):
    """Testa minha paginacao manual do db.py (sem ORM, listas na mao)."""

    def test_pagina_1_sem_total_count(self):
        # 30 itens, pagina 1 de 15 -> total 30 e a 1a metade (0..14)
        itens = list(range(30))
        page_obj, total = db.paginar(itens, pagina=1, por_pagina=15)
        self.assertEqual(total, 30)
        self.assertEqual(list(page_obj.object_list), list(range(15)))

    def test_pagina_2_sem_total_count(self):
        # mesma lista, pagina 2 -> a 2a metade (15..29)
        itens = list(range(30))
        page_obj, total = db.paginar(itens, pagina=2, por_pagina=15)
        self.assertEqual(total, 30)
        self.assertEqual(list(page_obj.object_list), list(range(15, 30)))

    def test_pagina_2_com_total_count(self):
        # quando passo total_count fixo, a lista ja vem so com a fatia da pagina
        # (os 15 itens) mas o total reportado tem que ser o que eu informei (30)
        itens = list(range(15))
        page_obj, total = db.paginar(itens, pagina=2, por_pagina=15, total_count=30)
        self.assertEqual(total, 30)
        self.assertEqual(list(page_obj.object_list), list(range(15)))

    def test_pagina_invalida_cai_para_1(self):
        # se pedirem pagina "abc" (lixo), nao pode explodir: cai pra pagina 1
        itens = list(range(30))
        page_obj, _ = db.paginar(itens, pagina="abc", por_pagina=15)
        self.assertEqual(page_obj.number, 1)

    def test_ultima_pagina_incompleta(self):
        # 25 itens, pagina 2 -> sobra so 10 (15..24) e nao deve ter proxima pagina
        itens = list(range(25))
        page_obj, total = db.paginar(itens, pagina=2, por_pagina=15)
        self.assertEqual(total, 25)
        self.assertEqual(list(page_obj.object_list), list(range(15, 25)))
        self.assertFalse(page_obj.has_next)


class PerfilCodigoTests(TestCase):
    """Testa como eu extraio o codigo de perfil do usuario (CID/GES/COL...)."""

    def test_cidadao_retorna_cid(self):
        # perfil CID volta CID na lata
        self.assertEqual(perfil_codigo(Mock(perfil="CID")), "CID")

    def test_gestor_retorna_ges(self):
        # idem pra gestor
        self.assertEqual(perfil_codigo(Mock(perfil="GES")), "GES")

    def test_perfil_com_espacos_retorna_limpo(self):
        # se vier com espaco em volta, a funcao tem que dar strip
        self.assertEqual(perfil_codigo(Mock(perfil="  COL  ")), "COL")

    def test_usuario_none_retorna_vazio(self):
        # usuario None (nao logado) -> string vazia, sem estourar
        self.assertEqual(perfil_codigo(None), "")

    def test_perfil_none_retorna_vazio(self):
        # usuario existe mas perfil None -> tambem string vazia
        self.assertEqual(perfil_codigo(Mock(perfil=None)), "")


class ValidarTabelaTests(TestCase):
    """Testa o _validar_tabela: a whitelist que me protege de SQL injection
    quando o nome da tabela vem montado em string."""

    def test_tabela_valida_cidadao_ok(self):
        from portal.db import _validar_tabela
        _validar_tabela("cidadao")  # tabela da whitelist: nao pode levantar nada

    def test_tabela_valida_servidor_ok(self):
        from portal.db import _validar_tabela
        _validar_tabela("servidor")  # idem, servidor tambem eh permitida

    def test_tabela_invalida_levanta_value_error(self):
        from portal.db import _validar_tabela
        # nome fora da whitelist -> ValueError
        with self.assertRaises(ValueError):
            _validar_tabela("tabela_inexistente")

    def test_tabela_injetada_levanta_value_error(self):
        from portal.db import _validar_tabela
        # tentativa classica de injection -> tem que barrar
        with self.assertRaises(ValueError):
            _validar_tabela("servidor; DROP TABLE chamado")


class SqlLateralUltimoStatusTests(TestCase):
    """Testa o sql_lateral_ultimo_status: mesma ideia de whitelist, mas pras
    colunas/alias que entram no JOIN LATERAL montado em string."""

    def test_colunas_validas_ok(self):
        from portal.db import sql_lateral_ultimo_status
        # sem args usa o default; confiro que o SQL gerado tem o JOIN e a coluna
        result = sql_lateral_ultimo_status()
        self.assertIn("JOIN LATERAL", result)
        self.assertIn("sc.sigla", result)

    def test_coluna_sigla_ok(self):
        from portal.db import sql_lateral_ultimo_status
        # passando uma coluna valida explicita, ela tem que aparecer no SQL
        result = sql_lateral_ultimo_status(colunas="sc.sigla")
        self.assertIn("sc.sigla", result)

    def test_coluna_invalida_levanta_value_error(self):
        from portal.db import sql_lateral_ultimo_status
        # coluna com injection -> ValueError, nao deixa montar o SQL
        with self.assertRaises(ValueError):
            sql_lateral_ultimo_status(colunas="1; DROP TABLE chamado")

    def test_alias_invalido_levanta_value_error(self):
        from portal.db import sql_lateral_ultimo_status
        # alias fora do permitido tambem barra
        with self.assertRaises(ValueError):
            sql_lateral_ultimo_status(alias="x")


class Mock:
    """Mock minimo que eu mesmo fiz: so seta os kwargs como atributos.
    Uso ele em vez do MagicMock onde so preciso de uns campos simples."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
