from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0003_part_subcategory_parent"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="internal_code",
            field=models.CharField(
                verbose_name="Внутренний код товара",
                max_length=32,
                unique=True,
                null=True,
                blank=True,
                db_index=True,
                help_text="Служебный внутренний код для техподдержки",
            ),
        ),
    ]

