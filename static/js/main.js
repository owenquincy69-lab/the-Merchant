
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const productGrid = document.getElementById("productGrid");
    const categoryButtons = [...document.querySelectorAll(".category-btn")];
    const categoryLinks = document.querySelectorAll("[data-category-link]");
    const menuToggle = document.getElementById("menuToggle");
    const nav = document.getElementById("mainNav");
    const countLabel = document.querySelector(".product-count");

    let selectedCategory = "all";

    const normalize = (value) =>
        String(value || "").trim().toLowerCase();

    function getCards() {
        return productGrid
            ? [...productGrid.querySelectorAll(".product-card")]
            : [];
    }

    function getEmptyMessage() {
        if (!productGrid) return null;

        let message = productGrid.querySelector(".filter-empty");

        if (!message) {
            message = document.createElement("div");
            message.className = "empty-products filter-empty";
            message.hidden = true;
            message.innerHTML = `
                <span class="empty-icon" aria-hidden="true">⌕</span>
                <h3>No matching products</h3>
                <p>Try another search or choose a different category.</p>
            `;
            productGrid.appendChild(message);
        }

        return message;
    }

    function filterProducts() {
        if (!productGrid) return;

        const query = normalize(searchInput?.value);
        const cards = getCards();
        let visibleCount = 0;

        cards.forEach((card) => {
            const name = normalize(card.dataset.name);
            const category = normalize(card.dataset.category);
            const searchableText = normalize(card.textContent);

            const matchesSearch =
                !query ||
                name.includes(query) ||
                searchableText.includes(query);

            const matchesCategory =
                selectedCategory === "all" ||
                category === selectedCategory;

            const visible = matchesSearch && matchesCategory;

            card.hidden = !visible;

            if (visible) visibleCount++;
        });

        if (countLabel) {
            countLabel.textContent =
                `${visibleCount} product${visibleCount === 1 ? "" : "s"}`;
        }

        const emptyMessage = getEmptyMessage();

        if (emptyMessage) {
            emptyMessage.hidden = visibleCount !== 0 || cards.length === 0;
        }
    }

    function selectCategory(category) {
        selectedCategory = normalize(category) || "all";

        categoryButtons.forEach((button) => {
            const active =
                normalize(button.dataset.category) === selectedCategory;

            button.classList.toggle("active", active);
            button.setAttribute("aria-pressed", String(active));
        });

        filterProducts();
    }

    categoryButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectCategory(button.dataset.category);
        });
    });

    categoryLinks.forEach((link) => {
        link.addEventListener("click", () => {
            const category = normalize(link.dataset.categoryLink);

            const matchingButton = categoryButtons.find(
                (button) =>
                    normalize(button.dataset.category) === category
            );

            if (matchingButton) {
                selectCategory(matchingButton.dataset.category);
            }
        });
    });

    searchInput?.addEventListener("input", filterProducts);

    function setMenuOpen(open) {
        if (!nav || !menuToggle) return;

        nav.classList.toggle("open", open);
        menuToggle.setAttribute("aria-expanded", String(open));
        menuToggle.setAttribute(
            "aria-label",
            open ? "Close navigation" : "Open navigation"
        );
    }

    menuToggle?.addEventListener("click", () => {
        setMenuOpen(!nav?.classList.contains("open"));
    });

    nav?.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => setMenuOpen(false));
    });

    document.addEventListener("keydown", (event) => {
        const target = event.target;
        const typing =
            target instanceof HTMLElement &&
            (target.isContentEditable ||
                ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

        if (event.key === "Escape") {
            setMenuOpen(false);
        }

        if (
            event.key === "/" &&
            !typing &&
            searchInput &&
            !event.ctrlKey &&
            !event.metaKey &&
            !event.altKey
        ) {
            event.preventDefault();
            searchInput.focus();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 760) setMenuOpen(false);
    });

    filterProducts();
});
