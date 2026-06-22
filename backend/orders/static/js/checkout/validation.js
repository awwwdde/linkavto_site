class FormValidator {
    validate() {
        if (!this.validateTermsAgreement()) {
            this.showError('Пожалуйста, подтвердите согласие с условиями покупки');
            return false;
        }

        if (!this.validatePaymentMethod()) {
            this.showError('Пожалуйста, выберите способ оплаты');
            return false;
        }

        return true;
    }

    validateTermsAgreement() {
        return document.getElementById('agreeTerms').checked;
    }

    validatePaymentMethod() {
        return document.querySelector('input[name="paymentMethod"]:checked') !== null;
    }

    showError(message) {
        // Можно заменить на красивый toast или модальное окно
        alert(message);
    }
}