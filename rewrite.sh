#!/bin/sh
git filter-branch -f --env-filter '
NEW_NAME="YuukiFST"
NEW_EMAIL="faustoyuuki@gmail.com"

FILES=$(git diff-tree --no-commit-id --name-only -r "$GIT_COMMIT")

if echo "$FILES" | grep -q -E "database/|models\.py|seed\.sql"; then
    NEW_NAME="RafaelPMarquesP"
    NEW_EMAIL="Rafpereiramar@gmail.com"
elif echo "$FILES" | grep -q -E "views_|forms\.py|decorators\.py|middleware\.py|commands/"; then
    NEW_NAME="bruno-df"
    NEW_EMAIL="brunoodfonteles@gmail.com"
fi

export GIT_AUTHOR_NAME="$NEW_NAME"
export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
export GIT_COMMITTER_NAME="$NEW_NAME"
export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
' HEAD