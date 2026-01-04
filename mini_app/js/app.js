// Пример данных (в реальности — от бота)
const products = window.Telegram?.WebApp.initDataUnsafe?.start_param === "debug"
  ? [
    { id: 1, article: "AP-100", name: "Jinsul Cream Rich", brand: "Amore Pacific", volume: "60ml", price: 19770, description: "Питательный крем с экстрактом женьшеня..." },
    { id: 2, article: "AP-101", name: "Brightening Ampoule", brand: "Amore Pacific", volume: "20ml", price: 16500, description: "Осветляющая сыворотка..." },
  ]
  : [];

const cart = {};
let cartCount = 0;
let totalPrice = 0;

// DOM
const productsEl = document.getElementById("products");
const cartBtn = document.getElementById("cartBtn");
const cartPanel = document.getElementById("cartPanel");
const closeCart = document.getElementById("closeCart");
const cartItems = document.getElementById("cartItems");
const totalPriceEl = document.getElementById("totalPrice");
const checkoutBtn = document.getElementById("checkoutBtn");

// Открыть/закрыть корзину
cartBtn.onclick = () => cartPanel.classList.add("open");
closeCart.onclick = () => cartPanel.classList.remove("open");

// Загрузка товаров
function loadProducts() {
  // Здесь вы будете получать данные от бота через WebApp.sendData или fetch
  // Пока — заглушка
  renderProducts(products);
}

function renderProducts(list) {
  productsEl.innerHTML = "";
  list.forEach(p => {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <div class="card-title">${p.name}</div>
      <div class="card-volume">${p.volume}</div>
      <div class="card-price">${p.price.toLocaleString('ru-RU')} ₽</div>
      <button class="add-to-cart" onclick="addToCart(${p.id})">+ Добавить</button>
    `;
    productsEl.appendChild(div);
  });
}

function addToCart(id) {
  const p = products.find(p => p.id === id);
  if (!p) return;
  if (!cart[id]) {
    cart[id] = { ...p, qty: 1 };
    cartCount++;
  } else {
    cart[id].qty++;
  }
  updateCart();
}

function updateCart() {
  cartItems.innerHTML = "";
  totalPrice = 0;
  Object.values(cart).forEach(item => {
    totalPrice += item.price * item.qty;
    const div = document.createElement("div");
    div.className = "cart-item";
    div.innerHTML = `
      <div class="cart-item-name">${item.name}</div>
      <div class="qty-controls">
        <button class="qty-btn" onclick="changeQty(${item.id}, -1)">−</button>
        <span>${item.qty}</span>
        <button class="qty-btn" onclick="changeQty(${item.id}, 1)">+</button>
      </div>
      <div class="cart-item-price">${(item.price * item.qty).toLocaleString('ru-RU')} ₽</div>
    `;
    cartItems.appendChild(div);
  });
  totalPriceEl.textContent = totalPrice.toLocaleString('ru-RU');
  document.getElementById("cartCount").textContent = cartCount;
}

function changeQty(id, delta) {
  if (delta < 0 && cart[id].qty <= 1) {
    delete cart[id];
    cartCount--;
  } else {
    cart[id].qty += delta;
  }
  updateCart();
}

// Оформление
checkoutBtn.onclick = () => {
  const order = Object.values(cart).map(item => `${item.name} ×${item.qty}`).join("\n");
  Telegram.WebApp.sendData(JSON.stringify({ action: "order", order, total: totalPrice }));
};

// Загрузка
loadProducts();

// Инициализация WebApp
Telegram.WebApp.ready();