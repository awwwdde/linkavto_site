class Dashboard {
    constructor() {
        this.initPhoneMask();
        this.initAddressHandlers();
        this.initPasswordReset();
        this.initModals();
    }

    initPhoneMask() {
        if (document.getElementById('id_phone')) {
            Inputmask({
                mask: "(999) 999-99-99",
                placeholder: "_",
                showMaskOnHover: false,
                showMaskOnFocus: true,
            }).mask(document.getElementById('id_phone'));
        }
    }

    initAddressHandlers() {
        // Обработчик сохранения адреса
        document.getElementById('confirmAddress')?.addEventListener('click', this.saveAddress.bind(this));

        // При открытии модального окна адресов обновляем список
        document.getElementById('addressListModal')?.addEventListener('shown.bs.modal', () => {
            console.log('Dashboard: Address list modal shown, updating...');
            if (window.addressListModalInstance) {
                window.addressListModalInstance.updateAddressList();
                window.addressListModalInstance.updateAddressCounter();
            } else {
                console.error('AddressListModal instance not found in dashboard!');
                // Fallback - обновляем напрямую
                this.updateAddressList();
            }
        });

        // Инициализация обработчиков при загрузке
        this.attachAddressEvents();
    }

    initPasswordReset() {
        const sendCodeBtn = document.getElementById('sendCodeBtn');
        if (sendCodeBtn) {
            sendCodeBtn.addEventListener('click', this.sendPasswordCode.bind(this));
        }
    }

    initModals() {
        // Bootstrap автоматически обрабатывает [data-bs-toggle="modal"],
        // поэтому не нужно добавлять дополнительные обработчики
        // Это предотвращает двойное открытие модальных окон и создание дубликатов backdrop
    }

    async sendPasswordCode() {
        try {
            const response = await fetch("{% url 'accounts:send_password_code' %}", {
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}',
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                document.getElementById('send-code-step').classList.add('d-none');
                document.getElementById('enter-code-step').classList.remove('d-none');
            } else {
                this.showToast(data.error || 'Ошибка при отправке кода', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Произошла ошибка', 'error');
        }
    }

    async saveAddress() {
        const address = document.getElementById('exactAddress').value;
        const postalCode = document.getElementById('postalCode').value;
        const flat = document.getElementById('flatNumber').value;
        const comment = document.getElementById('deliveryComment').value;

        if (!address) {
            this.showToast('Пожалуйста, укажите адрес', 'error');
            return;
        }

        const fullAddress = address + (flat ? ', кв. ' + flat : '');

        try {
            const response = await fetch("{% url 'accounts:save_address' %}", {
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    address: fullAddress,
                    postal_code: postalCode,
                    comment: comment
                })
            });

            const data = await response.json();

            if (data.success) {
                // Закрываем модальное окно карты
                const mapModal = bootstrap.Modal.getInstance(document.getElementById('addressMapModal'));
                mapModal.hide();

                // Обновляем список адресов
                await this.updateAddressList();

                // Показываем уведомление
                this.showToast('Адрес успешно сохранён!', 'success');
            } else {
                this.showToast(data.error || 'Ошибка при сохранении адреса', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Произошла ошибка', 'error');
        }
    }

    async updateAddressList() {
        try {
            const response = await fetch("{% url 'accounts:get_addresses' %}");
            const html = await response.text();
            document.getElementById('addressList').innerHTML = html;
            this.attachAddressEvents();
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Не удалось загрузить список адресов', 'error');
        }
    }

    attachAddressEvents() {
        // Установка адреса по умолчанию
        document.querySelectorAll('.set-default-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const addressId = btn.dataset.addressId;
                try {
                    const response = await fetch(`/account/set_default_address/${addressId}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': '{{ csrf_token }}'
                        }
                    });

                    const data = await response.json();

                    if (data.success) {
                        await this.updateAddressList();
                        this.showToast('Основной адрес изменён', 'success');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    this.showToast('Не удалось изменить основной адрес', 'error');
                }
            });
        });

        // Удаление адреса
        document.querySelectorAll('.delete-address-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (confirm('Вы уверены, что хотите удалить этот адрес?')) {
                    const addressId = btn.dataset.addressId;
                    try {
                        const response = await fetch(`/account/delete_address/${addressId}/`, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': '{{ csrf_token }}'
                            }
                        });

                        const data = await response.json();

                        if (data.success) {
                            await this.updateAddressList();
                            this.showToast('Адрес удалён', 'success');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        this.showToast('Не удалось удалить адрес', 'error');
                    }
                }
            });
        });
    }

    showToast(message, type = 'info') {
        // Реализация toast-уведомлений
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        const toast = document.createElement('div');

        toast.className = `toast show align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
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

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
    
    // Создаем экземпляр AddressListModal если он еще не создан
    if (!window.addressListModalInstance) {
        console.log('Creating AddressListModal instance in dashboard...');
        // Импортируем класс AddressListModal
        if (typeof AddressListModal !== 'undefined') {
            window.addressListModalInstance = new AddressListModal();
        } else {
            console.error('AddressListModal class not found!');
        }
    }
});