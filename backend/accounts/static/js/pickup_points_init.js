/**
 * Дополнительные функции для инициализации пунктов выдачи
 */

// Функция инициализации чекбоксов служб доставки
function initDeliveryProvidersCheckboxes() {
    const checkboxes = document.querySelectorAll('#deliveryServiceSelection input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Собираем выбранные провайдеры
            const selectedProviders = [];
            checkboxes.forEach(cb => {
                if (cb.checked) {
                    selectedProviders.push(cb.value);
                }
            });
            
            // Фильтруем пункты выдачи по выбранным провайдерам
            if (window.pickupPointsManager) {
                const allPoints = window.pickupPointsManager.pickupPoints;
                const filteredPoints = allPoints.filter(point => 
                    selectedProviders.includes(point.provider)
                );
                window.pickupPointsManager.displayPickupPoints(filteredPoints);
            }
        });
    });
}

// Обработчик события выбора пункта выдачи
document.addEventListener('pickupPointSelected', function(e) {
    const point = e.detail.point;
    console.log('Пункт выдачи выбран:', point);
    
    // Сохраняем выбранный пункт глобально
    window.selectedPickupPoint = point;
    
    // Обновляем поле адреса
    const addressInput = document.getElementById('addressInput');
    if (addressInput) {
        addressInput.value = `${point.provider_name}: ${point.name}, ${point.address}`;
    }
});

// Модифицированная функция сохранения адреса с учетом пункта выдачи
function saveAddressWithPickupPoint() {
    const addressInput = document.getElementById('addressInput');
    const deliveryTypeToggle = document.querySelector('input[name="deliveryType"]:checked');
    
    if (!addressInput) {
        alert('Пожалуйста, укажите адрес');
        return;
    }

    const address = addressInput.value.trim();
    const deliveryType = deliveryTypeToggle ? deliveryTypeToggle.value : 'delivery';

    if (!address) {
        alert('Пожалуйста, укажите адрес');
        return;
    }
    
    // Проверяем, выбран ли пункт выдачи при самовывозе
    if (deliveryType === 'pickup' && !window.selectedPickupPoint) {
        alert('Пожалуйста, выберите пункт выдачи на карте');
        return;
    }

    // Формируем данные для отправки
    const requestData = {
        address: address,
        delivery_type: deliveryType
    };
    
    // Добавляем данные пункта выдачи если это самовывоз
    if (deliveryType === 'pickup' && window.selectedPickupPoint) {
        const point = window.selectedPickupPoint;
        requestData.pickup_provider = point.provider;
        requestData.pickup_point_code = point.code;
        requestData.pickup_point_name = point.name;
        requestData.latitude = point.latitude;
        requestData.longitude = point.longitude;
    }

    fetch(document.querySelector('[name="csrfmiddlewaretoken"]')?.closest('form')?.action || '/accounts/save_address/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (response.status === 403) {
            window.location.href = '/accounts/login/?next=' + window.location.pathname;
            return Promise.reject();
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            const selectedAddress = {
                id: data.address_id || null,
                title: data.title || '',
                full_address: address,
                delivery_type: deliveryType,
                pickup_provider: requestData.pickup_provider || null,
                pickup_point_name: requestData.pickup_point_name || null,
                is_default: true
            };

            // Отправляем событие с данными адреса
            document.dispatchEvent(new CustomEvent('addressSelected', {
                detail: selectedAddress
            }));

            const modalElement = document.getElementById('addressMapModal');
            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
            modal.hide();

            // Показываем уведомление
            if (typeof showSuccessNotification === 'function') {
                showSuccessNotification('Адрес успешно добавлен!');
            }

            modalElement.addEventListener('hidden.bs.modal', () => {
                document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
                document.body.classList.remove('modal-open');
                document.body.style.removeProperty('padding-right');
            }, { once: true });
            
            // Очищаем выбранный пункт
            window.selectedPickupPoint = null;
        } else {
            alert('Ошибка: ' + (data?.error || 'Неизвестная ошибка'));
        }
    })
    .catch(err => console.error(err));
}

// Функция получения CSRF токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(cookie => {
            const c = cookie.trim();
            if (c.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}

// Переопределяем обработчик кнопки сохранения
document.addEventListener('DOMContentLoaded', function() {
    // Удаляем старый обработчик и добавляем новый
    const confirmBtn = document.getElementById('confirmAddress');
    if (confirmBtn) {
        // Клонируем кнопку чтобы удалить все обработчики
        const newBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
        
        // Добавляем новый обработчик
        newBtn.addEventListener('click', saveAddressWithPickupPoint);
    }
});

// Экспортируем функции
window.initDeliveryProvidersCheckboxes = initDeliveryProvidersCheckboxes;
window.saveAddressWithPickupPoint = saveAddressWithPickupPoint;

