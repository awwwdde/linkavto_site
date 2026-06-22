(function () {
    'use strict';

    var $ = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : (window.jQuery || window.$);
    if (typeof $ !== 'function') return;

    var TIRE_GROUP  = '#tire_details-group';
    var WHEEL_GROUP = '#wheel_details-group';

    function update() {
        var productType   = $('#id_product_type').val();
        var tireWheelType = $('#id_tire_wheel_type').val();
        var isTireWheel   = productType === 'tire_wheel';

        if (!isTireWheel) {
            $(TIRE_GROUP).hide();
            $(WHEEL_GROUP).hide();
            return;
        }

        if (tireWheelType === 'tire') {
            $(TIRE_GROUP).show();
            $(WHEEL_GROUP).hide();
        } else if (tireWheelType === 'wheel') {
            $(TIRE_GROUP).hide();
            $(WHEEL_GROUP).show();
        } else {
            $(TIRE_GROUP).show();
            $(WHEEL_GROUP).show();
        }
    }

    $(document).ready(function () {
        update();
        $('#id_product_type').on('change', update);
        $('#id_tire_wheel_type').on('change', update);
    });
})();
