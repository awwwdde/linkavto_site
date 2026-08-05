from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Seller, Category


class EmailVerificationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'required': 'required'
        })
    )


class SellerRegistrationForm(forms.ModelForm):

    class Meta:
        model = Seller
        fields = [
            'contact_person', 'phone', 'company_name', 'store_name', 'legal_form',
            'inn', 'ogrn', 'legal_address', 'actual_address', 'shipping_address', 'product_info'
        ]
        widgets = {
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Иванов Иван Иванович'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 999-99-99'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ООО "Ваша компания"'
            }),
            'store_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Как будет отображаться магазин покупателям'
            }),
            'legal_form': forms.Select(attrs={'class': 'form-select'}),
            'inn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10 или 12 цифр'
            }),
            'ogrn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '13 или 15 цифр'
            }),
            'legal_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Полный юридический адрес'
            }),
            'actual_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Фактический адрес (если отличается)'
            }),
            'shipping_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Адрес склада или точки отправки заказов'
            }),
            'product_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о вашем ассортименте, условиях поставки, наличии склада...'
            }),
        }

    def clean_inn(self):
        inn = self.cleaned_data['inn']
        if not re.match(r'^\d{10}$|^\d{12}$', inn):
            raise ValidationError('ИНН должен содержать 10 или 12 цифр')
        return inn

    def clean_ogrn(self):
        ogrn = self.cleaned_data['ogrn']
        if not re.match(r'^\d{13}$|^\d{15}$', ogrn):
            raise ValidationError('ОГРН должен содержать 13 цифр, ОГРНИП - 15 цифр')
        return ogrn


class CategoriesForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': 'Пожалуйста, выберите хотя бы одну категорию товаров'}
    )
    product_count = forms.ChoiceField(
        choices=[
            ('', 'Выберите количество...'),
            ('1-50', '1-50 товаров'),
            ('51-200', '51-200 товаров'),
            ('201-500', '201-500 товаров'),
            ('501-1000', '501-1000 товаров'),
            ('1000+', 'Более 1000 товаров'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )