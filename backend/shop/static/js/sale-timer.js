class SaleTimer {
    constructor() {
        this.timers = new Map();
        this.initTimers();
    }

    initTimers() {
        document.querySelectorAll('.sale-countdown').forEach(element => {
            const endTime = parseInt(element.dataset.endTime);
            if (endTime > 0) {
                this.startTimer(element, endTime);
            }
        });
    }

    startTimer(element, endTime) {
        const updateTimer = () => {
            const now = Math.floor(Date.now() / 1000);
            const remaining = endTime - now;

            if (remaining <= 0) {
                element.textContent = 'Акция завершена';
                element.closest('.sale-timer')?.remove();
                return;
            }

            const days = Math.floor(remaining / 86400);
            const hours = Math.floor((remaining % 86400) / 3600);
            const minutes = Math.floor((remaining % 3600) / 60);

            let text = '';
            if (days > 0) text += `${days}д `;
            if (hours > 0) text += `${hours}ч `;
            text += `${minutes}м`;

            element.textContent = `Осталось: ${text}`;
        };

        updateTimer();
        const interval = setInterval(updateTimer, 60000); // Обновляем каждую минуту
        this.timers.set(element, interval);
    }

    destroy() {
        this.timers.forEach(interval => clearInterval(interval));
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.saleTimer = new SaleTimer();
});