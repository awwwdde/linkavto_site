/**
 * Модуль управления модальным окном выбора адреса на Яндекс.Карте
 * Поддерживает режимы: доставка курьером и самовывоз (ПВЗ)
 * 
 * Скрипт загружается глобально через base.html (один раз)
 */

// ======================= Глобальные переменные =======================
let yandexMap = null;
let yandexPlacemark = null;
let selectedPickupPoint = null;
let selectedDeliveryGeoObject = null; // Сохраняем geoObject для адреса доставки
let currentProvider = 'russian_post';
let pickupPointsManager = null;
let pendingPickupLoad = null; // Провайдер для отложенной загрузки точек (если карта ещё не готова)

// ======================= Управление лоадером карты =======================
function showMapLoader() {
    const overlay = document.getElementById('mapLoadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
        overlay.classList.add('active');
    }
}

function hideMapLoader() {
    const overlay = document.getElementById('mapLoadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
        overlay.classList.remove('active');
    }
}

// ======================= Инициализация карты =======================
function initYandexMap() {
    // Если API ещё не загружен — загружаем его сначала
    if (typeof ymaps === 'undefined') {
        if (typeof window.loadYandexMapsAPI === 'function') {
            window.loadYandexMapsAPI(function() {
                initYandexMap(); // Повторно вызываем после загрузки
            });
        } else {
            console.error('❌ Функция loadYandexMapsAPI не найдена');
        }
        return;
    }
  
    ymaps.ready(() => {
        if (!document.getElementById('yandexMap')) return;
        if (yandexMap) yandexMap.destroy();

        // Получаем геолокацию пользователя
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const userLat = position.coords.latitude;
                    const userLon = position.coords.longitude;
                    initMapWithLocation(userLat, userLon);
                },
                (error) => {
                    // Детальная обработка ошибок геолокации
                    let errorMsg = '';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMsg = 'Пользователь отклонил запрос геолокации';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMsg = 'Информация о местоположении недоступна';
                            break;
                        case error.TIMEOUT:
                            errorMsg = 'Превышено время ожидания запроса';
                            break;
                        default:
                            errorMsg = 'Неизвестная ошибка';
                    }
                    console.warn('⚠️ Не удалось получить геолокацию:', errorMsg, error);
                    initMapWithLocation(55.751574, 37.573856); // Москва по умолчанию
                },
                {
                    enableHighAccuracy: false, // false для быстрого ответа
                    timeout: 15000, // 15 секунд
                    maximumAge: 300000 // Кэшировать на 5 минут
                }
            );
        } else {
            console.warn('⚠️ Геолокация не поддерживается браузером');
            initMapWithLocation(55.751574, 37.573856);
        }
    });
}

// Инициализация карты с заданными координатами
function initMapWithLocation(lat, lon) {
    // Если карта уже существует — просто центрируем
    if (yandexMap) {
        yandexMap.setCenter([lat, lon], 12);
        yandexMap.container.fitToViewport();
        hideMapLoader();
        return;
    }
    
    
    yandexMap = new ymaps.Map('yandexMap', {
        center: [lat, lon],
        zoom: 12,
        controls: ['zoomControl']
    });

    yandexMap.controls.get('zoomControl').options.set({
        size: 'small',
        position: { right: 10, top: 100 }
    });

    ['searchControl','trafficControl','typeSelector','fullscreenControl','rulerControl','geolocationControl']
        .forEach(c => yandexMap.controls.remove(c));

    // Обработчик клика на карту (только для режима доставки)
    yandexMap.events.add('click', e => {
        const deliveryTypePickup = document.getElementById('deliveryTypePickup');
        if (!deliveryTypePickup || !deliveryTypePickup.checked) {
            const coords = e.get('coords');
            ymaps.geocode(coords).then(res => updateAddressFromGeoObject(res.geoObjects.get(0)));
        }
    });

    // Пересчитываем размеры карты после инициализации
    setTimeout(() => {
        yandexMap.container.fitToViewport();
        // Скрываем лоадер после инициализации карты
        hideMapLoader();
    }, 100);

    // Инициализируем менеджер точек ПВЗ
    if (typeof PickupPointsManager !== 'undefined') {
        pickupPointsManager = new PickupPointsManager(yandexMap);
        window.pickupPointsManager = pickupPointsManager;
        
        // Переменные для отслеживания изменений карты
        let lastCenter = null;
        let lastZoom = null;
        
        // Обработчик изменения границ карты для перезагрузки точек при перемещении
        yandexMap.events.add('boundschange', function() {
            const deliveryTypePickup = document.getElementById('deliveryTypePickup');
            if (deliveryTypePickup && deliveryTypePickup.checked && currentProvider) {
                const newCenter = yandexMap.getCenter();
                const newZoom = yandexMap.getZoom();
                
                // Проверяем, достаточно ли изменилось положение для перезагрузки
                if (lastCenter && lastZoom !== null) {
                    const distance = Math.sqrt(
                        Math.pow(newCenter[0] - lastCenter[0], 2) + 
                        Math.pow(newCenter[1] - lastCenter[1], 2)
                    );
                    const zoomChanged = Math.abs(newZoom - lastZoom) >= 1;
                    
                    // Пропускаем мелкие изменения (порог зависит от текущего зума)
                    const threshold = 0.02 / Math.pow(2, newZoom - 10);
                    if (distance < threshold && !zoomChanged) {
                        return; // Слишком малое изменение, не загружаем
                    }
                }
                
                lastCenter = newCenter;
                lastZoom = newZoom;
                
                // Дебаунс для избежания слишком частых запросов
                // При отдалении (маленький зум) больше задержка, т.к. больше данных
                clearTimeout(window.boundsChangeTimeout);
                const debounceTime = newZoom < 11 ? 800 : 400;
                
                window.boundsChangeTimeout = setTimeout(() => {
                    loadPickupPoints(currentProvider);
                }, debounceTime);
            }
        });
        
        // Проверяем, была ли отложенная загрузка точек (если кликнули "Самовывоз" до готовности карты)
        if (pendingPickupLoad) {
            loadPickupPoints(pendingPickupLoad);
            pendingPickupLoad = null;
        }
    } else {
        console.error('❌ PickupPointsManager не загружен');
    }
}

// ======================= Загрузка точек ПВЗ =======================
async function loadPickupPoints(provider) {
    if (!yandexMap || !pickupPointsManager) {
        console.warn('Карта или менеджер точек не инициализированы');
        hideMapLoader();
        return;
    }
  
    try {
        const center = yandexMap.getCenter();
        const bounds = yandexMap.getBounds(); // [[lat1, lon1], [lat2, lon2]]
        const zoom = yandexMap.getZoom();
        const city = await getCityFromCoordinates(center[0], center[1]);
        
        // Загружаем точки через API
        const url = new URL('/account/api/pickup-points/', window.location.origin);
        url.searchParams.set('provider', provider);
        url.searchParams.set('city', city || 'Москва');
        url.searchParams.set('latitude', center[0]);
        url.searchParams.set('longitude', center[1]);
        url.searchParams.set('zoom', zoom); // Передаём zoom для расчёта количества точек
        
        // Передаём границы видимой области карты для вычисления радиуса
        if (bounds) {
            url.searchParams.set('bounds', JSON.stringify(bounds));
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Проверяем формат ответа
        let points = [];
        if (data.success && data.points && Array.isArray(data.points)) {
            points = data.points;
        } else if (Array.isArray(data)) {
            points = data;
        }
        
        if (points.length > 0) {
            // Добавляем новые точки на карту с указанием провайдера
            // displayPickupPoints сохранит их в кэш провайдера и добавит на карту
            pickupPointsManager.displayPickupPoints(points, provider, false);
        } else {
            console.warn('⚠️ Новых точек ПВЗ не получено от API');
        }
    } catch (error) {
        console.error('❌ Ошибка при загрузке точек ПВЗ:', error);
    } finally {
        // Всегда скрываем лоадер после завершения загрузки
        hideMapLoader();
    }
}

// Функция для определения города по координатам
async function getCityFromCoordinates(lat, lon) {
    try {
        const response = await ymaps.geocode([lat, lon], { results: 1 });
        const firstGeoObject = response.geoObjects.get(0);
        
        if (firstGeoObject) {
            const address = firstGeoObject.getAddressLine();
            // Пытаемся извлечь город из адреса
            const cityMatch = address.match(/([А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?)/);
            if (cityMatch) {
                return cityMatch[1];
            }
        }
        return 'Москва'; // По умолчанию
    } catch (error) {
        console.error('Ошибка определения города:', error);
        return 'Москва';
    }
}

// ======================= Обновление адреса =======================
function updateAddressFromGeoObject(geoObject) {
    if (!geoObject) return;

    const address = geoObject.getAddressLine();
    const addressInput = document.getElementById('addressInput');
    
    
    // Сохраняем geoObject для получения координат и postal_code при сохранении
    selectedDeliveryGeoObject = geoObject;
    
    if (addressInput && !addressInput.disabled) {
        addressInput.value = address;
    }

    if (yandexPlacemark) yandexMap.geoObjects.remove(yandexPlacemark);

    yandexPlacemark = new ymaps.Placemark(
        geoObject.geometry.getCoordinates(),
        {},
        { preset: 'islands#blueDotIcon' }
    );
    yandexMap.geoObjects.add(yandexPlacemark);
    yandexMap.setCenter(geoObject.geometry.getCoordinates(), 15);
}

// ======================= Переключение режима доставка/самовывоз =======================
function initDeliveryTypeToggle() {
    const addressInput = document.getElementById('addressInput');

    // Общая функция обработки переключения
    function handleDeliveryTypeChange(selectedType, source) {
        // Синхронизируем переключатели
        if (source === 'desktop') {
            const mobileInput = document.getElementById(selectedType === 'pickup' ? 'mobileDeliveryTypePickup' : 'mobileDeliveryTypeDelivery');
            if (mobileInput) mobileInput.checked = true;
        } else if (source === 'mobile') {
            const desktopInput = document.getElementById(selectedType === 'pickup' ? 'deliveryTypePickup' : 'deliveryTypeDelivery');
            if (desktopInput) desktopInput.checked = true;
        }
        
        handleDeliveryModeSwitch(selectedType, addressInput);
    }
    
    // Десктопные radio buttons
    const desktopDelivery = document.getElementById('deliveryTypeDelivery');
    const desktopPickup = document.getElementById('deliveryTypePickup');
    
    if (desktopDelivery) {
        desktopDelivery.addEventListener('change', () => {
            if (desktopDelivery.checked) handleDeliveryTypeChange('delivery', 'desktop');
        });
    }
    if (desktopPickup) {
        desktopPickup.addEventListener('change', () => {
            if (desktopPickup.checked) handleDeliveryTypeChange('pickup', 'desktop');
        });
    }
    
    // Мобильные radio buttons
    const mobileDelivery = document.getElementById('mobileDeliveryTypeDelivery');
    const mobilePickup = document.getElementById('mobileDeliveryTypePickup');
    
    if (mobileDelivery) {
        mobileDelivery.addEventListener('change', () => {
            if (mobileDelivery.checked) handleDeliveryTypeChange('delivery', 'mobile');
        });
    }
    if (mobilePickup) {
        mobilePickup.addEventListener('change', () => {
            if (mobilePickup.checked) handleDeliveryTypeChange('pickup', 'mobile');
        });
    }
}

// Общая логика переключения режима доставки
function handleDeliveryModeSwitch(selectedType, addressInput) {
    if (selectedType === 'pickup') {
        // РЕЖИМ САМОВЫВОЗА
        
        // Сбрасываем данные доставки
        selectedDeliveryGeoObject = null;
        if (yandexPlacemark) {
            yandexMap.geoObjects.remove(yandexPlacemark);
            yandexPlacemark = null;
        }
        
        // Очищаем поле адреса и делаем его только для чтения
        if (addressInput) {
            addressInput.value = 'Выберите пункт выдачи на карте';
            addressInput.disabled = true;
            addressInput.style.backgroundColor = '#f1f5f9';
        }
        
        // Скрываем кнопку "Моё местоположение" (не актуальна для самовывоза)
        const currentLocationBtnContainer = document.getElementById('currentLocationBtnContainer');
        if (currentLocationBtnContainer) {
            currentLocationBtnContainer.style.display = 'none';
        }
        
        // Показываем иконки переключения провайдеров
        const mapDeliveryIcons = document.getElementById('mapDeliveryIcons');
        if (mapDeliveryIcons) {
            mapDeliveryIcons.classList.add('visible');
        }
        
        // Устанавливаем Почту России как активного провайдера по умолчанию
        currentProvider = 'russian_post';
        const icons = document.querySelectorAll('.map-delivery-icon');
        icons.forEach(i => i.classList.remove('active'));
        const russianPostIcon = document.querySelector('[data-provider="russian_post"]');
        if (russianPostIcon) {
            russianPostIcon.classList.add('active');
        }
        
        // Загружаем точки ПВЗ Почты России
        if (yandexMap && pickupPointsManager) {
            // Карта готова - сначала восстанавливаем точки из кэша, потом дозагружаем новые
            pickupPointsManager.switchProvider('russian_post');
            
            // Проверяем, есть ли точки в кэше
            const cachedPoints = pickupPointsManager.pointsByProvider['russian_post'] || [];
            if (cachedPoints.length === 0) {
                // Точек нет - нужно загрузить
                showMapLoader();
                loadPickupPoints('russian_post');
            }
        } else {
            // Карта ещё не готова - откладываем загрузку
            showMapLoader();
            pendingPickupLoad = 'russian_post';
        }
        
    } else {
        // РЕЖИМ ДОСТАВКИ
        
        // Сбрасываем отложенную загрузку точек
        pendingPickupLoad = null;
        
        // Показываем кнопку "Моё местоположение"
        const currentLocationBtnContainer = document.getElementById('currentLocationBtnContainer');
        if (currentLocationBtnContainer) {
            currentLocationBtnContainer.style.display = '';
        }
        
        // Скрываем иконки переключения провайдеров
        const mapDeliveryIcons = document.getElementById('mapDeliveryIcons');
        if (mapDeliveryIcons) {
            mapDeliveryIcons.classList.remove('visible');
        }
        
        // Очищаем точки ПВЗ с карты
        if (pickupPointsManager) {
            pickupPointsManager.clearPlacemarks();
        }
        
        // При выборе доставки разблокируем поле
        if (addressInput) {
            addressInput.disabled = false;
            addressInput.style.backgroundColor = '#fff';
            addressInput.value = '';
            addressInput.placeholder = 'Начните вводить адрес';
        }
        selectedPickupPoint = null;
        selectedDeliveryGeoObject = null;
        
        // Убираем метку с карты
        if (yandexPlacemark) {
            yandexMap.geoObjects.remove(yandexPlacemark);
            yandexPlacemark = null;
        }
    }
}

// ======================= Обработчики кликов на иконки провайдеров =======================
function initProviderIcons() {
    const icons = document.querySelectorAll('.map-delivery-icon');
    
    icons.forEach(icon => {
        icon.addEventListener('click', function() {
            const provider = this.dataset.provider;
            
            // Если тот же провайдер — ничего не делаем
            if (provider === currentProvider) return;
            
            
            // Обновляем активное состояние иконок
            icons.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Обновляем текущий провайдер
            currentProvider = provider;
            
            // При смене провайдера переключаемся на его точки
            if (yandexMap && pickupPointsManager) {
                // Переключаемся на провайдера (показывает точки из кэша)
                pickupPointsManager.switchProvider(provider);
                
                // Если точек нет в кэше - загружаем их
                const cachedPoints = pickupPointsManager.pointsByProvider[provider] || [];
                if (cachedPoints.length === 0) {
                    // Показываем лоадер только если нужно загружать
                    showMapLoader();
                    loadPickupPoints(provider);
                } else {
                    // Точки уже в кэше, просто скрываем лоадер если был показан
                    hideMapLoader();
                }
            } else {
                // Карта ещё не готова - откладываем загрузку
                showMapLoader();
                pendingPickupLoad = provider;
            }
        });
    });
}

// ======================= Обработчик события выбора пункта выдачи =======================
function initPickupPointSelectedHandler() {
    document.addEventListener('pickupPointSelected', function(event) {
        const detail = event.detail;
        
        // Сохраняем выбранную точку
        selectedPickupPoint = {
            provider: detail.provider,
            code: detail.code,
            name: detail.point ? detail.point.name : `Пункт выдачи ${detail.code}`,
            address: detail.address,
            latitude: detail.latitude,
            longitude: detail.longitude,
            postal_code: detail.point ? (detail.point.postal_code || '') : ''
        };
        
        // Заполняем поле адреса
        const addressInput = document.getElementById('addressInput');
        if (addressInput && selectedPickupPoint.address) {
            addressInput.value = selectedPickupPoint.address;
        }
        
    });
}

// ======================= Автоподсказка адреса =======================
function initAddressAutocomplete() {
    const input = document.getElementById('addressInput');
    if (!input) return;

    const dropdown = document.getElementById('suggestionsDropdown');
    if (!dropdown) return;
    
    let debounceTimer;

    input.addEventListener('input', () => {
        // Пропускаем автоподсказки если поле disabled (самовывоз)
        if (input.disabled) return;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = input.value.trim();
            
            if (query.length < 2) {
                dropdown.style.display = 'none';
                return;
            }

            if (typeof ymaps === 'undefined') {
                console.error('Yandex Maps API not loaded');
                dropdown.style.display = 'none';
                return;
            }

            dropdown.innerHTML = '<div class="dropdown-item py-2 px-3 text-center"><i class="spinner-border spinner-border-sm me-2"></i>Поиск...</div>';
            dropdown.style.display = 'block';

            ymaps.geocode(query, { 
                results: 10,
                boundedBy: [[40.0, 20.0], [70.0, 180.0]],
                strictBounds: false
            }).then(res => {
                const geoObjects = res.geoObjects.toArray();
                dropdown.innerHTML = '';
                
                if (geoObjects.length === 0) {
                    dropdown.innerHTML = '<div class="dropdown-item py-2 px-3 text-muted">Ничего не найдено</div>';
                    dropdown.style.display = 'block';
                    return;
                }

                geoObjects.forEach((geoObject, index) => {
                    const btn = document.createElement('button');
                    btn.className = 'dropdown-item py-2 px-3';
                    btn.type = 'button';
                    
                    const address = geoObject.getAddressLine();
                    const description = geoObject.properties.get('description') || '';
                    
                    btn.innerHTML = `
                        <div class="d-flex align-items-center">
                            <i class="bi bi-geo-alt text-primary me-2"></i>
                            <div class="text-start">
                                <div class="fw-medium">${address}</div>
                                ${description ? `<small class="text-muted">${description}</small>` : ''}
                            </div>
                        </div>`;
                    
                    btn.addEventListener('click', () => {
                        updateAddressFromGeoObject(geoObject);
                        dropdown.style.display = 'none';
                    });
                    dropdown.appendChild(btn);
                });

                dropdown.style.display = 'block';
            }).catch(error => {
                console.error('Geocode error:', error);
                dropdown.innerHTML = '<div class="dropdown-item py-2 px-3 text-danger">Ошибка поиска</div>';
                dropdown.style.display = 'block';
            });
        }, 300);
    });

    document.addEventListener('click', e => {
        if (!dropdown.contains(e.target) && e.target !== input) {
            dropdown.style.display = 'none';
        }
    });
}

// ======================= Кнопка "Моё местоположение" =======================
function initCurrentLocationButton() {
    const btn = document.getElementById('currentLocationBtn');
    if (!btn) return;
    
    btn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            alert('Геолокация не поддерживается вашим браузером');
            return;
        }
        
        btn.disabled = true;
        btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Поиск...';
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                
                if (yandexMap) {
                    yandexMap.setCenter([lat, lon], 15);
                    ymaps.geocode([lat, lon]).then(res => {
                        const geoObject = res.geoObjects.get(0);
                        if (geoObject) {
                            updateAddressFromGeoObject(geoObject);
                        }
                    });
                }
                
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-geo-alt"></i> Моё местоположение';
            },
            (error) => {
                alert('Не удалось определить ваше местоположение');
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-geo-alt"></i> Моё местоположение';
            }
        );
    });
}

// ======================= Функции для работы с адресами в UI =======================
function addAddressToUI(addressData, fromSession = false) {
    // Обновляем адрес в шапке
    updateHeaderAddressFromData(addressData, fromSession);
    
    // Добавляем адрес в список адресов
    addAddressToList(addressData, fromSession);
}

function updateHeaderAddressFromData(addressData, fromSession = false) {
    // Формируем короткий адрес (город)
    // Пропускаем почтовый индекс и название страны, ищем город
    const addressParts = addressData.address.split(',').map(p => p.trim());
    let shortAddress = addressParts[0];
    
    let partIndex = 0;
    // Пропускаем почтовый индекс (5-6 цифр)
    if (/^\d{5,6}$/.test(shortAddress) && addressParts.length > partIndex + 1) {
        partIndex++;
        shortAddress = addressParts[partIndex];
    }
    // Пропускаем название страны (Россия, Russia, РФ)
    if (/^(Россия|Russia|РФ|Российская Федерация)$/i.test(shortAddress) && addressParts.length > partIndex + 1) {
        partIndex++;
        shortAddress = addressParts[partIndex];
    }
    
    // Обновляем десктопную версию
    const addressBlock = document.getElementById('header-address-block');
    if (addressBlock) {
        addressBlock.innerHTML = `
            <button class="btn btn-link p-0 text-decoration-none d-flex align-items-center text-truncate address-header-btn"
                    type="button"
                    data-bs-toggle="modal"
                    data-bs-target="#addressListModal"
                    style="max-width: 200px; font-size: 14px; color: #495057 !important;">
                <i class="bi bi-geo-alt-fill text-primary me-2"></i>
                <span class="text-truncate">${shortAddress}</span>
            </button>
        `;
    }
    
    // Обновляем мобильную версию
    const mobileAddressText = document.getElementById('mobile-header-address-text');
    if (mobileAddressText) {
        // Сокращаем длинный адрес для мобильной версии
        const maxLength = 25;
        const mobileShortAddress = shortAddress.length > maxLength 
            ? shortAddress.substring(0, maxLength) + '...' 
            : shortAddress;
        mobileAddressText.textContent = mobileShortAddress;
    }
}

function addAddressToList(addressData, fromSession = false) {
    const addressList = document.querySelector('#addressListModal .address-list');
    if (!addressList) return;
    
    // Удаляем заглушку "нет адресов" если она есть
    const emptyState = addressList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Формируем HTML для адреса
    const addressHtml = createAddressCardHtml(addressData, fromSession);
    
    // Добавляем в начало списка
    addressList.insertAdjacentHTML('afterbegin', addressHtml);
    
    // Получаем только что добавленную карточку (первый элемент)
    const addressCard = addressList.querySelector('.address-card');
    
    // Инициализируем dropdown для Bootstrap и добавляем обработчики после добавления в DOM
    setTimeout(() => {
        if (addressCard) {
            // Инициализируем dropdown
            if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
                const dropdownButton = addressCard.querySelector('[data-bs-toggle="dropdown"]');
                if (dropdownButton && !dropdownButton._dropdown) {
                    new bootstrap.Dropdown(dropdownButton);
                }
            }
            
            // Добавляем обработчик удаления из сессии
            if (fromSession) {
                const deleteBtn = addressCard.querySelector('.delete-address-from-session-btn');
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', handleDeleteAddressFromSession);
                }
            }
        }
    }, 10);
    
    // Обновляем счетчик адресов
    if (window.addressListModalInstance) {
        window.addressListModalInstance.updateAddressCounter();
    }
}

function handleDeleteAddressFromSession(e) {
    e.preventDefault();
    e.stopPropagation();
    
    if (!confirm('Вы уверены, что хотите удалить этот адрес?')) {
        return;
    }
    
    const addressCard = e.target.closest('.address-card');
    // Получаем session_index из data-атрибута карточки
    const sessionIndex = addressCard?.dataset.sessionIndex;
    
    fetch('/account/delete_address_from_session/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_index: sessionIndex !== undefined ? parseInt(sessionIndex) : null })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Анимация удаления карточки
            if (addressCard) {
                addressCard.style.transition = 'opacity 0.3s, transform 0.3s';
                addressCard.style.opacity = '0';
                addressCard.style.transform = 'translateX(-20px)';
                setTimeout(() => {
                    addressCard.remove();
                    
                    // Проверяем, есть ли еще адреса в списке
                    const addressList = document.querySelector('#addressListModal .address-list');
                    const remainingCards = addressList?.querySelectorAll('.address-card[data-from-session="true"]');
                    
                    // Обновляем session_index для оставшихся карточек из сессии
                    if (remainingCards && remainingCards.length > 0) {
                        remainingCards.forEach((card, newIndex) => {
                            card.dataset.sessionIndex = newIndex;
                        });
                    }
                    
                    // Проверяем, есть ли вообще адреса
                    const allCards = addressList?.querySelectorAll('.address-card');
                    if (!allCards || allCards.length === 0) {
                        if (addressList) {
                            addressList.innerHTML = `
                                <div class="empty-state text-center py-5">
                                    <i class="bi bi-map text-muted fs-1 mb-3"></i>
                                    <p class="text-muted">Нет сохранённых адресов</p>
                                </div>
                            `;
                        }
                    }
                    
                    // Обновляем счетчик адресов
                    if (window.addressListModalInstance) {
                        window.addressListModalInstance.updateAddressCounter();
                    }
                    
                    // Проверяем, есть ли еще адреса в сессии и обновляем шапку
                    checkAndUpdateSessionAddress();
                }, 300);
            } else {
                // Если карточка не найдена, просто обновляем шапку
                checkAndUpdateSessionAddress();
            }
        } else {
            alert('Ошибка при удалении адреса: ' + (data.error || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('Error deleting address from session:', error);
        alert('Ошибка при удалении адреса');
    });
}

function checkAndUpdateSessionAddress() {
    // Проверяем, есть ли адрес в сессии
    fetch('/account/get_address_from_session/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        const addressBlock = document.getElementById('header-address-block');
        if (!addressBlock) return;
        
        // Проверяем наличие адресов в списке
        const addresses = data.addresses || [];
        if (data.has_address && addresses.length > 0) {
            // Обновляем шапку с первым адресом из сессии
            updateHeaderAddressFromData(addresses[0], true);
        } else {
            // Показываем заглушку "Указать адрес"
            addressBlock.innerHTML = `
                <button class="btn btn-link p-0 text-decoration-none d-flex align-items-center address-header-btn"
                        data-bs-toggle="modal"
                        data-bs-target="#addressListModal"
                        style="font-size: 14px; color: #495057 !important;">
                    <i class="bi bi-geo-alt me-2"></i>
                    Указать адрес
                </button>
            `;
        }
    })
    .catch(error => {
        console.error('Error checking session address:', error);
        // Показываем заглушку в случае ошибки
        const addressBlock = document.getElementById('header-address-block');
        if (addressBlock) {
            addressBlock.innerHTML = `
                <button class="btn btn-link p-0 text-decoration-none d-flex align-items-center address-header-btn"
                        data-bs-toggle="modal"
                        data-bs-target="#addressListModal"
                        style="font-size: 14px; color: #495057 !important;">
                    <i class="bi bi-geo-alt me-2"></i>
                    Указать адрес
                </button>
            `;
        }
    });
}

function createAddressCardHtml(addressData, fromSession = false) {
    // Формируем заголовок адреса
    let title = '';
    if (addressData.pickup_point_name) {
        title = addressData.pickup_point_name;
    } else {
        // Берем город из адреса, пропуская индекс и страну
        const addressParts = addressData.address.split(',').map(p => p.trim());
        title = addressParts[0] || 'Адрес';
        
        let partIndex = 0;
        // Пропускаем почтовый индекс (5-6 цифр)
        if (/^\d{5,6}$/.test(title) && addressParts.length > partIndex + 1) {
            partIndex++;
            title = addressParts[partIndex];
        }
        // Пропускаем название страны (Россия, Russia, РФ)
        if (/^(Россия|Russia|РФ|Российская Федерация)$/i.test(title) && addressParts.length > partIndex + 1) {
            partIndex++;
            title = addressParts[partIndex];
        }
        title = title || 'Адрес';
    }
    
    // Формируем полный адрес для отображения
    let fullAddress = addressData.address;
    if (addressData.pickup_point_name && !addressData.address.includes(addressData.pickup_point_name)) {
        fullAddress = `${addressData.pickup_point_name}, ${addressData.address}`;
    }
    
    // Генерируем уникальный ID для dropdown
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 1000);
    const dropdownId = fromSession ? `dropdownMenuButtonSession${timestamp}` : `dropdownMenuButton${timestamp}${random}`;
    
    // Определяем ID для data-атрибута
    const addressId = fromSession ? 'session' : (addressData.id || '');
    // Для адресов из сессии сохраняем session_index
    const sessionIndex = fromSession ? (addressData.session_index !== undefined ? addressData.session_index : 0) : '';
    
    return `
        <div class="address-card ${fromSession ? 'border-warning' : ''} mb-3 p-3 rounded-3" 
             data-address-id="${addressId}" 
             data-from-session="${fromSession}"
             data-session-index="${sessionIndex}"
             data-delivery-type="${addressData.delivery_type || 'delivery'}"
             data-address="${addressData.address || ''}"
             data-pickup-code="${addressData.pickup_point_code || ''}"
             data-provider="${addressData.pickup_provider || ''}">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="d-flex align-items-center mb-2">
                        <h6 class="mb-0 fw-semibold">${title}</h6>
                    </div>
                    <p class="text-muted mb-1 small">${fullAddress}</p>
                    ${addressData.postal_code ? `<p class="text-muted small mb-0"><i class="bi bi-postcard me-1"></i> ${addressData.postal_code}</p>` : ''}
                </div>
                <div class="dropdown">
                    <button class="btn btn-link text-muted p-0"
                            type="button"
                            id="${dropdownId}"
                            data-address-dropdown="1"
                            data-bs-toggle="dropdown"
                            aria-expanded="false">
                        <i class="bi bi-three-dots-vertical"></i>
                    </button>
                    <ul class="dropdown-menu shadow-sm address-dropdown" aria-labelledby="${dropdownId}">
                        ${fromSession ? `
                        <li>
                            <button class="dropdown-item text-danger delete-address-from-session-btn"
                                    data-address-id="session">
                                <i class="bi bi-trash me-2"></i>Удалить
                            </button>
                        </li>
                        ` : `
                        <li>
                            <button class="dropdown-item set-default-btn"
                                    data-address-id="${addressId}"
                                    data-url="/account/set_default_address/${addressId}/">
                                <i class="bi bi-check-circle me-2"></i>Сделать основным
                            </button>
                        </li>
                        <li>
                            <button class="dropdown-item text-danger delete-address-btn"
                                    data-address-id="${addressId}"
                                    data-url="/account/delete_address/${addressId}/">
                                <i class="bi bi-trash me-2"></i>Удалить
                            </button>
                        </li>
                        `}
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function loadAddressOnPageLoad() {
    const modal = document.getElementById('addressMapModal');
    const isAuthenticated = modal?.dataset.isAuthenticated === 'true';
    
    if (isAuthenticated) {
        // Для авторизованных пользователей загружаем дефолтный адрес
        fetch('/account/get-default-address/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            if (!response.ok) return null;
            return response.json();
        })
        .then(data => {
            if (data && data.has_address && data.full_address) {
                // Обновляем UI с адресом
                updateHeaderAddressFromData({
                    address: data.full_address,
                    pickup_point_name: ''
                }, false);
            }
        })
        .catch(error => {
            console.error('Error loading default address:', error);
        });
    } else {
        // Для неавторизованных пользователей загружаем ВСЕ адреса из сессии
        fetch('/account/get_address_from_session/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.has_address && data.addresses && data.addresses.length > 0) {
                // Добавляем ВСЕ адреса из сессии в UI
                data.addresses.forEach((address, index) => {
                    // Убеждаемся, что session_index установлен
                    address.session_index = address.session_index !== undefined ? address.session_index : index;
                    addAddressToUI(address, true);
                });
            }
        })
        .catch(error => {
            console.error('Error loading addresses from session:', error);
        });
    }
}

// ======================= Сохранение адреса =======================
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

// Функция проверки на дубликаты адресов
function checkDuplicateAddress(requestData, isAuthenticated) {
    return new Promise((resolve, reject) => {
        if (!isAuthenticated) {
            // Для неавторизованных пользователей проверяем список адресов в сессии
            fetch('/account/get_address_from_session/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.has_address && data.addresses && data.addresses.length > 0) {
                    // Проверяем каждый существующий адрес в списке
                    for (const existingAddress of data.addresses) {
                        if (requestData.delivery_type === 'pickup') {
                            // Для самовывоза сравниваем код пункта выдачи
                            if (existingAddress.pickup_point_code === requestData.pickup_point_code &&
                                existingAddress.pickup_provider === requestData.pickup_provider) {
                                reject(new Error('Этот адрес уже добавлен'));
                                return;
                            }
                        } else {
                            // Для доставки сравниваем полный адрес
                            if (existingAddress.address && requestData.address &&
                                existingAddress.address.trim().toLowerCase() === requestData.address.trim().toLowerCase()) {
                                reject(new Error('Этот адрес уже добавлен'));
                                return;
                            }
                        }
                    }
                }
                resolve();
            })
            .catch(() => resolve()); // В случае ошибки разрешаем сохранение
        } else {
            // Для авторизованных пользователей проверяем БД через список адресов в модальном окне
            // Проверяем существующие адреса в DOM
            const addressList = document.querySelector('#addressListModal .address-list');
            if (addressList) {
                const addressCards = addressList.querySelectorAll('.address-card');
                
                for (const card of addressCards) {
                    const cardAddress = card.dataset.address || '';
                    const cardDeliveryType = card.dataset.deliveryType || '';
                    const cardPickupCode = card.dataset.pickupCode || '';
                    const cardProvider = card.dataset.provider || '';
                    
                    if (requestData.delivery_type === 'pickup') {
                        // Для самовывоза сравниваем код пункта выдачи и провайдера
                        if (cardDeliveryType === 'pickup' &&
                            cardPickupCode === requestData.pickup_point_code &&
                            cardProvider === requestData.pickup_provider) {
                            reject(new Error('Этот адрес уже добавлен'));
                            return;
                        }
                    } else {
                        // Для доставки сравниваем полный адрес
                        if (cardDeliveryType === 'delivery' && 
                            cardAddress.trim().toLowerCase() === requestData.address.trim().toLowerCase()) {
                            reject(new Error('Этот адрес уже добавлен'));
                            return;
                        }
                    }
                }
            }
            resolve();
        }
    });
}

function initConfirmAddressButton() {
    const confirmBtn = document.getElementById('confirmAddress');
    if (!confirmBtn) return;
    
    // Удаляем старые обработчики, если они есть
    const newBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
    
    newBtn.addEventListener('click', (e) => {
        // Проверяем, что это форма с картой (не другая форма)
        const addressInput = document.getElementById('addressInput');
        const exactAddress = document.getElementById('exactAddress');
        
        // Если есть exactAddress, значит это другая форма, не обрабатываем
        if (exactAddress) {
            return;
        }
        
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
        
        // Проверка для самовывоза
        if (deliveryType === 'pickup') {
            if (!selectedPickupPoint) {
                alert('❗ Пожалуйста, выберите пункт выдачи на карте, кликнув по нему');
                return;
            }
        }
        
        // Формируем данные для отправки
        const requestData = {
            address: address,
            delivery_type: deliveryType
        };
        
        // Если выбран самовывоз, добавляем данные о пункте выдачи
        if (deliveryType === 'pickup' && selectedPickupPoint) {
            requestData.pickup_point_code = selectedPickupPoint.code || '';
            requestData.pickup_point_name = selectedPickupPoint.name || '';
            requestData.pickup_provider = selectedPickupPoint.provider || '';
            requestData.latitude = selectedPickupPoint.latitude;
            requestData.longitude = selectedPickupPoint.longitude;
            // Добавляем postal_code для самовывоза
            if (selectedPickupPoint.postal_code) {
                requestData.postal_code = selectedPickupPoint.postal_code;
            }
        }
        
        // Если выбран режим доставки и на карте есть метка (значит адрес был выбран на карте)
        if (deliveryType === 'delivery' && yandexPlacemark && selectedDeliveryGeoObject) {
            const coords = selectedDeliveryGeoObject.geometry.getCoordinates();
            requestData.latitude = coords[0];
            requestData.longitude = coords[1];
            
            // Пытаемся получить postal_code из geoObject
            let postalCode = selectedDeliveryGeoObject.properties.get('postalCode') || '';
            
            // Если индекс не найден, пытаемся получить его из метаданных
            if (!postalCode) {
                const metaData = selectedDeliveryGeoObject.properties.get('metaDataProperty');
                if (metaData && metaData.GeocoderMetaData) {
                    const addressDetails = metaData.GeocoderMetaData.AddressDetails;
                    if (addressDetails) {
                        postalCode = addressDetails?.Country?.AdministrativeArea?.Locality?.Thoroughfare?.Premise?.PostalCode?.PostalCodeNumber || 
                                    addressDetails?.Country?.AdministrativeArea?.SubAdministrativeArea?.Locality?.Thoroughfare?.Premise?.PostalCode?.PostalCodeNumber ||
                                    addressDetails?.Country?.AdministrativeArea?.Locality?.DependentLocality?.Thoroughfare?.Premise?.PostalCode?.PostalCodeNumber ||
                                    '';
                    }
                }
            }
            
            if (postalCode) {
                requestData.postal_code = postalCode;
            }
        }
        

        // Проверяем авторизацию пользователя
        const modal = document.getElementById('addressMapModal');
        const isAuthenticated = modal?.dataset.isAuthenticated === 'true';
        
        // Выбираем URL в зависимости от авторизации
        let saveAddressUrl;
        if (isAuthenticated) {
            saveAddressUrl = modal?.dataset.saveUrl || '/account/save_address/';
        } else {
            saveAddressUrl = modal?.dataset.saveSessionUrl || '/account/save_address_to_session/';
        }

        // Проверяем на дубликаты перед сохранением
        checkDuplicateAddress(requestData, isAuthenticated)
        .then(() => {
            return fetch(saveAddressUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(requestData)
            });
        })
        .then(async response => {
            // Обработка ошибки авторизации (только для авторизованных пользователей)
            if (isAuthenticated && (response.status === 403 || response.status === 401)) {
                // Для AJAX запросов не делаем редирект, чтобы избежать циклов
                // Показываем модальное окно авторизации, если оно есть
                const authModal = document.getElementById('authModal');
                if (authModal) {
                    const modal = bootstrap.Modal.getOrCreateInstance(authModal);
                    modal.show();
                    return Promise.reject(new Error('Требуется авторизация. Пожалуйста, войдите в систему.'));
                } else {
                    // Если модального окна нет, просто показываем ошибку
                    return Promise.reject(new Error('Требуется авторизация. Пожалуйста, обновите страницу и войдите в систему.'));
                }
            }
            
            // Проверяем, что ответ - JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Ожидался JSON, получен:', contentType, text.substring(0, 200));
                throw new Error(`Сервер вернул неверный формат ответа (${response.status})`);
            }
            
            // Парсим JSON только если это действительно JSON
            const data = await response.json();
            
            // Если статус не успешный, обрабатываем как ошибку
            if (!response.ok) {
                throw new Error(data.error || `Ошибка сервера (${response.status})`);
            }
            
            return data;
        })
        .then(data => {
            if (data && data.success) {
                // Закрываем модальное окно в любом случае успешного сохранения
                const modalElement = document.getElementById('addressMapModal');
                if (modalElement) {
                    try {
                        // Используем Bootstrap API для правильного закрытия с анимацией
                        const modalInstance = bootstrap.Modal.getInstance(modalElement);
                        
                        if (modalInstance) {
                            // Исправляем рассинхронизацию состояния: если DOM показывает, что модальное окно открыто,
                            // но Bootstrap считает его закрытым, синхронизируем состояние
                            const isActuallyShown = modalElement.classList.contains('show');
                            if (isActuallyShown && !modalInstance._isShown) {
                                modalInstance._isShown = true;
                            }
                            
                            // Проверяем, не находится ли модальное окно в процессе закрытия
                            if (!modalInstance._isTransitioning) {
                                modalInstance.hide();
                                
                                // Проверяем через небольшую задержку, закрылось ли модальное окно
                                setTimeout(() => {
                                    if (modalElement.classList.contains('show')) {
                                        // Еще раз синхронизируем состояние перед повторной попыткой
                                        if (!modalInstance._isShown) {
                                            modalInstance._isShown = true;
                                        }
                                        modalInstance.hide();
                                    }
                                }, 200);
                            }
                        } else {
                            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                            modal.hide();
                        }
                    } catch (error) {
                        console.error('Ошибка при закрытии модального окна:', error);
                        // Только в случае критической ошибки используем принудительное закрытие
                        setTimeout(() => {
                            if (modalElement.classList.contains('show')) {
                                try {
                                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                                    modal.hide();
                                } catch (e) {
                                    console.error('Критическая ошибка при закрытии:', e);
                                }
                            }
                        }, 500);
                    }
                }
                
                // Добавляем адрес в UI
                if (data.address) {
                    const fromSession = data.requires_auth === true;
                    addAddressToUI(data.address, fromSession);
                    
                    // Для авторизованных пользователей показываем уведомление
                    if (!fromSession) {
                        if (typeof showSuccessNotification === 'function') {
                            showSuccessNotification('Адрес успешно добавлен!');
                        }
                    }
                }
            } else {
                alert(data.error || 'Ошибка при сохранении адреса');
            }
        })
        .catch(error => {
            console.error('Ошибка сохранения адреса:', error);
            const errorMessage = error.message || 'Ошибка при сохранении адреса';
            
            // Если это ошибка дубликата, не закрываем модальное окно
            if (errorMessage.includes('уже добавлен')) {
                alert(errorMessage);
            } else {
                alert(errorMessage);
            }
        });
    });
}

// ======================= Обработчики модального окна =======================
function initModalHandlers() {
    // Инициализация карты при открытии модального окна
    document.getElementById('addressMapModal')?.addEventListener('shown.bs.modal', function() {
        if (!yandexMap) {
            // Показываем лоадер пока карта загружается
            showMapLoader();
            // initYandexMap сам загрузит API если нужно
            initYandexMap();
        } else {
            setTimeout(() => {
                yandexMap.container.fitToViewport();
                
                // Проверяем, выбран ли режим самовывоза, и если да — восстанавливаем точки
                const deliveryTypePickup = document.getElementById('deliveryTypePickup');
                if (deliveryTypePickup && deliveryTypePickup.checked && pickupPointsManager) {
                    // Показываем иконки провайдеров
                    const mapDeliveryIcons = document.getElementById('mapDeliveryIcons');
                    if (mapDeliveryIcons) {
                        mapDeliveryIcons.classList.add('visible');
                    }
                    
                    // Восстанавливаем точки из кэша или загружаем новые
                    const cachedPoints = pickupPointsManager.pointsByProvider[currentProvider] || [];
                    if (cachedPoints.length > 0) {
                        // Восстанавливаем из кэша
                        pickupPointsManager.switchProvider(currentProvider);
                    } else {
                        // Загружаем новые
                        showMapLoader();
                        loadPickupPoints(currentProvider);
                    }
                }
            }, 100);
        }
    });
    
    // Очистка при закрытии модального окна
    document.getElementById('addressMapModal')?.addEventListener('hidden.bs.modal', function() {
        if (yandexMap) {
            // Очищаем точки ПВЗ
            if (pickupPointsManager) {
                pickupPointsManager.clearPlacemarks();
            }
            // Убираем метку
            if (yandexPlacemark) {
                yandexMap.geoObjects.remove(yandexPlacemark);
                yandexPlacemark = null;
            }
        }
        selectedPickupPoint = null;
        selectedDeliveryGeoObject = null;
        
        // Удаляем backdrop если нет других открытых модальных окон
        cleanupModalBackdrop();
    });
}

// Глобальная функция для очистки backdrop после закрытия модальных окон
function cleanupModalBackdrop() {
    // Проверяем, есть ли открытые модальные окна
    const openModals = document.querySelectorAll('.modal.show');
    
    // Если нет открытых модальных окон, удаляем backdrop с анимацией
    if (openModals.length === 0) {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            // Убираем класс show для анимации закрытия (opacity уходит в 0)
            backdrop.classList.remove('show');
            // Удаляем после завершения анимации
            setTimeout(() => {
                if (backdrop.parentNode) {
                    backdrop.remove();
                }
            }, 150);
        });
        
        // Удаляем класс modal-open с body
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('padding-right');
        document.body.style.removeProperty('overflow');
    }
}

// ======================= Синхронизация мобильного переключателя =======================
function initMobileToggleSync() {
    const mobileDeliveryTypeToggle = document.getElementById('mobileDeliveryTypeToggle');
    const deliveryTypeToggle = document.getElementById('deliveryTypeToggle');
    
    if (mobileDeliveryTypeToggle && deliveryTypeToggle) {
        mobileDeliveryTypeToggle.addEventListener('change', function(e) {
            const value = e.target.value;
            const deliveryTypeDelivery = document.getElementById('deliveryTypeDelivery');
            const deliveryTypePickup = document.getElementById('deliveryTypePickup');
            
            if (value === 'delivery' && deliveryTypeDelivery) {
                deliveryTypeDelivery.checked = true;
            } else if (value === 'pickup' && deliveryTypePickup) {
                deliveryTypePickup.checked = true;
            }
            
            // Триггерим событие change
            deliveryTypeToggle.dispatchEvent(new Event('change'));
        });
    }
}

// ======================= Инициализация при загрузке =======================
function initAddressMapModal() {
    initModalHandlers();
    initDeliveryTypeToggle();
    initProviderIcons();
    initPickupPointSelectedHandler();
    initAddressAutocomplete();
    initCurrentLocationButton();
    initConfirmAddressButton();
    initMobileToggleSync();
    
}

// Автоматическая инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('addressMapModal')) {
        initAddressMapModal();
    }
    // Загружаем адрес при загрузке страницы (из сессии или из БД)
    loadAddressOnPageLoad();
});

// Экспорт функций в глобальную область для использования извне
window.initYandexMap = initYandexMap;
window.loadPickupPoints = loadPickupPoints;
window.updateAddressFromGeoObject = updateAddressFromGeoObject;
window.initAddressMapModal = initAddressMapModal;
window.updateHeaderAddressFromData = updateHeaderAddressFromData;
window.addAddressToUI = addAddressToUI;
window.handleDeleteAddressFromSession = handleDeleteAddressFromSession;
window.checkAndUpdateSessionAddress = checkAndUpdateSessionAddress;
window.cleanupModalBackdrop = cleanupModalBackdrop;
window.loadAddressOnPageLoad = loadAddressOnPageLoad;

// Обработчик события успешной авторизации - обновляем UI
document.addEventListener('userAuthenticated', function() {
    // Удаляем адреса из сессии из UI
    document.querySelectorAll('[data-from-session="true"]').forEach(el => el.remove());
    
    // Обновляем адрес в шапке и список адресов из БД
    if (window.addressFunctions && typeof window.addressFunctions.updateHeaderAddress === 'function') {
        window.addressFunctions.updateHeaderAddress();
    }
    if (window.addressListModalInstance) {
        window.addressListModalInstance.updateAddressList();
    }
    
    // Обновляем флаг авторизации в модальном окне
    const modal = document.getElementById('addressMapModal');
    if (modal) {
        modal.dataset.isAuthenticated = 'true';
    }
});

