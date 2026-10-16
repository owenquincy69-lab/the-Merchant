
document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.getElementById("menuToggle");
    const mainNav = document.getElementById("mainNav");
    const cartDialog = document.getElementById("cartDialog");
    const cartTrigger = document.getElementById("cartTrigger");
    const closeCart = document.getElementById("closeCart");
    const cartItems = document.getElementById("cartItems");
    const cartCount = document.getElementById("cartCount");
    const cartTotal = document.getElementById("cartTotal");
    const cartPayload = document.getElementById("cartPayload");
    const checkoutForm = document.getElementById("checkoutForm");
    const checkoutButton = document.getElementById("checkoutButton");

    const STORAGE_KEY = "theMerchantCartV1";
    let cart = [];

    try {
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
        if (Array.isArray(saved)) {
            cart = saved.filter(item =>
                item &&
                Number.isInteger(Number(item.id)) &&
                Number.isInteger(Number(item.quantity)) &&
                Number(item.quantity) > 0 &&
                Number(item.quantity) <= 50 &&
                Number.isFinite(Number(item.price)) &&
                Number(item.price) >= 0
            ).map(item => ({
                id: Number(item.id),
                name: String(item.name || "Product").slice(0, 150),
                price: Number(item.price),
                image: String(item.image || ""),
                quantity: Number(item.quantity)
            }));
        }
    } catch {
        cart = [];
    }

    const formatMoney = amount =>
        "KSh " + Number(amount).toLocaleString("en-KE", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });

    function saveCart() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
        renderCart();
    }

    function addToCart(product) {
        if (!Number.isInteger(product.id) || product.price < 0) return;

        const existing = cart.find(item => item.id === product.id);

        if (existing) {
            if (existing.quantity >= 50) {
                alert("The maximum quantity per product is 50.");
                return;
            }
            existing.quantity += 1;
        } else {
            cart.push({ ...product, quantity: 1 });
        }

        saveCart();
    }

    function createElement(tag, className, text) {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (text !== undefined) element.textContent = text;
        return element;
    }

    function renderCart() {
        const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);
        const totalPrice = cart.reduce(
            (sum, item) => sum + item.price * item.quantity, 0
        );

        if (cartCount) cartCount.textContent = String(totalQuantity);
        if (cartTotal) cartTotal.textContent = formatMoney(totalPrice);
        if (cartPayload) cartPayload.value = JSON.stringify(
            cart.map(item => ({ id: item.id, quantity: item.quantity }))
        );

        if (!cartItems) return;
        cartItems.replaceChildren();

        if (cart.length === 0) {
            const empty = createElement("div", "empty-inline");
            empty.append(
                createElement("h3", "", "Your bag is waiting."),
                createElement("p", "", "Add something you love from the collection.")
            );
            cartItems.append(empty);
        }

        for (const item of cart) {
            const line = createElement("article", "cart-line");

            if (item.image.startsWith("https://") || item.image.startsWith("http://")) {
                const image = document.createElement("img");
                image.src = item.image;
                image.alt = item.name;
                image.loading = "lazy";
                line.append(image);
            } else {
                line.append(createElement("div", "image-placeholder", "TM"));
            }

            const details = createElement("div");
            details.append(
                createElement("h3", "", item.name),
                createElement("p", "", formatMoney(item.price))
            );

            const quantity = createElement("div", "quantity-control");
            const decrease = createElement("button", "", "−");
            decrease.type = "button";
            decrease.setAttribute("aria-label", "Decrease quantity of " + item.name);
            decrease.addEventListener("click", () => {
                item.quantity -= 1;
                if (item.quantity <= 0) {
                    cart = cart.filter(product => product.id !== item.id);
                }
                saveCart();
            });

            const quantityText = createElement("span", "", String(item.quantity));
            const increase = createElement("button", "", "+");
            increase.type = "button";
            increase.setAttribute("aria-label", "Increase quantity of " + item.name);
            increase.addEventListener("click", () => {
                if (item.quantity >= 50) return;
                item.quantity += 1;
                saveCart();
            });

            quantity.append(decrease, quantityText, increase);

            const remove = createElement("button", "remove-item", "Remove");
            remove.type = "button";
            remove.addEventListener("click", () => {
                cart = cart.filter(product => product.id !== item.id);
                saveCart();
            });

            details.append(quantity, remove);
            line.append(details, createElement("strong", "", formatMoney(item.price * item.quantity)));
            cartItems.append(line);
        }

        if (checkoutButton) {
            checkoutButton.disabled = cart.length === 0;
            checkoutButton.textContent = cart.length ? "Proceed to order" : "Your bag is empty";
        }
    }

    document.querySelectorAll("[data-add-to-cart]").forEach(button => {
        button.addEventListener("click", () => {
            addToCart({
                id: Number(button.dataset.id),
                name: button.dataset.name || "Product",
                price: Number(button.dataset.price),
                image: button.dataset.image || ""
            });

            const originalText = button.textContent;
            button.textContent = "Added to bag ✓";
            window.setTimeout(() => {
                button.textContent = originalText;
            }, 1200);
        });
    });

    if (cartTrigger && cartDialog) {
        cartTrigger.addEventListener("click", () => {
            renderCart();
            if (typeof cartDialog.showModal === "function") {
                cartDialog.showModal();
            }
        });
    }

    if (closeCart && cartDialog) {
        closeCart.addEventListener("click", () => cartDialog.close());
    }

    if (cartDialog) {
        cartDialog.addEventListener("click", event => {
            if (event.target === cartDialog) cartDialog.close();
        });
    }

    if (checkoutForm) {
        checkoutForm.addEventListener("submit", event => {
            if (!cart.length) {
                event.preventDefault();
                return;
            }
            cartPayload.value = JSON.stringify(
                cart.map(item => ({ id: item.id, quantity: item.quantity }))
            );
            // Preserve the bag if the order fails; clear it after a successful redirect.
            sessionStorage.setItem("theMerchantPendingCheckout", "1");
        });
    }

    if (sessionStorage.getItem("theMerchantPendingCheckout") === "1") {
        const message = new URLSearchParams(window.location.search).get("message");
        if (message === "Order placed successfully") {
            cart = [];
            saveCart();
            sessionStorage.removeItem("theMerchantPendingCheckout");
        }
    }

    if (menuToggle && mainNav) {
        menuToggle.addEventListener("click", () => {
            const isOpen = mainNav.classList.toggle("open");
            menuToggle.setAttribute("aria-expanded", String(isOpen));
            menuToggle.textContent = isOpen ? "✕" : "☰";
        });

        mainNav.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                mainNav.classList.remove("open");
                menuToggle.setAttribute("aria-expanded", "false");
                menuToggle.textContent = "☰";
            });
        });
    }

    document.querySelectorAll("[data-copy-referral]").forEach(button => {
        button.addEventListener("click", async () => {
            const input = document.getElementById("referralLink");
            if (!input) return;

            try {
                await navigator.clipboard.writeText(input.value);
                button.textContent = "Copied ✓";
            } catch {
                input.select();
                const copied = document.execCommand("copy");
                button.textContent = copied ? "Copied ✓" : "Select and copy";
            }

            window.setTimeout(() => {
                button.textContent = "Copy link";
            }, 1600);
        });
    });

    renderCart();
});
