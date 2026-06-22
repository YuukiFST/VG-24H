# Essa migration aqui roda SQL de verdade (RunSQL), diferente da 0001 que so
# espelhava os models. Eu uso pra criar duas tabelas de apoio que o ORM nao
# controla: o contador de protocolo e a config do semaforo de prazos.
from django.db import migrations


class Migration(migrations.Migration):
    # essa so roda depois que a 0001 ja passou
    dependencies = [
        ("portal", "0001_initial"),
    ]

    operations = [
        # 1a operacao: tabela que guarda o ultimo numero de protocolo por ano
        migrations.RunSQL(
            sql="""
            -- crio a tabela do contador (uma linha por ano)
            CREATE TABLE IF NOT EXISTS protocolo_seq (
                ano INTEGER PRIMARY KEY,
                ultimo_numero INTEGER NOT NULL DEFAULT 0
            );
            DO $$
            BEGIN
                -- so tento popular se a tabela chamado ja existir
                IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'chamado') THEN
                    -- olho os protocolos que ja existem e pego o maior numero de cada ano
                    INSERT INTO protocolo_seq (ano, ultimo_numero)
                    SELECT
                        LEFT(num_protocolo, 4)::INT AS ano,        -- os 4 primeiros digitos sao o ano
                        MAX(RIGHT(num_protocolo, 6)::INT) AS ultimo_numero  -- os 6 ultimos sao o sequencial
                    FROM chamado
                    GROUP BY ano
                    -- se o ano ja existir, fico com o maior numero entre o que tinha e o novo
                    ON CONFLICT (ano) DO UPDATE
                        SET ultimo_numero = GREATEST(protocolo_seq.ultimo_numero, EXCLUDED.ultimo_numero);
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,   # nao tem como desfazer direito, entao deixo "no-op"
        ),
        # 2a operacao: tabela de config do semaforo (prazos amarelo e vermelho)
        migrations.RunSQL(
            sql="""
            -- tabela de uma linha so (id sempre 1) com os prazos padrao do semaforo
            CREATE TABLE IF NOT EXISTS configuracao_semaforo (
                id                  INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
                prazo_amarelo_dias  INTEGER NOT NULL DEFAULT 15 CHECK (prazo_amarelo_dias >= 0),
                prazo_vermelho_dias INTEGER NOT NULL DEFAULT 30 CHECK (prazo_vermelho_dias >= 0)
            );
            -- ja insiro a config inicial (15 e 30 dias); se ja existir, nao faz nada
            INSERT INTO configuracao_semaforo (id, prazo_amarelo_dias, prazo_vermelho_dias)
            VALUES (1, 15, 30)
            ON CONFLICT (id) DO NOTHING;
            """,
            reverse_sql=migrations.RunSQL.noop,   # tambem sem reverter
        ),
    ]
