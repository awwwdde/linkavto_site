from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from shop.models import Category


class Seller(models.Model):
    LEGAL_FORM_CHOICES = [
        ('ip', 'ИП'),
        ('ooo', 'ООО'),
        ('ao', 'АО'),
    ]

    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонен'),
        ('suspended', 'Приостановлен'),
    ]

    PRODUCT_COUNT_CHOICES = [
        ('1-50', '1-50 товаров'),
        ('51-200', '51-200 товаров'),
        ('201-500', '201-500 товаров'),
        ('501-1000', '501-1000 товаров'),
        ('1000+', 'Более 1000 товаров'),
    ]

    # Основная информация
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller', verbose_name="Пользователь")
    contact_person = models.CharField(max_length=255, verbose_name="ФИО контактного лица")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Информация о компании
    company_name = models.CharField(max_length=255, verbose_name="Название компании")
    store_name = models.CharField(max_length=255, blank=True, verbose_name="Название магазина")
    legal_form = models.CharField(max_length=10, choices=LEGAL_FORM_CHOICES, verbose_name="Форма собственности")
    inn = models.CharField(max_length=12, unique=True, verbose_name="ИНН")
    ogrn = models.CharField(max_length=15, verbose_name="ОГРН/ОГРНИП")
    legal_address = models.TextField(verbose_name="Юридический адрес")
    actual_address = models.TextField(blank=True, verbose_name="Фактический адрес")
    shipping_address = models.TextField(blank=True, default='', verbose_name="Адрес отправки", help_text="Адрес склада/отправки товара — используется для расчёта стоимости доставки")
    website_url = models.URLField(blank=True, default='', verbose_name="Адрес сайта магазина")

    # Дополнительная информация
    product_info = models.TextField(blank=True, verbose_name="Информация о товарах")
    product_count = models.CharField(max_length=20, choices=PRODUCT_COUNT_CHOICES, blank=True, null=True,
                                     verbose_name="Количество товаров")

    # Статус и даты
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата одобрения")

    # Системные поля
    api_data = models.JSONField(null=True, blank=True, verbose_name="Данные из API ФНС")
    notes = models.TextField(blank=True, verbose_name="Заметки модератора")

    class Meta:
        verbose_name = "Продавец"
        verbose_name_plural = "Продавцы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name} ({self.contact_person})"

    def approve(self):
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()

    def reject(self, reason=""):
        self.status = 'rejected'
        self.notes = reason
        self.save()

    def can_auto_publish_products(self):
        """Может ли продавец публиковать товары без модерации (одобрен и есть история успешных заказов)."""
        if self.status != 'approved':
            return False
        from orders.models import Order
        successful_orders = Order.objects.filter(
            items__product__seller=self,
            status='delivered'
        ).distinct().count()
        return successful_orders >= 10


class SellerCategory(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='categories', verbose_name="Продавец")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Категория продавца"
        verbose_name_plural = "Категории продавцов"
        unique_together = ['seller', 'category']

    def __str__(self):
        return f"{self.seller.company_name} - {self.category.name}"


#### Аналитика ############

class MLAlgorithmResult(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    algorithm_name = models.CharField(max_length=100)
    input_data = models.JSONField()
    output_data = models.JSONField()
    accuracy = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SalesForecast(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    forecast_date = models.DateField()
    predicted_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    confidence_interval = models.JSONField()
    seasonality_factor = models.FloatField()


#### Финансы ####

class SellerFinanceProfile(models.Model):
    seller = models.OneToOneField('sellers.Seller', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hold_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # процент налогов
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    inn = models.CharField(max_length=20, blank=True)  # ИНН
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def available_balance(self):
        return self.balance - self.hold_amount


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('sale', 'Продажа товара'),
        ('refund', 'Возврат'),
        ('payout', 'Выплата'),
        ('commission', 'Комиссия площадки'),
        ('bonus', 'Бонус'),
        ('correction', 'Корректировка'),
        ('tax', 'Налог'),
    )

    STATUS_CHOICES = (
        ('pending', 'Ожидание'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
        ('hold', 'Холд'),
    )

    seller = models.ForeignKey('sellers.Seller', on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    reference_id = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['-transaction_date']


class Payout(models.Model):
    PAYOUT_METHODS = (
        ('bank_card', 'Банковская карта'),
        ('bank_account', 'Банковский счет'),
        ('yoomoney', 'ЮMoney'),
        ('qiwi', 'QIWI'),
    )

    PAYOUT_STATUS = (
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('completed', 'Выполнен'),
        ('failed', 'Ошибка'),
        ('canceled', 'Отменен'),
    )

    seller = models.ForeignKey('sellers.Seller', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHODS)
    account_details = models.JSONField()  # Реквизиты для выплаты
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    payout_reference = models.CharField(max_length=100, unique=True)


class FinancialReport(models.Model):
    REPORT_TYPES = (
        ('daily', 'Ежедневный'),
        ('weekly', 'Еженедельный'),
        ('monthly', 'Ежемесячный'),
        ('quarterly', 'Квартальный'),
        ('yearly', 'Годовой'),
        ('custom', 'Произвольный'),
    )

    seller = models.ForeignKey('sellers.Seller', on_delete=models.CASCADE)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_payouts = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    generated_at = models.DateTimeField(auto_now_add=True)
    report_file = models.FileField(upload_to='financial_reports/', null=True, blank=True)


class TaxCalculation(models.Model):
    seller = models.ForeignKey('sellers.Seller', on_delete=models.CASCADE)
    period = models.DateField()  # Месяц/квартал расчета
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    calculated_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(null=True, blank=True)


##### Отзывы ###########


class ProductReview(models.Model):
    REVIEW_STATUS = (
        ('pending', 'Ожидает модерации'),
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонен'),
        ('edited', 'Отредактирован продавцом'),
    )

    RATING_CHOICES = [
        (1, '1 - Ужасно'),
        (2, '2 - Плохо'),
        (3, '3 - Нормально'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    ]

    # Основная информация - ИСПРАВЛЕНО related_name
    product = models.ForeignKey('shop.Product', on_delete=models.CASCADE, related_name='seller_reviews')  # ИЗМЕНЕНО
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='seller_reviews')    # ИЗМЕНЕНО
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_reviews')              # ИЗМЕНЕНО

    # Контент отзыва
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True, verbose_name="Заголовок отзыва")
    comment = models.TextField(verbose_name="Текст отзыва")
    advantages = models.TextField(blank=True, verbose_name="Достоинства")
    disadvantages = models.TextField(blank=True, verbose_name="Недостатки")

    # Модерация и статус
    status = models.CharField(max_length=20, choices=REVIEW_STATUS, default='pending')
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='moderated_seller_reviews')  # ИЗМЕНЕНО
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_comment = models.TextField(blank=True, verbose_name="Комментарий модератора")

    # Ответ продавца
    seller_response = models.TextField(blank=True, verbose_name="Ответ продавца")
    responded_at = models.DateTimeField(null=True, blank=True)

    # Системные поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Полезность отзыва
    helpful_yes = models.PositiveIntegerField(default=0, verbose_name="Полезно")
    helpful_no = models.PositiveIntegerField(default=0, verbose_name="Не полезно")

    # Флаги
    is_verified_purchase = models.BooleanField(default=True, verbose_name="Подтвержденная покупка")
    is_edited = models.BooleanField(default=False, verbose_name="Редактировался")
    has_media = models.BooleanField(default=False, verbose_name="Есть медиафайлы")

    class Meta:
        verbose_name = "Отзыв о товаре"
        verbose_name_plural = "Отзывы о товарах"
        ordering = ['-created_at']
        unique_together = ['order', 'product']

    def __str__(self):
        return f"Отзыв на {self.product.name} от {self.user.get_full_name()}"

    def get_rating_stars(self, rating=None):
        """Возвращает звезды рейтинга (можно использовать для отдельных отзывов)"""
        if rating is None:
            rating = self.average_rating

        full_stars = int(rating)
        half_star = rating - full_stars >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        return {
            'full_stars': full_stars,
            'half_star': half_star,
            'empty_stars': empty_stars,
            'rating': rating
        }

    def get_rating_stars_html(self):
        """Возвращает HTML с звездами рейтинга"""
        rating = self.average_rating
        stars = []
        for i in range(1, 6):
            if i <= rating:
                stars.append('<i class="fas fa-star text-warning"></i>')
            elif i - 0.5 <= rating:
                stars.append('<i class="fas fa-star-half-alt text-warning"></i>')
            else:
                stars.append('<i class="far fa-star text-warning"></i>')
        return mark_safe(''.join(stars))

    def helpful_score(self):
        total = self.helpful_yes + self.helpful_no
        return (self.helpful_yes / total * 100) if total > 0 else 0


class ReviewMedia(models.Model):
    MEDIA_TYPES = (
        ('image', 'Изображение'),
        ('video', 'Видео'),
    )

    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='media_files')  # ИЗМЕНЕНО
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='image')
    file = models.FileField(upload_to='reviews/media/%Y/%m/')
    thumbnail = models.ImageField(upload_to='reviews/thumbnails/%Y/%m/', null=True, blank=True)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return f"Медиа для отзыва #{self.review.id}"


class ReviewReport(models.Model):
    REPORT_TYPES = (
        ('spam', 'Спам'),
        ('inappropriate', 'Неуместный контент'),
        ('false_info', 'Ложная информация'),
        ('personal_data', 'Личные данные'),
        ('other', 'Другое'),
    )

    REPORT_STATUS = (
        ('pending', 'На рассмотрении'),
        ('reviewed', 'Рассмотрено'),
        ('dismissed', 'Отклонено'),
    )

    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='seller_reports')  # ИЗМЕНЕНО
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True, verbose_name="Описание проблемы")
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_seller_reports')  # ИЗМЕНЕНО
    reviewed_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.TextField(blank=True, verbose_name="Принятые меры")

    class Meta:
        verbose_name = "Жалоба на отзыв"
        verbose_name_plural = "Жалобы на отзывы"


class SellerReviewSummary(models.Model):
    """Сводная статистика отзывов по продавцу"""
    seller = models.OneToOneField('sellers.Seller', on_delete=models.CASCADE, related_name='review_summary')

    # Общая статистика
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    # Распределение по рейтингам
    rating_5 = models.PositiveIntegerField(default=0)
    rating_4 = models.PositiveIntegerField(default=0)
    rating_3 = models.PositiveIntegerField(default=0)
    rating_2 = models.PositiveIntegerField(default=0)
    rating_1 = models.PositiveIntegerField(default=0)

    # Показатели качества
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_response_time = models.DurationField(null=True, blank=True)
    verified_reviews = models.PositiveIntegerField(default=0)

    # Обновляется автоматически
    last_calculated = models.DateTimeField(auto_now=True)

    def update_statistics(self):
        """Обновление статистики отзывов"""
        from django.db.models import Count, Avg, F

        reviews = ProductReview.objects.filter(
            product__seller=self.seller,
            status='approved'
        )

        # Основная статистика
        self.total_reviews = reviews.count()
        self.average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

        # Распределение по рейтингам
        rating_counts = reviews.values('rating').annotate(count=Count('id'))
        for rating_count in rating_counts:
            setattr(self, f'rating_{rating_count["rating"]}', rating_count['count'])

        # Статистика ответов
        responded_reviews = reviews.exclude(seller_response='')
        self.response_rate = (responded_reviews.count() / self.total_reviews * 100) if self.total_reviews > 0 else 0

        # Время ответа
        if responded_reviews.exists():
            avg_response_time = responded_reviews.annotate(
                response_delay=F('responded_at') - F('created_at')
            ).aggregate(avg=Avg('response_delay'))['avg']
            self.average_response_time = avg_response_time

        self.verified_reviews = reviews.filter(is_verified_purchase=True).count()
        self.save()

    def get_rating_percentage(self):
        """Возвращает словарь с процентами для каждого рейтинга"""
        if self.total_reviews == 0:
            return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        return {
            5: (self.rating_5 / self.total_reviews) * 100,
            4: (self.rating_4 / self.total_reviews) * 100,
            3: (self.rating_3 / self.total_reviews) * 100,
            2: (self.rating_2 / self.total_reviews) * 100,
            1: (self.rating_1 / self.total_reviews) * 100,
        }

    def __str__(self):
        return f"Статистика отзывов {self.seller.company_name}"




###### Настройки ########


class SellerSettings(models.Model):
    """Настройки продавца"""
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE, related_name='settings')

    # Уведомления
    email_notifications = models.BooleanField(default=True, verbose_name="Email уведомления")
    sms_notifications = models.BooleanField(default=False, verbose_name="SMS уведомления")
    push_notifications = models.BooleanField(default=True, verbose_name="Push уведомления")

    # Уведомления о событиях
    notify_new_orders = models.BooleanField(default=True, verbose_name="Новые заказы")
    notify_low_stock = models.BooleanField(default=True, verbose_name="Низкий остаток")
    notify_new_reviews = models.BooleanField(default=True, verbose_name="Новые отзывы")
    notify_payouts = models.BooleanField(default=True, verbose_name="Выплаты")

    # Автоматизация
    auto_confirm_orders = models.BooleanField(default=False, verbose_name="Автоподтверждение заказов")
    auto_update_stock = models.BooleanField(default=False, verbose_name="Автообновление остатков")
    auto_response_reviews = models.BooleanField(default=False, verbose_name="Автоответ на отзывы")

    # Внешний вид
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Светлая'),
            ('dark', 'Темная'),
            ('auto', 'Авто')
        ],
        default='light',
        verbose_name="Тема"
    )
    language = models.CharField(
        max_length=10,
        choices=[
            ('ru', 'Русский'),
            ('en', 'English')
        ],
        default='ru',
        verbose_name="Язык"
    )

    # Безопасность
    two_factor_auth = models.BooleanField(default=False, verbose_name="Двухфакторная аутентификация")
    login_alerts = models.BooleanField(default=True, verbose_name="Оповещения о входе")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройки продавца"
        verbose_name_plural = "Настройки продавцов"

    def __str__(self):
        return f"Настройки {self.seller.company_name}"


class SellerIntegration(models.Model):
    """Интеграции продавца"""
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE, related_name='integrations')

    # API ключи
    api_key = models.CharField(max_length=255, blank=True, verbose_name="API ключ")
    api_secret = models.CharField(max_length=255, blank=True, verbose_name="API секрет")

    # Интеграции
    google_analytics = models.BooleanField(default=False, verbose_name="Google Analytics")
    google_analytics_id = models.CharField(max_length=50, blank=True, verbose_name="GA ID")

    yandex_metrika = models.BooleanField(default=False, verbose_name="Яндекс.Метрика")
    yandex_metrika_id = models.CharField(max_length=50, blank=True, verbose_name="YM ID")

    # Автоматизация
    auto_export_orders = models.BooleanField(default=False, verbose_name="Автоэкспорт заказов")
    export_format = models.CharField(
        max_length=10,
        choices=[
            ('csv', 'CSV'),
            ('json', 'JSON'),
            ('xml', 'XML')
        ],
        default='csv',
        verbose_name="Формат экспорта"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Интеграция продавца"
        verbose_name_plural = "Интеграции продавцов"


class SellerNotification(models.Model):
    """История уведомлений продавца"""
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    message = models.TextField(verbose_name="Сообщение")
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Информация'),
            ('warning', 'Предупреждение'),
            ('error', 'Ошибка'),
            ('success', 'Успех')
        ],
        default='info'
    )
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление продавца"
        verbose_name_plural = "Уведомления продавцов"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.seller.company_name}"


