document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    const dropdown = document.createElement('div');
    dropdown.className = 'autocomplete-dropdown';
    document.querySelector('.search-form').appendChild(dropdown);

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();

        if (query.length >= 2) {
            fetch(`/search/autocomplete/?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                dropdown.innerHTML = html;
                dropdown.style.display = 'block';
            });
        } else {
            dropdown.style.display = 'none';
        }
    });

    // Закрываем dropdown при клике вне его
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-form')) {
            dropdown.style.display = 'none';
        }
    });
});