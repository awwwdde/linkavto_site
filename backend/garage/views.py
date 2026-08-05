from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from .models import Vehicle, VehicleNote
from .services import VINService, LicensePlateService
import json
import logging

logger = logging.getLogger(__name__)


def get_brand_model_class(vehicle_type):
    """Возвращает класс модели марки по типу транспорта"""
    type_map = {
        'cars': 'shop.CarBrand',
        'trucks': 'shop.TruckBrand',
        'moto': 'shop.MotoBrand',
        'special': 'shop.SpecialBrand',
    }
    model_path = type_map.get(vehicle_type)
    if model_path:
        app_label, model_name = model_path.split('.')
        return ContentType.objects.get(app_label=app_label.lower(), model=model_name.lower())
    return None


@login_required
def garage_list(request):
    """Список пользовательских транспортных средств"""
    vehicles = Vehicle.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-created_at')
    
    vehicles_count = vehicles.count()
    
    # Пагинация
    paginator = Paginator(vehicles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'vehicles': page_obj,
        'vehicles_count': vehicles_count,
        'page_obj': page_obj,
    }
    
    return render(request, 'garage/list.html', context)


@login_required
def vehicle_detail(request, vehicle_id):
    """Детальная информация о транспортном средстве"""
    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id,
        user=request.user,
        is_active=True
    )
    
    context = {
        'vehicle': vehicle,
    }
    
    return render(request, 'garage/detail.html', context)


@login_required
def vehicle_add(request):
    """Добавление нового транспортного средства"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.headers.get('Content-Type') == 'application/json' else request.POST

            vin = VINService.normalize_vin(data.get('vin', ''))
            license_plate = data.get('license_plate', '').strip()
            
            # Валидация VIN если указан
            if vin:
                vin_validation = VINService.validate_vin(vin)
                if not vin_validation['valid']:
                    return JsonResponse({'success': False, 'error': vin_validation['error']}, status=400)

                if Vehicle.objects.filter(user=request.user, vin=vin, is_active=True).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Автомобиль с таким VIN уже есть в вашем гараже'
                    }, status=400)
            
            # Валидация госномера если указан
            if license_plate:
                plate_validation = LicensePlateService.validate_license_plate(license_plate)
                if not plate_validation['valid']:
                    return JsonResponse({'success': False, 'error': plate_validation['error']}, status=400)
            
            from shop import models as shop_models

            brand_id = data.get('brand_id')
            vehicle_type = data.get('vehicle_type', data.get('brand_type', 'cars'))
            type_prefix = {'cars': 'car', 'trucks': 'truck', 'moto': 'moto', 'special': 'special'}.get(vehicle_type, 'car')
            type_brand_map = {
                'cars': 'CarBrand', 'trucks': 'TruckBrand', 'moto': 'MotoBrand', 'special': 'SpecialBrand',
            }
            type_model_map = {
                'cars': 'CarModel', 'trucks': 'TruckModel', 'moto': 'MotoModel', 'special': 'SpecialModel',
            }
            type_gen_map = {
                'cars': 'CarGeneration', 'trucks': 'TruckGeneration', 'moto': 'MotoGeneration', 'special': 'SpecialGeneration',
            }
            type_mod_map = {
                'cars': 'CarModification', 'trucks': 'TruckModification', 'moto': 'MotoModification', 'special': 'SpecialModification',
            }

            model_id = data.get('model_id')
            generation_id = data.get('generation_id')
            modification_id = data.get('modification_id')

            brand_obj = None
            model_obj = None
            generation_obj = None

            if brand_id:
                BrandClass = getattr(shop_models, type_brand_map.get(vehicle_type, 'CarBrand'), None)
                if BrandClass:
                    try:
                        brand_obj = BrandClass.objects.get(pk=int(brand_id))
                    except BrandClass.DoesNotExist:
                        pass

            if model_id:
                ModelClass = getattr(shop_models, type_model_map.get(vehicle_type, 'CarModel'), None)
                if ModelClass:
                    try:
                        model_obj = ModelClass.objects.get(pk=int(model_id))
                    except ModelClass.DoesNotExist:
                        pass

            if generation_id:
                GenClass = getattr(shop_models, type_gen_map.get(vehicle_type, 'CarGeneration'), None)
                if GenClass:
                    try:
                        generation_obj = GenClass.objects.get(pk=int(generation_id))
                    except GenClass.DoesNotExist:
                        pass

            # Создаем транспортное средство
            year = int(data.get('year')) if data.get('year') else None
            if vin and not year:
                decoded_vin = VINService.decode_vin(vin)
                year = decoded_vin.get('year') if decoded_vin.get('success') else None

            vehicle_data = {
                'user': request.user,
                'vin': vin if vin else None,
                'license_plate': license_plate if license_plate else None,
                'year': year,
                'is_active': data.get('is_active', True),
            }

            if brand_obj:
                brand_ct = get_brand_model_class(vehicle_type)
                if brand_ct:
                    vehicle_data['brand_content_type'] = brand_ct
                    vehicle_data['brand_object_id'] = int(brand_id)

            if model_obj:
                vehicle_data['model_content_type'] = ContentType.objects.get(app_label='shop', model=f'{type_prefix}model')
                vehicle_data['model_object_id'] = int(model_id)

            if generation_obj:
                vehicle_data['generation_content_type'] = ContentType.objects.get(app_label='shop', model=f'{type_prefix}generation')
                vehicle_data['generation_object_id'] = int(generation_id)

            if modification_id:
                ModClass = getattr(shop_models, type_mod_map.get(vehicle_type, 'CarModification'), None)
                if ModClass:
                    try:
                        ModClass.objects.get(pk=int(modification_id))
                        vehicle_data['modification_content_type'] = ContentType.objects.get(app_label='shop', model=f'{type_prefix}modification')
                        vehicle_data['modification_object_id'] = int(modification_id)
                    except ModClass.DoesNotExist:
                        pass

            vehicle = Vehicle.objects.create(**vehicle_data)
            
            # Обработка изображения
            if 'custom_image' in request.FILES:
                vehicle.custom_image = request.FILES['custom_image']
                vehicle.save()
            
            return JsonResponse({
                'success': True,
                'vehicle_id': vehicle.id,
                'vin': vehicle.vin,
                'year': vehicle.year,
                'message': 'Транспортное средство успешно добавлено'
            })
            
        except Exception as e:
            logger.error(f"Error adding vehicle: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return render(request, 'garage/add.html')


@login_required
@require_POST
def vehicle_edit(request, vehicle_id):
    """Редактирование транспортного средства"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    
    try:
        data = json.loads(request.body) if request.headers.get('Content-Type') == 'application/json' else request.POST
        
        if 'vin' in data:
            vin = VINService.normalize_vin(data['vin'])
            if vin:
                vin_validation = VINService.validate_vin(vin)
                if not vin_validation['valid']:
                    return JsonResponse({'success': False, 'error': vin_validation['error']}, status=400)

                if Vehicle.objects.filter(
                    user=request.user,
                    vin=vin,
                    is_active=True
                ).exclude(pk=vehicle.pk).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Автомобиль с таким VIN уже есть в вашем гараже'
                    }, status=400)
            vehicle.vin = vin if vin else None
        
        if 'license_plate' in data:
            plate = data['license_plate'].strip()
            if plate:
                plate_validation = LicensePlateService.validate_license_plate(plate)
                if not plate_validation['valid']:
                    return JsonResponse({'success': False, 'error': plate_validation['error']}, status=400)
            vehicle.license_plate = plate if plate else None
        
        if 'year' in data:
            vehicle.year = int(data['year']) if data['year'] else None
            if vehicle.vin and not vehicle.year:
                decoded_vin = VINService.decode_vin(vehicle.vin)
                vehicle.year = decoded_vin.get('year') if decoded_vin.get('success') else None
        
        if 'is_active' in data:
            vehicle.is_active = bool(data['is_active'])
        
        if 'custom_image' in request.FILES:
            vehicle.custom_image = request.FILES['custom_image']

        if vehicle.vin and not vehicle.year:
            decoded_vin = VINService.decode_vin(vehicle.vin)
            vehicle.year = decoded_vin.get('year') if decoded_vin.get('success') else None
        
        vehicle.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Транспортное средство успешно обновлено'
        })
        
    except Exception as e:
        logger.error(f"Error editing vehicle: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def vehicle_delete(request, vehicle_id):
    """Удаление транспортного средства"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    
    try:
        vehicle.is_active = False
        vehicle.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Транспортное средство успешно удалено'
        })
        
    except Exception as e:
        logger.error(f"Error deleting vehicle: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def vehicle_update_image(request, vehicle_id):
    """Обновление изображения транспортного средства"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    
    try:
        if 'custom_image' in request.FILES:
            vehicle.custom_image = request.FILES['custom_image']
            vehicle.save()
            
            return JsonResponse({
                'success': True,
                'image_url': vehicle.get_image_url(),
                'message': 'Изображение успешно обновлено'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Файл не найден'}, status=400)
            
    except Exception as e:
        logger.error(f"Error updating vehicle image: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# API endpoints остаются как в предыдущей версии
@require_GET
def get_brands(request):
    """API для получения списка марок"""
    vehicle_type = request.GET.get('type', 'cars')
    
    type_models = {
        'cars': 'shop.CarBrand',
        'trucks': 'shop.TruckBrand',
        'moto': 'shop.MotoBrand',
        'special': 'shop.SpecialBrand',
    }
    
    model_path = type_models.get(vehicle_type)
    if not model_path:
        return JsonResponse({'success': False, 'error': 'Invalid type'}, status=400)
    
    app_label, model_name = model_path.split('.')
    
    from shop import models as shop_models
    ModelClass = getattr(shop_models, model_name)
    
    brands = ModelClass.objects.all().order_by('name')

    data = [
        {
            'id': brand.id,
            'name': brand.name,
            'slug': brand.slug,
            'logo_url': brand.logo.url if brand.logo else None,
        }
        for brand in brands
    ]

    return JsonResponse({'success': True, 'brands': data})


@require_GET  
def get_models(request):
    """API для получения списка моделей"""
    brand_id = request.GET.get('brand_id')
    vehicle_type = request.GET.get('type', 'cars')
    
    if not brand_id:
        return JsonResponse({'success': False, 'error': 'brand_id is required'}, status=400)
    
    type_models = {
        'cars': 'CarModel',
        'trucks': 'TruckModel',
        'moto': 'MotoModel',
        'special': 'SpecialModel',
    }
    
    model_name = type_models.get(vehicle_type)
    if not model_name:
        return JsonResponse({'success': False, 'error': 'Invalid type'}, status=400)
    
    from shop import models as shop_models
    ModelClass = getattr(shop_models, model_name)
    
    models_list = ModelClass.objects.filter(brand_id=brand_id).order_by('name')
    
    data = [
        {
            'id': model.id,
            'name': model.name,
            'slug': model.slug
        }
        for model in models_list
    ]
    
    return JsonResponse({'success': True, 'models': data})


@require_GET
def get_generations(request):
    """API для получения списка поколений"""
    model_id = request.GET.get('model_id')
    vehicle_type = request.GET.get('type', 'cars')
    
    if not model_id:
        return JsonResponse({'success': False, 'error': 'model_id is required'}, status=400)
    
    type_models = {
        'cars': 'CarGeneration',
        'trucks': 'TruckGeneration',
        'moto': 'MotoGeneration',
        'special': 'SpecialGeneration',
    }
    
    model_name = type_models.get(vehicle_type)
    if not model_name:
        return JsonResponse({'success': False, 'error': 'Invalid type'}, status=400)
    
    from shop import models as shop_models
    ModelClass = getattr(shop_models, model_name)
    
    generations = ModelClass.objects.filter(model_id=model_id).order_by('-year_start')
    
    data = [
        {
            'id': gen.id,
            'name': gen.name,
            'year_start': getattr(gen, 'year_start', None),
            'year_end': getattr(gen, 'year_end', None),
            'image_url': gen.image.url if getattr(gen, 'image', None) else None,
        }
        for gen in generations
    ]

    return JsonResponse({'success': True, 'generations': data})


@require_GET
def get_modifications(request):
    """API для получения списка модификаций"""
    generation_id = request.GET.get('generation_id')
    vehicle_type = request.GET.get('type', 'cars')
    
    if not generation_id:
        return JsonResponse({'success': False, 'error': 'generation_id is required'}, status=400)
    
    type_models = {
        'cars': 'CarModification',
        'trucks': 'TruckModification',
        'moto': 'MotoModification',
        'special': 'SpecialModification',
    }
    
    model_name = type_models.get(vehicle_type)
    if not model_name:
        return JsonResponse({'success': False, 'error': 'Invalid type'}, status=400)
    
    from shop import models as shop_models
    ModelClass = getattr(shop_models, model_name)
    
    modifications = ModelClass.objects.filter(generation_id=generation_id).order_by('name')
    
    data = [
        {
            'id': mod.id,
            'name': mod.name
        }
        for mod in modifications
    ]
    
    return JsonResponse({'success': True, 'modifications': data})


@login_required
@require_GET
def vehicle_products(request, vehicle_id):
    """Получение товаров для транспортного средства"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user, is_active=True)
    
    vehicle_type = vehicle.get_vehicle_type()
    
    # Slug корневых категорий в shop (как в shop/templates/shop/category.html и footer)
    category_map = {
        'cars': 'legkovye-avtomobili',
        'trucks': 'gruzovye-avtomobili',
        'moto': 'mototehnika',
        'special': 'spectehnika',
    }
    
    category_slug = category_map.get(vehicle_type, 'legkovye-avtomobili')
    
    params = []
    
    if vehicle.brand:
        params.append(f'brand={vehicle.brand.slug}')
    if vehicle.vehicle_model:
        params.append(f'model={vehicle.vehicle_model.slug}')
    if vehicle.generation:
        params.append(f'generation={vehicle.generation.slug}')
    if vehicle.modification:
        params.append(f'modification={vehicle.modification.slug}')
    if vehicle.year:
        params.append(f'year={vehicle.year}')
    
    params.append(f'vehicle_id={vehicle.id}')
    
    url = f'/category/{category_slug}/'
    if params:
        url += '?' + '&'.join(params)
    
    return redirect(url)
