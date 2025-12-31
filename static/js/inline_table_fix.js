/* Inline Table Fix - Align Headers with Data */
document.addEventListener('DOMContentLoaded', function () {
    // Find all inline tables
    const inlineTables = document.querySelectorAll('.inline-group table');

    inlineTables.forEach(function (table) {
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');

        if (!thead || !tbody) return;

        // Get first data row to count actual visible cells
        const firstDataRow = tbody.querySelector('tr');
        if (!firstDataRow) return;

        const dataCells = firstDataRow.querySelectorAll('td');
        const headerCells = thead.querySelectorAll('th');

        // Hide "original" column header if it exists
        headerCells.forEach(function (th) {
            if (th.classList.contains('original') || th.textContent.trim() === '') {
                th.style.display = 'none';
            }
        });

        // Hide "original" column in data rows
        dataCells.forEach(function (td) {
            if (td.classList.contains('original')) {
                td.style.display = 'none';
            }
        });

        // Also apply to all rows
        tbody.querySelectorAll('tr').forEach(function (row) {
            row.querySelectorAll('td.original').forEach(function (td) {
                td.style.display = 'none';
            });
        });
    });
});
