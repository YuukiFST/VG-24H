#!/bin/sh
rm -f /tmp/commit_counter
echo 0 > /tmp/commit_counter

git filter-branch -f --env-filter '
COUNTER=$(cat /tmp/commit_counter)

FILES=$(git diff-tree --no-commit-id --name-only -r "$GIT_COMMIT")

# Hard role rules
if echo "$FILES" | grep -q -E "database/|models\.py|seed\.sql"; then
    NEW_NAME="RafaelPMarquesP"
    NEW_EMAIL="Rafpereiramar@gmail.com"
elif echo "$FILES" | grep -q -E "views_|forms\.py|decorators\.py|middleware\.py|commands/"; then
    NEW_NAME="bruno-df"
    NEW_EMAIL="brunoodfonteles@gmail.com"
elif echo "$FILES" | grep -q -E "templates/|static/"; then
    NEW_NAME="YuukiFST"
    NEW_EMAIL="faustoyuuki@gmail.com"
else
    # Distribute docs/chores/merges evenly (round-robin)
    MOD=$((COUNTER % 3))
    if [ $MOD -eq 0 ]; then
        NEW_NAME="bruno-df"
        NEW_EMAIL="brunoodfonteles@gmail.com"
    elif [ $MOD -eq 1 ]; then
        NEW_NAME="RafaelPMarquesP"
        NEW_EMAIL="Rafpereiramar@gmail.com"
    else
        NEW_NAME="YuukiFST"
        NEW_EMAIL="faustoyuuki@gmail.com"
    fi
    echo $((COUNTER + 1)) > /tmp/commit_counter
fi

export GIT_AUTHOR_NAME="$NEW_NAME"
export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
export GIT_COMMITTER_NAME="$NEW_NAME"
export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
' HEAD