"""
forms.py — Formularios do Portal VG 24H

Os formularios usam ModelChoiceField e ModelForm do Django para validacao
de Foreign Keys (ex: id_servico, id_status, id_categoria). Isso eh
intencional: o Django valida automaticamente que o valor selecionado
existe na tabela referenciada, evitando erro de FK no banco.

As views, por sua vez, usam SQL puro para todas as operacoes de leitura
e escrita (INSERT, UPDATE, SELECT, DELETE). O form.save() nunca eh chamado.
"""

from django import forms

from portal.models import (
    Bairro,
    CategoriaServico,
    Servico,
    StatusChamado,
)


# ------------------------------------------------------------------
# Formularios do cidadao
# ------------------------------------------------------------------

class CadastroCidadaoForm(forms.Form):
    """Formulario de cadastro de cidadao com validacao de CPF e senhas.

    O wizard de cadastro tem 3 etapas (dados pessoais, endereco, foto),
    mas o formulario Python unifica todos os campos. A etapa de foto
    eh tratada separadamente na view.
    """
    nome_completo = forms.CharField(max_length=200, label="Nome completo")
    cpf = forms.CharField(max_length=14, label="CPF")
    dt_nascimento = forms.DateField(label="Data de nascimento")
    telefone = forms.CharField(max_length=20, label="Telefone")
    email = forms.EmailField(max_length=255, label="E-mail")
    senha = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Senha")
    senha2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    # Campos de endereco (etapa 2 do wizard).
    rua = forms.CharField(max_length=100, required=False)
    num_endereco = forms.CharField(max_length=10, required=False)
    complemento_endereco = forms.CharField(max_length=200, required=False)
    bairro_endereco = forms.CharField(max_length=200, required=False)
    cep_endereco = forms.CharField(max_length=10, required=False)

    def clean_cpf(self):
        """Remove caracteres nao numericos do CPF antes de validar."""
        cpf = self.cleaned_data.get("cpf", "")
        return "".join(filter(str.isdigit, cpf))

    def clean_telefone(self):
        """Remove caracteres nao numericos do telefone."""
        tel = self.cleaned_data.get("telefone", "")
        tel = "".join(filter(str.isdigit, tel))
        if len(tel) < 8:
            raise forms.ValidationError("Telefone deve ter pelo menos 8 digitos.")
        return tel

    def clean(self):
        """Valida que as duas senhas digitadas sao iguais."""
        d = super().clean()
        if d.get("senha") and d.get("senha2") and d.get("senha") != d.get("senha2"):
            raise forms.ValidationError("As senhas nao coincidem.")
        return d


class RecuperarSenhaForm(forms.Form):
    """Formulario para solicitacao de recuperacao de senha via email."""
    email = forms.EmailField(label="E-mail cadastrado")


class RedefinirSenhaForm(forms.Form):
    """Formulario para definir nova senha (apos clicar no link do email)."""
    senha = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Nova senha")
    senha2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    def clean(self):
        d = super().clean()
        if d.get("senha") != d.get("senha2"):
            raise forms.ValidationError("As senhas nao coincidem.")
        return d


class TrocaSenhaObrigatoriaForm(RedefinirSenhaForm):
    """Troca obrigatoria de senha no primeiro acesso de servidores.

    Herda RedefinirSenhaForm com a mesma validacao (senha + confirmacao).
    """
    pass


class NovaSenhaForm(forms.Form):
    """Formulario para troca de senha (campo unico)."""
    nova_senha = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Nova senha")


class ChamadoNovoForm(forms.Form):
    """Formulario de abertura de chamado pelo cidadao.

    O campo id_servico usa ModelChoiceField para validar que o servico
    selecionado existe e esta ativo. O select cascata (categoria -> servico)
    eh implementado no template com JavaScript.
    """
    id_servico = forms.ModelChoiceField(
        queryset=Servico.objects.filter(ativo=True).select_related("id_categoria"),
        label="Servico",
    )
    id_bairro = forms.ModelChoiceField(
        queryset=Bairro.objects.filter(ativo=True),
        label="Bairro",
    )
    descricao = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Descricao do problema",
    )
    ponto_de_referencia = forms.CharField(
        max_length=100,
        required=False,
        label="Ponto de referencia",
    )
    foto = forms.ImageField(label="Foto (obrigatoria)")


class ObservacaoForm(forms.Form):
    """Formulario para adicionar observacao (mensagem) a um chamado."""
    texto = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Mensagem",
    )


class AvaliacaoForm(forms.Form):
    """Avaliacao de chamado concluido: nota de 1 a 5 + comentario opcional."""
    nota = forms.TypedChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        coerce=int,
        label="Nota de 1 a 5",
    )
    comentario = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Comentario (opcional)",
    )


class CancelarChamadoForm(forms.Form):
    """Formulario de cancelamento de chamado pelo cidadao (motivo obrigatorio)."""
    motivo = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Motivo do cancelamento",
    )


# ------------------------------------------------------------------
# Formularios de gestao (equipe)
# ------------------------------------------------------------------

class EquipeStatusForm(forms.Form):
    """Formulario de alteracao de status do chamado pela equipe.

    O campo resolucao eh obrigatorio apenas quando o novo status
    eh CO (Concluido) ou CA (Cancelado). A validacao no clean()
    verifica essa regra.
    """
    id_status = forms.ModelChoiceField(
        queryset=StatusChamado.objects.all(),
        label="Novo status",
    )
    resolucao = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Resolucao / motivo (obrigatorio ao concluir ou cancelar)",
    )

    def clean(self):
        d = super().clean()
        st = d.get("id_status")
        r = (d.get("resolucao") or "").strip()
        if st and st.sigla.strip() in ("CO", "CA") and not r:
            raise forms.ValidationError(
                "Informe a resolucao ou motivo ao concluir ou cancelar."
            )
        return d


class FotoForm(forms.Form):
    """Formulario simples para upload de foto (chamado ou perfil)."""
    foto = forms.ImageField(label="Foto")


class CategoriaForm(forms.ModelForm):
    """Formulario de categoria de servico (nome + descricao)."""
    class Meta:
        model = CategoriaServico
        fields = ["nome", "descricao"]


class ServicoForm(forms.ModelForm):
    """Formulario de servico (prazos removidos para config global)."""
    class Meta:
        model = Servico
        fields = ["id_categoria", "nome", "descricao"]


class BairroForm(forms.ModelForm):
    """Formulario de bairro (nome, CEP, regiao, ativo).

    O campo regiao eh um combobox com valores predefinidos
    (Central, Norte, Sul, etc.) conforme configurado no model.
    """
    class Meta:
        model = Bairro
        fields = ["nome_bairro", "cep", "regiao", "ativo"]


class ColaboradorNovoForm(forms.Form):
    """Criacao de colaborador pelo gestor.

    O gestor define uma senha provisoria que o colaborador deve
    trocar no primeiro acesso (senha_temporaria="1").
    """
    nome_completo = forms.CharField(max_length=200)
    cpf = forms.CharField(max_length=11)
    dt_nascimento = forms.DateField()
    telefone = forms.CharField(max_length=20)
    email = forms.EmailField(max_length=255)

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf", "")
        return "".join(filter(str.isdigit, cpf))

    def clean_telefone(self):
        tel = self.cleaned_data.get("telefone", "")
        tel = "".join(filter(str.isdigit, tel))
        if len(tel) < 8:
            raise forms.ValidationError("Telefone deve ter pelo menos 8 digitos.")
        return tel

    senha_provisoria = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput,
        label="Senha provisoria",
    )
