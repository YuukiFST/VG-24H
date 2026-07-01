"""
forms.py — Formularios do Portal VG 24H

Aqui ficam todos os meus forms. Detalhe importante que eu mesmo decidi:
uso ModelChoiceField e ModelForm so pra deixar o Django validar as Foreign
Keys (id_servico, id_status, id_categoria). Assim o proprio Django ja
confere se o valor escolhido existe na tabela, e eu nao tomo erro de FK
la no banco na hora do INSERT.

Lembrete pra mim: as views fazem TUDO em SQL puro (INSERT, UPDATE, SELECT,
DELETE). Ou seja, eu NUNCA chamo form.save() aqui. O form eh so pra validar.
"""

# re pra checar a senha com regex, forms/ValidationError do Django, e os
# models que eu uso nos ModelChoiceField/ModelForm
import re

from django import forms
from django.core.exceptions import ValidationError

from portal.models import (
    Bairro,
    CategoriaServico,
    Servico,
    StatusChamado,
)


# meu validator de senha forte: uso ele em todo campo de senha la embaixo.
# se quebrar alguma regra eu solto ValidationError com a msg certinha
def _validar_senha_forte(value):
    # pelo menos 8 caracteres
    if len(value) < 8:
        raise ValidationError("Senha deve ter pelo menos 8 caracteres.")
    # tem que ter pelo menos uma MAIUSCULA
    if not re.search(r"[A-Z]", value):
        raise ValidationError("Senha deve conter pelo menos uma letra maiuscula.")
    # pelo menos uma minuscula
    if not re.search(r"[a-z]", value):
        raise ValidationError("Senha deve conter pelo menos uma letra minuscula.")
    # pelo menos um numero (\d)
    if not re.search(r"\d", value):
        raise ValidationError("Senha deve conter pelo menos um numero.")
    # e pelo menos um caractere especial. essa lista grande eh o conjunto
    # de simbolos que eu aceito como "especial"
    if not re.search(r"[!@#$%&*()_+\-=\[\]{};':\"\\|,.<>\/?]", value):
        raise ValidationError("Senha deve conter pelo menos um caractere especial.")


# ------------------------------------------------------------------
# Formularios do cidadao
# ------------------------------------------------------------------

class CadastroCidadaoForm(forms.Form):
    """Form de cadastro do cidadao, com validacao de CPF e das senhas.

    Detalhe: meu wizard no front tem 3 etapas (dados pessoais, endereco,
    foto), mas aqui no Python eu junto tudo num form so. A foto eu trato
    separado la na view, por isso ela nem aparece nesse form.
    """
    # dados pessoais (etapa 1 do wizard)
    nome_completo = forms.CharField(max_length=200, label="Nome completo")
    cpf = forms.CharField(max_length=14, label="CPF")  # 14 pra caber a mascara 000.000.000-00
    dt_nascimento = forms.DateField(label="Data de nascimento")
    telefone = forms.CharField(max_length=20, label="Telefone")
    email = forms.EmailField(max_length=255, label="E-mail")
    # senha passa pelo meu validator de senha forte; senha2 eh so confirmacao
    senha = forms.CharField(widget=forms.PasswordInput, min_length=8, label="Senha", validators=[_validar_senha_forte])
    senha2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    # campos de endereco (etapa 2 do wizard). required=False porque o cidadao
    # pode terminar o cadastro sem preencher endereco agora
    rua = forms.CharField(max_length=100, required=False)
    num_endereco = forms.CharField(max_length=10, required=False)
    complemento_endereco = forms.CharField(max_length=200, required=False)
    # bairro_endereco envia o nome do bairro (texto); validamos que o nome
    # existe na tabela bairro para garantir consistencia dos dados
    bairro_endereco = forms.CharField(max_length=200, required=False)
    cep_endereco = forms.CharField(max_length=10, required=False)

    def clean_bairro_endereco(self):
        """Valida que o nome do bairro informado existe na tabela bairro (ativo)."""
        nome = self.cleaned_data.get("bairro_endereco", "")
        if nome:
            from portal import db
            if not db.existe_nome("bairro", "nome_bairro", nome):
                raise forms.ValidationError("Bairro não encontrado.")
        return nome

    def clean_cpf(self):
        # tiro tudo que nao eh numero do CPF (a mascara manda ponto e traco)
        # e guardo so os digitos, que eh o que vai pro banco
        cpf = self.cleaned_data.get("cpf", "")
        return "".join(filter(str.isdigit, cpf))

    def clean_telefone(self):
        # mesma ideia do CPF: limpo o telefone deixando so digito
        tel = self.cleaned_data.get("telefone", "")
        tel = "".join(filter(str.isdigit, tel))
        # e exijo no minimo 8 digitos pra nao aceitar telefone capenga
        if len(tel) < 8:
            raise forms.ValidationError("Telefone deve ter pelo menos 8 digitos.")
        return tel

    def clean(self):
        # clean geral do form: aqui eu confiro se senha e senha2 batem.
        # so comparo se as duas vieram preenchidas
        d = super().clean()
        if d.get("senha") and d.get("senha2") and d.get("senha") != d.get("senha2"):
            raise forms.ValidationError("As senhas nao coincidem.")
        return d


class RecuperarSenhaForm(forms.Form):
    """Form do "esqueci minha senha": o cara so digita o email cadastrado."""
    email = forms.EmailField(label="E-mail cadastrado")


class RedefinirSenhaForm(forms.Form):
    """Form pra definir a nova senha depois que clicou no link do email."""
    # de novo o validator de senha forte + a confirmacao
    senha = forms.CharField(widget=forms.PasswordInput, min_length=8, label="Nova senha", validators=[_validar_senha_forte])
    senha2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    def clean(self):
        # confiro se as duas senhas batem (aqui comparo direto)
        d = super().clean()
        if d.get("senha") != d.get("senha2"):
            raise forms.ValidationError("As senhas nao coincidem.")
        return d


class TrocaSenhaObrigatoriaForm(RedefinirSenhaForm):
    """Troca de senha obrigatoria no primeiro acesso do servidor.

    Eu so herdo o RedefinirSenhaForm porque a validacao eh identica
    (senha + confirmacao). Por isso o pass, nao preciso adicionar nada.
    """
    pass


class NovaSenhaForm(forms.Form):
    """Form de troca de senha mais simples, com um campo unico de nova senha."""
    nova_senha = forms.CharField(widget=forms.PasswordInput, min_length=8, label="Nova senha", validators=[_validar_senha_forte])


class ChamadoNovoForm(forms.Form):
    """Form de abertura de chamado pelo cidadao.

    O id_servico eh ModelChoiceField com queryset so de servico ativo: assim
    o Django ja valida que o servico existe e ta ativo. O select cascata
    (escolhe categoria -> filtra servico) eu faco no template com JavaScript,
    aqui eu so passo o queryset completo.
    """
    # so servico ativo entra na lista; select_related ja traz a categoria junto
    id_servico = forms.ModelChoiceField(
        queryset=Servico.objects.filter(ativo=True).select_related("id_categoria"),
        label="Serviço",
    )
    # mesma ideia: so bairro ativo
    id_bairro = forms.ModelChoiceField(
        queryset=Bairro.objects.filter(ativo=True),
        label="Bairro",
    )
    # textarea de 4 linhas pro cidadao descrever o problema
    descricao = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Descrição do problema",
    )
    # ponto de referencia eh opcional (required=False)
    ponto_de_referencia = forms.CharField(
        max_length=100,
        required=False,
        label="Ponto de referência",
    )
    # foto obrigatoria pra abrir chamado
    foto = forms.ImageField(label="Foto (obrigatória)")


class ObservacaoForm(forms.Form):
    """Form pra mandar uma observacao/mensagem num chamado ja existente."""
    texto = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Mensagem",
    )


class AvaliacaoForm(forms.Form):
    """Form de avaliacao de chamado concluido: nota de 1 a 5 + comentario."""
    # TypedChoiceField com choices 1..6 (range para no 6, entao vai de 1 a 5)
    # e coerce=int pra ja receber a nota como inteiro, nao string
    nota = forms.TypedChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        coerce=int,
        label="Nota de 1 a 5",
    )
    # comentario eh opcional
    comentario = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Comentário (opcional)",
    )


class CancelarChamadoForm(forms.Form):
    """Form de cancelamento de chamado pelo cidadao. Aqui o motivo eh obrigatorio."""
    motivo = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Motivo do cancelamento",
    )


# ------------------------------------------------------------------
# Formularios de gestao (equipe)
# ------------------------------------------------------------------

class EquipeStatusForm(forms.Form):
    """Form que a equipe usa pra mudar o status do chamado.

    Regra que eu mesmo botei: a resolucao so eh obrigatoria quando o novo
    status eh CO (Concluido) ou CA (Cancelado). Quem cobra isso eh o meu
    clean() la embaixo.
    """
    # lista todos os status do catalogo (AB, EA, EE, CO, CA)
    id_status = forms.ModelChoiceField(
        queryset=StatusChamado.objects.all(),
        label="Novo status",
    )
    # resolucao required=False aqui, mas o clean() torna obrigatoria pra CO/CA
    resolucao = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Resolução / motivo (obrigatório ao concluir ou cancelar)",
    )

    def clean(self):
        d = super().clean()
        st = d.get("id_status")
        # pego a resolucao ja sem espacos nas pontas
        r = (d.get("resolucao") or "").strip()
        # se o status escolhido eh CO ou CA e nao veio resolucao -> erro
        if st and st.sigla.strip() in ("CO", "CA") and not r:
            raise forms.ValidationError(
                "Informe a resolução ou motivo ao concluir ou cancelar."
            )
        return d


class FotoForm(forms.Form):
    """Form simples so pra subir uma foto (serve pro chamado ou pro perfil)."""
    foto = forms.ImageField(label="Foto")


class CategoriaForm(forms.ModelForm):
    """Form de categoria de servico. Aqui sim eh ModelForm, mas a view ainda
    salva via SQL; eu so aproveito o ModelForm pra montar os campos."""
    class Meta:
        # ligo no model CategoriaServico e exponho so nome e descricao
        model = CategoriaServico
        fields = ["nome", "descricao"]


class ServicoForm(forms.ModelForm):
    """Form de servico. Tirei os prazos daqui porque agora prazo eh config
    global (semaforo), nao fica mais por servico."""
    class Meta:
        model = Servico
        # categoria + nome + descricao
        fields = ["id_categoria", "nome", "descricao"]


class BairroForm(forms.ModelForm):
    """Form de bairro (nome, CEP, regiao, ativo).

    O campo regiao usa choices fixos definidos aqui (mesmos valores
    que o template renderiza no <select>), garantindo que o backend
    valide contra a lista canonica e nao aceite strings arbitrarias.
    """
    REGIAO_CHOICES = [
        ("Central", "Central"),
        ("Norte", "Norte"),
        ("Sul", "Sul"),
        ("Leste", "Leste"),
        ("Oeste", "Oeste"),
        ("Rural", "Rural"),
    ]

    cep = forms.CharField(
        max_length=8,
        required=True,
        label="CEP",
        error_messages={"required": "O CEP é obrigatório."},
    )

    regiao = forms.ChoiceField(
        choices=REGIAO_CHOICES,
        required=False,
        label="Região",
    )

    class Meta:
        model = Bairro
        fields = ["nome_bairro", "cep", "regiao", "ativo"]


class ColaboradorNovoForm(forms.Form):
    """Form que o gestor usa pra cadastrar um colaborador novo.

    O gestor define uma senha provisoria, e o colaborador eh obrigado a
    trocar no primeiro acesso (la no banco isso fica marcado com
    senha_temporaria="1").
    """
    nome_completo = forms.CharField(max_length=200)
    cpf = forms.CharField(max_length=11)  # aqui ja espero so os 11 digitos
    dt_nascimento = forms.DateField()
    telefone = forms.CharField(max_length=20)
    email = forms.EmailField(max_length=255)

    def clean_cpf(self):
        # limpo o CPF deixando so digito (mesma logica do form do cidadao)
        cpf = self.cleaned_data.get("cpf", "")
        return "".join(filter(str.isdigit, cpf))

    def clean_telefone(self):
        # limpo o telefone e exijo no minimo 8 digitos
        tel = self.cleaned_data.get("telefone", "")
        tel = "".join(filter(str.isdigit, tel))
        if len(tel) < 8:
            raise forms.ValidationError("Telefone deve ter pelo menos 8 digitos.")
        return tel

    # senha provisoria tambem passa pelo validator de senha forte. ta
    # declarada depois dos clean_* de proposito, mas o Django monta na boa
    senha_provisoria = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput,
        label="Senha provisória",
        validators=[_validar_senha_forte],
    )
