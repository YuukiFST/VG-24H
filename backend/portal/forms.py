from django import forms

from portal.models import (
    Bairro,
    CategoriaServico,
    Servico,
    StatusChamado,
)


class CadastroCidadaoForm(forms.Form):
    nome_completo = forms.CharField(max_length=200, label="Nome completo")
    cpf = forms.CharField(max_length=14, label="CPF")
    dt_nascimento = forms.DateField(label="Data de nascimento")
    telefone = forms.CharField(max_length=20, label="Telefone")
    email = forms.EmailField(max_length=255, label="E-mail")
    senha = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Senha")
    senha2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    # Address fields (Step 2)
    rua = forms.CharField(max_length=100, required=False)
    num_endereco = forms.CharField(max_length=10, required=False)
    complemento_endereco = forms.CharField(max_length=200, required=False)
    bairro_endereco = forms.CharField(max_length=200, required=False)
    cep_endereco = forms.CharField(max_length=10, required=False)

    def clean_cpf(self):
        # Allow frontend to send masked CPF, keep only digits for the backend log/DB
        cpf = self.cleaned_data.get("cpf", "")
        return "".join(filter(str.isdigit, cpf))

    def clean(self):
        d = super().clean()
        if d.get("senha") and d.get("senha2") and d.get("senha") != d.get("senha2"):
            raise forms.ValidationError("As senhas não coincidem.")
        return d


class RecuperarSenhaForm(forms.Form):
    email = forms.EmailField(label="E-mail cadastrado")


class RedefinirSenhaForm(forms.Form):
    senha = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Nova senha")
    senha2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    def clean(self):
        d = super().clean()
        if d.get("senha") != d.get("senha2"):
            raise forms.ValidationError("As senhas não coincidem.")
        return d


class TrocaSenhaObrigatoriaForm(RedefinirSenhaForm):
    pass


class ChamadoNovoForm(forms.Form):
    id_servico = forms.ModelChoiceField(
        queryset=Servico.objects.filter(ativo=True).select_related("id_categoria"),
        label="Serviço",
    )
    id_bairro = forms.ModelChoiceField(
        queryset=Bairro.objects.filter(ativo=True),
        label="Bairro",
    )
    descricao = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Descrição do problema",
    )
    ponto_de_referencia = forms.CharField(
        max_length=100,
        required=False,
        label="Ponto de referência",
    )
    foto = forms.ImageField(label="Foto (obrigatória)")


class ObservacaoForm(forms.Form):
    texto = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Mensagem",
    )


class AvaliacaoForm(forms.Form):
    nota = forms.TypedChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        coerce=int,
        label="Nota de 1 a 5",
    )
    comentario = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Comentário (opcional)",
    )


class CancelarChamadoForm(forms.Form):
    motivo = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Motivo do cancelamento",
    )


class EquipeStatusForm(forms.Form):
    id_status = forms.ModelChoiceField(
        queryset=StatusChamado.objects.all(),
        label="Novo status",
    )
    resolucao = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Resolução / motivo (obrigatório ao concluir ou cancelar)",
    )

    def clean(self):
        d = super().clean()
        st = d.get("id_status")
        r = (d.get("resolucao") or "").strip()
        if st and st.sigla.strip() in ("CO", "CA") and not r:
            raise forms.ValidationError(
                "Informe a resolução ou motivo ao concluir ou cancelar."
            )
        return d


class FotoForm(forms.Form):
    foto = forms.ImageField(label="Foto")


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = CategoriaServico
        fields = ["nome", "descricao"]


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = [
            "id_categoria",
            "nome",
            "descricao",
            "prazo_amarelo_dias",
            "prazo_vermelho_dias",
        ]


class BairroForm(forms.ModelForm):
    class Meta:
        model = Bairro
        fields = ["nome_bairro", "cep", "regiao"]


class ColaboradorNovoForm(forms.Form):
    nome_completo = forms.CharField(max_length=200)
    cpf = forms.CharField(max_length=11)
    dt_nascimento = forms.DateField()
    telefone = forms.CharField(max_length=20)
    email = forms.EmailField(max_length=255)
    senha_provisoria = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput,
        label="Senha provisória",
    )
