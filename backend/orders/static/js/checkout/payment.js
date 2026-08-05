class PaymentProcessor {
    constructor() {
        this.paymentMethod = null;
        this.initEventListeners();
    }

    initEventListeners() {
        document.getElementById('submitOrderBtn').addEventListener('click', this.handleOrderSubmit.bind(this));
        document.querySelectorAll('input[name="paymentMethod"]').forEach(radio => {
            radio.addEventListener('change', this.handlePaymentMethodChange.bind(this));
        });
    }

    handlePaymentMethodChange(e) {
        this.paymentMethod = e.target.id;
    }

    async handleOrderSubmit() {
        if (!this.validateForm()) return;

        try {
            const loader = new PaymentLoader();
            loader.show();

            if (this.paymentMethod === 'paymentCard') {
                await this.processCardPayment();
            } else if (this.paymentMethod === 'paymentSPB') {
                await this.processSBPPayment();
            }

            loader.hide();
        } catch (error) {
            console.error('Payment error:', error);
            new PaymentLoader().showError('Ошибка при обработке платежа');
        }
    }

    validateForm() {
        const validator = new FormValidator();
        return validator.validate();
    }

    async processCardPayment() {
        const formData = {
            order_id: window.orderId, // Должен быть установлен в шаблоне
            payment_method: 'card',
            card_number: document.getElementById('cardNumber').value,
        };

        const response = await fetch('/api/payment/process/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.status === 'succeeded') {
            window.location.href = `/order/success/${data.payment_id}/`;
        } else {
            throw new Error(data.message || 'Payment failed');
        }
    }

    async processSBPPayment() {
        return new Promise((resolve, reject) => {
            const modal = new bootstrap.Modal(document.getElementById('spbPaymentModal'));
            modal.show();

            // Имитация обработки платежа
            const checkInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/payment/status/${window.orderId}/`);
                    const data = await response.json();

                    if (data.status === 'succeeded') {
                        clearInterval(checkInterval);
                        modal.hide();
                        window.location.href = `/order/success/${data.payment_id}/`;
                        resolve();
                    }
                } catch (error) {
                    clearInterval(checkInterval);
                    reject(error);
                }
            }, 3000);

            modal._element.addEventListener('hidden.bs.modal', () => {
                clearInterval(checkInterval);
                reject(new Error('Payment canceled'));
            });
        });
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new PaymentProcessor();
});