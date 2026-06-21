from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS protocolo_seq (
                ano INTEGER PRIMARY KEY,
                ultimo_numero INTEGER NOT NULL DEFAULT 0
            );
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'chamado') THEN
                    INSERT INTO protocolo_seq (ano, ultimo_numero)
                    SELECT
                        LEFT(num_protocolo, 4)::INT AS ano,
                        MAX(RIGHT(num_protocolo, 6)::INT) AS ultimo_numero
                    FROM chamado
                    GROUP BY ano
                    ON CONFLICT (ano) DO UPDATE
                        SET ultimo_numero = GREATEST(protocolo_seq.ultimo_numero, EXCLUDED.ultimo_numero);
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS configuracao_semaforo (
                id                  INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
                prazo_amarelo_dias  INTEGER NOT NULL DEFAULT 15 CHECK (prazo_amarelo_dias >= 0),
                prazo_vermelho_dias INTEGER NOT NULL DEFAULT 30 CHECK (prazo_vermelho_dias >= 0)
            );
            INSERT INTO configuracao_semaforo (id, prazo_amarelo_dias, prazo_vermelho_dias)
            VALUES (1, 15, 30)
            ON CONFLICT (id) DO NOTHING;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
