from django.db import migrations, models
import django.db.models.deletion


def normalize_article(value):
    if not value:
        return ''
    return ''.join(char for char in str(value).upper() if char.isalnum())


def populate_normalized_part_numbers(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    for product in Product.objects.exclude(part_number__isnull=True).exclude(part_number='').iterator():
        Product.objects.filter(pk=product.pk).update(
            normalized_part_number=normalize_article(product.part_number)
        )


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_merge_0013_shop'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='normalized_part_number',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                editable=False,
                help_text='Service field for part-number and cross-reference search',
                max_length=100,
                verbose_name='Normalized part number',
            ),
        ),
        migrations.RunPython(populate_normalized_part_numbers, migrations.RunPython.noop),
        migrations.CreateModel(
            name='ProductCrossReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('article_number', models.CharField(db_index=True, max_length=100)),
                ('normalized_article', models.CharField(blank=True, db_index=True, default='', editable=False, max_length=100)),
                ('brand', models.CharField(blank=True, default='', max_length=100)),
                ('relation_type', models.CharField(choices=[('cross', 'Cross'), ('analog', 'Analog'), ('oem', 'OEM'), ('replacement', 'Replacement')], db_index=True, default='cross', max_length=20)),
                ('comment', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('analog_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='incoming_cross_references', to='shop.product')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cross_references', to='shop.product')),
            ],
            options={
                'verbose_name': 'Product cross reference',
                'verbose_name_plural': 'Product cross references',
                'ordering': ['brand', 'article_number'],
                'unique_together': {('product', 'normalized_article', 'brand', 'relation_type')},
                'indexes': [
                    models.Index(fields=['normalized_article', 'is_active'], name='shop_produc_normali_82ddf3_idx'),
                    models.Index(fields=['product', 'relation_type'], name='shop_produc_product_ce0e1f_idx'),
                    models.Index(fields=['analog_product', 'is_active'], name='shop_produc_analog__3c688c_idx'),
                ],
            },
        ),
    ]
