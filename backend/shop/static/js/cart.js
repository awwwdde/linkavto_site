// Унифицированный обработчик ошибок
function handleFetchError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    showToast(`Ошибка ${context}`, 'danger');
    return Promise.reject(error);
}

// Обновленный обработчик корзины
function setupCart() {
    // Обновление бейджа корзины
    function updateCartBadge(count) {
        const badge = document.getElementById('cart-badge');
        if (!badge) return;

        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
        badge.classList.add('pulse');
        setTimeout(() => badge.classList.remove('pulse'), 500);
    }

    // Показ уведомлений
    function showToast(message, type = 'success') {
        // Реализация с использованием Toast из Bootstrap
        const toastEl = document.getElementById('cart-toast');
        if (!toastEl) return;

        toastEl.querySelector('.toast-body').textContent = message;
        toastEl.classList.remove('bg-success', 'bg-danger');
        toastEl.classList.add(`bg-${type}`);

        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }

    // Обработчик добавления в корзину
    function handleAddToCart(e) {
        e.preventDefault();
        const button = e.currentTarget;
        const { productId, quantity = 1 } = button.dataset;

        // Сохраняем исходное состояние
        const originalHTML = button.innerHTML;
        
        // Сразу меняем кнопку на "В корзине" как на мобильной версии
        button.classList.remove('btn-primary');
        button.classList.add('btn-cart-success');
        button.innerHTML = '<i class="bi bi-cart-check me-2"></i> В корзине';

        fetch(`/cart/add/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                quantity: quantity,
                override_quantity: button.dataset.override || false
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                updateCartBadge(data.total_items);
                showToast('Товар добавлен в корзину!', 'success');

                // Отправляем событие для других модулей
                document.dispatchEvent(new CustomEvent('cartUpdated', {
                    detail: { totalItems: data.total_items }
                }));
            } else {
                // Откат при ошибке
                button.classList.remove('btn-cart-success');
                button.classList.add('btn-primary');
                button.innerHTML = originalHTML;
                showToast(data.message || 'Произошла ошибка', 'danger');
            }
        })
        .catch(error => {
            // Откат при ошибке
            button.classList.remove('btn-cart-success');
            button.classList.add('btn-primary');
            button.innerHTML = originalHTML;
            handleFetchError(error, 'добавления в корзину');
        });
    }

    // Инициализация
    document.querySelectorAll('.add-to-cart').forEach(btn => {
        btn.addEventListener('click', handleAddToCart);
    });

    // Загрузка начального состояния
    fetch(`${APP_URL}cart/count/`)
        .then(response => response.json())
        .then(data => updateCartBadge(data.count))
        //.catch(error => handleFetchError(error, 'получения количества товаров'));

    // Синхронизация между вкладками
    window.addEventListener('storage', event => {
        if (event.key === 'cart_updated') {
            updateCartBadge(JSON.parse(event.newValue).total_items);
        }
    });
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', setupCart);