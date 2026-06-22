document.addEventListener('DOMContentLoaded', function() {
    console.log("МикроФункции подключены")



    function microSearch(buttonId, cardsSelector, inputId) {
        const button = document.getElementById(buttonId);
        const input = document.getElementById(inputId);
        const cards = document.querySelectorAll(cardsSelector);

        
        if (!button || !input || !cards.length) return;

    }
   
   
   

    function setupCategoryTitle(selectId, titleId, storageKey = 'rootcategoryst') {
    const select = document.getElementById(selectId);
    const title = document.getElementById(titleId);
    
    if (!select || !title) return; 

    function updateSubTitle() {
        const selectedOption = select.options[select.selectedIndex];
        const selectedText = selectedOption ? selectedOption.textContent.trim() : 'Сосал';
        
        title.textContent = selectedText;
        sessionStorage.setItem(storageKey, selectedText);
    }

    
    const saved = sessionStorage.getItem(storageKey);
    if (saved) {
        title.textContent = saved;
    } else {
        updateSubTitle(); 
    }

    
    select.addEventListener('change', updateSubTitle);
}

    function setupSortTitle(menuSelector, buttonId, mobileTextId, sortTextsm) {
    const sortMenu = document.querySelector(menuSelector);
    const sortirovka = document.querySelector(menuSelector);
    const sortbut = document.getElementById(buttonId);
    let menuactive = false;
    
    document.addEventListener('click', function(event) {
        if (event.target.id === buttonId || sortbut.contains(event.target)) {
            menuactive = !menuactive;
            if (menuactive) {
                sortMenu.style.display = 'flex';
            }
        } else {
            if (!sortirovka.contains(event.target) && menuactive) {
                sortMenu.style.display = 'none';
                menuactive = false;
            }
        }
    });
    
    const sortopt = document.querySelectorAll('[data-sort]');
    const mobtext = document.getElementById(mobileTextId);
    
    sortopt.forEach(sm => {
        sm.addEventListener('click', function(e) {
            const sortValuem = this.getAttribute('data-sort');
            mobtext.textContent = sortTextsm[sortValuem] || 'Сортировка';
        });
    });
    
    sortMenu.style.display = 'none';
}
   
    
});