/**
 * Модуль для работы с пунктами выдачи на карте
 */

class PickupPointsManager {
    constructor(map) {
        this.map = map;
        this.pickupPoints = []; // Текущие отображаемые точки
        this.placemarks = [];
        this.loadedPointCodes = new Set(); // Отслеживание уже загруженных точек по code
        this.selectedProvider = 'all'; // all, cdek, boxberry, russian_post
        this.selectedPoint = null;
        this.clusterer = null;
        
        // Кэш точек по провайдерам
        this.pointsByProvider = {
            'russian_post': [],
            'cdek': [],
            'boxberry': []
        };
        
        // Кэш загруженных кодов по провайдерам
        this.loadedCodesByProvider = {
            'russian_post': new Set(),
            'cdek': new Set(),
            'boxberry': new Set()
        };
        
        // Инициализируем кластеризатор
        this._initClusterer();
        
        // Цвета для разных провайдеров
        this.providerColors = {
            'cdek': '#00A651',
            'boxberry': '#FF6B00',
            'russian_post': '#0066CC'
        };
        
        // Иконки для разных провайдеров
        this.providerIcons = {
            'cdek': 'https://cdn-icons-png.flaticon.com/32/2838/2838912.png',
            'boxberry': 'https://cdn-icons-png.flaticon.com/32/3081/3081648.png',
            'russian_post': 'https://cdn-icons-png.flaticon.com/32/542/542689.png'
        };
    }
    
    /**
     * Инициализация кластеризатора
     */
    _initClusterer() {
        if (this.clusterer) {
            // Удаляем старый кластеризатор
            this.map.geoObjects.remove(this.clusterer);
        }
        
        // Создаём новый кластеризатор
        this.clusterer = new ymaps.Clusterer({
            preset: 'islands#invertedBlueClusterIcons',
            clusterDisableClickZoom: false,
            clusterOpenBalloonOnClick: true,
            clusterBalloonContentLayout: 'cluster#balloonCarousel',
            clusterBalloonPanelMaxMapArea: 0,
            clusterBalloonContentLayoutWidth: 300,
            clusterBalloonContentLayoutHeight: 200,
            clusterBalloonPagerSize: 5,
            // Важно: группировка по координатам
            groupByCoordinates: false
        });
        
        // Добавляем кластеризатор на карту
        this.map.geoObjects.add(this.clusterer);
        console.log('✅ Кластеризатор инициализирован и добавлен на карту');
    }
    
    /**
     * Загрузка пунктов выдачи с сервера
     */
    async loadPickupPoints(provider = 'all', city = 'Москва') {
        try {
            const mapCenter = this.map.getCenter();
            const url = new URL('/account/api/pickup-points/', window.location.origin);
            url.searchParams.set('provider', provider);
            url.searchParams.set('city', city);
            url.searchParams.set('latitude', mapCenter[0]);
            url.searchParams.set('longitude', mapCenter[1]);
            
            console.log('Загрузка пунктов выдачи:', url.toString());
            
            const response = await fetch(url);
            const data = await response.json();
            
            console.log('Ответ сервера:', data);
            
            // Проверяем формат ответа - может быть {success: true, points: []} или просто массив
            if (data.success && data.points) {
                this.pickupPoints = data.points;
                console.log(`Загружено ${this.pickupPoints.length} пунктов выдачи`);
                return this.pickupPoints;
            } else if (Array.isArray(data)) {
                // Если ответ - это массив напрямую
                this.pickupPoints = data;
                console.log(`Загружено ${this.pickupPoints.length} пунктов выдачи`);
                return this.pickupPoints;
            } else {
                console.error('Неожиданный формат ответа:', data);
                return [];
            }
        } catch (error) {
            console.error('Ошибка при загрузке пунктов выдачи:', error);
            return [];
        }
    }
    
    /**
     * Отображение пунктов выдачи на карте С КЛАСТЕРИЗАЦИЕЙ
     * Сохраняет точки в кэш провайдера и добавляет новые на карту
     */
    displayPickupPoints(points = null, provider = null, clearExisting = false) {
        if (!points || points.length === 0) {
            console.log('Нет новых пунктов для отображения');
            return;
        }
        
        // Определяем провайдера из первой точки если не указан
        if (!provider && points.length > 0) {
            provider = points[0].provider;
        }
        
        if (!provider) {
            console.warn('⚠️ Не указан провайдер для точек');
            return;
        }
        
        // Если нужно очистить — очищаем только текущий провайдер
        if (clearExisting) {
            this.clearProviderPoints(provider);
        }
        
        // Проверяем и переинициализируем кластеризатор если нужно
        if (!this.clusterer) {
            console.log('⚠️ Кластеризатор не инициализирован, создаём...');
            this._initClusterer();
        }
        
        // Получаем кэш для этого провайдера
        const providerCache = this.loadedCodesByProvider[provider] || new Set();
        
        // Фильтруем только новые точки (которых ещё нет в кэше провайдера)
        const newPoints = points.filter(point => {
            if (!point.code) return false;
            return !providerCache.has(point.code);
        });
        
        if (newPoints.length === 0) {
            console.log(`Все точки провайдера ${provider} уже в кэше, новых нет`);
            return;
        }
        
        // Сохраняем новые точки в кэш провайдера
        if (!this.pointsByProvider[provider]) {
            this.pointsByProvider[provider] = [];
        }
        if (!this.loadedCodesByProvider[provider]) {
            this.loadedCodesByProvider[provider] = new Set();
        }
        
        newPoints.forEach(point => {
            this.pointsByProvider[provider].push(point);
            this.loadedCodesByProvider[provider].add(point.code);
        });
        
        console.log(`📍 Добавляем ${newPoints.length} новых точек для ${provider} (в кэше: ${this.pointsByProvider[provider].length})`);
        
        // Создаем массив меток для кластеризатора
        const geoObjects = [];
        
        newPoints.forEach((point, index) => {
            const placemark = this.createPlacemark(point, this.pickupPoints.length + index);
            if (placemark) {
                geoObjects.push(placemark);
                // Добавляем в общий массив отображаемых точек
                this.pickupPoints.push(point);
                this.placemarks.push(placemark);
            }
        });
        
        if (geoObjects.length === 0) {
            console.warn('⚠️ Не удалось создать ни одной метки');
            return;
        }
        
        // Добавляем новые метки в кластеризатор
        try {
            this.clusterer.add(geoObjects);
            console.log(`✅ Добавлено ${geoObjects.length} новых меток для ${provider} (всего на карте: ${this.placemarks.length})`);
        } catch (e) {
            console.error('❌ Ошибка добавления меток в кластеризатор:', e);
            // Fallback: добавляем метки напрямую на карту
            geoObjects.forEach(placemark => {
                this.map.geoObjects.add(placemark);
            });
        }
    }
    
    /**
     * Создание метки (для кластеризатора)
     */
    createPlacemark(point, index) {
        if (!point.latitude || !point.longitude) {
            console.warn('Пропущена точка без координат:', point);
            return null;
        }
        
        // Инициализируем флаг загрузки деталей
        point.detailsLoaded = false;
        
        const placemark = new ymaps.Placemark(
            [point.latitude, point.longitude],
            {
                balloonContentHeader: `<strong>${point.provider_name}</strong>`,
                balloonContentBody: this.getBalloonHtml(point, point),
                hintContent: point.name
            },
            {
                preset: 'islands#icon',
                iconColor: this.providerColors[point.provider] || '#0066CC'
            }
        );
        
        // Обработчик открытия balloon - загружаем детали
        placemark.events.add('balloonopen', () => {
            const code = point.code;
            const provider = point.provider;
            
            // Если детали ещё не загружены - загружаем их
            if (!point.detailsLoaded && provider === 'russian_post') {
                this.loadPointDetails(placemark, point, code, provider);
            }
            
            // Добавляем обработчик для кнопки выбора
            setTimeout(() => {
                const selectBtn = document.querySelector('.select-pickup-point');
                if (selectBtn) {
                    selectBtn.addEventListener('click', (e) => {
                        const code = e.target.dataset.code;
                        const provider = e.target.dataset.provider;
                        this.selectPickupPoint(code, provider);
                    });
                }
            }, 100);
        });
        
        // НЕ добавляем напрямую на карту - вернем для кластеризатора
        return placemark;
    }
    
    /**
     * Загрузка детальной информации о пункте выдачи
     */
    async loadPointDetails(placemark, point, code, provider) {
        // Показываем индикатор загрузки в balloon
        const loadingHtml = `
            <div class="pickup-point-balloon">
                <p class="mb-1"><strong>${point.name}</strong></p>
                <p class="mb-1 small">${point.address}</p>
                <p class="mb-1 small text-muted">
                    <i class="spinner-border spinner-border-sm me-2"></i>Загрузка деталей...
                </p>
            </div>
        `;
        placemark.properties.set('balloonContentBody', loadingHtml);
        
        try {
            // URL-кодируем код для безопасной передачи
            const encodedCode = encodeURIComponent(code);
            const url = `/account/api/pickup-points/${provider}/${encodedCode}/`;
            console.log(`📡 Загрузка деталей для ${code}:`, url);
            
            const response = await fetch(url);
            if (!response.ok) {
                if (response.status === 404) {
                    console.warn(`⚠️ Детали для ${code} не найдены (404)`);
                    // Показываем базовые данные если детали не найдены
                    const basicHtml = this.getBalloonHtml(point, point);
                    placemark.properties.set('balloonContentBody', basicHtml);
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const details = await response.json();
            console.log('✅ Получены детали:', details);
            
            if (details && details.success && details.point) {
                const detailedPoint = details.point;
                
                // Обновляем точку в кэше с детальными данными
                if (detailedPoint.full_address && detailedPoint.full_address !== point.address) {
                    point.address = detailedPoint.full_address;
                    point.full_address = detailedPoint.full_address;
                }
                if (detailedPoint.work_time && detailedPoint.work_time !== 'Уточняйте режим работы') {
                    point.work_time = detailedPoint.work_time;
                }
                if (detailedPoint.phone) {
                    point.phone = detailedPoint.phone;
                }
                if (detailedPoint.phones && detailedPoint.phones.length > 0) {
                    point.phones = detailedPoint.phones;
                }
                point.detailsLoaded = true;
                
                // Обновляем точку в кэше провайдера и в основном массиве
                const providerPoints = this.pointsByProvider[provider] || [];
                const cachedPoint = providerPoints.find(p => p.code === code);
                if (cachedPoint) {
                    Object.assign(cachedPoint, point);
                }
                
                // Обновляем в основном массиве отображаемых точек
                const displayedPoint = this.pickupPoints.find(p => p.code === code);
                if (displayedPoint) {
                    Object.assign(displayedPoint, point);
                }
                
                // Обновляем balloon с детальными данными
                const detailedHtml = this.getBalloonHtml(point, point);
                placemark.properties.set('balloonContentBody', detailedHtml);
                
                // Добавляем обработчик для кнопки выбора после обновления
                setTimeout(() => {
                    const selectBtn = document.querySelector('.select-pickup-point');
                    if (selectBtn) {
                        selectBtn.addEventListener('click', (e) => {
                            const code = e.target.dataset.code;
                            const provider = e.target.dataset.provider;
                            this.selectPickupPoint(code, provider);
                        });
                    }
                }, 100);
                
                console.log('✅ Balloon обновлён с детальными данными:', {
                    address: point.full_address,
                    work_time: point.work_time,
                    phone: point.phone
                });
            } else {
                // Если детали не получены, показываем базовые данные
                const basicHtml = this.getBalloonHtml(point, point);
                placemark.properties.set('balloonContentBody', basicHtml);
                console.warn('⚠️ Детали не получены, показываем базовые данные');
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки деталей:', error);
            // Показываем базовые данные при ошибке (это нормально - не все точки имеют детали)
            const basicHtml = this.getBalloonHtml(point, point);
            placemark.properties.set('balloonContentBody', basicHtml);
            
            // Добавляем обработчик для кнопки выбора
            setTimeout(() => {
                const selectBtn = document.querySelector('.select-pickup-point');
                if (selectBtn) {
                    selectBtn.addEventListener('click', (e) => {
                        const code = e.target.dataset.code;
                        const provider = e.target.dataset.provider;
                        this.selectPickupPoint(code, provider);
                    });
                }
            }, 100);
        }
    }
    
    /**
     * Генерация HTML для balloon
     */
    getBalloonHtml(point, originalPoint) {
        const workTime = point.work_time || 'Уточняйте режим работы';
        const phone = point.phone || (point.phones && point.phones.length > 0 ? point.phones[0] : '');
        const address = point.full_address || point.address || 'Адрес не указан';
        
        return `
            <div class="pickup-point-balloon">
                <p class="mb-1"><strong>${point.name}</strong></p>
                <p class="mb-1 small">${address}</p>
                <p class="mb-1 small"><i class="bi bi-clock"></i> ${workTime}</p>
                ${phone ? `<p class="mb-1 small"><i class="bi bi-telephone"></i> ${phone}</p>` : ''}
                <button class="btn btn-sm btn-primary mt-2 select-pickup-point" 
                        data-code="${originalPoint.code}" 
                        data-provider="${originalPoint.provider}">
                    Выбрать этот пункт
                </button>
            </div>
        `;
    }
    
    /**
     * Удаление всех меток с карты (из кластеризатора)
     * НЕ очищает кэш провайдеров - только убирает с карты
     */
    clearPlacemarks() {
        // Очищаем кластеризатор
        if (this.clusterer) {
            this.clusterer.removeAll();
        }
        this.placemarks = [];
        this.pickupPoints = [];
        this.loadedPointCodes.clear();
        console.log('🗑️ Все метки удалены с карты (кэш провайдеров сохранён)');
    }
    
    /**
     * Очистка точек конкретного провайдера (и с карты, и из кэша)
     */
    clearProviderPoints(provider) {
        if (!provider) return;
        
        // Удаляем метки этого провайдера с карты
        const providerPoints = this.pointsByProvider[provider] || [];
        const providerCodes = this.loadedCodesByProvider[provider] || new Set();
        
        // Фильтруем метки и точки
        const codesToRemove = Array.from(providerCodes);
        this.placemarks = this.placemarks.filter((placemark, index) => {
            const point = this.pickupPoints[index];
            if (point && codesToRemove.includes(point.code)) {
                if (this.clusterer) {
                    this.clusterer.remove(placemark);
                }
                return false;
            }
            return true;
        });
        
        this.pickupPoints = this.pickupPoints.filter(point => {
            return !codesToRemove.includes(point.code);
        });
        
        // Очищаем кэш провайдера
        this.pointsByProvider[provider] = [];
        this.loadedCodesByProvider[provider].clear();
        
        console.log(`🗑️ Очищены точки провайдера ${provider}`);
    }
    
    /**
     * Переключение на провайдера - показывает его точки из кэша или загружает новые
     */
    switchProvider(provider) {
        if (!provider) return;
        
        console.log(`🔄 Переключение на провайдера: ${provider}`);
        
        // Очищаем карту от всех точек
        this.clearPlacemarks();
        
        // Показываем точки из кэша этого провайдера
        const cachedPoints = this.pointsByProvider[provider] || [];
        if (cachedPoints.length > 0) {
            console.log(`📦 Загружаем ${cachedPoints.length} точек из кэша для ${provider}`);
            // Восстанавливаем метки из кэша
            const geoObjects = [];
            cachedPoints.forEach((point, index) => {
                const placemark = this.createPlacemark(point, index);
                if (placemark) {
                    geoObjects.push(placemark);
                    this.pickupPoints.push(point);
                    this.placemarks.push(placemark);
                }
            });
            
            if (geoObjects.length > 0 && this.clusterer) {
                this.clusterer.add(geoObjects);
                console.log(`✅ Отображено ${geoObjects.length} точек из кэша для ${provider}`);
            }
        } else {
            console.log(`📭 Кэш для ${provider} пуст, нужно загрузить точки`);
        }
        
        this.selectedProvider = provider;
    }
    
    /**
     * Центрирование карты по всем точкам
     */
    fitMapToPoints(points) {
        if (!points || points.length === 0) return;
        
        const coords = points
            .filter(p => p.latitude && p.longitude)
            .map(p => [p.latitude, p.longitude]);
        
        if (coords.length > 0) {
            try {
                this.map.setBounds(this.map.geoObjects.getBounds(), {
                    checkZoomRange: true,
                    zoomMargin: 50
                });
            } catch (e) {
                // Если не удалось установить границы, центрируем по первой точке
                this.map.setCenter(coords[0], 12);
            }
        }
    }
    
    /**
     * Выбор пункта выдачи
     */
    selectPickupPoint(code, provider) {
        const point = this.pickupPoints.find(p => p.code === code && p.provider === provider);
        
        if (!point) {
            console.error('Пункт выдачи не найден');
            return;
        }
        
        this.selectedPoint = point;
        
        // Закрываем все balloon
        this.map.balloon.close();
        
        // Отправляем событие о выборе пункта выдачи
        const event = new CustomEvent('pickupPointSelected', {
            detail: {
                point: point,
                address: point.address,
                code: code,
                provider: provider,
                provider_name: point.provider_name,
                latitude: point.latitude,
                longitude: point.longitude
            }
        });
        document.dispatchEvent(event);
        
        console.log('Выбран пункт выдачи:', point);
    }
    
    /**
     * Фильтрация по провайдеру (устаревший метод, используйте switchProvider)
     * Оставлен для совместимости
     */
    filterByProvider(provider) {
        if (provider === 'all') {
            // Для 'all' показываем все точки из всех провайдеров
            this.clearPlacemarks();
            const allPoints = [];
            Object.values(this.pointsByProvider).forEach(providerPoints => {
                allPoints.push(...providerPoints);
            });
            allPoints.forEach((point, index) => {
                const placemark = this.createPlacemark(point, index);
                if (placemark) {
                    this.pickupPoints.push(point);
                    this.placemarks.push(placemark);
                }
            });
            if (this.clusterer && this.placemarks.length > 0) {
                this.clusterer.add(this.placemarks);
            }
        } else {
            // Используем новый метод переключения
            this.switchProvider(provider);
        }
        this.selectedProvider = provider;
    }
    
    /**
     * Получение выбранного пункта
     */
    getSelectedPoint() {
        return this.selectedPoint;
    }
    
    /**
     * Сброс выбранного пункта
     */
    resetSelection() {
        this.selectedPoint = null;
    }
}

// Экспортируем класс в глобальную область видимости
window.PickupPointsManager = PickupPointsManager;

