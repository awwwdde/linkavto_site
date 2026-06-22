from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import default_storage
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )
    phone = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Телефон",
        help_text="Заполните телефон или email"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Город"
    )
    photo = models.ImageField(
        upload_to='profile_photos/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Фото профиля",
        help_text="Загрузите ваше фото для профиля"
    )

    def __str__(self):
        return f"Профиль {self.user.username}"

    def clean(self):
        """Валидация: должно быть заполнено хотя бы одно поле (email или телефон)"""
        if not self.phone and not self.user.email:
            raise ValidationError('Необходимо указать либо телефон, либо email')

    def save(self, *args, **kwargs):
        # Вызываем валидацию перед сохранением
        self.clean()

        # Удаляем старое фото при обновлении
        try:
            old = Profile.objects.get(pk=self.pk)
            if old.photo and old.photo != self.photo:
                self.delete_photo(old.photo)
        except Profile.DoesNotExist:
            pass

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Удаляем фото при удалении профиля
        if self.photo:
            self.delete_photo(self.photo)
        super().delete(*args, **kwargs)

    def delete_photo(self, photo_field):
        """Безопасное удаление файла фото"""
        if photo_field and default_storage.exists(photo_field.name):
            try:
                default_storage.delete(photo_field.name)
            except Exception as e:
                print(f"Ошибка при удалении фото: {e}")

    @property
    def photo_url(self):
        """Возвращает URL фото или None"""
        return self.photo.url if self.photo else None

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


# Автоматическое создание профиля при регистрации (отключено)
# Профиль создается только при успешной регистрации через форму
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         try:
#             # Проверяем, есть ли уже профиль
#             instance.profile
#         except Profile.DoesNotExist:
#             try:
#                 # Создаем профиль с email как телефон для уникальности
#                 Profile.objects.create(user=instance, phone=instance.email or '')
#             except Exception as e:
#                 print(f"Ошибка при создании профиля для {instance.email}: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # Профиль не существует, пропускаем
        pass


class PasswordResetCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).seconds > 600  # 10 мин


class Address(models.Model):
    DELIVERY_TYPE_CHOICES = [
        ('delivery', 'Доставка'),
        ('pickup', 'Самовывоз'),
    ]

    PICKUP_PROVIDER_CHOICES = [
        ('cdek', 'СДЭК'),
        ('russian_post', 'Почта России'),
        ('boxberry', 'Boxberry'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField('Название', max_length=100, blank=True)
    full_address = models.TextField('Полный адрес')
    postal_code = models.CharField('Почтовый индекс', max_length=20, blank=True)
    delivery_type = models.CharField(
        'Способ доставки',
        max_length=20,
        choices=DELIVERY_TYPE_CHOICES,
        default='delivery'
    )
    is_default = models.BooleanField('По умолчанию', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    comment = models.TextField('Комментарий', blank=True)

    # Поля для пунктов выдачи
    pickup_provider = models.CharField(
        'Служба доставки',
        max_length=20,
        choices=PICKUP_PROVIDER_CHOICES,
        blank=True,
        null=True
    )
    pickup_point_code = models.CharField('Код пункта выдачи', max_length=100, blank=True)
    pickup_point_name = models.CharField('Название пункта выдачи', max_length=255, blank=True)
    latitude = models.DecimalField('Широта', max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField('Долгота', max_digits=10, decimal_places=7, blank=True, null=True)

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.title or 'Адрес'} {self.user}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Сбрасываем флаг is_default у других адресов пользователя
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def short_address(self):
        """Короткое представление адреса для шапки"""
        # Парсим полный адрес для извлечения города/населенного пункта
        address_parts = self.full_address.split(',')
        if address_parts:
            # Берем первую часть (обычно город/населенный пункт)
            location_part = address_parts[0].strip()

            # Убираем возможные префиксы
            prefixes = ['г.', 'город', 'с.', 'село', 'пос.', 'поселок', 'пгт.', 'д.', 'деревня', 'х.', 'хутор']
            for prefix in prefixes:
                if location_part.lower().startswith(prefix.lower()):
                    location_part = location_part[len(prefix):].strip()
                    break

            return location_part if location_part else "Адрес"
        return "Адрес"

    @property
    def formatted_full_address(self):
        """Форматированное представление полного адреса"""
        return self.full_address.replace(',', ', ')


def user_get_default_address(self):
    """Получить основной адрес пользователя"""
    try:
        return self.addresses.get(is_default=True)
    except Address.DoesNotExist:
        return None


# Добавляем метод к модели User
User.add_to_class('get_default_address', user_get_default_address)


class VerificationCode(models.Model):
    login = models.CharField(max_length=255)  # email или телефон
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=3)  # количество попыток

    def is_expired(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).seconds > 300  # 5 минут

    class Meta:
        verbose_name = "Код верификации"
        verbose_name_plural = "Коды верификации"


