# Generated manually for store_name field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sellers', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='seller',
            name='store_name',
            field=models.CharField(blank=True, max_length=255, verbose_name='Название магазина'),
        ),
    ]
