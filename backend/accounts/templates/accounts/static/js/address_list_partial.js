class AddressListPartial {
    constructor() {
        this.init();
    }

    init() {
        this.bindAddressActions();
    }

    bindAddressActions() {
        const addressList = document.querySelector('#addressListModal .address-list');
        if (!addressList) return;

        addressList.addEventListener('click', (e) => {
            const setDefaultBtn = e.target.closest('.set-default-btn');
            if (setDefaultBtn) {
                e.preventDefault();
                const addressId = setDefaultBtn.dataset.addressId;
                this.setDefaultAddress(addressId);
                return;
            }

            const deleteBtn = e.target.closest('.delete-address-btn');
            if (deleteBtn) {
                e.preventDefault();
                const addressId = deleteBtn.dataset.addressId;
                this.deleteAddress(addressId);
            }
        });
    }

    async setDefaultAddress(addressId) {
        try {
            const response = await fetch(`/account/set_default_address/${addressId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Unknown error');
            }

            this.showToast('Основной адрес изменён', 'success');
            this.updateAddressList();
        } catch (error) {
            console.error('Error setting default address:', error);
            this.showToast('Не удалось изменить основной адрес', 'error');
        }
    }

    async deleteAddress(addressId) {
        if (!confirm('Вы уверены, что хотите удалить этот адрес?')) return;

        try {
            const response = await fetch(`/account/delete_address/${addressId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Unknown error');
            }

            this.showToast('Адрес удалён', 'success');
            this.updateAddressList();
        } catch (error) {
            console.error('Error deleting address:', error);
            this.showToast('Не удалось удалить адрес', 'error');
        }
    }

    async updateAddressList() {
        try {
            const response = await fetch('/account/addresses/');
            if (!response.ok) throw new Error('Network response was not ok');

            const html = await response.text();
            const addressList = document.querySelector('#addressListModal .address-list');

            if (addressList) {
                const scrollPos = addressList.scrollTop;
                addressList.innerHTML = html;
                addressList.scrollTop = scrollPos;
            }
        } catch (error) {
            console.error('Error updating address list:', error);
            this.showToast('Не удалось обновить список адресов', 'error');
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        const toast = document.createElement('div');

        toast.className = `toast show align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Закрыть"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
        return container;
    }
}

// Инициализация
if (document.querySelector('#addressListModal .address-list'))