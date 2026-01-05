kdocument.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const session_id = urlParams.get('session');
    const productsContainer = document.getElementById('products');

    if (!session_id) {
        productsContainer.innerHTML = '<p>❌ Не указана сессия. Откройте через Telegram бота.</p>';
        return;
    }

    console.log('Session ID:', session_id);
    fetch(`http://158.160.133.167:5000/api/products?session=${session_id}`)
        .then(response => {
            if (!response.ok) throw new Error(`Сетевая ошибка: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('Полученные товары:', data);
            if (!Array.isArray(data) || data.length === 0) {
                productsContainer.innerHTML = '<p>❌ Товары не найдены в этой сессии.</p>';
                return;
            }

            productsContainer.innerHTML = ''; // Очистить "Загрузка..."

            data.forEach(product => {
                const div = document.createElement('div');
                div.className = 'product';
                div.innerHTML = `
                    <div class="product-card">
                        <h3>${escapeHtml(product.name || 'Без названия')}</h3>
                        <p><strong>Артикул:</strong> ${escapeHtml(product.article || '—')}</p>
                        <p><strong>Бренд:</strong> ${escapeHtml(product.brand || '—')}</p>
                        <p><strong>Объём:</strong> ${escapeHtml(product.volume || '—')}</p>
                        <p class="price"><strong>Цена:</strong> ${formatPrice(product.price)} ₽</p>
                        <p class="description">${escapeHtml(product.description || 'Описание отсутствует')}</p>
                        <button class="add-to-cart" onclick="addToCart(${product.id})">➕ Добавить в корзину</button>
                    </div>
                `;
                productsContainer.appendChild(div);
            });
        })
        .catch(error => {
            console.error('Ошибка загрузки:', error);
            productsContainer.innerHTML = `
                <p>❌ Ошибка загрузки:</p>
                <pre>${error.message}</pre>
                <p><a href="http://158.160.133.167:5000/api/products?session=${session_id}" target="_blank">👉 Проверить данные вручную</a></p>
            `;
        });
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatPrice(price) {
    return Number(price).toLocaleString('ru-RU');
}

function addToCart(productId) {
    alert(`Товар ID ${productId} добавлен в корзину (заглушка). В боте будет реальное добавление.`);
}
