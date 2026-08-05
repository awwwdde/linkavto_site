from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxLengthValidator
from .models import Vehicle
from .services import VINService


class VehicleAdminForm(forms.ModelForm):
    """Кастомная форма для удобного выбора марки, модели, поколения и модификации"""
    
    # Выпадающие списки вместо ContentType + ID
    vehicle_type = forms.ChoiceField(
        label='Тип транспорта',
        choices=[
            ('', '---------'),
            ('cars', 'Легковые автомобили'),
            ('trucks', 'Грузовые автомобили'),
            ('moto', 'Мототехника'),
            ('special', 'Спецтехника'),
        ],
        required=False,
        help_text='Сначала выберите тип транспорта'
    )
    
    brand_choice = forms.ChoiceField(
        label='Марка',
        choices=[('', '---------')],
        required=False
    )
    
    model_choice = forms.ChoiceField(
        label='Модель',
        choices=[('', '---------')],
        required=False
    )
    
    generation_choice = forms.ChoiceField(
        label='Поколение',
        choices=[('', '---------')],
        required=False
    )
    
    modification_choice = forms.ChoiceField(
        label='Модификация',
        choices=[('', '---------')],
        required=False
    )
    
    class Meta:
        model = Vehicle
        exclude = ('name',)
        widgets = {
            'brand_content_type': forms.HiddenInput(),
            'brand_object_id': forms.HiddenInput(),
            'model_content_type': forms.HiddenInput(),
            'model_object_id': forms.HiddenInput(),
            'generation_content_type': forms.HiddenInput(),
            'generation_object_id': forms.HiddenInput(),
            'modification_content_type': forms.HiddenInput(),
            'modification_object_id': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'vin' in self.fields:
            self.fields['vin'].max_length = 32
            self.fields['vin'].validators = [
                validator for validator in self.fields['vin'].validators
                if not isinstance(validator, MaxLengthValidator)
            ]
            self.fields['vin'].widget.attrs.update({
                'maxlength': 32,
                'autocomplete': 'off',
                'spellcheck': 'false',
            })
        
        # Если редактируем существующий объект
        if self.instance.pk:
            # Определяем тип транспорта
            vehicle_type = self.instance.get_vehicle_type()
            self.fields['vehicle_type'].initial = vehicle_type
            
            # Загружаем марки для выбранного типа
            self._load_brands(vehicle_type)
            
            # Если марка выбрана, загружаем модели
            if self.instance.brand:
                self.fields['brand_choice'].initial = self.instance.brand_object_id
                self._load_models(vehicle_type, self.instance.brand_object_id)
                
                # Если модель выбрана, загружаем поколения
                if self.instance.vehicle_model:
                    self.fields['model_choice'].initial = self.instance.model_object_id
                    self._load_generations(vehicle_type, self.instance.model_object_id)
                    
                    # Если поколение выбрано, загружаем модификации
                    if self.instance.generation:
                        self.fields['generation_choice'].initial = self.instance.generation_object_id
                        self._load_modifications(vehicle_type, self.instance.generation_object_id)
                        
                        if self.instance.modification:
                            self.fields['modification_choice'].initial = self.instance.modification_object_id
        # Повторное отображение формы после ошибки сохранения — восстанавливаем варианты из POST
        elif self.data.get('vehicle_type'):
            vehicle_type = self.data.get('vehicle_type')
            self._load_brands(vehicle_type)
            brand_id = self.data.get('brand_choice')
            if brand_id:
                self._load_models(vehicle_type, brand_id)
                model_id = self.data.get('model_choice')
                if model_id:
                    self._load_generations(vehicle_type, model_id)
                    gen_id = self.data.get('generation_choice')
                    if gen_id:
                        self._load_modifications(vehicle_type, gen_id)

    def clean_vin(self):
        vin = self.cleaned_data.get('vin')
        if not vin:
            return None

        vin_validation = VINService.validate_vin(vin)
        if not vin_validation['valid']:
            raise forms.ValidationError(vin_validation['error'])

        return vin_validation['normalized_vin']
    
    def _load_brands(self, vehicle_type):
        """Загружает марки для выбранного типа транспорта"""
        if not vehicle_type:
            return
        
        from shop import models as shop_models
        
        model_map = {
            'cars': 'CarBrand',
            'trucks': 'TruckBrand',
            'moto': 'MotoBrand',
            'special': 'SpecialBrand',
        }
        
        model_name = model_map.get(vehicle_type)
        if model_name:
            ModelClass = getattr(shop_models, model_name)
            brands = ModelClass.objects.all().order_by('name')
            self.fields['brand_choice'].choices = [('', '---------')] + [
                (brand.id, brand.name) for brand in brands
            ]
    
    def _load_models(self, vehicle_type, brand_id):
        """Загружает модели для выбранной марки"""
        if not vehicle_type or not brand_id:
            return
        
        from shop import models as shop_models
        
        model_map = {
            'cars': 'CarModel',
            'trucks': 'TruckModel',
            'moto': 'MotoModel',
            'special': 'SpecialModel',
        }
        
        model_name = model_map.get(vehicle_type)
        if model_name:
            ModelClass = getattr(shop_models, model_name)
            models = ModelClass.objects.filter(brand_id=brand_id).order_by('name')
            self.fields['model_choice'].choices = [('', '---------')] + [
                (model.id, model.name) for model in models
            ]
    
    def _load_generations(self, vehicle_type, model_id):
        """Загружает поколения для выбранной модели"""
        if not vehicle_type or not model_id:
            return
        
        from shop import models as shop_models
        
        model_map = {
            'cars': 'CarGeneration',
            'trucks': 'TruckGeneration',
            'moto': 'MotoGeneration',
            'special': 'SpecialGeneration',
        }
        
        model_name = model_map.get(vehicle_type)
        if model_name:
            ModelClass = getattr(shop_models, model_name)
            generations = ModelClass.objects.filter(model_id=model_id).order_by('-year_start')
            self.fields['generation_choice'].choices = [('', '---------')] + [
                (gen.id, f"{gen.name} ({gen.year_start}-{gen.year_end or 'н.в.'})") for gen in generations
            ]
    
    def _load_modifications(self, vehicle_type, generation_id):
        """Загружает модификации для выбранного поколения"""
        if not vehicle_type or not generation_id:
            return
        
        from shop import models as shop_models
        
        model_map = {
            'cars': 'CarModification',
            'trucks': 'TruckModification',
            'moto': 'MotoModification',
            'special': 'SpecialModification',
        }
        
        model_name = model_map.get(vehicle_type)
        if model_name:
            ModelClass = getattr(shop_models, model_name)
            modifications = ModelClass.objects.filter(generation_id=generation_id).order_by('name')
            self.fields['modification_choice'].choices = [('', '---------')] + [
                (mod.id, mod.name) for mod in modifications
            ]
    
    def save(self, commit=True):
        """Сохраняем объект с правильными ContentType и ID"""
        instance = super().save(commit=False)
        
        vehicle_type = self.cleaned_data.get('vehicle_type')
        
        # Устанавливаем марку
        brand_id = self.cleaned_data.get('brand_choice')
        if brand_id:
            ct_map = {
                'cars': 'carbrand',
                'trucks': 'truckbrand',
                'moto': 'motobrand',
                'special': 'specialbrand',
            }
            ct_model = ct_map.get(vehicle_type)
            if ct_model:
                instance.brand_content_type = ContentType.objects.get(app_label='shop', model=ct_model)
                instance.brand_object_id = int(brand_id)
        
        # Устанавливаем модель
        model_id = self.cleaned_data.get('model_choice')
        if model_id:
            ct_map = {
                'cars': 'carmodel',
                'trucks': 'truckmodel',
                'moto': 'motomodel',
                'special': 'specialmodel',
            }
            ct_model = ct_map.get(vehicle_type)
            if ct_model:
                instance.model_content_type = ContentType.objects.get(app_label='shop', model=ct_model)
                instance.model_object_id = int(model_id)
        
        # Устанавливаем поколение
        generation_id = self.cleaned_data.get('generation_choice')
        if generation_id:
            ct_map = {
                'cars': 'cargeneration',
                'trucks': 'truckgeneration',
                'moto': 'motogeneration',
                'special': 'specialgeneration',
            }
            ct_model = ct_map.get(vehicle_type)
            if ct_model:
                instance.generation_content_type = ContentType.objects.get(app_label='shop', model=ct_model)
                instance.generation_object_id = int(generation_id)
        
        # Устанавливаем модификацию
        modification_id = self.cleaned_data.get('modification_choice')
        if modification_id:
            ct_map = {
                'cars': 'carmodification',
                'trucks': 'truckmodification',
                'moto': 'motomodification',
                'special': 'specialmodification',
            }
            ct_model = ct_map.get(vehicle_type)
            if ct_model:
                instance.modification_content_type = ContentType.objects.get(app_label='shop', model=ct_model)
                instance.modification_object_id = int(modification_id)
        
        if commit:
            instance.save()
        
        return instance
