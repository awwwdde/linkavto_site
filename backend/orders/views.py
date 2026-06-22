from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from .forms import OrderCreateForm
from .models import Order, OrderItem, Payment
from cart.models import Cart  # Используем модель Cart вместо session-based корзины
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tbank_service import create_tbank_payment, get_tbank_payment_status
import json
import logging

logger = logging.getLogger(__name__)


def order_create(request):
    # Получаем корзину из модели (а не из сессии)
    cart = Cart.get_cart(request)
    
    logger.info(f"Order create view called. Method: {request.method}, Cart items: {cart.items.count()}")

    if request.method == 'POST':
        logger.info(f"POST data: {request.POST}")
        logger.info(f"Phone from POST: '{request.POST.get('phone', 'NOT_FOUND')}'")
        form = OrderCreateForm(request.POST, user=request.user, request=request)
        logger.info(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            logger.error(f"Form errors: {form.errors}")
            logger.error(f"Phone field errors: {form.errors.get('phone', 'No phone errors')}")
            logger.error(f"Phone field value: '{form.data.get('phone', 'NOT_FOUND')}'")
        
        if form.is_valid():
            # Сохраняем телефон в сессии для будущего использования
            cleaned_phone = form.cleaned_data.get('phone', '')
            if cleaned_phone:
                request.session['last_phone'] = cleaned_phone
                logger.info(f"Saved phone to session: '{cleaned_phone}'")
            with transaction.atomic():
                # Создаем заказ в БД
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                order.save()

                # Создаем OrderItem на основе CartItem
                order_items = [
                    OrderItem(
                        order=order,
                        product=item.product,
                        price=item.product.price,  # Сохраняем цену на момент заказа
                        quantity=item.quantity
                    ) for item in cart.items.all()
                ]
                OrderItem.objects.bulk_create(order_items)

                # Создаем платеж через Т-Банк
                total_cost = order.get_total_cost()
                logger.info(f"Creating TBank payment for order {order.id}, amount: {total_cost}")
                payment_data = create_tbank_payment(
                    order_id=order.id,
                    amount=total_cost,
                    description=f"Оплата заказа #{order.id}",
                    order_items=order_items,
                    customer_email=order.email,
                    customer_phone=order.phone
                )
                
                logger.info(f"TBank payment response: {payment_data}")
                
                if payment_data and payment_data.get('Success'):
                    # Сохраняем данные платежа
                    payment = Payment.objects.create(
                        order=order,
                        amount=total_cost,
                        method='tbank',
                        transaction_id=payment_data.get('PaymentId'),
                        status='pending'
                    )
                    
                    # Очищаем корзину
                    cart.items.all().delete()
                    
                    # Перенаправляем на страницу оплаты Т-Банк
                    payment_url = payment_data.get('PaymentURL')
                    if payment_url:
                        logger.info(f"Redirecting to payment URL: {payment_url}")
                        # Проверяем, это AJAX запрос?
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': True,
                                'order_id': order.id,
                                'payment_url': payment_url,
                                'message': 'Заказ успешно создан'
                            })
                        else:
                            return redirect(payment_url)
                    else:
                        logger.error("No PaymentURL in response")
                        error_message = 'Ошибка: не получен URL для оплаты'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'error': error_message
                            })
                        else:
                            messages.error(request, error_message)
                            return render(request, 'orders/create.html', {
                                'cart': cart,
                                'form': form
                            })
                else:
                    # Если платеж не создался, удаляем заказ
                    order.delete()
                    
                    error_message = 'Ошибка создания платежа. Попробуйте еще раз.'
                    if payment_data and 'ErrorCode' in payment_data:
                        error_code = payment_data.get('ErrorCode')
                        error_msg = payment_data.get('Message', 'Неизвестная ошибка')
                        error_details = payment_data.get('Details', '')
                        error_message = f"Ошибка Т-Банк (код {error_code}): {error_msg}"
                        if error_details:
                            error_message += f" - {error_details}"
                    
                    logger.error(f"TBank payment failed: {payment_data}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_message
                        })
                    else:
                        messages.error(request, error_message)
                        return render(request, 'orders/create.html', {
                            'cart': cart,
                            'form': form
                        })
    else:
        # Предзаполнение формы (как было раньше)
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'name': request.user.get_full_name(),
                'email': request.user.email
            }
        form = OrderCreateForm(initial=initial, user=request.user, request=request)

    return render(request, 'orders/create.html', {
        'cart': Cart.get_cart(request),
        'form': form
    })


def send_order_notification(order):
    """Упрощенная отправка уведомлений для локальной разработки"""
    print("\n" + "=" * 50)
    print(f"ДЕМО: Уведомление для заказа #{order.id}")
    print(f"Клиент: {order.name} ({order.email})")
    print(f"Сумма: {order.get_total_cost()} руб.")
    print(f"Статус: {order.get_status_display()}")
    print("=" * 50 + "\n")

    # Для тестирования реальной отправки раскомментируйте:
    # send_mail(
    #     'AvtoLink: Заказ #{}'.format(order.id),
    #     'Это тестовое уведомление',
    #     'noreply@avtolink.local',
    #     [order.email],
    #     fail_silently=True,
    # )


def order_success(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product'),
        id=order_id
    )

    # Проверка доступа (если нужно)
    if (request.user != order.user and
            order.session_key != request.session.session_key):
        return redirect('shop:index')

    return render(request, 'orders/order_success.html', {
        'order': order,
        'total_cost': order.get_total_cost()
    })


@login_required
def my_orders(request):
    # Получаем все заказы пользователя
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Определяем статусы для активных и завершенных заказов
    active_statuses = ['processing', 'confirmed', 'on_hold', 'shipped', 'ready_for_pickup']
    completed_statuses = ['delivered', 'canceled', 'refunded']

    # Разделяем заказы
    active_orders = orders.filter(status__in=active_statuses)
    completed_orders = orders.filter(status__in=completed_statuses)

    return render(request, 'orders/my_orders.html', {
        'orders': orders,  # оставляем для обратной совместимости
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'active_orders_count': active_orders.count(),
        'completed_orders_count': completed_orders.count()
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@require_POST
@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'processing':
        order.status = 'canceled'
        order.save()
        # Здесь можно добавить логику возврата платежа
        messages.success(request, f'Заказ #{order_id} успешно отменен')
    return redirect('orders:order_detail', order_id=order_id)


@login_required
def get_orders_count(request):
    count = Order.objects.filter(user=request.user).count()
    return JsonResponse({'count': count})


@csrf_exempt
def tbank_notify(request):
    """
    Обработка уведомлений от Т-Банк о статусе платежа
    """
    if request.method == 'GET':
        # Т-Банк может проверять URL доступности
        return JsonResponse({'status': 'ok', 'message': 'TBank notify endpoint is working'})
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        payment_id = data.get('PaymentId')
        status = data.get('Status')
        
        logger.info(f"TBank notification: PaymentId={payment_id}, Status={status}")
        
        # Находим платеж по transaction_id
        payment = Payment.objects.filter(transaction_id=payment_id).first()
        if not payment:
            logger.error(f"Payment not found: {payment_id}")
            return JsonResponse({'error': 'Payment not found'}, status=404)
        
        # Обновляем статус платежа согласно API Т-Банк
        if status == 'CONFIRMED':
            payment.status = 'succeeded'
            payment.order.mark_as_paid()
        elif status == 'REJECTED':
            payment.status = 'failed'
        elif status == 'REFUNDED':
            payment.status = 'refunded'
        elif status == 'AUTHORIZED':
            payment.status = 'authorized'
        
        payment.save()
        
        logger.info(f"Payment {payment_id} status updated to {status}")
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"TBank notification error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


def payment_success(request, order_id):
    """
    Страница успешной оплаты
    """
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/payment_success.html', {'order': order})


def payment_fail(request, order_id):
    """
    Страница неуспешной оплаты
    """
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/payment_fail.html', {'order': order})


