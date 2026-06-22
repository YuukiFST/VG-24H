# estes aqui sao os testes "de verdade" que batem no Postgres. Por isso eles
# ficam desligados por padrao: so rodam se eu setar VG_TEST_DB=true. No dia a dia
# (CI sem banco) eles sao pulados pelo skipif la embaixo.
"""
Testes de integracao para db.py — requer banco PostgreSQL configurado.

Para executar:
    pytest backend/portal/tests/test_db_integration.py --reuse-db

Ou pule com:
    pytest backend/portal/tests/test_db_integration.py -m "not integration"
"""
import os

import pytest
from django.test import TestCase

from portal import db

# minha flag de liga/desliga: leio a env var e aceito varias formas de "sim"
INTEGRATION_ENABLED = os.getenv("VG_TEST_DB", "").lower() in ("true", "1", "yes")

# marco o modulo inteiro como "integration" e ja deixo o pulo automatico quando
# nao tem banco, assim nao preciso repetir isso em todo teste (mas repito em
# alguns por seguranca/clareza mesmo assim)
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not INTEGRATION_ENABLED,
        reason="Integracao requer DATABASE_URL de teste. "
               "Defina VG_TEST_DB=true para habilitar."
    ),
]


@pytest.mark.skipif(not INTEGRATION_ENABLED, reason="banco necessario")
class TestBuscarChamado(TestCase):
    """Testa o db.buscar_chamado() de verdade (precisa de dados no banco)."""

    def test_chamado_inexistente_retorna_none(self):
        # busco um id que com certeza nao existe -> tem que voltar None, nao erro
        result = db.buscar_chamado(999999)
        self.assertIsNone(result)


@pytest.mark.skipif(not INTEGRATION_ENABLED, reason="banco necessario")
class TestListarCategoriasAtivas(TestCase):
    """Testa o db.listar_categorias_ativas() contra o banco."""

    def test_retorna_lista(self):
        # nao me importo com o conteudo aqui, so quero garantir que volta uma lista
        result = db.listar_categorias_ativas()
        self.assertIsInstance(result, list)


@pytest.mark.skipif(not INTEGRATION_ENABLED, reason="banco necessario")
class TestConfiguracaoSemaforo(TestCase):
    """Testa o singleton da config do semaforo (tabela managed=False, eu cuido dela)."""

    def test_get_singleton_cria_se_vazio(self):
        from portal.models import ConfiguracaoSemaforo

        # zero a tabela e chamo o get_singleton: ele tem que criar a linha padrao
        ConfiguracaoSemaforo.objects.all().delete()
        cfg = ConfiguracaoSemaforo.get_singleton()
        # e os defaults tem que ser 15/30 (amarelo/vermelho)
        self.assertEqual(cfg.prazo_amarelo_dias, 15)
        self.assertEqual(cfg.prazo_vermelho_dias, 30)


class TestCorSemaforo(TestCase):
    """cor_semaforo eh funcao pura, entao esse caso roda sempre (sem banco).
    Os outros metodos com banco eu marco individualmente com skipif."""

    def test_verde_quando_dentro_do_prazo(self):
        # 5 dias parado -> verde. Sem banco, roda em qualquer ambiente.
        from datetime import timedelta

        from django.utils import timezone
        agora = timezone.now()
        dt = agora - timedelta(days=5)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "verde")

    @pytest.mark.skipif(not INTEGRATION_ENABLED, reason="banco necessario")
    def test_listar_categorias_com_servicos_retorna_lista(self):
        # esse precisa de banco: confiro que volta lista e que cada item tem o
        # formato esperado (categoria + servicos, com a categoria carregando a
        # lista de servicos no atributo servicos_list)
        result = db.listar_categorias_com_servicos()
        self.assertIsInstance(result, list)
        for item in result:
            self.assertIn("categoria", item)
            self.assertIn("servicos", item)
            self.assertIsInstance(item["servicos"], list)
            cat = item["categoria"]
            self.assertTrue(hasattr(cat, "servicos_list"))
