/* Phase 3: List Enhancements - Sortable columns, pagination, search */

(function() {
    'use strict';

    // Add sort indicators to all table headers with data-sort attribute
    function initSortableTables() {
        document.querySelectorAll('table th[data-sort]').forEach(function(th) {
            th.style.cursor = 'pointer';
            th.addEventListener('click', function() {
                var table = th.closest('table');
                var tbody = table.querySelector('tbody');
                var rows = Array.from(tbody.querySelectorAll('tr'));
                var colIdx = Array.from(th.parentElement.children).indexOf(th);
                var key = th.getAttribute('data-sort');
                var currentDir = th.getAttribute('data-dir') || 'none';

                // Reset other headers
                table.querySelectorAll('th[data-sort]').forEach(function(h) {
                    if (h !== th) {
                        h.removeAttribute('data-dir');
                        h.textContent = h.textContent.replace(/ ?[▲▼]$/, '');
                    }
                });

                if (currentDir === 'none' || currentDir === 'desc') {
                    rows.sort(function(a, b) {
                        var va = a.children[colIdx] ? a.children[colIdx].textContent.trim().toLowerCase() : '';
                        var vb = b.children[colIdx] ? b.children[colIdx].textContent.trim().toLowerCase() : '';
                        if (va === vb) return 0;
                        if (!isNaN(parseFloat(va)) && !isNaN(parseFloat(vb))) {
                            return parseFloat(va) - parseFloat(vb);
                        }
                        return va < vb ? -1 : 1;
                    });
                    th.setAttribute('data-dir', 'asc');
                    th.textContent = th.textContent.replace(/ ?[▲▼]$/, '') + ' ▲';
                } else {
                    rows.sort(function(a, b) {
                        var va = a.children[colIdx] ? a.children[colIdx].textContent.trim().toLowerCase() : '';
                        var vb = b.children[colIdx] ? b.children[colIdx].textContent.trim().toLowerCase() : '';
                        if (va === vb) return 0;
                        if (!isNaN(parseFloat(va)) && !isNaN(parseFloat(vb))) {
                            return parseFloat(vb) - parseFloat(va);
                        }
                        return va > vb ? -1 : 1;
                    });
                    th.setAttribute('data-dir', 'desc');
                    th.textContent = th.textContent.replace(/ ?[▲▼]$/, '') + ' ▼';
                }
                rows.forEach(function(row) { tbody.appendChild(row); });
            });
        });
    }

    // Client-side search for tables
    function initSearchFilter(inputId, tableId) {
        var input = document.getElementById(inputId);
        var table = document.getElementById(tableId);
        if (!input || !table) return;

        input.addEventListener('keyup', function() {
            var q = input.value.toLowerCase();
            var rows = table.querySelectorAll('tbody tr');
            rows.forEach(function(row) {
                var text = row.textContent.toLowerCase();
                row.style.display = text.indexOf(q) > -1 ? '' : 'none';
            });
        });
    }

    // Client-side pagination
    function initPagination(tableId, perPage) {
        perPage = perPage || 25;
        var table = document.getElementById(tableId);
        if (!table) return;
        var tbody = table.querySelector('tbody');
        var rows = Array.from(tbody.querySelectorAll('tr'));
        if (rows.length <= perPage) return;

        var wrapper = document.createElement('div');
        wrapper.className = 'pagination-controls';
        wrapper.style.cssText = 'display:flex;justify-content:space-between;align-items:center;padding:8px 0;font-size:13px';

        var info = document.createElement('span');
        info.className = 'pagination-info';
        wrapper.appendChild(info);

        var pages = document.createElement('div');
        pages.className = 'pagination-pages';
        wrapper.appendChild(pages);

        table.parentElement.appendChild(wrapper);

        var totalPages = Math.ceil(rows.length / perPage);
        var currentPage = 1;

        function showPage(page) {
            currentPage = page;
            var start = (page - 1) * perPage;
            var end = start + perPage;
            rows.forEach(function(row, i) {
                row.style.display = (i >= start && i < end) ? '' : 'none';
            });
            info.textContent = 'Showing ' + (start + 1) + '-' + Math.min(end, rows.length) + ' of ' + rows.length;
            pages.innerHTML = '';
            var prev = document.createElement('button');
            prev.textContent = 'Previous';
            prev.className = 'btn btn-sm btn-outline';
            prev.disabled = page === 1;
            prev.addEventListener('click', function() { if (currentPage > 1) showPage(currentPage - 1); });
            pages.appendChild(prev);
            for (var i = 1; i <= totalPages && i <= 10; i++) {
                var btn = document.createElement('button');
                btn.textContent = i;
                btn.className = 'btn btn-sm ' + (i === page ? 'btn-primary' : 'btn-outline');
                btn.addEventListener('click', function(p) { return function() { showPage(p); }; }(i));
                pages.appendChild(btn);
            }
            var next = document.createElement('button');
            next.textContent = 'Next';
            next.className = 'btn btn-sm btn-outline';
            next.disabled = page === totalPages;
            next.addEventListener('click', function() { if (currentPage < totalPages) showPage(currentPage + 1); });
            pages.appendChild(next);
        }
        showPage(1);
    }

    // Auto-init on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
        initSortableTables();
        // initSearchFilter and initPagination are called explicitly by page templates
        // with specific element IDs
    });

    // Expose to global scope
    window.initSortableTables = initSortableTables;
    window.initSearchFilter = initSearchFilter;
    window.initPagination = initPagination;
})();
