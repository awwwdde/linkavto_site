/**
 * Совместимость товара — интерактивный builder в Django admin.
 *
 * Схема хранения в БД:
 *   car_brand  (FK)   — не используем напрямую, т.к. только одна марка
 *   car_models        (M2M) ← сюда пишем модели
 *   car_generations   (M2M) ← сюда пишем поколения
 *   car_modifications (M2M) ← сюда пишем модификации
 *
 * Логика добавления:
 *   [+ марка целиком]   → загружаем все её модели → пишем в car_models
 *   [+ модель целиком]  → загружаем все её поколения → пишем в car_generations
 *   [+ поколение]       → загружаем все его модификации → пишем в car_modifications
 *   [+ модификация]     → пишем эту модификацию в car_modifications
 *
 * Отображение (правая панель): каждая добавленная строка показывает
 * «Марка › Модель › Поколение › Модификация» с кнопкой удаления.
 *
 * При удалении строки — удаляем соответствующие ID из нативных <select>.
 */
(function () {
    'use strict';

    var $ = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : (window.jQuery || window.$);
    if (typeof $ !== 'function') { console.error('product_compatibility: jQuery not found'); return; }

    var API = {
        brands:        '/garage/api/brands/',
        models:        '/garage/api/models/',
        generations:   '/garage/api/generations/',
        modifications: '/garage/api/modifications/',
    };
    var API_TYPE = { car: 'cars', truck: 'trucks', moto: 'moto', special: 'special' };

    var SECTIONS = ['car', 'truck', 'moto', 'special'];

    /* ── AJAX ────────────────────────────────────────────────────────────── */
    function api(url, params, cb) {
        $.ajax({ url: url, data: params, success: function (d) { if (d && d.success) cb(d); } });
    }

    /* ══════════════════════════════════════════════════════════════════════
       Структура entries[prefix]:
       Array of { key, label, modelIds[], genIds[], modIds[] }
       key — уникальная строка для идентификации записи в UI
    ══════════════════════════════════════════════════════════════════════ */

    /* ── Инициализация секции ────────────────────────────────────────────── */
    function initSection(prefix) {
        var apiType  = API_TYPE[prefix];
        var $sec     = $('.compat-section[data-section="' + prefix + '"]');
        if (!$sec.length) return;

        var $brandSel    = $sec.find('.cb-brand');
        var $btnBrand    = $sec.find('.btn-add-brand');
        var $modelList   = $sec.find('.cb-models');
        var $genList     = $sec.find('.cb-gens');
        var $modList     = $sec.find('.cb-mods');
        var $resultList  = $sec.find('.compat-result-list');
        var $count       = $sec.find('.compat-section-count');

        /* Нативные скрытые <select multiple> */
        var $hidModels = $('#id_' + prefix + '_models');
        var $hidGens   = $('#id_' + prefix + '_generations');
        var $hidMods   = $('#id_' + prefix + '_modifications');

        /* Навигационное состояние */
        var nav = { brand: null, model: null, gen: null };

        /* Список строк совместимости для отображения и синхронизации */
        /* row = { key, html, modelIds:[], genIds:[], modIds:[] } */
        var rows = [];

        /* ── Загрузка марок ────────────────────────────────────────────── */
        api(API.brands, { type: apiType }, function (d) {
            var html = '<option value="">— выберите марку —</option>';
            d.brands.forEach(function (b) {
                html += '<option value="' + b.id + '" data-name="' + esc(b.name) + '">' + esc(b.name) + '</option>';
            });
            $brandSel.html(html);

            /* Восстановление из скрытых select */
            restore(d.brands);
        });

        /* ── Восстановление при редактировании существующего товара ─────── */
        function restore(brands) {
            var savedModelIds = hidIds($hidModels);
            var savedGenIds   = hidIds($hidGens);
            var savedModIds   = hidIds($hidMods);
            if (!savedModelIds.length && !savedGenIds.length && !savedModIds.length) return;

            var brandsMap = {};
            brands.forEach(function (b) { brandsMap[b.id] = b.name; });

            /* Загружаем модели для всех марок параллельно */
            var allModels = {}; /* modelId → {name, brandId} */
            var pending = brands.length;
            if (!pending) return;

            brands.forEach(function (b) {
                api(API.models, { type: apiType, brand_id: b.id }, function (d) {
                    d.models.forEach(function (m) {
                        allModels[m.id] = { name: m.name, brandId: b.id };
                    });
                    pending--;
                    if (pending === 0) restoreStep2(allModels, brandsMap, savedModelIds, savedGenIds, savedModIds);
                });
            });
        }

        function restoreStep2(allModels, brandsMap, savedModelIds, savedGenIds, savedModIds) {
            /* Добавляем строки для моделей */
            savedModelIds.forEach(function (mId) {
                var m = allModels[mId];
                if (!m) return;
                var bName = brandsMap[m.brandId] || '?';
                pushRow(
                    spanB(bName) + sep() + spanM(m.name) + span('gen','(все поколения)'),
                    [mId], [], []
                );
            });

            if (!savedGenIds.length && !savedModIds.length) { renderResults(); return; }

            /* Загружаем поколения для всех моделей */
            var allGens = {}; /* genId → {label, modelId} */
            var modelIds = Object.keys(allModels);
            var pending = modelIds.length;
            if (!pending) { renderResults(); return; }

            modelIds.forEach(function (mId) {
                api(API.generations, { type: apiType, model_id: mId }, function (d) {
                    d.generations.forEach(function (g) {
                        allGens[g.id] = { label: genLabel(g), modelId: mId };
                    });
                    pending--;
                    if (pending === 0) restoreStep3(allModels, allGens, brandsMap, savedGenIds, savedModIds);
                });
            });
        }

        function restoreStep3(allModels, allGens, brandsMap, savedGenIds, savedModIds) {
            savedGenIds.forEach(function (gId) {
                var g = allGens[gId];
                if (!g) return;
                var m = allModels[g.modelId];
                if (!m) return;
                pushRow(
                    spanB(brandsMap[m.brandId]||'?') + sep() + spanM(m.name) + sep() + spanG(g.label) + span('gen','(все мод.)'),
                    [], [gId], []
                );
            });

            if (!savedModIds.length) { renderResults(); return; }

            var allMods = {}; /* modId → {name, genId} */
            var genIds = Object.keys(allGens);
            var pending = genIds.length;
            if (!pending) { renderResults(); return; }

            genIds.forEach(function (gId) {
                api(API.modifications, { type: apiType, generation_id: gId }, function (d) {
                    d.modifications.forEach(function (md) {
                        allMods[md.id] = { name: md.name, genId: gId };
                    });
                    pending--;
                    if (pending === 0) restoreStep4(allModels, allGens, allMods, brandsMap, savedModIds);
                });
            });
        }

        function restoreStep4(allModels, allGens, allMods, brandsMap, savedModIds) {
            savedModIds.forEach(function (mdId) {
                var md = allMods[mdId];
                if (!md) return;
                var g = allGens[md.genId];
                if (!g) return;
                var m = allModels[g.modelId];
                if (!m) return;
                pushRow(
                    spanB(brandsMap[m.brandId]||'?') + sep() + spanM(m.name) + sep() + spanG(g.label) + sep() + spanMod(md.name),
                    [], [], [mdId]
                );
            });
            renderResults();
        }

        /* ── Обработчики UI ────────────────────────────────────────────── */

        $brandSel.on('change', function () {
            var id   = $(this).val();
            var name = $(this).find('option:selected').data('name') || '';
            nav.brand = id ? { id: id, name: name } : null;
            nav.model = null; nav.gen = null;
            $btnBrand.prop('disabled', !id);
            clearList($modelList, 'выберите марку');
            clearList($genList,   'выберите модель');
            clearList($modList,   'выберите поколение');
            if (!id) return;
            clearList($modelList, '…');
            api(API.models, { type: apiType, brand_id: id }, function (d) {
                renderList($modelList, d.models, null, true);
            });
        });

        /* [+] у марки — добавить все модели марки */
        $btnBrand.on('click', function () {
            if (!nav.brand) return;
            var b = nav.brand;
            clearList($modelList, '…');
            api(API.models, { type: apiType, brand_id: b.id }, function (d) {
                renderList($modelList, d.models, null, true);
                var modelIds = d.models.map(function (m) { return m.id; });
                if (!modelIds.length) { showToast('У этой марки нет моделей'); return; }
                pushRow(
                    spanB(b.name) + span('gen','(все модели)'),
                    modelIds, [], []
                );
                renderResults(); sync();
            });
        });

        /* Клик по строке модели — навигация → загрузить поколения */
        $modelList.on('click', '.btn-nav-item', function (e) {
            e.stopPropagation();
            var $item = $(this).closest('.compat-list-item');
            selectItem($modelList, $item);
            nav.model = { id: $item.data('id'), name: $item.data('name') };
            nav.gen   = null;
            clearList($genList, '…');
            clearList($modList, 'выберите поколение');
            api(API.generations, { type: apiType, model_id: nav.model.id }, function (d) {
                renderList($genList, d.generations, genLabel, true);
            });
        });

        /* [+] у модели — добавить все поколения модели */
        $modelList.on('click', '.btn-add-item', function (e) {
            e.stopPropagation();
            var $item = $(this).closest('.compat-list-item');
            var m = { id: $item.data('id'), name: $item.data('name') };
            if (!nav.brand) return;
            var b = nav.brand;
            api(API.generations, { type: apiType, model_id: m.id }, function (d) {
                var genIds = d.generations.map(function (g) { return g.id; });
                pushRow(
                    spanB(b.name) + sep() + spanM(m.name) + span('gen', genIds.length ? '(все поколения)' : '(нет поколений)'),
                    genIds.length ? [] : [m.id],
                    genIds,
                    []
                );
                renderResults(); sync();
            });
        });

        /* Клик по строке поколения — навигация */
        $genList.on('click', '.btn-nav-item', function (e) {
            e.stopPropagation();
            var $item = $(this).closest('.compat-list-item');
            selectItem($genList, $item);
            nav.gen = { id: $item.data('id'), name: $item.data('name') };
            clearList($modList, '…');
            api(API.modifications, { type: apiType, generation_id: nav.gen.id }, function (d) {
                renderList($modList, d.modifications, null, false);
            });
        });

        /* [+] у поколения — добавить все модификации поколения */
        $genList.on('click', '.btn-add-item', function (e) {
            e.stopPropagation();
            var $item = $(this).closest('.compat-list-item');
            var g = { id: $item.data('id'), name: $item.data('name') };
            if (!nav.brand || !nav.model) return;
            api(API.modifications, { type: apiType, generation_id: g.id }, function (d) {
                var modIds = d.modifications.map(function (m) { return m.id; });
                pushRow(
                    spanB(nav.brand.name) + sep() + spanM(nav.model.name) + sep() + spanG(g.name) + span('gen', modIds.length ? '(все мод.)' : '(нет мод.)'),
                    [],
                    modIds.length ? [] : [g.id],
                    modIds
                );
                renderResults(); sync();
            });
        });

        /* [+] у модификации */
        $modList.on('click', '.btn-add-item', function (e) {
            e.stopPropagation();
            var $item = $(this).closest('.compat-list-item');
            var md = { id: $item.data('id'), name: $item.data('name') };
            if (!nav.brand || !nav.model || !nav.gen) return;
            pushRow(
                spanB(nav.brand.name) + sep() + spanM(nav.model.name) + sep() + spanG(nav.gen.name) + sep() + spanMod(md.name),
                [], [], [md.id]
            );
            renderResults(); sync();
        });

        /* Удаление строки из итогов */
        $resultList.on('click', '.btn-remove-item', function () {
            var key = $(this).data('key');
            rows = rows.filter(function (r) { return r.key !== key; });
            renderResults(); sync();
        });

        /* Очистить всё */
        $sec.find('.compat-result-clear').on('click', function () {
            rows = [];
            renderResults(); sync();
        });

        /* ── Хелперы рендера браузера ───────────────────────────────────── */

        function renderList($el, items, labelFn, withNav) {
            if (!items || !items.length) {
                clearList($el, 'нет данных');
                return;
            }
            var html = '';
            items.forEach(function (item) {
                var label = labelFn ? labelFn(item) : item.name;
                var nav = withNav
                    ? '<button type="button" class="btn-nav-item" title="Открыть">›</button>'
                    : '';
                html += '<div class="compat-list-item" data-id="' + item.id + '" data-name="' + esc(label) + '">' +
                    '<span class="compat-list-item-name" title="' + esc(label) + '">' + esc(label) + '</span>' +
                    nav +
                    '<button type="button" class="btn-add-item" title="Добавить">+</button>' +
                    '</div>';
            });
            $el.html(html);
        }

        function clearList($el, msg) {
            $el.html('').attr('data-empty', msg || '');
        }

        function selectItem($list, $item) {
            $list.find('.compat-list-item').removeClass('selected');
            $item.addClass('selected');
        }

        /* ── Хелперы строк (rows) ───────────────────────────────────────── */

        var rowCounter = 0;
        function pushRow(html, modelIds, genIds, modIds) {
            /* Проверяем покрытие — не добавляем если уже есть */
            var newModelSet = setOf(modelIds);
            var newGenSet   = setOf(genIds);
            var newModSet   = setOf(modIds);

            /* Проверяем нет ли дублей */
            var dup = rows.some(function (r) {
                return setsOverlap(setOf(r.modelIds), newModelSet) ||
                       setsOverlap(setOf(r.genIds),   newGenSet)   ||
                       setsOverlap(setOf(r.modIds),   newModSet);
            });
            if (dup) { showToast('Часть совместимостей уже добавлена'); }

            rowCounter++;
            rows.push({
                key:      prefix + '_' + rowCounter,
                html:     html,
                modelIds: modelIds,
                genIds:   genIds,
                modIds:   modIds,
            });
        }

        /* ── Рендер итогового списка ────────────────────────────────────── */

        function renderResults() {
            $count.text(rows.length).toggleClass('has-items', rows.length > 0);
            if (!rows.length) { $resultList.html(''); return; }
            var html = '';
            rows.forEach(function (r) {
                html += '<div class="compat-result-item">' +
                    '<div class="compat-result-item-text">' + r.html + '</div>' +
                    '<button type="button" class="btn-remove-item" data-key="' + r.key + '" title="Удалить">×</button>' +
                    '</div>';
            });
            $resultList.html(html);
        }

        /* ── Синхронизация в нативные <select> ─────────────────────────── */

        function sync() {
            var allModelIds = {}, allGenIds = {}, allModIds = {};
            rows.forEach(function (r) {
                r.modelIds.forEach(function (id) { allModelIds[id] = true; });
                r.genIds.forEach(function (id)   { allGenIds[id]   = true; });
                r.modIds.forEach(function (id)   { allModIds[id]   = true; });
            });
            applyIds($hidModels, Object.keys(allModelIds));
            applyIds($hidGens,   Object.keys(allGenIds));
            applyIds($hidMods,   Object.keys(allModIds));
        }

        function applyIds($el, ids) {
            if (!$el.length) return;
            var existing = {};
            $el.find('option').each(function () { existing[$(this).val()] = true; });
            ids.forEach(function (id) {
                if (!existing[id]) $el.append('<option value="' + id + '" selected>' + id + '</option>');
            });
            $el.find('option').each(function () {
                $(this).prop('selected', ids.indexOf(String($(this).val())) !== -1);
            });
        }
    }

    /* ══════════════════════════════════════════════════════════════════════
       Вспомогательные функции (общие)
    ══════════════════════════════════════════════════════════════════════ */

    function hidIds($el) {
        if (!$el.length) return [];
        return $el.find('option:selected').map(function () { return String($(this).val()); }).get().filter(Boolean);
    }

    function genLabel(g) {
        var label = g.name;
        if (g.year_start) label += ' (' + g.year_start + '—' + (g.year_end || 'н.в.') + ')';
        return label;
    }

    function esc(str) { return $('<span>').text(String(str || '')).html(); }

    function sep() { return '<span class="ri-sep">›</span>'; }
    function spanB(t)   { return '<span class="ri-brand">' + esc(t) + '</span>'; }
    function spanM(t)   { return '<span class="ri-model">' + esc(t) + '</span>'; }
    function spanG(t)   { return '<span class="ri-gen">'   + esc(t) + '</span>'; }
    function spanMod(t) { return '<span class="ri-mod">'   + esc(t) + '</span>'; }
    function span(cls, t){ return '<span class="ri-' + cls + '">' + esc(t) + '</span>'; }

    function setOf(arr) {
        var s = {};
        (arr || []).forEach(function (x) { s[x] = true; });
        return s;
    }
    function setsOverlap(a, b) {
        return Object.keys(a).some(function (k) { return b[k]; });
    }

    var toastTimer = null;
    function showToast(msg) {
        var $t = $('#compat-toast');
        if (!$t.length) {
            $t = $('<div id="compat-toast" style="' +
                'position:fixed;bottom:24px;right:24px;' +
                'background:#1f6feb;color:#fff;padding:8px 16px;border-radius:6px;' +
                'font-size:13px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,.4);' +
                'opacity:0;transition:opacity .3s;">' + esc(msg) + '</div>').appendTo('body');
        } else { $t.text(msg); }
        $t.css('opacity', '1');
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { $t.css('opacity', '0'); }, 2400);
    }

    /* ── Сворачиваемые секции ────────────────────────────────────────────── */
    function setupCollapsible() {
        $('.compat-section').each(function () {
            var $sec = $(this);
            var key  = 'compat_' + $sec.data('section');
            if (sessionStorage.getItem(key) === '1') {
                $sec.addClass('collapsed');
                $sec.find('.compat-section-body').hide();
                $sec.find('.toggle-arrow').text('▶');
            }
        });
        $(document).on('click', '.compat-section-toggle', function () {
            var $sec  = $(this).closest('.compat-section');
            var $body = $sec.find('.compat-section-body');
            var key   = 'compat_' + $sec.data('section');
            if ($sec.hasClass('collapsed')) {
                $sec.removeClass('collapsed');
                $body.slideDown(180);
                $(this).find('.toggle-arrow').text('▼');
                sessionStorage.setItem(key, '0');
            } else {
                $sec.addClass('collapsed');
                $body.slideUp(180);
                $(this).find('.toggle-arrow').text('▶');
                sessionStorage.setItem(key, '1');
            }
        });
    }

    /* ── Entry point ─────────────────────────────────────────────────────── */
    $(document).ready(function () {
        SECTIONS.forEach(initSection);
        setupCollapsible();
    });
})();
