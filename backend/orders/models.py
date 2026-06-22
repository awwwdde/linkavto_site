from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from shop.models import Product
from simple_history.models import HistoricalRecords
from django.db.models import Sum, F


class Order(models.Model):
    payment_id = models.CharField('ID платежа', max_length=100, blank=True)
    payment_method = models.CharField('Способ оплаты', max_length=50, blank=True)
    payment_details = models.JSONField('Детали платежа', default=dict)
    delivery_address = models.ForeignKey('accounts.Address', on_delete=models.SET_NULL, null=True, blank=True)
    STATUS_CHOICES = [
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменён'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Пользователь'
    )
    session_key = models.CharField('Ключ сессии', max_length=40, blank=True, null=True)

    # Контактные данные
    name = models.CharField('Имя', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField(
        'Телефон',
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Формат: '+999999999'. До 15 цифр."
        )]
    )
    address = models.TextField('Адрес')
    comment = models.TextField('Комментарий', blank=True)
    
    # Способ доставки
    DELIVERY_TYPE_CHOICES = [
        ('delivery', 'Доставка'),
        ('pickup', 'Самовывоз'),
    ]
    delivery_type = models.CharField(
        'Способ доставки',
        max_length=20,
        choices=DELIVERY_TYPE_CHOICES,
        default='delivery'
    )

    # Статусы
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)
    paid = models.BooleanField('Оплачен', default=False)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='processing'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Заказ #{self.id}"

    def get_total_cost(self):
        """Вычисляем сумму заказа через аннотацию"""
        return self.items.aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0

    total_cost = property(get_total_cost)  # Добавляем property для удобства

    def mark_as_paid(self):
        if not self.paid:
            self.paid = True
            if self.status == 'processing':
                self.status = 'shipped'
            self.save(update_fields=['paid', 'status'])

    def get_payment_link(self):
        if self.payment_method == 'yookassa':
            return f"https://yookassa.ru/payments/{self.payment_id}"
        elif self.payment_method == 'stripe':
            return f"https://dashboard.stripe.com/payments/{self.payment_id}"
        return None

    history = HistoricalRecords(
        excluded_fields=['updated_at'],
        history_change_reason_field=models.TextField(null=True)
    )

    @property
    def changes(self):
        return self.history.all().order_by('-history_date')


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Товар'
    )
    price = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField(
        'Количество',
        default=1
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def get_cost(self):
    # Если цены нет (None), возвращаем 0
        if not self.price:
            return 0
        return self.price * self.quantity


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('card', 'Банковская карта'),
        ('sbp', 'СБП'),
        ('yookassa', 'ЮKassa'),
        ('stripe', 'Stripe')
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('succeeded', 'Успешно'),
        ('failed', 'Ошибка'),
        ('refunded', 'Возврат')
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Заказ'
    )
    amount = models.DecimalField(
        'Сумма',
        max_digits=10,
        decimal_places=2
    )
    method = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=PAYMENT_METHODS
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(
        'ID транзакции',
        max_length=100,
        blank=True
    )
    created_at = models.DateTimeField(
        'Создан',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Обновлён',
        auto_now=True
    )
    card_last4 = models.CharField(
        'Последние 4 цифры карты',
        max_length=4,
        blank=True
    )

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']

    def __str__(self):
        return f"Платеж #{self.id} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if self.status == 'succeeded' and not self.order.paid:
            self.order.mark_as_paid()
        super().save(*args, **kwargs)