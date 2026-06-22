class FavoriteManager {
    constructor() {
        this.initEventListeners();
        this.checkFavoritesOnLoad();
    }

    initEventListeners() {
        document.querySelectorAll('.wishlist-btn').forEach(btn => {
            btn.addEventListener('click', this.handleFavoriteClick.bind(this));
        });
    }

    async checkFavoritesOnLoad() {
        try {
            const response = await fetch('/favorites/ids/');
            const data = await response.json();

            data.favorite_ids.forEach(productId => {
                const icon = document.querySelector(`.wishlist-btn[data-product-id="${productId}"] i`);
                if (icon) {
                    icon.classList.remove('bi-heart');
                    icon.classList.add('bi-heart-fill', 'text-danger');
                }
            });
        } catch (error) {
            console.error('Error checking favorites:', error);
        }
    }

    handleFavoriteClick(event) {
        const button = event.currentTarget;
        const productId = button.dataset.productId;
        const icon = button.querySelector('i');

        if (!this.isUserAuthenticated()) {
            this.showAuthModal();
            return;
        }

        this.toggleFavorite(icon, productId);
    }

    isUserAuthenticated() {
        return {% if user.is_authenticated %}true{% else %}false{% endif %};
    }

    showAuthModal() {
        const authModal = new bootstrap.Modal(document.getElementById('authModal'));
        authModal.show();

        const nextUrl = window.location.pathname;
        const loginForm = document.querySelector('#authModal form[action*="login"]');
        if (loginForm) {
            let nextInput = loginForm.querySelector('input[name="next"]');
            if (!nextInput) {
                nextInput = document.createElement('input');
                nextInput.type = 'hidden';
                nextInput.name = 'next';
                loginForm.appendChild(nextInput);
            }
            nextInput.value = nextUrl;
        }
    }

    async toggleFavorite(icon, productId) {
        try {
            const response = await fetch(`/favorites/toggle/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success) {
                if (data.is_favorite) {
                    icon.classList.remove('bi-heart');
                    icon.classList.add('bi-heart-fill', 'text-danger');
                } else {
                    icon.classList.remove('bi-heart-fill', 'text-danger');
                    icon.classList.add('bi-heart');
                }


            } else if (data.action === 'auth_required') {
                window.location.href = '/accounts/login/?next=' + window.location.pathname;
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    showToast(message) {
        // Реализация toast-уведомлений
        console.log(message); // Замените на реальную реализацию
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
    new FavoriteManager();
});