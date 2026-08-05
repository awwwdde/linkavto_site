from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0009_add_tire_load_speed_index_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarouselSlide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название')),
                ('image', models.ImageField(upload_to='carousel/', verbose_name='Изображение')),
                ('url', models.CharField(blank=True, default='', help_text='URL для перехода при клике на слайд', max_length=500, verbose_name='Ссылка')),
                ('status', models.CharField(
                    choices=[('none', 'Без статуса'), ('ad', 'Реклама')],
                    default='none',
                    max_length=10,
                    verbose_name='Статус',
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
            ],
            options={
                'verbose_name': 'Слайд карусели',
                'verbose_name_plural': 'Слайды карусели',
                'ordering': ['order', 'created_at'],
            },
        ),
    ]
