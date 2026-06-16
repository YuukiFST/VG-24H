from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            INSERT INTO protocolo_seq (ano, ultimo_numero)
            SELECT
                LEFT(num_protocolo, 4)::INT AS ano,
                MAX(RIGHT(num_protocolo, 6)::INT) AS ultimo_numero
            FROM chamado
            GROUP BY ano
            ON CONFLICT (ano) DO UPDATE
                SET ultimo_numero = GREATEST(protocolo_seq.ultimo_numero, EXCLUDED.ultimo_numero);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
