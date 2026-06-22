"""Testes de validacao de formularios — puros, sem banco."""
from django.test import TestCase

from portal.forms import CadastroCidadaoForm, RedefinirSenhaForm, ServicoForm


class ServicoFormTests(TestCase):
    """ServicoForm nao deve conter campos de prazo (agora global no semaforo)."""

    def test_servico_form_nao_tem_campos_prazo(self):
        self.assertNotIn("prazo_amarelo_dias", ServicoForm().fields)
        self.assertNotIn("prazo_vermelho_dias", ServicoForm().fields)


class CadastroCidadaoFormTests(TestCase):
    """Testa a validacao do formulario de cadastro de cidadao."""

    def _base_data(self):
        return {
            "nome_completo": "Joao Silva",
            "cpf": "123.456.789-01",
            "dt_nascimento": "1990-01-15",
            "telefone": "65999990000",
            "email": "joao@email.com",
            "senha": "Minhasenha123!",
            "senha2": "Minhasenha123!",
        }

    def test_form_valido(self):
        """Form com dados completos e senhas iguais eh valido."""
        form = CadastroCidadaoForm(data=self._base_data())
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes_invalida(self):
        """Form com senhas diferentes eh invalido."""
        data = self._base_data()
        data["senha2"] = "outrasenha456"
        form = CadastroCidadaoForm(data=data)
        self.assertFalse(form.is_valid())

    def test_cpf_limpa_mascara(self):
        """CPF com mascara (123.456.789-01) retorna apenas digitos."""
        data = self._base_data()
        data["cpf"] = "123.456.789-01"
        form = CadastroCidadaoForm(data=data)
        form.is_valid()
        self.assertEqual(form.cleaned_data["cpf"], "12345678901")

    def test_senha_curta_invalida(self):
        """Senha com menos de 8 caracteres eh invalida."""
        data = self._base_data()
        data["senha"] = "abc"
        data["senha2"] = "abc"
        form = CadastroCidadaoForm(data=data)
        self.assertFalse(form.is_valid())


class RedefinirSenhaFormTests(TestCase):
    """Testa a validacao do formulario de redefinicao de senha."""

    def test_senhas_iguais_valido(self):
        """Form com senhas iguais e na politica (8+, maiuscula, numero, especial)."""
        form = RedefinirSenhaForm(data={"senha": "Novasenha1!", "senha2": "Novasenha1!"})
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes_invalido(self):
        """Form com senhas diferentes eh invalido."""
        form = RedefinirSenhaForm(data={"senha": "Novasenha1!", "senha2": "Outrasenha1!"})
        self.assertFalse(form.is_valid())
