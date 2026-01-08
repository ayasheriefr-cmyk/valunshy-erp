// Auto-populate barcode field when category is selected
(function () {
    'use strict';

    django.jQuery(document).ready(function ($) {
        const $categoryField = $('#id_category');
        const $barcodeField = $('#id_barcode');

        if (!$categoryField.length || !$barcodeField.length) {
            return; // Fields not found, exit
        }

        // Function to fetch and set next barcode
        function updateBarcode() {
            const categoryId = $categoryField.val();

            // Only fetch if category is selected and barcode is empty
            if (!categoryId || $barcodeField.val().trim() !== '') {
                return;
            }

            // Fetch next barcode from server
            $.ajax({
                url: '/api/inventory/next-barcode/',
                method: 'GET',
                data: { category_id: categoryId },
                success: function (data) {
                    if (data.barcode) {
                        $barcodeField.val(data.barcode);
                        $barcodeField.addClass('auto-filled');
                        // Add visual feedback
                        $barcodeField.css('background-color', 'rgba(76, 175, 80, 0.1)');
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Error fetching barcode:', error);
                }
            });
        }

        // Trigger on category change
        $categoryField.on('change', updateBarcode);

        // Also trigger on page load if category is selected but barcode is empty
        if ($categoryField.val() && !$barcodeField.val()) {
            updateBarcode();
        }
    });
})();
