class CartManager {
    constructor() {
        this.initEventListeners();
    }

    initEventListeners() {
        // Обработка кнопок "+" и "-"
        document.querySelectorAll('.quantity-btn').forEach(btn => {
            btn.addEventListener('click', this.handleQuantityButtonClick.bind(this));
        });

        // Обработка ручного ввода количества
        document.querySelectorAll('.quantity-input').forEach(input => {
            input.addEventListener('change', this.handleQuantityInputChange.bind(this));
        });
    }

    handleQuantityButtonClick(event) {
        const button = event.currentTarget;
        const productId = button.dataset.productId;
        const input = document.querySelector(`.quantity-input[data-product-id="${productId}"]`);
        let quantity = parseInt(input.value);

        if (button.classList.contains('increase')) {
            quantity += 1;
        } else if (button.classList.contains('decrease') && quantity > 1) {
            quantity -= 1;
        }

        input.value = quantity;
        this.updateCartItem(productId, quantity);
    }

    handleQuantityInputChange(event) {
        const input = event.currentTarget;
        const productId = input.dataset.productId;
        const quantity = parseInt(input.value) || 1;
        input.value = quantity;
        this.updateCartItem(productId, quantity);
    }

    async updateCartItem(productId, quantity) {
        const totalElement = document.querySelector(`.item-total[data-product-id="${productId}"]`);
        totalElement.classList.add('updating');

        try {
            const response = await fetch(`/cart/update/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 'quantity': quantity })
            });

            const data = await response.json();

            if (data.success) {
                totalElement.textContent = data.item_total + ' ₽';
                this.updateCartTotals(data);

                if (data.new_quantity <= 0) {
                    this.removeCartItem(productId);
                }
            }
        } catch (error) {
            console.error('Error:', error);
        } finally {
            totalElement.classList.remove('updating');
        }
    }

    updateCartTotals(data) {
        document.querySelectorAll('.cart-total-quantity').forEach(el => {
            el.textContent = data.total_quantity;
        });

        document.querySelectorAll('.cart-total-price').forEach(el => {
            el.textContent = data.total_price + ' ₽';
        });
    }

    removeCartItem(productId) {
        const row = document.querySelector(`tr[data-product-id="${productId}"]`);
        if (row) {
            row.style.transition = 'opacity 0.3s';
            row.style.opacity = '0';
            setTimeout(() => row.remove(), 300);
        }
    }

    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new CartManager();
});