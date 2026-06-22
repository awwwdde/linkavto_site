document.addEventListener('DOMContentLoaded', function() {
    // Инициализация состояния кнопок
    document.querySelectorAll('.btn-favorite[data-initial-favorite="true"]').forEach(btn => {
        btn.classList.add('active');
    });

    // Обработчик кликов
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.btn-favorite');
        if (!btn) return;

        e.preventDefault();
        const productId = btn.dataset.productId;
        const isFavorite = btn.classList.contains('active');
        const icon = btn.querySelector('i');

        // Визуальное изменение
        btn.classList.add('animate');
        btn.classList.toggle('active');
        icon.classList.toggle('far');
        icon.classList.toggle('fas');

        // Отправка запроса
        const url = isFavorite
            ? `/favorites/remove/${productId}/`
            : `/favorites/add/${productId}/`;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(response => response.json())
          .then(data => {
              if (data.success) {
                  // Обновление счетчика в шапке
                  const counter = document.querySelector('.favorites-count');
                  if (counter) counter.textContent = data.count;
              }
          }).finally(() => {
              setTimeout(() => btn.classList.remove('animate'), 600);
          });
    });
});

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