"""
Testes de integracao para db.py — requer banco PostgreSQL configurado.

Para executar:
    pytest backend/portal/tests/test_db_integration.py --reuse-db

Ou pule com:
    pytest backend/portal/tests/test_db_integration.py -m "not integration"
"""
import pytest
from django.test import TestCase

"""
Testes de integracao para db.py — requer banco PostgreSQL configurado.

Para executar:
    pytest backend/portal/tests/test_db_integration.py --reuse-db

Ou pule com:
    pytest backend/portal/tests/test_db_integration.py -m "not integration"
"""
import os

from portal import db

INTEGRATION_ENABLED = os.getenv("VG_TEST_DB", "").lower() in ("true", "1", "yes")

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
    """Testes para db.buscar_chamado() — requer dados no banco."""

    def test_chamado_inexistente_retorna_none(self):
        result = db.buscar_chamado(999999)
        self.assertIsNone(result)


@pytest.mark.skipif(not INTEGRATION_ENABLED, reason="banco necessario")
class TestListarCategoriasAtivas(TestCase):
    """Testes para db.listar_categorias_ativas()."""

    def test_retorna_lista(self):
        result = db.listar_categorias_ativas()
        self.assertIsInstance(result, list)


class TestCorSemaforo(TestCase):
    """Testes para db.cor_semaforo() — funcao pura movida do integration."""

    def test_verde_quando_dentro_do_prazo(self):
        from datetime import timedelta

        from django.utils import timezone
        agora = timezone.now()
        dt = agora - timedelta(days=5)
        self.assertEqual(db.cor_semaforo(dt, 15, 30), "verde")

    @pytest.mark.skipif(not INTEGRATION_ENABLED, reason="banco necessario")
    def test_listar_categorias_com_servicos_retorna_lista(self):
        result = db.listar_categorias_com_servicos()
        self.assertIsInstance(result, list)
        for item in result:
            self.assertIn("categoria", item)
            self.assertIn("servicos", item)
            self.assertIsInstance(item["servicos"], list)
            cat = item["categoria"]
            self.assertTrue(hasattr(cat, "servicos_list"))
