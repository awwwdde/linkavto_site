def create_order_from_cart(cart, cleaned_data):
    order = Order.objects.create(
        user=cart.user,
        total=cart.get_total(),
        **cleaned_data
    )

    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price  # Фиксируем цену
        )
    return order