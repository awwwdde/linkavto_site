class PaymentLoader {
    constructor() {
        this.loader = document.getElementById('paymentLoader');
        this.progressElement = document.getElementById('loaderProgress');
        this.spinner = this.loader.querySelector('.loader-spinner');
        this.textElement = this.loader.querySelector('.loader-text');
        this.progress = 0;
        this.progressInterval = null;
    }

    show() {
        this.loader.style.display = 'flex';
        this.startProgressAnimation();
    }

    hide() {
        this.stopProgressAnimation();
        this.loader.style.display = 'none';
    }

    showError(message) {
        this.stopProgressAnimation();
        this.spinner.style.borderTopColor = '#e74c3c';
        this.textElement.textContent = message;
        this.progressElement.textContent = 'Попробуйте снова';

        setTimeout(() => {
            this.hide();
        }, 3000);
    }

    startProgressAnimation() {
        this.progress = 0;
        this.progressInterval = setInterval(() => {
            this.progress += Math.random() * 10;
            if (this.progress > 100) this.progress = 100;
            this.progressElement.textContent = `${Math.floor(this.progress)}%`;
            this.progressElement.style.animation = 'progressPulse 1s infinite';
        }, 300);
    }

    stopProgressAnimation() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
}