from django.db import models
from django.conf import settings
from django.utils import timezone
from shop.models import Product


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        return f"Корзина {self.id} ({self.user or 'Гость'})"

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @classmethod
    def get_cart(cls, request):
        """Получает или создаёт корзину для пользователя/сессии"""
        if request.user.is_authenticated:
            cart, _ = cls.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, _ = cls.objects.get_or_create(session_key=request.session.session_key)
        return cart


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')   # предотвращает дубли

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    def total_price(self):
        return self.product.price * self.quantity
