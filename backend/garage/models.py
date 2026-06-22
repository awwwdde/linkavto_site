from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Vehicle(models.Model):
    """Пользовательское транспортное средство в гараже"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='garage_vehicles',
        verbose_name='Пользователь'
    )

    name = models.CharField(
        'Пользовательское название',
        max_length=200,
        blank=True,
        default='',
    )
    
    # Используем Generic Foreign Key для поддержки разных типов брендов/моделей
    # Марка (CarBrand, TruckBrand, MotoBrand, SpecialBrand)
    brand_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        related_name='garage_brand_vehicles',
        null=True,
        blank=True,
        limit_choices_to={
            'model__in': ['carbrand', 'truckbrand', 'motobrand', 'specialbrand']
        }
    )
    brand_object_id = models.PositiveIntegerField(null=True, blank=True)
    brand = GenericForeignKey('brand_content_type', 'brand_object_id')
    
    # Модель (CarModel, TruckModel, MotoModel, SpecialModel)
    model_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        related_name='garage_model_vehicles',
        null=True,
        blank=True,
        limit_choices_to={
            'model__in': ['carmodel', 'truckmodel', 'motomodel', 'specialmodel']
        }
    )
    model_object_id = models.PositiveIntegerField(null=True, blank=True)
    vehicle_model = GenericForeignKey('model_content_type', 'model_object_id')
    
    # Поколение (CarGeneration, TruckGeneration, MotoGeneration, SpecialGeneration)
    generation_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        related_name='garage_generation_vehicles',
        null=True,
        blank=True,
        limit_choices_to={
            'model__in': ['cargeneration', 'truckgeneration', 'motogeneration', 'specialgeneration']
        }
    )
    generation_object_id = models.PositiveIntegerField(null=True, blank=True)
    generation = GenericForeignKey('generation_content_type', 'generation_object_id')
    
    # Модификация (CarModification, TruckModification, MotoModification, SpecialModification)
    modification_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        related_name='garage_modification_vehicles',
        null=True,
        blank=True,
        limit_choices_to={
            'model__in': ['carmodification', 'truckmodification', 'motomodification', 'specialmodification']
        }
    )
    modification_object_id = models.PositiveIntegerField(null=True, blank=True)
    modification = GenericForeignKey('modification_content_type', 'modification_object_id')
    
    # VIN и госномер
    vin = models.CharField(
        'VIN номер',
        max_length=17,
        blank=True,
        null=True,
        help_text='17-значный VIN номер'
    )
    
    license_plate = models.CharField(
        'Госномер',
        max_length=20,
        blank=True,
        null=True
    )
    
    # Год выпуска
    year = models.IntegerField(
        'Год выпуска',
        null=True,
        blank=True
    )
    
    # Пользовательское фото
    custom_image = models.ImageField(
        'Пользовательское фото',
        upload_to='garage/vehicles/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Активность
    is_active = models.BooleanField(
        'Активен',
        default=True,
        help_text='Отметьте, если транспорт используется'
    )
    
    # Метаданные
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Пользовательское транспортное средство'
        verbose_name_plural = 'Пользовательские транспортные средства'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['vin']),
            models.Index(fields=['license_plate']),
        ]
    
    def __str__(self):
        return f"{self.get_display_name()} ({self.user.username})"
    
    def clean(self):
        """Валидация VIN номера"""
        if self.vin:
            from .services import VINService

            vin_validation = VINService.validate_vin(self.vin)
            self.vin = vin_validation.get('normalized_vin') or VINService.normalize_vin(self.vin)
            if not vin_validation['valid']:
                raise ValidationError({'vin': vin_validation['error']})

            if self.user_id and self.is_active:
                duplicate_qs = self.__class__.objects.filter(
                    user_id=self.user_id,
                    vin=self.vin,
                    is_active=True,
                )
                if self.pk:
                    duplicate_qs = duplicate_qs.exclude(pk=self.pk)
                if duplicate_qs.exists():
                    raise ValidationError({
                        'vin': 'Автомобиль с таким VIN уже есть в гараже пользователя'
                    })

            # Убираем пробелы и приводим к верхнему регистру
            self.vin = self.vin.replace(' ', '').upper()
            
            # Проверяем длину VIN
            if len(self.vin) != 17:
                raise ValidationError({
                    'vin': 'VIN номер должен содержать ровно 17 символов'
                })
            
            # Проверяем допустимые символы (нет I, O, Q)
            forbidden_chars = set('IOQ')
            if any(char in forbidden_chars for char in self.vin):
                raise ValidationError({
                    'vin': 'VIN номер не должен содержать символы I, O, Q'
                })
    
    def get_display_name(self):
        """Возвращает отображаемое название"""
        parts = []
        if self.brand:
            parts.append(str(self.brand))
        if self.vehicle_model:
            parts.append(str(self.vehicle_model))
        if self.generation:
            parts.append(str(self.generation))
        if self.year:
            parts.append(str(self.year))
        
        if parts:
            return ' '.join(parts)
        if self.vin:
            return f'VIN {self.vin}'
        if self.license_plate:
            return self.license_plate
        return 'Транспорт'
    
    def get_vehicle_type(self):
        """Определяет тип транспорта"""
        if self.brand_content_type:
            model_name = self.brand_content_type.model
            if 'car' in model_name:
                return 'cars'
            elif 'truck' in model_name:
                return 'trucks'
            elif 'moto' in model_name:
                return 'moto'
            elif 'special' in model_name:
                return 'special'
        return 'cars'
    
    def get_image_url(self):
        """Возвращает URL изображения"""
        if self.custom_image:
            return self.custom_image.url
        return None
    
    def save(self, *args, **kwargs):
        if self.vin:
            from .services import VINService
            self.vin = VINService.normalize_vin(self.vin)

        self.full_clean()
        super().save(*args, **kwargs)


class VehicleNote(models.Model):
    """Заметки к транспортному средству"""
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Транспортное средство'
    )
    title = models.CharField('Заголовок', max_length=200)
    content = models.TextField('Содержание')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Заметка'
        verbose_name_plural = 'Заметки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.vehicle.get_display_name()}"
