
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const search = document.getElementById("adminOrderSearch");
    const table = document.getElementById("adminOrdersTable");
    const emptyMessage = document.getElementById("adminOrderSearchEmpty");

    if (!search || !table) {
        return;
    }

    const rows = Array.from(table.querySelectorAll("tbody tr"));

    search.addEventListener("input", () => {
        const term = search.value.trim().toLowerCase();
        let visibleRows = 0;

        rows.forEach((row) => {
            const isEmptyState = row.querySelector(".empty-table-cell");

            if (isEmptyState) {
                row.hidden = term.length > 0;
                return;
            }

            const matches = row.textContent.toLowerCase().includes(term);
            row.hidden = !matches;

            if (matches) {
                visibleRows++;
            }
        });

        if (emptyMessage) {
            emptyMessage.hidden = !(term && visibleRows === 0);
        }
    });
});
