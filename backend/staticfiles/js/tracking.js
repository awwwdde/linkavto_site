class ProductTracker {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Отслеживание кликов по товарам
        document.addEventListener('click', (e) => {
            const productLink = e.target.closest('a[href*="/product/"]');
            if (productLink) {
                const productId = this.extractProductId(productLink.href);
                if (productId) {
                    this.trackClick(productId);
                }
            }
        });

        // Отслеживание добавления в корзину
        document.addEventListener('click', (e) => {
            const cartButton = e.target.closest('.add-to-cart');
            if (cartButton) {
                const productId = cartButton.dataset.productId;
                this.trackCartAdd(productId);
            }
        });
    }

    extractProductId(url) {
        const match = url.match(/product\/([^\/]+)/);
        return match ? match[1] : null;
    }

    trackClick(productId) {
        fetch('/track/click/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ product_id: productId })
        }).catch(console.error);
    }

    trackCartAdd(productId) {
        fetch('/track/cart-add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ product_id: productId })
        }).catch(console.error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.productTracker = new ProductTracker();
});