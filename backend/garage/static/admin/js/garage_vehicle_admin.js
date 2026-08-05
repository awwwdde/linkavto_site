/**
 * JavaScript для динамической загрузки марок, моделей, поколений и модификаций
 * в админке Django для модуля Garage
 */

(function() {
    'use strict';
    
    // jQuery: сначала django.jQuery (после jquery.init.js), иначе глобальный jQuery
    var $ = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : (window.jQuery || window.$);
    if (typeof $ !== 'function') {
        console.error('Garage vehicle admin: jQuery not found');
        return;
    }
    
    $(document).ready(function() {
        var $vehicleType = $('#id_vehicle_type');
        var $brandChoice = $('#id_brand_choice');
        var $modelChoice = $('#id_model_choice');
        var $generationChoice = $('#id_generation_choice');
        var $modificationChoice = $('#id_modification_choice');
        
        // При изменении типа транспорта - загружаем марки
        $vehicleType.on('change', function() {
            var vehicleType = $(this).val();
            
            // Очищаем зависимые поля
            clearSelect($brandChoice);
            clearSelect($modelChoice);
            clearSelect($generationChoice);
            clearSelect($modificationChoice);
            
            if (vehicleType) {
                loadBrands(vehicleType);
            }
        });
        
        // При изменении марки - загружаем модели
        $brandChoice.on('change', function() {
            var brandId = $(this).val();
            var vehicleType = $vehicleType.val();
            
            // Очищаем зависимые поля
            clearSelect($modelChoice);
            clearSelect($generationChoice);
            clearSelect($modificationChoice);
            
            if (brandId && vehicleType) {
                loadModels(vehicleType, brandId);
            }
        });
        
        // При изменении модели - загружаем поколения
        $modelChoice.on('change', function() {
            var modelId = $(this).val();
            var vehicleType = $vehicleType.val();
            
            // Очищаем зависимые поля
            clearSelect($generationChoice);
            clearSelect($modificationChoice);
            
            if (modelId && vehicleType) {
                loadGenerations(vehicleType, modelId);
            }
        });
        
        // При изменении поколения - загружаем модификации
        $generationChoice.on('change', function() {
            var generationId = $(this).val();
            var vehicleType = $vehicleType.val();
            
            // Очищаем зависимые поля
            clearSelect($modificationChoice);
            
            if (generationId && vehicleType) {
                loadModifications(vehicleType, generationId);
            }
        });
        
        // Функция очистки select
        function clearSelect($select) {
            $select.html('<option value="">---------</option>');
        }
        
        // Загрузка марок
        function loadBrands(vehicleType) {
            $.ajax({
                url: '/garage/api/brands/',
                data: { type: vehicleType },
                success: function(data) {
                    if (data.success && data.brands) {
                        var options = '<option value="">---------</option>';
                        data.brands.forEach(function(brand) {
                            options += '<option value="' + brand.id + '">' + brand.name + '</option>';
                        });
                        $brandChoice.html(options);
                    }
                },
                error: function() {
                    alert('Ошибка загрузки марок');
                }
            });
        }
        
        // Загрузка моделей
        function loadModels(vehicleType, brandId) {
            $.ajax({
                url: '/garage/api/models/',
                data: { 
                    type: vehicleType,
                    brand_id: brandId 
                },
                success: function(data) {
                    if (data.success && data.models) {
                        var options = '<option value="">---------</option>';
                        data.models.forEach(function(model) {
                            options += '<option value="' + model.id + '">' + model.name + '</option>';
                        });
                        $modelChoice.html(options);
                    }
                },
                error: function() {
                    alert('Ошибка загрузки моделей');
                }
            });
        }
        
        // Загрузка поколений
        function loadGenerations(vehicleType, modelId) {
            $.ajax({
                url: '/garage/api/generations/',
                data: { 
                    type: vehicleType,
                    model_id: modelId 
                },
                success: function(data) {
                    if (data.success && data.generations) {
                        var options = '<option value="">---------</option>';
                        data.generations.forEach(function(gen) {
                            var label = gen.name;
                            if (gen.year_start) {
                                var yearEnd = gen.year_end || 'н.в.';
                                label += ' (' + gen.year_start + '-' + yearEnd + ')';
                            }
                            options += '<option value="' + gen.id + '">' + label + '</option>';
                        });
                        $generationChoice.html(options);
                    }
                },
                error: function() {
                    alert('Ошибка загрузки поколений');
                }
            });
        }
        
        // Загрузка модификаций
        function loadModifications(vehicleType, generationId) {
            $.ajax({
                url: '/garage/api/modifications/',
                data: { 
                    type: vehicleType,
                    generation_id: generationId 
                },
                success: function(data) {
                    if (data.success && data.modifications) {
                        var options = '<option value="">---------</option>';
                        data.modifications.forEach(function(mod) {
                            options += '<option value="' + mod.id + '">' + mod.name + '</option>';
                        });
                        $modificationChoice.html(options);
                    }
                },
                error: function() {
                    alert('Ошибка загрузки модификаций');
                }
            });
        }
    });
})();
