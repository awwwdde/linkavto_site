from django.contrib.auth import logout, update_session_auth_hash
from django.core.exceptions import ObjectDoesNotExist
from .models import Profile, PasswordResetCode
from .forms import ProfileForm, PasswordChangeForm
from orders.models import Order
from django.contrib.auth import authenticate, login
from django.core.cache import cache
from django.template.loader import render_to_string
from django.contrib.auth import login
from django.http import JsonResponse
from .models import Address
import json
from django.views.decorators.http import require_POST, require_GET
import os
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from shop.models import Review
from favorites.models import Favorite
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import VerificationCode, User, Profile
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import login as auth_login
import logging
from .sms_service import send_sms
from django.utils.crypto import get_random_string


@login_required
def dashboard(request):
    try:
        last_order = Order.objects.filter(user=request.user).order_by('-created').first()
    except Exception as e:
        last_order = None

    # Получаем все счетчики
    reviews_count = Review.objects.filter(user=request.user).count()
    favorites_count = Favorite.objects.filter(user=request.user).count()
    orders_count = Order.objects.filter(user=request.user).count()
    addresses_count = request.user.addresses.count()  # если у модели User есть related_name='addresses'

    # Для карт, если есть модель Card
    try:
        cards_count = request.user.cards.count()
    except AttributeError:
        cards_count = 0

    return render(request, 'accounts/dashboard.html', {
        'last_order': last_order,
        'reviews_count': reviews_count,
        'favorites_count': favorites_count,
        'orders_count': orders_count,
        'addresses_count': addresses_count,
        'cards_count': cards_count
    })


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Вы успешно вышли из системы.")
    next_url = request.POST.get('next', 'index')  # Получаем URL для перенаправления
    return redirect(next_url)


@login_required
def profile_edit(request):
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

            # Обновляем email если он изменился
            new_email = request.POST.get('email')
            if new_email and new_email != request.user.email:
                request.user.email = new_email
                request.user.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, '')
            return redirect('accounts:dashboard')

        messages.error(request, 'Исправьте ошибки в форме.')

    else:
        form = ProfileForm(instance=profile)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('accounts/profile_form.html', {'form': form}, request=request)
        return JsonResponse({'html': html})

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён!')
            return redirect('accounts:dashboard')

        messages.error(request, 'Ошибка при смене пароля. Проверьте данные.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def order_history(request):
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created')
        return render(request, 'orders/history.html', {'orders': orders})
    except Exception as e:
        messages.error(request, f"Ошибка загрузки истории заказов: {str(e)}")
        return redirect('accounts:dashboard')


@login_required
def send_password_code(request):
    if request.method == 'POST':
        try:
            code = get_random_string(6, allowed_chars='0123456789')
            PasswordResetCode.objects.create(
                user=request.user,
                code=code,
                expires_at=timezone.now() + timezone.timedelta(minutes=15))

            send_mail(
                'Код подтверждения смены пароля',
                f'Ваш код: {code}',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False
            )
            return JsonResponse({'message': 'Код отправлен'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Неверный метод'}, status=405)


@login_required
def verify_password_code(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            reset_code = PasswordResetCode.objects.get(
                user=request.user,
                code=code,
                expires_at__gt=timezone.now(),
                is_used=False
            )
            reset_code.is_used = True
            reset_code.save()
            request.session['password_code_verified'] = True
            return redirect('accounts:set_new_password')

        except PasswordResetCode.DoesNotExist:
            messages.error(request, 'Неверный или просроченный код.')

    return redirect('accounts:dashboard')


@login_required
def set_new_password(request):
    if not request.session.get('password_code_verified'):
        messages.error(request, 'Сначала подтвердите код.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'Пароли не совпадают.')
            return redirect('accounts:set_new_password')

        if len(new_password) < 8:
            messages.error(request, 'Пароль должен содержать минимум 8 символов.')
            return redirect('accounts:set_new_password')

        user = request.user
        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)
        request.session.pop('password_code_verified', None)
        messages.success(request, 'Пароль успешно изменен.')
        return redirect('accounts:dashboard')

    return render(request, 'accounts/set_new_password.html')


def create_addresses_from_session(request):
    """Создание всех адресов из сессии после авторизации"""
    pending_addresses = request.session.get('pending_addresses', [])
    
    # Обратная совместимость: проверяем старый формат pending_address
    if not pending_addresses and 'pending_address' in request.session:
        pending_addresses = [request.session['pending_address']]
    
    if not pending_addresses:
        return []
    
    created_addresses = []
    has_existing_addresses = request.user.addresses.exists()
    
    try:
        for i, address_data in enumerate(pending_addresses):
            # Проверяем, нет ли уже такого адреса у пользователя
            existing = request.user.addresses.filter(
                full_address=address_data.get('address'),
                delivery_type=address_data.get('delivery_type', 'delivery')
            )
            if address_data.get('pickup_point_code'):
                existing = existing.filter(pickup_point_code=address_data.get('pickup_point_code'))
            
            if existing.exists():
                logger.info(f"Address already exists for user {request.user.id}, skipping")
                continue
            
            # Создаем адрес
            address = Address.objects.create(
                user=request.user,
                full_address=address_data.get('address'),
                postal_code=address_data.get('postal_code', ''),
                delivery_type=address_data.get('delivery_type', 'delivery'),
                pickup_provider=address_data.get('pickup_provider'),
                pickup_point_code=address_data.get('pickup_point_code'),
                pickup_point_name=address_data.get('pickup_point_name'),
                latitude=address_data.get('latitude'),
                longitude=address_data.get('longitude'),
                # Первый адрес делаем дефолтным, если у пользователя нет адресов
                is_default=(not has_existing_addresses and i == 0 and len(created_addresses) == 0)
            )
            created_addresses.append(address)
            logger.info(f"Address created from session for user {request.user.id}: {address.id}")
        
        # Очищаем сессию
        if 'pending_addresses' in request.session:
            del request.session['pending_addresses']
        if 'pending_address' in request.session:
            del request.session['pending_address']
        request.session.modified = True
        
        return created_addresses
    except Exception as e:
        logger.error(f"Error creating addresses from session: {e}", exc_info=True)
        return created_addresses


# Обратная совместимость
def create_address_from_session(request):
    """Создание адресов из сессии после авторизации (обратная совместимость)"""
    addresses = create_addresses_from_session(request)
    return addresses[0] if addresses else None


@require_POST
def authenticate_user(request):
    login_input = request.POST.get('login')
    password = request.POST.get('password')
    next_url = request.POST.get('next', 'index')  # Получаем URL для перенаправления

    # Пытаемся аутентифицировать по email или телефону
    user = None

    # Проверяем, является ли ввод email
    if '@' in login_input:
        try:
            user = User.objects.get(email=login_input)
        except User.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Неверные учетные данные'}, status=400)
            messages.error(request, 'Неверные учетные данные')
            return redirect('shop:index')
    else:
        # Проверяем как телефон
        try:
            profile = Profile.objects.get(phone=login_input)
            user = profile.user
        except Profile.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Неверные учетные данные'}, status=400)
            messages.error(request, 'Неверные учетные данные')
            return redirect('shop:index')

    if user is not None:
        user = authenticate(username=user.username, password=password)
        if user is not None:
            login(request, user)
            # Проверяем, есть ли адреса в сессии, и создаем их
            addresses = create_addresses_from_session(request)
            address = addresses[0] if addresses else None
            if addresses:
                logger.info(f"{len(addresses)} address(es) created from session after login for user {user.id}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'redirect_url': next_url, 
                    'address_created': address is not None,
                    'address_id': address.id if address else None
                })
            messages.success(request, 'Вы успешно вошли в систему')
            return redirect(next_url)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Неверные учетные данные'}, status=400)
    messages.error(request, 'Неверные учетные данные')
    return redirect('shop:index')


@require_POST
def register_user(request):
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    password = request.POST.get('password')
    confirm_password = request.POST.get('confirm_password')  # Новое поле
    next_url = request.POST.get('next', 'index')

    try:
        # Проверка совпадения паролей
        if password != confirm_password:
            return JsonResponse({
                'success': False,
                'error': 'Пароли не совпадают'
            }, status=400)

        # Проверка сложности пароля (минимум 8 символов)
        if len(password) < 8:
            return JsonResponse({
                'success': False,
                'error': 'Пароль должен содержать минимум 8 символов'
            }, status=400)

        # Проверка существующих пользователей
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'Пользователь с таким email уже существует'
            }, status=400)

        if Profile.objects.filter(phone=phone).exists():
            return JsonResponse({
                'success': False,
                'error': 'Пользователь с таким телефоном уже существует'
            }, status=400)

        # Создание пользователя
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        Profile.objects.create(user=user, phone=phone)
        login(request, user)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': next_url
            })

        messages.success(request, 'Регистрация прошла успешно!')
        return redirect(next_url)

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

        messages.error(request, f'Ошибка регистрации: {str(e)}')
        return redirect('shop:index')


@require_POST
def password_reset_request(request):
    recovery_data = request.POST.get('recovery_data')

    try:
        user = None
        # Проверяем email
        if '@' in recovery_data:
            try:
                user = User.objects.get(email=recovery_data)
            except User.DoesNotExist:
                pass
        else:
            # Проверяем телефон
            try:
                profile = Profile.objects.get(phone=recovery_data)
                user = profile.user
            except Profile.DoesNotExist:
                pass

        if user:
            # Генерируем 6-значный код
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Сохраняем код в кэш на 15 минут
            cache_key = f'password_reset_{user.id}'
            cache.set(cache_key, {
                'code': code,
                'attempts': 3,
                'recovery_data': recovery_data
            }, 900)  # 15 минут

            # Отправляем код (email или SMS)
            if '@' in recovery_data:
                send_mail(
                    'Код подтверждения для сброса пароля',
                    f'Ваш код подтверждения: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            else:
                # Здесь должна быть логика отправки SMS
                # Например, через внешний API
                pass

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, 'Код подтверждения отправлен')
            return redirect('shop:index')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'}, status=400)

        messages.error(request, 'Пользователь с такими данными не найден')
        return redirect('shop:index')

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('shop:index')


@require_POST
def verify_reset_code(request):
    recovery_data = request.POST.get('recovery_data')
    code = request.POST.get('code')

    try:
        user = None
        if '@' in recovery_data:
            user = User.objects.get(email=recovery_data)
        else:
            profile = Profile.objects.get(phone=recovery_data)
            user = profile.user

        cache_key = f'password_reset_{user.id}'
        cached_data = cache.get(cache_key)

        if not cached_data or cached_data['code'] != code:
            # Уменьшаем количество попыток
            if cached_data:
                cached_data['attempts'] -= 1
                cache.set(cache_key, cached_data, cache.ttl(cache_key))

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Неверный код',
                    'attempts_left': cached_data['attempts'] if cached_data else 0
                }, status=400)

            messages.error(request, 'Неверный код подтверждения')
            return redirect('shop:index')

        # Помечаем код как использованный
        cached_data['verified'] = True
        cache.set(cache_key, cached_data, 600)  # 10 минут на смену пароля

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        messages.success(request, 'Код подтверждён')
        return redirect('accounts:password_reset_complete')

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('shop:index')


@require_POST
def password_reset_complete(request):
    recovery_data = request.POST.get('recovery_data')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')

    try:
        if new_password != confirm_password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Пароли не совпадают'}, status=400)

            messages.error(request, 'Пароли не совпадают')
            return redirect('shop:index')

        user = None
        if '@' in recovery_data:
            user = User.objects.get(email=recovery_data)
        else:
            profile = Profile.objects.get(phone=recovery_data)
            user = profile.user

        cache_key = f'password_reset_{user.id}'
        cached_data = cache.get(cache_key)

        if not cached_data or not cached_data.get('verified'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Необходимо подтверждение кода'}, status=400)

            messages.error(request, 'Необходимо подтверждение кода')
            return redirect('shop:index')

        # Устанавливаем новый пароль
        user.set_password(new_password)
        user.save()

        # Очищаем кэш
        cache.delete(cache_key)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        messages.success(request, 'Пароль успешно изменён')
        return redirect('accounts:login')

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('shop:index')


def get_addresses(request):
    """Возвращает HTML списка адресов (частичный шаблон)"""
    # Принудительно обновляем данные из БД
    addresses = request.user.addresses.all().order_by('-id')
    print(f"DEBUG: User {request.user.id} has {addresses.count()} addresses")

    # Добавляем флаг is_pickup для каждого адреса
    PICKUP_ADDRESS = 'Москва, Центральный административный округ, Тверской район, Кремль, 1'
    addresses_with_flags = []
    for addr in addresses:
        # Определяем, является ли адрес самовывозом
        is_pickup = (
                addr.delivery_type == 'pickup' or
                'Кремль, 1' in addr.full_address or
                PICKUP_ADDRESS in addr.full_address
        )
        # Создаем объект с дополнительным атрибутом
        addr.is_pickup_address = is_pickup
        # Если адрес самовывоза, но в БД delivery_type='delivery', обновляем для отображения
        if is_pickup and addr.delivery_type != 'pickup':
            addr.display_delivery_type = 'pickup'
        else:
            addr.display_delivery_type = addr.delivery_type or 'delivery'
        addresses_with_flags.append(addr)
        print(
            f"DEBUG: Address {addr.id}: {addr.full_address}, delivery_type: {addr.delivery_type}, is_pickup: {is_pickup}")

    response = render(request, 'accounts/modals/address_list_items.html', {
        'addresses': addresses_with_flags
    })

    # Добавляем заголовки для предотвращения кэширования
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


@login_required
def get_addresses_count(request):
    """Возвращает количество адресов пользователя"""
    count = request.user.addresses.count()
    return JsonResponse({'count': count})


@require_POST
@login_required
def save_address(request):
    """Сохранение нового адреса"""
    try:
        logger.info(f"Save address request from user {request.user.id}")
        
        # Проверяем, что это AJAX-запрос и данные в формате JSON
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logger.warning(f"Invalid request: missing X-Requested-With header")
            return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

        data = json.loads(request.body)
        logger.info(f"Received data: {data}")

        # Валидация обязательных полей
        if not data.get('address'):
            logger.warning(f"Address is missing in request data")
            return JsonResponse({'success': False, 'error': 'Address is required'}, status=400)

        # Создаем адрес с базовыми полями
        address_data = {
            'user': request.user,
            'full_address': data.get('address'),
            'postal_code': data.get('postal_code', ''),
            'delivery_type': data.get('delivery_type', 'delivery'),
            'comment': data.get('comment', ''),
            'is_default': not request.user.addresses.exists()
        }

        # Добавляем данные пункта выдачи если это самовывоз
        if data.get('delivery_type') == 'pickup':
            logger.info(f"Pickup address: provider={data.get('pickup_provider')}, code={data.get('pickup_point_code')}, name={data.get('pickup_point_name')}")
            address_data['pickup_provider'] = data.get('pickup_provider')
            address_data['pickup_point_code'] = data.get('pickup_point_code')
            address_data['pickup_point_name'] = data.get('pickup_point_name')

            # Сохраняем координаты если они есть
            if data.get('latitude'):
                address_data['latitude'] = data.get('latitude')
            if data.get('longitude'):
                address_data['longitude'] = data.get('longitude')

        logger.info(f"Creating address with data: {address_data}")
        address = Address.objects.create(**address_data)

        return JsonResponse({
            'success': True,
            'address_id': address.id,
            'message': 'Address saved successfully',
            'address': {
                'id': address.id,
                'address': address.full_address,
                'postal_code': address.postal_code or '',
                'delivery_type': address.delivery_type,
                'pickup_provider': address.pickup_provider,
                'pickup_point_code': address.pickup_point_code,
                'pickup_point_name': address.pickup_point_name,
                'latitude': float(address.latitude) if address.latitude else None,
                'longitude': float(address.longitude) if address.longitude else None,
                'is_default': address.is_default,
            }
        })

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}, body: {request.body[:200]}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error saving address: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def save_address_to_session(request):
    """Сохранение адреса в сессию для неавторизованных пользователей (поддержка списка адресов)"""
    try:
        # Проверяем, что это AJAX-запрос и данные в формате JSON
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

        data = json.loads(request.body)
        
        # Валидация обязательных полей
        if not data.get('address'):
            return JsonResponse({'success': False, 'error': 'Address is required'}, status=400)

        # Формируем данные нового адреса
        new_address = {
            'address': data.get('address'),
            'postal_code': data.get('postal_code', ''),
            'delivery_type': data.get('delivery_type', 'delivery'),
            'pickup_provider': data.get('pickup_provider'),
            'pickup_point_code': data.get('pickup_point_code'),
            'pickup_point_name': data.get('pickup_point_name'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
        }
        
        # Получаем существующий список адресов или создаём новый
        pending_addresses = request.session.get('pending_addresses', [])
        
        # Проверяем на дубликаты
        is_duplicate = False
        for existing in pending_addresses:
            if new_address['delivery_type'] == 'pickup':
                # Для самовывоза сравниваем код пункта и провайдера
                if (existing.get('pickup_point_code') == new_address['pickup_point_code'] and
                    existing.get('pickup_provider') == new_address['pickup_provider']):
                    is_duplicate = True
                    break
            else:
                # Для доставки сравниваем адрес
                if existing.get('address', '').lower().strip() == new_address['address'].lower().strip():
                    is_duplicate = True
                    break
        
        if is_duplicate:
            return JsonResponse({'success': False, 'error': 'Этот адрес уже добавлен'}, status=400)
        
        # Добавляем индекс для идентификации
        new_address['session_index'] = len(pending_addresses)
        
        # Добавляем новый адрес в список
        pending_addresses.append(new_address)
        request.session['pending_addresses'] = pending_addresses
        request.session.modified = True
        
        logger.info(f"Address saved to session (total: {len(pending_addresses)}): {new_address['address'][:50]}")

        return JsonResponse({
            'success': True,
            'message': 'Address saved to session',
            'requires_auth': True,
            'address': new_address
        })

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}, body: {request.body[:200]}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error saving address to session: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def get_address_from_session(request):
    """Получение адресов из сессии для неавторизованных пользователей (возвращает список)"""
    pending_addresses = request.session.get('pending_addresses', [])
    
    # Обратная совместимость: проверяем старый формат pending_address
    if not pending_addresses and 'pending_address' in request.session:
        old_address = request.session['pending_address']
        old_address['session_index'] = 0
        pending_addresses = [old_address]
        # Мигрируем на новый формат
        request.session['pending_addresses'] = pending_addresses
        del request.session['pending_address']
        request.session.modified = True
    
    if pending_addresses:
        # Возвращаем список адресов
        return JsonResponse({
            'has_address': True,
            'addresses': pending_addresses,
            # Для обратной совместимости: первый адрес как основной
            'address': pending_addresses[0] if pending_addresses else None,
            'from_session': True
        })
    
    return JsonResponse({'has_address': False, 'addresses': []})


@require_POST
def delete_address_from_session(request):
    """Удаление адреса из сессии для неавторизованных пользователей (по индексу)"""
    try:
        # Пытаемся получить индекс из тела запроса
        session_index = None
        try:
            data = json.loads(request.body) if request.body else {}
            session_index = data.get('session_index')
        except json.JSONDecodeError:
            pass
        
        pending_addresses = request.session.get('pending_addresses', [])
        
        # Обратная совместимость со старым форматом
        if not pending_addresses and 'pending_address' in request.session:
            del request.session['pending_address']
            request.session.modified = True
            logger.info("Address deleted from session (old format)")
            return JsonResponse({'success': True, 'message': 'Address deleted from session'})
        
        if not pending_addresses:
            return JsonResponse({'success': False, 'error': 'No addresses in session'}, status=404)
        
        if session_index is not None:
            # Удаляем конкретный адрес по индексу
            try:
                session_index = int(session_index)
                if 0 <= session_index < len(pending_addresses):
                    removed = pending_addresses.pop(session_index)
                    # Обновляем индексы оставшихся адресов
                    for i, addr in enumerate(pending_addresses):
                        addr['session_index'] = i
                    request.session['pending_addresses'] = pending_addresses
                    request.session.modified = True
                    logger.info(f"Address at index {session_index} deleted from session")
                    return JsonResponse({'success': True, 'message': 'Address deleted from session'})
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid address index'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid session_index'}, status=400)
        else:
            # Если индекс не указан, удаляем все адреса (для обратной совместимости)
            del request.session['pending_addresses']
            request.session.modified = True
            logger.info("All addresses deleted from session")
            return JsonResponse({'success': True, 'message': 'All addresses deleted from session'})
            
    except Exception as e:
        logger.error(f"Error deleting address from session: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
def set_default_address(request, address_id):
    """Установка адреса по умолчанию"""
    try:
        address = request.user.addresses.get(id=address_id)
        # Снимаем "основной" со всех адресов
        request.user.addresses.update(is_default=False)
        # Делаем выбранный адрес основным
        address.is_default = True
        address.save()
        return JsonResponse({'success': True})
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Адрес не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
@login_required
def delete_address(request, address_id):
    """Удаление адреса"""
    try:
        address = request.user.addresses.get(id=address_id)
        address.delete()
        return JsonResponse({'success': True})
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Адрес не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_GET
def get_selected_address(request):
    """Получаем последний выбранный адрес пользователя"""
    try:
        # Ищем черновик заказа или создаем новый
        order, created = Order.objects.get_or_create(
            user=request.user,
            status='draft',  # специальный статус для черновика
            defaults={}
        )

        if order.delivery_address:
            address = {
                'id': order.delivery_address.id,
                'title': order.delivery_address.title or 'Адрес доставки',
                'full_address': order.delivery_address.full_address,
                'postal_code': order.delivery_address.postal_code or '',
                'delivery_type': order.delivery_address.delivery_type or 'delivery',
                'is_default': order.delivery_address.is_default
            }
            return JsonResponse({'address': address})
    except Exception as e:
        print(f"Error getting selected address: {e}")

    return JsonResponse({'address': None})


@login_required
@require_POST
def save_selected_address(request):
    """Сохраняем выбранный адрес в черновике заказа"""
    try:
        data = json.loads(request.body)
        address_id = data.get('address_id')

        # Получаем или создаем черновик заказа
        order, created = Order.objects.get_or_create(
            user=request.user,
            status='draft',
            defaults={}
        )

        if address_id:
            address = Address.objects.get(id=address_id, user=request.user)
            order.delivery_address = address
            order.save()
        else:
            order.delivery_address = None
            order.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_avatar(request):
    profile = request.user.profile
    if profile.photo:
        try:
            photo_path = profile.photo.path
            profile.photo.delete(save=True)
            # удаляем файл с диска, если он ещё существует
            if os.path.exists(photo_path):
                os.remove(photo_path)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Аватар не найден'}, status=404)


@login_required
@require_POST
def upload_profile_photo(request):
    if 'photo' in request.FILES:
        try:
            profile = request.user.profile
            profile.photo = request.FILES['photo']
            profile.save()
            return JsonResponse({
                'success': True,
                'photo_url': profile.photo.url
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': 'No photo provided'
    }, status=400)


@login_required
def get_default_address(request):
    """API для получения основного адреса пользователя"""
    try:
        default_address = request.user.get_default_address()

        if default_address:
            return JsonResponse({
                'has_address': True,
                'short_address': default_address.short_address,
                'full_address': default_address.full_address,
                'postal_code': default_address.postal_code
            })

        return JsonResponse({'has_address': False})
    except Exception as e:
        logger.error(f"Error getting default address: {e}")
        return JsonResponse({'has_address': False}, status=500)


@login_required
def my_reviews(request):
    # Получаем фильтр из GET-параметра
    status_filter = request.GET.get('status', 'all')

    # Базовый queryset - только отзывы текущего пользователя
    reviews = Review.objects.filter(user=request.user).select_related('product')

    # Применяем фильтр
    if status_filter == 'published':
        reviews = reviews.filter(is_published=True)
    elif status_filter == 'moderation':
        reviews = reviews.filter(is_published=False)

    # Сортируем по дате создания (новые сначала)
    reviews = reviews.order_by('-created_at')

    # Пагинация
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Получаем счетчики для бокового меню
    from favorites.models import Favorite
    from orders.models import Order

    favorites_count = Favorite.objects.filter(user=request.user).count()
    orders_count = Order.objects.filter(user=request.user).count()

    context = {
        'reviews': page_obj,
        'reviews_count': reviews.count(),
        'favorites_count': favorites_count,
        'orders_count': orders_count,
        'current_filter': status_filter,
        'page_obj': page_obj,
    }

    return render(request, 'accounts/my_reviews.html', context)


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == 'POST':
        review.delete()

        return redirect('accounts:my_reviews')

    return redirect('accounts:my_reviews')


logger = logging.getLogger(__name__)


@require_POST
def send_verification_code(request):
    """Отправка кода подтверждения на email"""
    login = request.POST.get('login')

    # Логируем начало процесса
    logger.info(f"Attempting to send verification code to: {login}")

    if not login:
        logger.warning("Empty login provided")
        return JsonResponse({'success': False, 'error': 'Введите email'}, status=400)

    # Проверяем, что это email
    if '@' not in login:
        logger.warning("Non-email login provided")
        return JsonResponse({'success': False, 'error': 'Введите корректный email'}, status=400)

    # Проверяем, не отправлялся ли код недавно (в течение 30 секунд)
    from django.utils import timezone
    from datetime import timedelta

    recent_codes = VerificationCode.objects.filter(
        login=login,
        created_at__gte=timezone.now() - timedelta(seconds=30)
    )

    if recent_codes.exists():
        logger.warning(f"Code already sent recently for {login}")
        return JsonResponse({
            'success': False,
            'error': 'Код уже отправлен. Подождите 30 секунд перед повторной отправкой.'
        }, status=429)

    # Проверяем, существует ли пользователь
    user_exists = User.objects.filter(email=login).exists()
    logger.info(f"Email login: {login}, user exists: {user_exists}")

    # Генерируем 6-значный код
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    logger.info(f"Generated code: {code}")

    # Сохраняем код в базе
    try:
        VerificationCode.objects.create(
            login=login,
            code=code
        )
        logger.info("Code saved to database")
    except Exception as e:
        logger.error(f"Error saving code to database: {e}")
        return JsonResponse({'success': False, 'error': 'Ошибка сохранения кода'}, status=500)

    # Отправляем код по email
    try:
        logger.info(f"Attempting to send email to: {login}")

        # Отправка email с улучшенным содержимым
        subject = 'Код подтверждения для входа в LinkAvto'
        message = f'''Здравствуйте!

Ваш код подтверждения для входа в LinkAvto: {code}

Код действителен в течение 10 минут.

Если вы не запрашивали код подтверждения, проигнорируйте это письмо.

С уважением,
Команда LinkAvto
https://linkavto.ru'''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [login],
            fail_silently=False,
        )
        logger.info("Email sent successfully")

        return JsonResponse({
            'success': True,
            'message': 'Код отправлен на email',
            'user_exists': user_exists
        })

    except Exception as e:
        # Детальное логирование ошибки
        logger.error(f"Error sending verification code: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback:", exc_info=True)

        return JsonResponse({'success': False, 'error': 'Произошла ошибка при отправке кода'}, status=500)


@require_POST
def verify_code_and_login(request):
    """Проверка кода и вход пользователя"""
    login_data = request.POST.get('login_data')  # переименовали переменную!
    code = request.POST.get('code')

    logger.info(f"Verifying code for: {login_data}")
    logger.info(f"Code received: {code}")

    if not login_data or not code:
        return JsonResponse({'success': False, 'error': 'Неверные данные'}, status=400)

    # Ищем актуальный код
    try:
        verification_code = VerificationCode.objects.filter(
            login=login_data,  # используем переименованную переменную
            is_used=False,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).latest('created_at')

        logger.info(f"Found verification code: {verification_code.code}")

    except VerificationCode.DoesNotExist:
        logger.error("Verification code not found or expired")
        return JsonResponse({'success': False, 'error': 'Код не найден или устарел'}, status=400)

    # Проверяем код
    if verification_code.code != code:
        verification_code.attempts -= 1
        verification_code.save()

        if verification_code.attempts <= 0:
            verification_code.is_used = True
            verification_code.save()
            return JsonResponse({'success': False, 'error': 'Превышено количество попыток'}, status=400)

        return JsonResponse({
            'success': False,
            'error': 'Неверный код',
            'attempts_left': verification_code.attempts
        }, status=400)

    # Код верный, помечаем как использованный
    verification_code.is_used = True
    verification_code.save()
    logger.info("Code verified successfully")

    # Ищем пользователя по email
    user = None
    try:
        user = User.objects.get(email=login_data)
        logger.info(f"User found by email: {user.username}")
    except User.DoesNotExist:
        # Пользователь не существует - нужно зарегистрировать
        logger.info("User not found, needs registration")
        return JsonResponse({
            'success': True,
            'needs_registration': True,
            'login': login_data
        })

    # Если пользователь существует - логиним
    if user:
        try:
            # Проверяем, есть ли профиль
            try:
                user.profile
                logger.info(f"User {user.username} profile exists")
            except Profile.DoesNotExist:
                logger.error(f"User {user.username} has no profile")
                return JsonResponse({'success': False, 'error': 'Профиль пользователя не найден'}, status=400)

            auth_login(request, user)  # ← Используем переименованную функцию auth_login!
            # Проверяем, есть ли адреса в сессии, и создаем их
            addresses = create_addresses_from_session(request)
            address = addresses[0] if addresses else None
            if addresses:
                logger.info(f"{len(addresses)} address(es) created from session after code login for user {user.id}")
            logger.info(f"User {user.username} logged in successfully")
            return JsonResponse({
                'success': True,
                'redirect_url': request.POST.get('next', '/'),
                'address_created': address is not None,
                'address_id': address.id if address else None
            })
        except Exception as e:
            logger.error(f"Login error: {e}")
            return JsonResponse({'success': False, 'error': 'Ошибка входа'}, status=400)

    return JsonResponse({'success': False, 'error': 'Ошибка входа'}, status=400)


@require_POST
def register_with_code(request):
    """Регистрация после подтверждения кода"""
    login_data = request.POST.get('login')
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')

    logger.info(f"Registering new user: {login_data}")

    try:
        # Проверяем, не существует ли уже пользователь
        if User.objects.filter(username=login_data).exists():
            logger.warning(f"User with login {login_data} already exists")
            return JsonResponse({'success': False, 'error': 'Пользователь с таким email/телефоном уже существует'},
                                status=400)

        if '@' in login_data:  # Регистрация по email
            # Создаем пользователя с email
            user = User.objects.create_user(
                username=login_data,
                email=login_data,
                first_name=first_name,
                last_name=last_name
            )
            # Создаем профиль только при успешной регистрации
            Profile.objects.create(user=user, phone=login_data)
            logger.info(f"User created with email: {login_data}")

        else:  # Регистрация по телефону
            # Создаем пользователя с телефоном
            user = User.objects.create_user(
                username=login_data,
                first_name=first_name,
                last_name=last_name
            )
            # Создаем профиль с телефоном
            Profile.objects.create(user=user, phone=login_data)
            logger.info(f"User created with phone: {login_data}")

        auth_login(request, user)  # ← Используем auth_login!
        # Проверяем, есть ли адреса в сессии, и создаем их
        addresses = create_addresses_from_session(request)
        address = addresses[0] if addresses else None
        if addresses:
            logger.info(f"{len(addresses)} address(es) created from session after registration for user {user.id}")
        logger.info(f"User {user.username} logged in after registration")
        
        # Возвращаем информацию об адресе
        return JsonResponse({
            'success': True,
            'redirect_url': request.POST.get('next', '/'),
            'address_created': address is not None,
            'address_id': address.id if address else None
        })

        return JsonResponse({
            'success': True,
            'redirect_url': request.POST.get('next', '/')
        })

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return JsonResponse({'success': False, 'error': f'Ошибка регистрации: {str(e)}'}, status=400)


def calculate_radius_from_bounds(bounds):
    """
    Вычисление радиуса в метрах из границ карты (bounds)
    
    Args:
        bounds: [[lat1, lon1], [lat2, lon2]] - границы видимой области
        
    Returns:
        Радиус в метрах (половина диагонали видимой области)
    """
    import math
    
    if not bounds or len(bounds) != 2:
        return 10000  # 10 км по умолчанию
    
    lat1, lon1 = bounds[0]
    lat2, lon2 = bounds[1]
    
    # Формула Haversine для расчета расстояния между двумя точками
    R = 6371000  # Радиус Земли в метрах
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Расстояние по диагонали
    diagonal = R * c
    
    # Возвращаем радиус (половина диагонали) + 20% запас
    radius = int(diagonal / 2 * 1.2)
    
    # Ограничиваем минимум 1 км, максимум 50 км
    return max(1000, min(radius, 50000))


@require_GET
def get_pickup_points(request):
    """
    API для получения пунктов выдачи
    
    Параметры:
    - provider: 'russian_post', 'cdek' или 'all'
    - city: Название города
    - latitude: Широта центра карты
    - longitude: Долгота центра карты
    - zoom: Уровень масштабирования карты (для расчёта количества точек)
    - bounds: JSON строка с границами карты [[lat1, lon1], [lat2, lon2]]
    """
    import logging
    import json
    logger = logging.getLogger(__name__)
    
    provider = request.GET.get('provider', 'all')
    city = request.GET.get('city', 'Москва')
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    zoom_str = request.GET.get('zoom')
    bounds_str = request.GET.get('bounds')
    
    try:
        # Преобразуем координаты в float если они есть
        lat = None
        lon = None
        bounds = None
        zoom = 12  # По умолчанию
        radius = 10000  # По умолчанию 10 км
        
        if latitude:
            try:
                lat = float(latitude)
            except (ValueError, TypeError):
                logger.warning(f"Некорректная широта: {latitude}")
        
        if longitude:
            try:
                lon = float(longitude)
            except (ValueError, TypeError):
                logger.warning(f"Некорректная долгота: {longitude}")
        
        if zoom_str:
            try:
                zoom = int(float(zoom_str))
            except (ValueError, TypeError):
                logger.warning(f"Некорректный zoom: {zoom_str}")
        
        # Парсим bounds и вычисляем радиус
        if bounds_str:
            try:
                bounds = json.loads(bounds_str)
                radius = calculate_radius_from_bounds(bounds)
                logger.info(f"Вычислен радиус из bounds: {radius}м, zoom: {zoom}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Ошибка парсинга bounds: {e}")
        
        points = []
        
        # Получаем точки Почты России через API nearby (до 1000 точек)
        if provider == 'russian_post' or provider == 'all':
            try:
                from accounts.delivery_services.russian_post_service import RussianPostService
                service = RussianPostService()
                
                if lat and lon:
                    # API nearby поддерживает до 1000+ точек за раз!
                    post_points = service.get_nearby_post_offices(
                        latitude=lat,
                        longitude=lon,
                        top=1000  # Загружаем максимум
                    )
                    logger.info(f"Получено {len(post_points)} точек Почты России (nearby, zoom={zoom})")
                else:
                    # Fallback: координаты Москвы по умолчанию
                    post_points = service.get_nearby_post_offices(
                        latitude=55.751574,
                        longitude=37.573856,
                        top=1000
                    )
                    logger.info(f"Получено {len(post_points)} точек Почты России (fallback Москва)")
                
                points.extend(post_points)
            except Exception as e:
                logger.error(f"Ошибка получения ПВЗ Почты России: {e}", exc_info=True)
        
        # Получаем точки СДЭК
        if provider == 'cdek' or provider == 'all':
            try:
                from accounts.delivery_services.cdek_service import CDEKService
                service = CDEKService()
                
                # CDEK API не поддерживает bounding box, загружаем по городу
                cdek_points = service.get_pickup_points(
                    city=city,
                    latitude=lat,
                    longitude=lon
                )
                points.extend(cdek_points)
                logger.info(f"Получено {len(cdek_points)} точек СДЭК")
            except Exception as e:
                logger.error(f"Ошибка получения ПВЗ СДЭК: {e}", exc_info=True)
                # Продолжаем работу, даже если один провайдер не ответил
        
        return JsonResponse({
            'success': True,
            'points': points,
            'count': len(points),
            'provider': provider,
            'radius': radius
        })
    except Exception as e:
        logger.error(f"Общая ошибка в get_pickup_points: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'points': [],
            'count': 0
        })


@require_GET
def get_pickup_point_details(request, provider, code):
    """
    API для получения детальной информации о пункте выдачи
    
    Параметры:
    - provider: 'russian_post' или 'cdek'
    - code: Код пункта выдачи
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Запрос деталей: provider={provider}, code={code}")
    
    try:
        point = None
        
        if provider == 'russian_post':
            try:
                from accounts.delivery_services.russian_post_service import RussianPostService
                service = RussianPostService()
                logger.info(f"Запрос деталей для Почты России: code={code}")
                point = service.get_pickup_point_by_code(code)
                if point:
                    logger.info(f"Получена информация о пункте Почты России: {code}")
                else:
                    logger.warning(f"Пункт Почты России не найден: {code}")
            except Exception as e:
                logger.error(f"Ошибка получения деталей ПВЗ Почты России: {e}", exc_info=True)
        
        elif provider == 'cdek':
            try:
                from accounts.delivery_services.cdek_service import CDEKService
                service = CDEKService()
                point = service.get_pickup_point_by_code(code)
                if point:
                    logger.info(f"Получена информация о пункте СДЭК: {code}")
            except Exception as e:
                logger.error(f"Ошибка получения деталей ПВЗ СДЭК: {e}", exc_info=True)
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown provider: {provider}',
                'point': None
            }, status=400)
        
        if point:
            return JsonResponse({
                'success': True,
                'point': point
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Point not found',
                'point': None
            }, status=404)
            
    except Exception as e:
        logger.error(f"Общая ошибка в get_pickup_point_details: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'point': None
        }, status=500)


@login_required
def edit_review(request, review_id):
    """Редактирование отзыва"""
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == 'POST':
        try:
            # Получаем данные из формы
            rating = request.POST.get('rating')
            comment = request.POST.get('comment', '')

            # Обновляем данные отзыва
            if rating:
                review.rating = int(rating)
            review.comment = comment

            # Сбрасываем статус публикации при редактировании
            # Отзыв должен пройти модерацию заново
            review.is_published = False

            review.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Отзыв успешно обновлен и отправлен на модерацию.'
                })

            messages.success(request, 'Отзыв успешно обновлен и отправлен на модерацию.')
            return redirect('accounts:my_reviews')

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка при сохранении отзыва: {str(e)}'
                })

            messages.error(request, f'Ошибка при сохранении отзыва: {str(e)}')
            return redirect('accounts:my_reviews')

    # Если метод не POST, перенаправляем обратно
    return redirect('accounts:my_reviews')
