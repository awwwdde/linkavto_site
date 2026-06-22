class CheckoutManager {
    constructor() {
        this.initEventListeners();
    }

    initEventListeners() {
        const checkoutButton = document.getElementById('checkoutButton');
        if (checkoutButton) {
            checkoutButton.addEventListener('click', this.handleCheckoutClick.bind(this));
        }
    }

    handleCheckoutClick(event) {
        {% if not user.is_authenticated %}
            event.preventDefault();
            const authModalElement = document.getElementById('authModal');
            if (authModalElement) {
                const authModal = bootstrap.Modal.getOrCreateInstance(authModalElement, {
                    backdrop: true,
                    keyboard: true
                });
                authModal.show();
            }
        {% endif %}
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new CheckoutManager();
});