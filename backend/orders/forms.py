from django import forms
from django.core.validators import RegexValidator
from .models import Order


class OrderCreateForm(forms.ModelForm):
    # Кастомные поля с дополнительной валидацией
    phone = forms.CharField(
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 123-45-67'
        })
    )

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru'
        })
    )

    class Meta:
        model = Order
        fields = ['name', 'email', 'phone', 'address', 'comment', 'delivery_type']
        labels = {
            'name': 'ФИО',
            'address': 'Адрес доставки',
            'comment': 'Комментарий',
            'delivery_type': 'Способ доставки'
        }
        help_texts = {
            'phone': 'Номер в международном формате',
            'email': 'Для отправки информации о заказе'
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Иванов Иван Иванович'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Город, улица, дом, квартира'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Особенности доставки'
            }),
        }

    def clean_phone(self):
        """Очистка и валидация номера телефона"""
        phone = self.cleaned_data['phone']
        
        # Очищаем от форматирования: убираем пробелы, скобки, дефисы, плюсы
        cleaned_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
        
        # Логируем для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Phone validation - Original: '{phone}', Cleaned: '{cleaned_phone}'")
        
        # Проверяем формат после очистки
        import re
        # Принимаем номера начинающиеся с 7 или 8, длиной 11 цифр
        if not re.match(r'^[78]\d{10}$', cleaned_phone):
            logger.error(f"Phone validation failed for: '{cleaned_phone}'")
            raise forms.ValidationError("Введите корректный номер телефона")
        
        # Нормализуем к формату +7XXXXXXXXXX
        if cleaned_phone.startswith('8'):
            cleaned_phone = '7' + cleaned_phone[1:]
        
        normalized_phone = '+' + cleaned_phone
        logger.info(f"Phone validation successful: '{normalized_phone}'")
        return normalized_phone

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields['email'].initial = user.email
            self.fields['name'].initial = user.get_full_name()
        
        # Загружаем сохраненный телефон из сессии
        if request and hasattr(request, 'session'):
            saved_phone = request.session.get('last_phone', '')
            if saved_phone:
                self.fields['phone'].initial = saved_phone