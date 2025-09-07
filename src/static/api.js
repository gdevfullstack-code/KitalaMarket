// API Configuration
const API_BASE_URL = window.location.origin;

// API Helper functions
class KitalamarketAPI {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'include', // Include cookies for session management
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Authentication
    async login(email, password) {
        return this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    async register(userData) {
        return this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    async logout() {
        return this.request('/api/auth/logout', {
            method: 'POST'
        });
    }

    async getCurrentUser() {
        return this.request('/api/auth/me');
    }

    async checkSession() {
        return this.request('/api/auth/check-session');
    }

    // Products
    async getProducts(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/products?${queryString}`);
    }

    async getProduct(productId) {
        return this.request(`/api/products/${productId}`);
    }

    async compareProducts(productIds) {
        return this.request('/api/products/compare', {
            method: 'POST',
            body: JSON.stringify({ product_ids: productIds })
        });
    }

    async getCategories() {
        return this.request('/api/products/categories');
    }

    async getBrands(category = null) {
        const params = category ? `?category=${category}` : '';
        return this.request(`/api/products/brands${params}`);
    }

    async getTrendingProducts(limit = 10) {
        return this.request(`/api/products/trending?limit=${limit}`);
    }

    async toggleFavorite(productId) {
        return this.request('/api/products/favorites', {
            method: 'POST',
            body: JSON.stringify({ product_id: productId })
        });
    }

    async getUserFavorites() {
        return this.request('/api/products/user-favorites');
    }

    async getMarketAnalysis(category = null, brand = null) {
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (brand) params.append('brand', brand);
        return this.request(`/api/products/market-analysis?${params.toString()}`);
    }

    // Messages/Chat
    async getConversations() {
        return this.request('/api/messages/conversations');
    }

    async getConversationMessages(partnerId) {
        return this.request(`/api/messages/conversation/${partnerId}`);
    }

    async sendMessage(receiverId, content, productId = null) {
        return this.request('/api/messages/send', {
            method: 'POST',
            body: JSON.stringify({
                receiver_id: receiverId,
                content: content,
                product_id: productId
            })
        });
    }

    async getUnreadCount() {
        return this.request('/api/messages/unread-count');
    }

    async checkNewMessages(since = null) {
        const params = since ? `?since=${since}` : '';
        return this.request(`/api/messages/new-messages${params}`);
    }

    // Cart and Orders
    async getCart() {
        return this.request('/api/orders/cart');
    }

    async addToCart(productId, quantity = 1) {
        return this.request('/api/orders/cart/add', {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        });
    }

    async updateCartItem(productId, quantity) {
        return this.request('/api/orders/cart/update', {
            method: 'PUT',
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        });
    }

    async removeFromCart(productId) {
        return this.request('/api/orders/cart/remove', {
            method: 'DELETE',
            body: JSON.stringify({ product_id: productId })
        });
    }

    async clearCart() {
        return this.request('/api/orders/cart/clear', {
            method: 'DELETE'
        });
    }

    async createOrder(orderData) {
        return this.request('/api/orders/create', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    async getMyOrders(status = null, page = 1) {
        const params = new URLSearchParams({ page: page.toString() });
        if (status) params.append('status', status);
        return this.request(`/api/orders/my-orders?${params.toString()}`);
    }

    async getMySales(status = null, page = 1) {
        const params = new URLSearchParams({ page: page.toString() });
        if (status) params.append('status', status);
        return this.request(`/api/orders/my-sales?${params.toString()}`);
    }

    async getOrder(orderId) {
        return this.request(`/api/orders/${orderId}`);
    }

    // Location
    async geocodeAddress(address) {
        return this.request('/api/location/geocode', {
            method: 'POST',
            body: JSON.stringify({ address })
        });
    }

    async reverseGeocode(latitude, longitude) {
        return this.request('/api/location/reverse-geocode', {
            method: 'POST',
            body: JSON.stringify({ latitude, longitude })
        });
    }

    async getStaticMap(lat, lon, zoom = 15, width = 400, height = 300, marker = true) {
        const params = new URLSearchParams({
            lat: lat.toString(),
            lon: lon.toString(),
            zoom: zoom.toString(),
            width: width.toString(),
            height: height.toString(),
            marker: marker.toString()
        });
        return `${this.baseURL}/api/location/static-map?${params.toString()}`;
    }

    async getStaticMapBase64(lat, lon, zoom = 15, width = 400, height = 300, marker = true) {
        const params = new URLSearchParams({
            lat: lat.toString(),
            lon: lon.toString(),
            zoom: zoom.toString(),
            width: width.toString(),
            height: height.toString(),
            marker: marker.toString()
        });
        return this.request(`/api/location/static-map-base64?${params.toString()}`);
    }

    async getProductLocation(productId) {
        return this.request(`/api/location/product-location/${productId}`);
    }

    async getNearbyProducts(lat, lon, radius = 10) {
        const params = new URLSearchParams({
            lat: lat.toString(),
            lon: lon.toString(),
            radius: radius.toString()
        });
        return this.request(`/api/location/nearby-products?${params.toString()}`);
    }

    // Payment
    async getPaymentMethods() {
        return this.request('/api/payment/methods');
    }

    async requestMTNPayment(orderId, phoneNumber) {
        return this.request('/api/payment/mtn/request-to-pay', {
            method: 'POST',
            body: JSON.stringify({
                order_id: orderId,
                phone_number: phoneNumber
            })
        });
    }

    async checkMTNPaymentStatus(transactionId) {
        return this.request(`/api/payment/mtn/status/${transactionId}`);
    }

    async getPendingPayments() {
        return this.request('/api/payment/pending-payments');
    }

    async cancelPayment(transactionId) {
        return this.request('/api/payment/cancel-payment', {
            method: 'POST',
            body: JSON.stringify({ transaction_id: transactionId })
        });
    }

    async getPaymentHistory(page = 1) {
        return this.request(`/api/payment/payment-history?page=${page}`);
    }

    // OAuth Authentication
    async googleLogin() {
        return this.request('/api/oauth/google/login');
    }

    async facebookLogin() {
        return this.request('/api/oauth/facebook/login');
    }

    async simulateGoogleLogin(email = null) {
        return this.request('/api/oauth/google/simulate', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    async simulateFacebookLogin(email = null) {
        return this.request('/api/oauth/facebook/simulate', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    async linkOAuthAccount(provider, providerId) {
        return this.request('/api/oauth/link-account', {
            method: 'POST',
            body: JSON.stringify({
                provider: provider,
                provider_id: providerId
            })
        });
    }

    async unlinkOAuthAccount(provider) {
        return this.request('/api/oauth/unlink-account', {
            method: 'POST',
            body: JSON.stringify({ provider })
        });
    }

    async getLinkedAccounts() {
        return this.request('/api/oauth/linked-accounts');
    }

    // Premium Subscription
    async getPremiumPlans() {
        return this.request('/api/premium/plans');
    }

    async getCurrentPlan() {
        return this.request('/api/premium/current-plan');
    }

    async subscribeToPremium(planId, phoneNumber) {
        return this.request('/api/premium/subscribe', {
            method: 'POST',
            body: JSON.stringify({
                plan_id: planId,
                phone_number: phoneNumber
            })
        });
    }

    async checkPremiumPaymentStatus(transactionId) {
        return this.request(`/api/premium/payment-status/${transactionId}`);
    }

    async cancelPremiumSubscription() {
        return this.request('/api/premium/cancel-subscription', {
            method: 'POST'
        });
    }

    async getPremiumFeatures() {
        return this.request('/api/premium/features');
    }

    async getPremiumUsageStats() {
        return this.request('/api/premium/usage-stats');
    }

    async getPendingPremiumPayments() {
        return this.request('/api/premium/pending-payments');
    }

    // Mobile Money (unified MTN/Airtel)
    async requestMobileMoneyPayment(orderId, phoneNumber) {
        return this.request('/api/payment/mobile-money/request-to-pay', {
            method: 'POST',
            body: JSON.stringify({
                order_id: orderId,
                phone_number: phoneNumber
            })
        });
    }

    async checkMobileMoneyPaymentStatus(transactionId) {
        return this.request(`/api/payment/mobile-money/status/${transactionId}`);
    }
}

// Create global API instance
const api = new KitalamarketAPI();

// Utility functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;

    // Add to page
    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function formatPrice(price) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR'
    }).format(price);
}

function formatDate(dateString) {
    return new Intl.DateTimeFormat('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(dateString));
}

function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) {
        return 'À l\'instant';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `Il y a ${minutes} minute${minutes > 1 ? 's' : ''}`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `Il y a ${hours} heure${hours > 1 ? 's' : ''}`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `Il y a ${days} jour${days > 1 ? 's' : ''}`;
    }
}

// Auto-refresh for chat (every 30 seconds)
let chatRefreshInterval = null;
let lastMessageCheck = null;

function startChatAutoRefresh() {
    if (chatRefreshInterval) {
        clearInterval(chatRefreshInterval);
    }

    chatRefreshInterval = setInterval(async () => {
        try {
            const response = await api.checkNewMessages(lastMessageCheck);
            if (response.new_messages && response.new_messages.length > 0) {
                // Update UI with new messages
                updateChatUI(response.new_messages);
            }
            lastMessageCheck = response.timestamp;
        } catch (error) {
            console.error('Failed to check new messages:', error);
        }
    }, 30000); // 30 seconds
}

function stopChatAutoRefresh() {
    if (chatRefreshInterval) {
        clearInterval(chatRefreshInterval);
        chatRefreshInterval = null;
    }
}

function updateChatUI(newMessages) {
    // This function should be implemented in each page that needs chat updates
    if (typeof handleNewMessages === 'function') {
        handleNewMessages(newMessages);
    }
}

// Session management
async function checkAuthStatus() {
    try {
        const response = await api.checkSession();
        return response.authenticated;
    } catch (error) {
        return false;
    }
}

// Initialize API when page loads
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication status
    const isAuthenticated = await checkAuthStatus();
    
    // Update UI based on auth status
    updateAuthUI(isAuthenticated);
    
    // Start chat auto-refresh if on chat page
    if (window.location.pathname.includes('chat.html') && isAuthenticated) {
        startChatAutoRefresh();
    }
});

function updateAuthUI(isAuthenticated) {
    // Update navigation and other UI elements based on auth status
    const authLinks = document.querySelectorAll('.auth-required');
    const guestLinks = document.querySelectorAll('.guest-only');
    
    authLinks.forEach(link => {
        link.style.display = isAuthenticated ? 'block' : 'none';
    });
    
    guestLinks.forEach(link => {
        link.style.display = isAuthenticated ? 'none' : 'block';
    });
}

// Export for use in other scripts
window.api = api;
window.showNotification = showNotification;
window.formatPrice = formatPrice;
window.formatDate = formatDate;
window.formatRelativeTime = formatRelativeTime;

