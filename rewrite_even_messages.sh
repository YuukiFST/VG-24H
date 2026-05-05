#!/bin/sh

git filter-branch -f --env-filter '
MSG=$(git log -1 --format=%s "$GIT_COMMIT")
NEW_NAME="$GIT_AUTHOR_NAME"
NEW_EMAIL="$GIT_AUTHOR_EMAIL"

# Shift docs/chores from Fausto to others
case "$MSG" in
    *"Aprimorados guias e roteiros"*)
        NEW_NAME="bruno-df"; NEW_EMAIL="brunoodfonteles@gmail.com" ;;
    *"atualiza documentacao e roteiros"*)
        NEW_NAME="RafaelPMarquesP"; NEW_EMAIL="Rafpereiramar@gmail.com" ;;
    *"Update Breadcrumb.md"*)
        NEW_NAME="bruno-df"; NEW_EMAIL="brunoodfonteles@gmail.com" ;;
    *"remove menção a cookies"*)
        NEW_NAME="bruno-df"; NEW_EMAIL="brunoodfonteles@gmail.com" ;;
    *"adiciona PERGUNTAS_FREQUENTES_CODIGO"*)
        NEW_NAME="RafaelPMarquesP"; NEW_EMAIL="Rafpereiramar@gmail.com" ;;
    *"atualiza roteiros de apresentação"*)
        NEW_NAME="RafaelPMarquesP"; NEW_EMAIL="Rafpereiramar@gmail.com" ;;
    *"add comprehensive frontend guide"*)
        NEW_NAME="bruno-df"; NEW_EMAIL="brunoodfonteles@gmail.com" ;;
    *"Adicionado Guia para Novos Desenvolvedores"*)
        NEW_NAME="RafaelPMarquesP"; NEW_EMAIL="Rafpereiramar@gmail.com" ;;
    *"Adicionado Guia de Inicialização"*)
        NEW_NAME="bruno-df"; NEW_EMAIL="brunoodfonteles@gmail.com" ;;
    *"Adição dos roteiros de apresentação"*)
        NEW_NAME="RafaelPMarquesP"; NEW_EMAIL="Rafpereiramar@gmail.com" ;;
    *"Revise license terms"*)
        NEW_NAME="bruno-df"; NEW_EMAIL="brunoodfonteles@gmail.com" ;;
    *"add GNU GPLv3 license"*)
        NEW_NAME="RafaelPMarquesP"; NEW_EMAIL="Rafpereiramar@gmail.com" ;;
    *"Initialize README"*)
        NEW_NAME="bruno-df"; NEW_EMAIL="brunoodfonteles@gmail.com" ;;
    *"estruturação inicial django"*|*"Merge branch"*)
        # Alternate initial structure
        if [ $(( $(git log -1 --format=%ct "$GIT_COMMIT") % 2 )) -eq 0 ]; then
            NEW_NAME="RafaelPMarquesP"; NEW_EMAIL="Rafpereiramar@gmail.com"
        else
            NEW_NAME="bruno-df"; NEW_EMAIL="brunoodfonteles@gmail.com"
        fi
        ;;
esac

export GIT_AUTHOR_NAME="$NEW_NAME"
export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
export GIT_COMMITTER_NAME="$NEW_NAME"
export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
' HEAD