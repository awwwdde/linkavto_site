// Функция для сохранения выбранного элемента в историю поиска
function saveSearchSelection(text, type) {
    fetch('/search/api/save_selection/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            text: text,
            type: type
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Search selection saved:', text);
        } else {
            console.error('Error saving search selection:', data.error);
        }
    })
    .catch(error => {
        console.error('Error saving search selection:', error);
    });
}

// Функция для получения CSRF токена
function getCookie(name) {
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

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    const searchForm = document.querySelector('.search-form');
    
    if (!searchInput || !searchForm) return;
    
    const dropdown = document.createElement('div');
    dropdown.className = 'autocomplete-dropdown';
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #e5e7eb;
        border-top: none;
        border-radius: 0 0 8px 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        max-height: 300px;
        overflow-y: auto;
        display: none;
    `;
    searchForm.appendChild(dropdown);

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();

        // Скрываем историю поиска при вводе
        const searchHistoryDropdown = document.getElementById('searchHistoryDropdown');
        if (searchHistoryDropdown) {
            searchHistoryDropdown.classList.add('d-none');
        }

        if (query.length >= 2) {
            fetch(`/search/autocomplete/?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => {
                console.log('Web autocomplete response status:', response.status);
                return response.text();
            })
            .then(html => {
                console.log('Web autocomplete HTML response:', html);
                dropdown.innerHTML = html;
                dropdown.style.display = 'block';
                
                // Добавляем обработчики клика для элементов автоподстановки
                const items = dropdown.querySelectorAll('.autocomplete-item');
                items.forEach(item => {
                    item.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        const slug = this.dataset.slug;
                        const text = this.dataset.value || this.textContent.trim();
                        const type = this.dataset.type || 'name';
                        
                        // Сохраняем выбранный элемент в историю
                        console.log('Desktop: Saving search selection:', text, type);
                        if (typeof window.saveSearchSelection === 'function') {
                            window.saveSearchSelection(text, type);
                        } else {
                            console.error('saveSearchSelection function not found');
                        }
                        
                        if (slug) {
                            // Переходим к странице товара
                            window.location.href = `/product/${slug}/`;
                        } else {
                            // Fallback: если нет slug, используем старую логику
                            if (text) {
                                searchInput.value = text;
                                dropdown.style.display = 'none';
                                searchForm.submit();
                            }
                        }
                    });
                });
            })
            .catch(error => {
                console.error('Error loading autocomplete:', error);
            });
        } else {
            dropdown.style.display = 'none';
            // Показываем историю обратно, если поле пустое
            const searchHistoryDropdown = document.getElementById('searchHistoryDropdown');
            if (searchHistoryDropdown && query.length === 0) {
                searchHistoryDropdown.classList.remove('d-none');
            }
        }
    });

    // Закрываем dropdown при клике вне его
    document.addEventListener('click', function(e) {
        if (!searchForm.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    // Закрываем dropdown при потере фокуса
    searchInput.addEventListener('blur', function() {
        // Небольшая задержка, чтобы клик по элементу автоподстановки успел сработать
        setTimeout(() => {
            dropdown.style.display = 'none';
        }, 150);
    });
});