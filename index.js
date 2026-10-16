
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const productGrid = document.getElementById("productGrid");
    const categoryButtons = document.querySelectorAll(".category-btn");
    const menuToggle = document.getElementById("menuToggle");
    const mainNav = document.getElementById("mainNav");
    const resultsCount = document.getElementById("resultsCount");
    const emptyState = document.getElementById("emptyState");
    const sortSelect = document.getElementById("sortSelect");
    const currentYear = document.getElementById("currentYear");

    let selectedCategory = "all";
    let searchTerm = "";
    let sortMode = "default";

    /*
     * Demo products.
     * Replace these with products from your existing data source or API
     * when your backend is connected.
     */
    const products = [
        {
            id: 1,
            name: "Classic Everyday Bag",
            category: "fashion",
            price: 1800,
            description: "A versatile bag for everyday use.",
            image: "",
            url: ""
        },
        {
            id: 2,
            name: "Wireless Earbuds",
            category: "electronics",
            price: 2500,
            description: "Wireless audio for work and travel.",
            image: "",
            url: ""
        },
        {
            id: 3,
            name: "Minimalist Desk Lamp",
            category: "home",
            price: 2200,
            description: "A simple light for your workspace.",
            image: "",
            url: ""
        },
        {
            id: 4,
            name: "Everyday Skincare Set",
            category: "beauty",
            price: 1600,
            description: "A convenient skincare collection.",
            image: "",
            url: ""
        },
        {
            id: 5,
            name: "Classic Wristwatch",
            category: "accessories",
            price: 3200,
            description: "A timeless accessory for your outfit.",
            image: "",
            url: ""
        },
        {
            id: 6,
            name: "Casual Sneakers",
            category: "fashion",
            price: 2800,
            description: "Comfortable footwear for everyday wear.",
            image: "",
            url: ""
        }
    ];

    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, (character) => {
            const entities = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            };

            return entities[character];
        });
    }

    function formatPrice(price) {
        return new Intl.NumberFormat("en-KE", {
            style: "currency",
            currency: "KES",
            maximumFractionDigits: 0
        }).format(Number(price) || 0);
    }

    function getFilteredProducts() {
        const filtered = products.filter((product) => {
            const matchesCategory =
                selectedCategory === "all" ||
                product.category.toLowerCase() === selectedCategory;

            const searchableText = [
                product.name,
                product.description,
                product.category
            ].join(" ").toLowerCase();

            const matchesSearch = searchableText.includes(searchTerm);

            return matchesCategory && matchesSearch;
        });

        if (sortMode === "price-low") {
            filtered.sort((a, b) => a.price - b.price);
        } else if (sortMode === "price-high") {
            filtered.sort((a, b) => b.price - a.price);
        } else if (sortMode === "name") {
            filtered.sort((a, b) => a.name.localeCompare(b.name));
        }

        return filtered;
    }

    function createProductCard(product) {
        const card = document.createElement("article");
        card.className = "product-card";

        const imageContainer = document.createElement("div");
        imageContainer.className = "product-image";

        if (product.image) {
            const image = document.createElement("img");
            image.src = product.image;
            image.alt = product.name;
            image.loading = "lazy";
            image.onerror = () => {
                image.remove();
                imageContainer.textContent = "The Merchant";
            };
            imageContainer.appendChild(image);
        } else {
            imageContainer.textContent = "The Merchant";
            imageContainer.setAttribute("aria-label", "Product image unavailable");
        }

        const details = document.createElement("div");
        details.className = "product-details";

        const category = document.createElement("p");
        category.className = "product-category";
        category.textContent = product.category;

        const title = document.createElement("h3");
        title.className = "product-title";
        title.textContent = product.name;

        const description = document.createElement("p");
        description.className = "product-description";
        description.textContent = product.description;

        const price = document.createElement("p");
        price.className = "product-price";
        price.textContent = formatPrice(product.price);

        details.append(category, title, description, price);

        if (product.url) {
            const link = document.createElement("a");
            link.className = "btn btn-primary product-action";
            link.href = product.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = "View Product";
            details.appendChild(link);
        }

        card.append(imageContainer, details);

        return card;
    }

    function renderProducts() {
        if (!productGrid) return;

        const filteredProducts = getFilteredProducts();
        productGrid.replaceChildren();

        filteredProducts.forEach((product) => {
            productGrid.appendChild(createProductCard(product));
        });

        if (resultsCount) {
            const count = filteredProducts.length;
            resultsCount.textContent =
                `${count} ${count === 1 ? "product" : "products"} found`;
        }

        if (emptyState) {
            emptyState.hidden = filteredProducts.length > 0;
        }
    }

    if (searchInput) {
        searchInput.addEventListener("input", (event) => {
            searchTerm = event.target.value.trim().toLowerCase();
            renderProducts();
        });
    }

    categoryButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectedCategory = button.dataset.category || "all";

            categoryButtons.forEach((item) => {
                const isActive = item === button;
                item.classList.toggle("active", isActive);
                item.setAttribute("aria-pressed", String(isActive));
            });

            renderProducts();
        });

        button.setAttribute(
            "aria-pressed",
            String(button.classList.contains("active"))
        );
    });

    if (sortSelect) {
        sortSelect.addEventListener("change", (event) => {
            sortMode = event.target.value;
            renderProducts();
        });
    }

    if (menuToggle && mainNav) {
        menuToggle.addEventListener("click", () => {
            const isExpanded =
                menuToggle.getAttribute("aria-expanded") === "true";

            menuToggle.setAttribute("aria-expanded", String(!isExpanded));
            mainNav.classList.toggle("open", !isExpanded);
        });

        mainNav.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                mainNav.classList.remove("open");
                menuToggle.setAttribute("aria-expanded", "false");
            });
        });
    }

    renderProducts();
});
