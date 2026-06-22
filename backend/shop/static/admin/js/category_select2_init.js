(function ($) {
    'use strict';

    function initCategorySelect2() {
        var darkOpts = {
            dropdownCssClass: 'admin-dark-dropdown',
            language: {
                noResults: function () { return 'Категории не найдены'; },
                searching: function () { return 'Поиск...'; },
            },
            matcher: function (params, data) {
                if (!params.term || params.term.trim() === '') return data;
                var term = params.term.toLowerCase();
                if (data.text.toLowerCase().indexOf(term) > -1) return data;
                return null;
            },
        };

        // Parent category field (with search)
        $('.parent-category-select2').each(function () {
            if ($(this).data('select2')) return;
            $(this).select2($.extend({}, darkOpts, {
                width: '100%',
                allowClear: true,
                placeholder: 'Корневая категория',
            }));
        });

        // Single-select (FK)
        $('.category-hierarchy-select2').each(function () {
            if ($(this).data('select2')) return;
            $(this).select2($.extend({}, darkOpts, {
                width: '100%',
                allowClear: true,
                placeholder: '---------',
            }));
        });

        // Multi-select (M2M)
        $('.category-hierarchy-select2-multiple').each(function () {
            if ($(this).data('select2')) return;
            $(this).select2($.extend({}, darkOpts, {
                width: '100%',
                placeholder: 'Выберите категории...',
                closeOnSelect: false,
            }));
        });
    }

    $(document).ready(function () {
        initCategorySelect2();

        // Re-init after Django admin inline rows are added
        $(document).on('formset:added', function () {
            initCategorySelect2();
        });
    });
}(django.jQuery));
