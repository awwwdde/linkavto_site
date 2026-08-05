function setupOrders() {
    const PULSE_ANIMATION_DURATION = 500;

    // Обновление счетчика заказов
    function updateOrdersCount(count) {
        const badge = document.getElementById('orders-badge');
        if (!badge) return;

        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';

        if (count > 0) {
            badge.classList.add('pulse-animation');
            setTimeout(() => {
                badge.classList.remove('pulse-animation');
            }, PULSE_ANIMATION_DURATION);
        }
    }

    // Загрузка количества заказов
    function loadOrdersCount() {
        if (typeof window.USER_IS_AUTHENTICATED !== 'undefined' && window.USER_IS_AUTHENTICATED && window.ORDERS_COUNT_URL) {
            fetch(window.ORDERS_COUNT_URL, {
                credentials: 'include'
            })
            .then(response => response.json())
            .then(data => updateOrdersCount(data.count))
            .catch(error => console.error('Ошибка получения количества заказов:', error));
        }
    }

    // Обработчик клика по кнопке заказов
    function handleOrdersClick(e) {
        const ordersLink = e.currentTarget;

        if (ordersLink.classList.contains('auth-btn')) {
            const loginForm = document.querySelector('#authModal form[action*="login"]');
            if (loginForm) {
                const nextInput = document.createElement('input');
                nextInput.type = 'hidden';
                nextInput.name = 'next';
                nextInput.value = (window.ORDERS_MY_ORDERS_URL || '/orders/');
                loginForm.appendChild(nextInput);
            }
        }
    }

    // Инициализация
    function init() {
        loadOrdersCount();

        const ordersLink = document.getElementById('orders-link');
        if (ordersLink) {
            ordersLink.addEventListener('click', handleOrdersClick);
        }

        // Слушаем события создания заказов
        document.addEventListener('orderCreated', e => {
            updateOrdersCount(e.detail.count);
        });
    }

    init();
}

document.addEventListener('DOMContentLoaded', setupOrders);