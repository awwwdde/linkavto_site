function setupFavorites() {
    const FAVORITE_ICON_SELECTOR = '#favorite-icon';
    const BADGE_SELECTOR = '.favorite-badge';

    // Обновление UI избранного
    function updateFavoriteUI(hasFavorites) {
        const icon = document.querySelector(FAVORITE_ICON_SELECTOR);
        const container = icon?.parentElement;
        if (!icon || !container) return;

        let badge = container.querySelector(BADGE_SELECTOR);

        if (hasFavorites) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'favorite-badge';
                badge.innerHTML = '<span class="visually-hidden">Есть избранные товары</span>';
                container.appendChild(badge);
            }
            icon.classList.add('favorite-active');
        } else {
            if (badge) badge.remove();
            icon.classList.remove('favorite-active');
        }
    }

    // Проверка состояния избранного
    function checkFavorites() {
        // Получаем URL из data-атрибута body
        const url = document.body.dataset.favoritesStatusUrl || `${APP_URL}favorites/status/`;

        return fetch(url, {
            credentials: 'include',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            updateFavoriteUI(data.has_favorites);
            return data;
        })
        .catch(error => {
            console.error('Ошибка при проверке избранного:', error);
            return { has_favorites: false };
        });
    }

    // Глобальная функция для обновления
    window.updateFavorites = checkFavorites;

    // Инициализация
    checkFavorites();

    // Событие для обновления из других модулей
    document.addEventListener('favoritesUpdated', () => checkFavorites());
}

document.addEventListener('DOMContentLoaded', setupFavorites);