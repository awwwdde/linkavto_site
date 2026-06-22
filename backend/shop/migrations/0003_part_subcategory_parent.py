# Generated manually for PartSubcategory.parent

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_remove_part_number_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='partsubcategory',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='children',
                to='shop.partsubcategory',
                verbose_name='Родительская подкатегория'
            ),
        ),
    ]
