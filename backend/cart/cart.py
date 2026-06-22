class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart_key = 'cart'  # Добавляем определение cart_key
        cart = self.session.get(self.cart_key)
        if not cart:
            cart = self.session[self.cart_key] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        """
        Добавляет товар в корзину или обновляет его количество
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}

        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def save(self):
        """Сохраняет изменения в сессии"""
        self.session.modified = True

    def remove(self, product):
        """Удаляет товар из корзины"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        """Полностью очищает корзину"""
        if self.cart_key in self.session:
            del self.session[self.cart_key]
            self.save()

    def __iter__(self):
        """Итератор по товарам в корзине"""
        from shop.models import Product
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            self.cart[str(product.id)]['product'] = product

        for item in self.cart.values():
            item['price'] = float(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Общее количество товаров в корзине"""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Общая стоимость корзины"""
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())