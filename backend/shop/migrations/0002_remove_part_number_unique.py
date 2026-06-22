# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='part_number',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Идентификатор товара (может повторяться)',
                max_length=50,
                null=True,
                verbose_name='Артикул'
            ),
        ),
    ]
