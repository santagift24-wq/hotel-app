/* Hotel Ordering System - Customer JS */

let currentOrderType = 'dine_in';
let cart = {
    dine_in: [],
    pre_order: [],
    parcel: []
};

let orderTimers = {
    dine_in: null,
    pre_order: null,
    parcel: null
};

// Initialize
async function loadMenu() {
    try {
        const response = await fetch('/api/menu');
        const data = await response.json();
        
        if (data.success) {
            displayMenu(data.data);
        }
    } catch (error) {
        console.error('Error loading menu:', error);
    }
}

// Display Menu
function displayMenu(items) {
    const grid = document.getElementById('menuGrid');
    grid.innerHTML = '';
    
    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'menu-item';
        div.innerHTML = `
            <div class="menu-item-body">
                <div class="menu-item-name">${item.name}</div>
                <div class="menu-item-category">${item.category}</div>
                <div class="menu-item-price">₹${item.price}</div>
                <div class="quantity-control">
                    <button class="qty-btn" onclick="decreaseQty(${item.id})">−</button>
                    <span class="qty-display" id="qty-${item.id}">0</span>
                    <button class="qty-btn" onclick="increaseQty(${item.id}, ${item.price})">+</button>
                </div>
            </div>
        `;
        grid.appendChild(div);
    });
}

// Increase Quantity
function increaseQty(itemId, price) {
    const cartType = currentOrderType;
    const existing = cart[cartType].find(i => i.id === itemId);
    
    if (existing) {
        existing.quantity += 1;
    } else {
        cart[cartType].push({ id: itemId, quantity: 1, price: price });
    }
    
    updateQtyDisplay(itemId);
    updateCartDisplay();
}

// Decrease Quantity
function decreaseQty(itemId) {
    const cartType = currentOrderType;
    const index = cart[cartType].findIndex(i => i.id === itemId);
    
    if (index !== -1) {
        if (cart[cartType][index].quantity > 1) {
            cart[cartType][index].quantity -= 1;
        } else {
            cart[cartType].splice(index, 1);
        }
    }
    
    updateQtyDisplay(itemId);
    updateCartDisplay();
}

// Update Quantity Display
function updateQtyDisplay(itemId) {
    const cartType = currentOrderType;
    const item = cart[cartType].find(i => i.id === itemId);
    document.getElementById(`qty-${itemId}`).textContent = item ? item.quantity : 0;
}

// Update Cart Display
function updateCartDisplay() {
    const cartType = currentOrderType;
    const items = cart[cartType];
    const totalItems = items.reduce((sum, i) => sum + i.quantity, 0);
    const subtotal = items.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    
    // Calculate bill
    const gstRate = HOTEL.gst_rate;
    const tax = (subtotal * gstRate) / 100;
    const serviceCharge = (subtotal * HOTEL.service_charge_rate) / 100;
    const total = subtotal + tax + serviceCharge;
    
    document.getElementById('cartItemCount').textContent = totalItems;
    document.getElementById('subtotal').textContent = subtotal.toFixed(2);
    document.getElementById('tax').textContent = tax.toFixed(2);
    document.getElementById('serviceCharge').textContent = serviceCharge.toFixed(2);
    document.getElementById('total').textContent = total.toFixed(2);
    
    // Enable/Disable order button
    document.querySelectorAll('.btn-primary').forEach(btn => {
        btn.disabled = totalItems === 0;
    });
}

// Select Order Type
function selectOrderType(type) {
    currentOrderType = type;
    
    // Update active button
    document.querySelectorAll('.order-type-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Reset quantities display
    document.querySelectorAll('.qty-display').forEach(el => {
        const itemId = el.id.replace('qty-', '');
        updateQtyDisplay(parseInt(itemId));
    });
    
    updateCartDisplay();
}

// Confirm Order
function confirmOrder() {
    if (currentOrderType === 'dine_in') {
        showDineInConfirm();
    } else if (currentOrderType === 'pre_order') {
        openModal('timeModal');
    } else if (currentOrderType === 'parcel') {
        openModal('timeModal');
    }
}

// Show Dine-In Confirmation
function showDineInConfirm() {
    const cartType = 'dine_in';
    const items = cart[cartType];
    
    if (items.length === 0) {
        alert('Please add items to cart');
        return;
    }
    
    const subtotal = items.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    const gstRate = HOTEL.gst_rate;
    const tax = (subtotal * gstRate) / 100;
    const serviceCharge = (subtotal * HOTEL.service_charge_rate) / 100;
    const total = subtotal + tax + serviceCharge;
    
    let summary = '<strong>Order Summary:</strong><br>';
    items.forEach(item => {
        summary += `<div class="order-summary-item">
            <span>${item.quantity}x Item #${item.id}</span>
            <span class="summary-price">₹${(item.price * item.quantity).toFixed(2)}</span>
        </div>`;
    });
    summary += `<div style="margin-top: 15px; padding-top: 15px; border-top: 2px solid #ddd;">
        <div class="order-summary-item">
            <span>Subtotal</span>
            <span>₹${subtotal.toFixed(2)}</span>
        </div>
        <div class="order-summary-item">
            <span>Tax (${gstRate}%)</span>
            <span>₹${tax.toFixed(2)}</span>
        </div>
        <div class="order-summary-item">
            <span>Service Charge</span>
            <span>₹${serviceCharge.toFixed(2)}</span>
        </div>
        <div class="order-summary-item" style="border: none; margin-top: 10px;">
            <strong>Total</strong>
            <strong style="color: #667eea; font-size: 18px;">₹${total.toFixed(2)}</strong>
        </div>
    </div>`;
    
    document.getElementById('orderSummary').innerHTML = summary;
    openModal('confirmModal');
    startTimer();
}

// Start 5-minute timer
function startTimer() {
    let timeLeft = 300; // 5 minutes
    
    const updateTimer = () => {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        document.getElementById('timerDisplay').textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        if (timeLeft === 0) {
            finalizeOrder();
        } else {
            timeLeft--;
            orderTimers.dine_in = setTimeout(updateTimer, 1000);
        }
    };
    
    updateTimer();
}

// Finalize Dine-In Order
async function finalizeOrder() {
    const cartType = 'dine_in';
    const items = cart[cartType];
    
    if (items.length === 0) return;
    
    const subtotal = items.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    
    try {
        const response = await fetch('/api/order/dine-in', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                table_id: TABLE_ID,
                items: items,
                subtotal: subtotal
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeModal('confirmModal');
            showSuccess(`Order #${data.order_id} placed successfully!`, data);
            cart[cartType] = [];
            updateCartDisplay();
        }
    } catch (error) {
        console.error('Error placing order:', error);
        alert('Error placing order');
    }
}

// Proceed with Time Selection
async function proceedWithTime() {
    const selectedTime = document.getElementById('selectedTime').value;
    
    if (!selectedTime) {
        alert('Please select a time');
        return;
    }
    
    const cartType = currentOrderType;
    const items = cart[cartType];
    
    if (items.length === 0) {
        alert('Please add items to cart');
        return;
    }
    
    const subtotal = items.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    const endpoint = cartType === 'pre_order' ? '/api/order/pre-order' : '/api/order/parcel';
    const timeKey = cartType === 'pre_order' ? 'arrival_time' : 'pickup_time';
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                items: items,
                subtotal: subtotal,
                [timeKey]: selectedTime
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeModal('timeModal');
            showSuccess(
                `${cartType === 'pre_order' ? 'Pre-order' : 'Parcel order'} placed!<br>Your Order ID: ${data.customer_id}`,
                data
            );
            cart[cartType] = [];
            updateCartDisplay();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error placing order');
    }
}

// Show Success
function showSuccess(message, orderData) {
    document.getElementById('successMessage').innerHTML = message;
    if (orderData.customer_id) {
        document.getElementById('orderIdDisplay').textContent = `Order ID: ${orderData.customer_id}`;
    } else {
        document.getElementById('orderIdDisplay').textContent = `Order ID: #${orderData.order_id}`;
    }
    openModal('successModal');
}

// Cancel Order
function cancelOrder() {
    closeModal('confirmModal');
    if (orderTimers.dine_in) {
        clearTimeout(orderTimers.dine_in);
    }
}

// Reset Order
function resetOrder() {
    closeModal('successModal');
    location.reload();
}

// Modal Functions
function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Close modal on outside click
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    loadMenu();
    updateCartDisplay();
});
