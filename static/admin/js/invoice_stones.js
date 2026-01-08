(function($) {
    $(document).ready(function() {
        // Function to fetch and update details
        function updateStoneDetails(selectElement) {
            var itemId = selectElement.val();
            var row = selectElement.closest('tr');
            var targetCell = row.find('.field-stones_breakdown');
            
            // If stones_breakdown is read-only, it might be inside a div.readonly or just a td
            // In tabular inline, it's a td with class field-stones_breakdown
            
            if (!targetCell.length) {
                // If it's not found (maybe hidden or different structure), try finding by index or other means
                // But standard django tabular inline has these classes
                return;
            }

            if (!itemId) {
                targetCell.html("-");
                return;
            }
            
            targetCell.html('<span style="color:#888;">جاري التحميل...</span>');

            $.ajax({
                url: '/sales/api/item-stones/' + itemId + '/',
                type: 'GET',
                success: function(data) {
                    if (data.html) {
                        targetCell.html(data.html);
                    } else {
                        targetCell.html("-");
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error fetching stones:", error);
                    targetCell.html('<span style="color:red;">خطأ في الجلب</span>');
                }
            });
        }

        // Bind change event to existing and new rows
        $(document).on('change', 'select[id^="id_items-"][id$="-item"]', function() {
            updateStoneDetails($(this));
        });
        
        // Also trigger on select2 select if select2 is used
        $(document).on('select2:select', 'select[id^="id_items-"][id$="-item"]', function(e) {
             updateStoneDetails($(this));
        });

    });
})(django.jQuery);
