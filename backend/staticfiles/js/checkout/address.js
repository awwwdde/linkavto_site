class AddressManager {
    constructor() {
        this.initMapModal();
        this.initEventListeners();
    }

    initEventListeners() {
        document.getElementById('addAddressBtn').addEventListener('click', this.handleAddAddressClick.bind(this));
    }

    initMapModal() {
        this.mapModal = new bootstrap.Modal(document.getElementById('addressMapModal'));

        // Инициализация карты (заглушка)
        this.mapModal._element.addEventListener('shown.bs.modal', () => {
            console.log('Map modal shown - initialize map here');
        });
    }

    handleAddAddressClick(e) {
        e.preventDefault();
        this.mapModal.show();
    }

    saveAddress(addressData) {
        // Логика сохранения адреса
        return fetch('/api/addresses/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify(addressData)
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AddressManager();
});