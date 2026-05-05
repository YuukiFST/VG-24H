#!/bin/sh

# Backup
cp -r .git .git_backup2

git filter-branch -f --env-filter '
# DEFAULT variables to avoid keeping previous commit values if bug
NEW_NAME="$GIT_AUTHOR_NAME"
NEW_EMAIL="$GIT_AUTHOR_EMAIL"

# Define mappings based on roles
# Fausto: Frontend/GOV.BR, Equipe, Gestão
if [ "$GIT_COMMIT" = "63d3f1b670979dae5189c29e5acef654d89c0e3e" ] || \
   [ "$GIT_COMMIT" = "087d614c66bdfa79aec2f46545281af7988f2711" ] || \
   [ "$GIT_COMMIT" = "4964768d64fdb4e89c8babc895a9e668e504dacc" ] || \
   [ "$GIT_COMMIT" = "df13cc39f4c8bd5ed966661c04327f495bb02f99" ] || \
   [ "$GIT_COMMIT" = "fcba448b28292c71742b89ae64113203fdb8f682" ] || \
   [ "$GIT_COMMIT" = "048e901fd7e565703bc9e6723e0420106a49ef40" ] || \
   [ "$GIT_COMMIT" = "5f135d1a14e6bf86d05b814e3fdd9bf2a4b4bd3c" ] || \
   [ "$GIT_COMMIT" = "3e5168846142d90249a7d90a127ea90c55c0db94" ] || \
   [ "$GIT_COMMIT" = "0edd20187fa6f3d8185bbcc028938e74fc526e29" ] || \
   [ "$GIT_COMMIT" = "a1cc5af60baea40ad98107802adb1c7652c56d2a" ] || \
   [ "$GIT_COMMIT" = "432f04b7fba4813ac42204718621ee67913e83a3" ] || \
   [ "$GIT_COMMIT" = "92a409caf3c636d81a400f8b3126f3c318aa3580" ] || \
   [ "$GIT_COMMIT" = "e518cf6233e3ea26b64c1c24a97486d203c2890e" ] || \
   [ "$GIT_COMMIT" = "3cdf88aba296d9aa69b945b270458109aa8d14a1" ] || \
   [ "$GIT_COMMIT" = "655e30108ec99d884cfd6edeba86857335c39e11" ] || \
   [ "$GIT_COMMIT" = "f8b6a41cd7766297db9a910aeb3a46bb3ae79c87" ]; then
    NEW_NAME="YuukiFST"
    NEW_EMAIL="faustoyuuki@gmail.com"

# Bruno: Auth, Cidadão, Root/Homepage
elif [ "$GIT_COMMIT" = "2a7c78c2e3c9d69b91ff310eb8a70f86b13ef127" ] || \
     [ "$GIT_COMMIT" = "bd6a4e4103eeee92022ee7d3a3adf83a1a7bde8c" ] || \
     [ "$GIT_COMMIT" = "e91a07816389b753beb07a81c251f4ad34400c25" ] || \
     [ "$GIT_COMMIT" = "13979ade06c54c36c3653c3e2e7c8c937588c125" ] || \
     [ "$GIT_COMMIT" = "d489977c8511316a0c4adc805043f2f552796af2" ] || \
     [ "$GIT_COMMIT" = "0c636067880f76a5fc74939d07a6216ec29fa803" ] || \
     [ "$GIT_COMMIT" = "f22c060fed34a3705993e398380832dfa30140ce" ] || \
     [ "$GIT_COMMIT" = "922786f3dad05ea81ccb5124cbceb9c854a3857a" ] || \
     [ "$GIT_COMMIT" = "a5ddf4a75343f974d44a12532e40dc9c47f991dc" ] || \
     [ "$GIT_COMMIT" = "bcc9bf3014f49d3623b91c7a3d362e4f417034db" ] || \
     [ "$GIT_COMMIT" = "0311d941f182e83f66ee24fcb2e560f5f52fbc5c" ]; then
    NEW_NAME="bruno-df"
    NEW_EMAIL="brunoodfonteles@gmail.com"

# Rafael: DB, Models, Settings, Initial Config
elif [ "$GIT_COMMIT" = "0e8d7e82acd6f8bd44dfff8e4ad42158d2d8f244" ] || \
     [ "$GIT_COMMIT" = "2331d262573f3fbaa12a34bc3c3ff479657530ed" ] || \
     [ "$GIT_COMMIT" = "b7e347178724b0d870b7818549747bfa2b1fa054" ] || \
     [ "$GIT_COMMIT" = "bac3ccd460e4b19f09db1974bdc0eace6b624bc3" ] || \
     [ "$GIT_COMMIT" = "5fae61b82b2178e06be0b29198a9206b40f1f3ab" ] || \
     [ "$GIT_COMMIT" = "9032538dc2a8e045162bd3039dca6eabd9db7f12" ] || \
     [ "$GIT_COMMIT" = "eb8cef35f56ad93c96937b147fbbcca7a7605736" ] || \
     [ "$GIT_COMMIT" = "b7fdd4a3eeb913300784726500e875c429559ed6" ] || \
     [ "$GIT_COMMIT" = "a99354d0e094328d00674df0f950274ad42e3631" ] || \
     [ "$GIT_COMMIT" = "860a22f56d68ff0248aaf32be20de469e6e102ef" ] || \
     [ "$GIT_COMMIT" = "a4f6edd8385a34e2edfe5ba48f4128512e4bbe68" ]; then
    NEW_NAME="RafaelPMarquesP"
    NEW_EMAIL="Rafpereiramar@gmail.com"
fi

export GIT_AUTHOR_NAME="$NEW_NAME"
export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
export GIT_COMMITTER_NAME="$NEW_NAME"
export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
' HEAD
