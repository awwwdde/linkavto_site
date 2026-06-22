/**
 * Универсальная инициализация Bootstrap дропдаунов
 * Исключает модальные окна адресов, которые имеют собственную инициализацию
 */

/**
 * Универсальная инициализация Bootstrap дропдаунов
 * Исключает модальные окна адресов, которые имеют собственную инициализацию
 */

// Глобальная функция инициализации дропдаунов
window.initBootstrapDropdowns = function() {
    // Защита от слишком частых вызовов
    if (window._dropdownInitInProgress) {
        console.log('Dropdown initialization already in progress, skipping...');
        return;
    }
    window._dropdownInitInProgress = true;
    
    console.log('=== initBootstrapDropdowns called ===');
    console.log('Bootstrap available:', typeof bootstrap !== 'undefined');
    console.log('Current URL:', window.location.href);
    
    if (typeof bootstrap !== 'undefined') {
        console.log('Bootstrap is available, initializing dropdowns');
        
        // Сначала найдем ВСЕ дропдауны (включая data-address-dropdown)
        const allDropdowns = document.querySelectorAll('[data-bs-toggle="dropdown"], [data-address-dropdown="1"]');
        console.log('All dropdowns found:', allDropdowns.length);
        
        // Найдем дропдауны в модалках адресов
        const addressModalDropdowns = document.querySelectorAll('#addressListModal [data-bs-toggle="dropdown"], #addressListModal [data-address-dropdown="1"], #addressMapModal [data-bs-toggle="dropdown"], #addressMapModal [data-address-dropdown="1"]');
        console.log('Address modal dropdowns found:', addressModalDropdowns.length);
        
        // Находим все dropdown элементы, исключая те, что находятся в модальных окнах адресов и кнопку каталога
        const dropdownElements = document.querySelectorAll('[data-bs-toggle="dropdown"]:not(#addressListModal [data-bs-toggle="dropdown"]):not(#addressMapModal [data-bs-toggle="dropdown"]):not(#categoriesDropdown)');
        console.log('Found dropdown elements (excluding address modals and catalog button):', dropdownElements.length);
        
        // Выведем информацию о каждом найденном дропдауне
        dropdownElements.forEach((element, index) => {
            console.log(`Dropdown ${index + 1}:`, {
                id: element.id || 'no-id',
                class: element.className,
                parent: element.parentElement?.tagName || 'no-parent',
                inModal: element.closest('.modal')?.id || 'not-in-modal',
                hasBsToggle: element.hasAttribute('data-bs-toggle'),
                hasAddressDropdown: element.hasAttribute('data-address-dropdown')
            });
        });
        
        // Инициализируем каждый dropdown
        dropdownElements.forEach((element, index) => {
            try {
                // Удаляем существующие экземпляры Bootstrap
                const existingInstance = bootstrap.Dropdown.getInstance(element);
                if (existingInstance) {
                    console.log(`Disposing existing dropdown instance for ${element.id || 'unnamed'}`);
                    existingInstance.dispose();
                }
                
                // Создаем новый экземпляр
                const dropdown = new bootstrap.Dropdown(element, {
                    autoClose: true,
                    boundary: 'viewport'
                });
                
                console.log(`Dropdown ${index + 1} (${element.id || 'unnamed'}) initialized successfully`);
            } catch (error) {
                console.error(`Error initializing dropdown ${index + 1}:`, error);
            }
        });
        
        console.log('All dropdowns initialized (excluding address modals)');
        
        // Дополнительно инициализируем дропдауны в модалке адресов, если она открыта
        const addressModal = document.getElementById('addressListModal');
        if (addressModal && addressModal.classList.contains('show')) {
            console.log('Address modal is open, initializing its dropdowns');
            initAddressModalDropdowns();
        }
    } else {
        console.error('Bootstrap is not available!');
    }
    console.log('=== initBootstrapDropdowns finished ===');
    
    // Сбрасываем флаг через небольшую задержку
    setTimeout(() => {
        window._dropdownInitInProgress = false;
    }, 100);
};

// Функция для инициализации дропдаунов в модалке адресов
function initAddressModalDropdowns() {
    console.log('=== initAddressModalDropdowns CALLED ===');
    console.log('Current URL:', window.location.href);
    console.log('Function called from:', new Error().stack);
    
    const addressModal = document.getElementById('addressListModal');
    if (!addressModal) {
        console.log('=== initAddressModalDropdowns called but addressListModal not found ===');
        return;
    }
    
    console.log('=== initAddressModalDropdowns called ===');
    console.log('Current URL:', window.location.href);
    console.log('Address modal found:', !!addressModal);
    
    // Принудительно закрываем все дропдауны при инициализации
    addressModal.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
        const btn = menu.previousElementSibling;
        if (btn) btn.setAttribute('aria-expanded', 'false');
    });
    console.log('All dropdowns closed during initialization');
    
    // Инициализируем дропдауны с data-bs-toggle="dropdown"
    const bsToggleDropdowns = addressModal.querySelectorAll('[data-bs-toggle="dropdown"]');
    console.log('Found data-bs-toggle dropdowns in address modal:', bsToggleDropdowns.length);
    
    bsToggleDropdowns.forEach(el => {
        try {
            const existingInstance = bootstrap.Dropdown.getInstance(el);
            if (existingInstance) {
                existingInstance.dispose();
            }
            
            const dropdown = new bootstrap.Dropdown(el, {
                autoClose: 'outside',
                boundary: addressModal,
                display: 'static'
            });
            
            console.log('Address modal dropdown initialized:', el.id || 'unnamed');
        } catch (error) {
            console.error('Error initializing address modal dropdown:', error);
        }
    });
    
    // Инициализируем fallback дропдауны с data-address-dropdown="1"
    const addressDropdowns = addressModal.querySelectorAll('[data-address-dropdown="1"]');
    console.log('Found data-address-dropdown elements in address modal:', addressDropdowns.length);
    
    // Также ищем элементы с data-bs-toggle="dropdown" (возможно, они были изменены Bootstrap)
    const bsToggleDropdownsInModal = addressModal.querySelectorAll('[data-bs-toggle="dropdown"]');
    console.log('Found data-bs-toggle="dropdown" elements in address modal:', bsToggleDropdownsInModal.length);
    
    // Объединяем оба типа элементов
    const allDropdowns = [...addressDropdowns, ...bsToggleDropdownsInModal];
    console.log('Total dropdown elements to process:', allDropdowns.length);
    
    // Детальное логирование найденных элементов
    allDropdowns.forEach((el, index) => {
        console.log(`Dropdown ${index + 1}:`, {
            id: el.id || 'no-id',
            className: el.className,
            tagName: el.tagName,
            parentElement: el.parentElement?.tagName,
            nextElementSibling: el.nextElementSibling?.tagName,
            hasClickHandler: !!el._clickHandler,
            hasAddressDropdown: el.hasAttribute('data-address-dropdown'),
            hasBsToggle: el.hasAttribute('data-bs-toggle')
        });
    });
    
    allDropdowns.forEach(el => {
        const dropdown = el.nextElementSibling;
        console.log('Processing dropdown element:', {
            id: el.id || 'unnamed',
            tagName: el.tagName,
            hasNextSibling: !!el.nextElementSibling,
            nextSiblingTag: el.nextElementSibling?.tagName,
            nextSiblingClass: el.nextElementSibling?.classList.toString(),
            isDropdownMenu: el.nextElementSibling?.classList.contains('dropdown-menu')
        });
        
        if (!dropdown || !dropdown.classList.contains('dropdown-menu')) {
            console.log('Skipping dropdown - no valid dropdown-menu sibling');
            return;
        }
        
        console.log('Initializing address dropdown:', el.id || 'unnamed');
        
        // Удаляем старые обработчики
        if (el._clickHandler) {
            el.removeEventListener('click', el._clickHandler);
        }
        
        el._clickHandler = (e) => {
            console.log('=== DROPDOWN CLICK DETECTED ===');
            console.log('Element ID:', el.id || 'unnamed');
            console.log('Element class:', el.className);
            console.log('Element data-address-dropdown:', el.getAttribute('data-address-dropdown'));
            console.log('Current URL:', window.location.href);
            console.log('Event target:', e.target);
            console.log('Event type:', e.type);
            console.log('Event bubbles:', e.bubbles);
            console.log('Event cancelable:', e.cancelable);
            
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Prevented default and stopped propagation');
            
            // Закрыть другие дропдауны в модалке
            addressModal.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                if (menu !== dropdown) menu.classList.remove('show');
            });
            
            // Переключаем текущий дропдаун
            const isCurrentlyOpen = dropdown.classList.contains('show');
            if (isCurrentlyOpen) {
                // Если открыт - закрываем
                dropdown.classList.remove('show');
                el.setAttribute('aria-expanded', 'false');
                console.log('Address dropdown closed:', el.id || 'unnamed');
            } else {
                // Если закрыт - открываем
                dropdown.classList.add('show');
                el.setAttribute('aria-expanded', 'true');
                dropdown.style.left = 'auto';
                dropdown.style.right = '0';
                console.log('Address dropdown opened:', el.id || 'unnamed');
            }
        };
        
        el.addEventListener('click', el._clickHandler);
        
        console.log('Successfully added click handler to:', el.id || 'unnamed');
        console.log('Handler function:', typeof el._clickHandler);
    });
    
    console.log('=== initAddressModalDropdowns finished ===');
    console.log('Total dropdowns processed:', allDropdowns.length);
    console.log('Dropdowns with handlers:', allDropdowns.filter(el => !!el._clickHandler).length);
}

// Инициализация при загрузке DOM - только для обычных дропдаунов (не в модалках)
document.addEventListener('DOMContentLoaded', function() {
    // Инициализируем только дропдауны вне модалок адресов
    window.initBootstrapDropdowns();
});

// Дополнительная инициализация при изменении размера окна
window.addEventListener('resize', function() {
    setTimeout(window.initBootstrapDropdowns, 100);
});

// Делаем функции доступными глобально для браузера
window.initAddressModalDropdowns = initAddressModalDropdowns;

// Экспортируем функции для использования в других скриптах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initBootstrapDropdowns: window.initBootstrapDropdowns,
        initAddressModalDropdowns: initAddressModalDropdowns
    };
}
