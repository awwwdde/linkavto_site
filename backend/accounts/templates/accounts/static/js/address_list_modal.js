class AddressListModal {
    constructor() {
        this.modalId = 'addressListModal';
        this.initModal();
        this.bindAddressActions();
        this.bindUpdateEvents();
    }

    initModal() {
        const modalElement = document.getElementById(this.modalId);
        if (modalElement) {
            // Принудительно обновляем при каждом открытии модалки
            modalElement.addEventListener('shown.bs.modal', () => {
                console.log('Modal shown, updating address list...');
                this.updateAddressList();
                this.updateAddressCounter();
            });

            // Дополнительно слушаем событие открытия модалки через Bootstrap API
            modalElement.addEventListener('show.bs.modal', () => {
                console.log('Modal show event, updating address list...');
                this.updateAddressList();
                this.updateAddressCounter();
            });

            // Также обновляем при клике на кнопку открытия модалки
            const openButtons = document.querySelectorAll('[data-bs-target="#addressListModal"]');
            openButtons.forEach(button => {
                button.addEventListener('click', () => {
                    console.log('Address list modal button clicked, will update...');
                    setTimeout(() => {
                        this.updateAddressList();
                        this.updateAddressCounter();
                    }, 100);
                });
            });

            const addAddressBtn = modalElement.querySelector('[data-bs-target="#addressMapModal"]');
            if (addAddressBtn) {
                addAddressBtn.addEventListener('click', () => {
                    const listModal = bootstrap.Modal.getInstance(modalElement);
                    if (listModal) {
                        listModal.hide();
                    }
                });
            }
        }
    }

    bindUpdateEvents() {
        document.addEventListener('addressUpdated', () => {
            // Обновляем список адресов только если модальное окно открыто
            const modal = document.getElementById(this.modalId);
            if (modal && modal.classList.contains('show')) {
                this.updateAddressList();
            }
            // Счетчик обновляем всегда
            this.updateAddressCounter();
        });
        
        // Дополнительно слушаем событие обновления адресов при любых изменениях
        document.addEventListener('addressListNeedsUpdate', () => {
            this.updateAddressList();
            this.updateAddressCounter();
        });

        // Глобальный обработчик для всех кнопок address-header-btn
        document.addEventListener('click', (e) => {
            if (e.target.closest('.address-header-btn')) {
                console.log('Address header button clicked via global handler');
                setTimeout(() => {
                    if (window.addressListModalInstance) {
                        window.addressListModalInstance.updateAddressList();
                        window.addressListModalInstance.updateAddressCounter();
                    } else {
                        console.error('AddressListModal instance not found in global handler!');
                        // Fallback - создаем временный экземпляр
                        const tempInstance = new AddressListModal();
                        tempInstance.updateAddressList();
                        tempInstance.updateAddressCounter();
                    }
                }, 100);
            }
        });
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

    async updateAddressList() {
        try {
            console.log('Updating address list...');
            const response = await fetch('/account/addresses/', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });
            if (!response.ok) throw new Error('Network response was not ok');

            const html = await response.text();
            console.log('Received HTML:', html);
            const addressList = document.querySelector(`#${this.modalId} .address-list`);

            if (addressList) {
                const scrollPos = addressList.scrollTop;
                addressList.innerHTML = html;
                addressList.scrollTop = scrollPos;
                this.closeAllDropdowns();
                console.log('Address list updated successfully');
            } else {
                console.error('Address list element not found');
            }

            // Обновляем счетчик после обновления списка
            this.updateAddressCounter();
        } catch (error) {
            console.error('Error updating address list:', error);
            this.showToast('Не удалось загрузить список адресов', 'error');
        }
    }

    async updateAddressCounter() {
        try {
            const response = await fetch('/account/get_addresses_count/');
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            const count = data.count || 0;

            const addressBadge = document.querySelector('a[aria-label="Мои адреса"] .badge');
            const addressLink = document.querySelector('a[aria-label="Мои адреса"]');

            if (count > 0) {
                if (addressBadge) {
                    addressBadge.textContent = count;
                } else {
                    const badge = document.createElement('span');
                    badge.className = 'badge bg-primary rounded-pill float-end';
                    badge.textContent = count;
                    addressLink.appendChild(badge);
                }
            } else if (addressBadge) {
                addressBadge.remove();
            }
        } catch (error) {
            console.error('Error updating address counter:', error);
        }
    }

    closeAllDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        dropdowns.forEach(dropdown => {
            const instance = bootstrap.Dropdown.getInstance(dropdown);
            if (instance) instance.hide();
        });
    }

    bindAddressActions() {
        document.addEventListener('click', (e) => {
            const setDefaultBtn = e.target.closest('.set-default-btn');
            if (setDefaultBtn) {
                e.preventDefault();
                e.stopPropagation();
                const addressId = setDefaultBtn.dataset.addressId;
                this.setDefaultAddress(addressId);
                return;
            }

            const deleteBtn = e.target.closest('.delete-address-btn');
            if (deleteBtn) {
                e.preventDefault();
                e.stopPropagation();
                const addressId = deleteBtn.dataset.addressId;
                this.deleteAddress(addressId);
                return;
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

            await this.updateAddressList();
            this.showToast('Основной адрес изменён', 'success');
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

            await this.updateAddressList();
            this.showToast('Адрес удалён', 'success');
        } catch (error) {
            console.error('Error deleting address:', error);
            this.showToast('Не удалось удалить адрес', 'error');
        }
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

document.addEventListener('DOMContentLoaded', () => {
    window.addressListModalInstance = new AddressListModal();
});