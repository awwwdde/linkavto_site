
from django.shortcuts import render, redirect
from cart.utils import get_cart  # Ваша функция для получения корзины


def checkout_view(request):
    cart = get_cart(request)
    if not cart.items.exists():
        return redirect('cart:detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = create_order_from_cart(cart, form.cleaned_data)
            cart.clear()
            return redirect('orders:success', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, 'checkout/checkout.html', {'form': form})