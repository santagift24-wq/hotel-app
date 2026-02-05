/* Admin JS Functions */

// Approve Order
async function approveOrder(orderId) {
    try {
        const response = await fetch('/api/admin/approve-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId })
        });
        
        const data = await response.json();
        if (data.success) {
            alert('Order approved');
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error approving order');
    }
}

// Decline Order
async function declineOrder(orderId) {
    if (confirm('Are you sure you want to decline this order?')) {
        try {
            const response = await fetch('/api/admin/decline-order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_id: orderId })
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Order declined');
                location.reload();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error declining order');
        }
    }
}

// Generate Bill
async function generateBill(orderId) {
    try {
        const response = await fetch('/api/admin/generate-bill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId })
        });
        
        const data = await response.json();
        if (data.success) {
            alert('Bill generated: ' + data.bill_number);
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Update Order Status
async function updateOrderStatus(orderId, status) {
    try {
        const response = await fetch('/api/admin/update-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId, status: status })
        });
        
        const data = await response.json();
        if (data.success) {
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Download QR
function downloadQR(tableId) {
    alert(`QR Code for Table ${tableId} download functionality would be implemented here`);
}

// Regenerate QR
function regenerateQR(tableId) {
    if (confirm('Are you sure you want to regenerate the QR code for this table?')) {
        alert('QR code regenerated for Table ' + tableId);
    }
}

// Toggle Availability
function toggleAvailability(itemId) {
    alert('Toggle availability for item ' + itemId);
}

// View Bill
function viewBill(orderId) {
    alert('Bill details for order ' + orderId);
}

// Print Bill
function printBill(orderId) {
    window.print();
}

// Download Bill as PDF
function downloadBill(orderId) {
    alert('Downloading bill PDF for order ' + orderId);
}

// Open Add Table Modal
function openAddTableModal() {
    alert('Add table functionality would open a modal here');
}

// Open Add Menu Modal
function openAddMenuModal() {
    alert('Add menu item functionality would open a modal here');
}

// Edit Item
function editItem(itemId) {
    alert('Edit item ' + itemId);
}

// Delete Item
function deleteItem(itemId) {
    if (confirm('Are you sure you want to delete this item?')) {
        alert('Item ' + itemId + ' deleted');
    }
}

// Edit Table
function editTable(tableId) {
    alert('Edit table ' + tableId);
}

// Delete Table
function deleteTable(tableId) {
    if (confirm('Are you sure you want to delete this table?')) {
        alert('Table ' + tableId + ' deleted');
    }
}

// Helper: Format Price
function formatPrice(price) {
    return '₹' + price.toFixed(2);
}

// Helper: Format Date
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}
