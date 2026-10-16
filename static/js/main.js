
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const productGrid = document.getElementById("productGrid");
    const categoryButtons = document.querySelectorAll(".category-btn");
    const categoryLinks = document.querySelectorAll("[data-category-link]");
    const menuToggle = document.getElementById("menuToggle");
    const nav = document.querySelector(".main-nav");

    let selectedCategory = "all";

    function filterProducts() {
        if (!productGrid) return;

        const query = (searchInput?.value || "").trim().toLowerCase();
        const cards = productGrid.querySelectorAll(".product-card");
        let visibleCount = 0;

        cards.forEach((card) => {
            const name = card.dataset.name || "";
            const category = card.dataset.category || "";
            const matchesSearch = name.includes(query) ||
                card.textContent.toLowerCase().includes(query);

            const matchesCategory = selectedCategory === "all" ||
                category === selectedCategory.toLowerCase();

            const visible = matchesSearch && matchesCategory;
            card.hidden = !visible;

            if (visible) visibleCount++;
        });

        const countLabel = document.querySelector(".product-count");
        if (countLabel) {
            countLabel.textContent = `${visibleCount} product${visibleCount === 1 ? "" : "s"}`;
        }

        let emptyMessage = productGrid.querySelector(".filter-empty");

        if (visibleCount === 0 && cards.length > 0) {
            if (!emptyMessage) {
                emptyMessage = document.createElement("div");
                emptyMessage.className = "empty-products filter-empty";
                emptyMessage.innerHTML =
                    "<span class='empty-icon'>⌕</span>" +
                    "<h3>No matching products</h3>" +
                    "<p>Try another search or choose a different category.</p>";
                productGrid.appendChild(emptyMessage);
            }
            emptyMessage.hidden = false;
        } else if (emptyMessage) {
            emptyMessage.hidden = true;
        }
    }

    categoryButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectedCategory = button.dataset.category || "all";

            categoryButtons.forEach((item) => {
                const active = item === button;
                item.classList.toggle("active", active);
                item.setAttribute("aria-pressed", String(active));
            });

            filterProducts();
        });
    });

    categoryLinks.forEach((link) => {
        link.addEventListener("click", () => {
            const category = link.dataset.categoryLink;
            const matchingButton = Array.from(categoryButtons).find(
                (button) => button.dataset.category.toLowerCase() === category.toLowerCase()
            );

            if (matchingButton) matchingButton.click();
        });
    });

    searchInput?.addEventListener("input", filterProducts);

    menuToggle?.addEventListener("click", () => {
        const isOpen = nav?.classList.toggle("open") || false;
        menuToggle.setAttribute("aria-expanded", String(isOpen));
        menuToggle.textContent = isOpen ? "✕" : "☰";
    });

    nav?.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            nav.classList.remove("open");
            menuToggle?.setAttribute("aria-expanded", "false");
            if (menuToggle) menuToggle.textContent = "☰";
        });
    });

    filterProducts();
});
