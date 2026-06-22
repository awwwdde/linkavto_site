function setupFullScreenMegaMenu() {
    const DESKTOP_BREAKPOINT = 992;
    const megaMenu = document.querySelector('.mega-menu');
    const header = document.querySelector('header.sticky-top');

    if (!megaMenu) return;

    // Селекторы для ховер-логики
    const MENU_CATEGORY_SELECTOR = '.menu-category';
    const MENU_SUBCATEGORIES_SELECTOR = '.menu-subcategories';

    function getHeaderBottom() {
        if (!header) return 0;
        const rect = header.getBoundingClientRect();
        // header фиксированный, поэтому bottom — это фактическая высота, даже при скролле
        return Math.max(rect.bottom, header.offsetHeight || 0);
    }

    function applyFullScreenLayout() {
        const top = getHeaderBottom();
        const height = Math.max(window.innerHeight - top, 0);

        // Устанавливаем css-переменную для перекрытия любых top через !important
        document.documentElement.style.setProperty('--mega-top', `${top}px`);

        megaMenu.style.position = 'fixed';
        megaMenu.style.top = `${top}px`;
        megaMenu.style.left = '0';
        megaMenu.style.right = '0';
        megaMenu.style.width = '100vw';
        megaMenu.style.maxWidth = '100vw';
        megaMenu.style.height = `${height}px`;
        megaMenu.style.bottom = '';
    }

    function resetBodyScroll() {
        document.body.style.overflow = '';
    }

    function lockBodyScroll() {
        document.body.style.overflow = 'hidden';
    }

    // Следим за изменением класса у мега-меню, чтобы на открытие занимало весь экран
    const observer = new MutationObserver(() => {
        const isOpen = megaMenu.classList.contains('show');
        if (isOpen) {
            applyFullScreenLayout();
            lockBodyScroll();
        } else {
            resetBodyScroll();
        }
    });

    observer.observe(megaMenu, { attributes: true, attributeFilter: ['class'] });

    // Пересчитываем позицию при ресайзе, когда меню открыто
    function handleResize() {
        if (megaMenu.classList.contains('show')) {
            applyFullScreenLayout();
        }
    }

    // Закрытие по Esc
    function handleKeydown(e) {
        if (e.key === 'Escape' && megaMenu.classList.contains('show')) {
            megaMenu.classList.remove('show');
        }
    }

    window.addEventListener('resize', handleResize);
    document.addEventListener('keydown', handleKeydown);

    // Начальная подстройка, если вдруг уже открыт (например, из другого скрипта)
    if (megaMenu.classList.contains('show')) {
        applyFullScreenLayout();
        lockBodyScroll();
    }

    // Ховер-логика для левой колонки: показываем соответствующие подкаталоги справа
    function bindHover() {
        const categories = document.querySelectorAll(MENU_CATEGORY_SELECTOR);
        const subcontainers = document.querySelectorAll(MENU_SUBCATEGORIES_SELECTOR);
        if (!categories.length || !subcontainers.length) return;

        categories.forEach(category => {
            category.addEventListener('mouseenter', () => {
                // активируем текущую категорию
                categories.forEach(c => {
                    c.classList.remove('active');
                    const link = c.querySelector('.menu-category-link');
                    if (link) link.classList.remove('active');
                });
                
                category.classList.add('active');
                const link = category.querySelector('.menu-category-link');
                if (link) link.classList.add('active');

                const categoryId = category.dataset.sectionId;
                if (!categoryId) return;

                subcontainers.forEach(sub => {
                    sub.classList.toggle('active', sub.dataset.category === categoryId);
                });
            });
        });

        // При первом открытии активируем первую категорию и её подкаталоги
        const first = categories[0];
        if (first) {
            first.dispatchEvent(new Event('mouseenter'));
        }
    }

    // Привяжем обработчики один раз после загрузки
    bindHover();
}

document.addEventListener('DOMContentLoaded', setupFullScreenMegaMenu);