# estes sao os testes mais tranquilos: form e validacao pura, nao toco em banco
# nem em mock. So instancio o form com uns dados e vejo se is_valid() reage certo.
"""Testes de validacao de formularios — puros, sem banco."""
from django.test import TestCase

from portal.forms import CadastroCidadaoForm, RedefinirSenhaForm, ServicoForm


class ServicoFormTests(TestCase):
    """Os campos de prazo sairam do ServicoForm (viraram config global do semaforo)."""

    def test_servico_form_nao_tem_campos_prazo(self):
        # garanto que os campos antigos de prazo nao voltaram pro form por engano
        self.assertNotIn("prazo_amarelo_dias", ServicoForm().fields)
        self.assertNotIn("prazo_vermelho_dias", ServicoForm().fields)


class CadastroCidadaoFormTests(TestCase):
    """Testa a validacao do form de cadastro de cidadao."""

    def _base_data(self):
        # dados base de um cadastro valido; cada teste copia isso e estraga 1 campo
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
        """Caminho feliz: dados completos e senhas batendo -> form valido."""
        form = CadastroCidadaoForm(data=self._base_data())
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes_invalida(self):
        """Se a confirmacao de senha nao bate, o form tem que recusar."""
        data = self._base_data()
        data["senha2"] = "outrasenha456"  # estrago so a confirmacao
        form = CadastroCidadaoForm(data=data)
        self.assertFalse(form.is_valid())

    def test_cpf_limpa_mascara(self):
        """Mando CPF com mascara e espero que o clean tire ponto/traco (so digitos)."""
        data = self._base_data()
        data["cpf"] = "123.456.789-01"
        form = CadastroCidadaoForm(data=data)
        form.is_valid()  # preciso rodar a validacao pra ter o cleaned_data
        self.assertEqual(form.cleaned_data["cpf"], "12345678901")

    def test_senha_curta_invalida(self):
        """Senha com menos de 8 caracteres deve furar a politica e invalidar o form."""
        data = self._base_data()
        data["senha"] = "abc"
        data["senha2"] = "abc"
        form = CadastroCidadaoForm(data=data)
        self.assertFalse(form.is_valid())


class RedefinirSenhaFormTests(TestCase):
    """Testa o form de redefinicao de senha (mesma ideia, so senha + confirmacao)."""

    def test_senhas_iguais_valido(self):
        """Senhas iguais e dentro da politica (8+, maiuscula, numero, especial) -> valido."""
        form = RedefinirSenhaForm(data={"senha": "Novasenha1!", "senha2": "Novasenha1!"})
        self.assertTrue(form.is_valid())

    def test_senhas_diferentes_invalido(self):
        """Senhas diferentes -> form invalido."""
        form = RedefinirSenhaForm(data={"senha": "Novasenha1!", "senha2": "Outrasenha1!"})
        self.assertFalse(form.is_valid())
