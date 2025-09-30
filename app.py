import os
import time

from flask import Flask, request, jsonify
import xendit
from xendit.apis import InvoiceApi

app = Flask(__name__)

# Set API key
xendit.set_api_key(os.getenv("XENDIT_API_KEY"))


@app.route("/pay", methods=["POST"])
def pay():
    """Create an invoice with multiple payment method options"""
    data = request.get_json()
    name = data.get("name")
    amount = data.get("amount")
    email = data.get("email", "customer@example.com")
    phone = data.get("phone_number")
    description = data.get("description", "Payment")
    
    client = xendit.ApiClient()
    api_instance = InvoiceApi(client)
    
    # Invoice parameters
    invoice_parameters = {
        "external_id": f"invoice-{int(time.time())}",
        "amount": int(amount),
        "payer_email": email,
        "description": description,
        "currency": "PHP",
        "invoice_duration": 86400,  # 24 hours in seconds
        "success_redirect_url": "http://localhost:5000/success",
        "failure_redirect_url": "http://localhost:5000/failed",
        "customer": {
            "given_names": name,
            "mobile_number": phone,
            "email": email
        },
        "customer_notification_preference": {
            "invoice_created": ["email"],
            "invoice_reminder": ["email"],
            "invoice_paid": ["email"]
        },
        "payment_methods": [
            # eWallets
            "GCASH",
            "PAYMAYA", 
            "GRABPAY",
            "SHOPEEPAY",
            
            # Cards
            "CREDIT_CARD",
            "DEBIT_CARD",
        ],
            
        "items": [
            {
                "name": description,
                "quantity": 1,
                "price": int(amount)
            }
        ]
    }
    
    try:
        response = api_instance.create_invoice(
            create_invoice_request=invoice_parameters
        )
        
        return jsonify({
            "id": response.id,
            "external_id": response.external_id,
            "status": str(response.status),
            "amount": response.amount,
            "currency": str(response.currency),
            "invoice_url": response.invoice_url,
            "expiry_date": str(response.expiry_date) if response.expiry_date else None
        })
    except xendit.XenditSdkException as e:
        return jsonify({
            "error": str(e),
            "status": e.status if hasattr(e, 'status') else None
        }), 400


@app.route("/invoice/status/<invoice_id>", methods=["GET"])
def get_invoice_status(invoice_id):
    """Get invoice status"""
    client = xendit.ApiClient()
    api_instance = InvoiceApi(client)
    
    try:
        response = api_instance.get_invoice_by_id(invoice_id)
        return jsonify({
            "id": response.id,
            "external_id": response.external_id,
            "status": str(response.status),
            "amount": response.amount,
            "paid_amount": response.paid_amount if hasattr(response, 'paid_amount') else None
        })
    except xendit.XenditSdkException as e:
        return jsonify({"error": str(e)}), 400


@app.route("/webhook", methods=["POST"])
def catch_webhook():
    webhook_data = request.json
    print("Webhook received:", webhook_data)
    
    # Handle invoice paid webhook
    if webhook_data.get("status") == "PAID":
        print(f"Invoice paid: {webhook_data.get('external_id')}")
    
    return jsonify({}), 200


@app.route("/success")
def payment_success():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            h1 { color: #28a745; }
        </style>
    </head>
    <body>
        <h1>✓ Payment Successful!</h1>
        <p>Thank you for your payment.</p>
        <a href="/">Back to Home</a>
    </body>
    </html>
    """


@app.route("/failed")
def payment_failed():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Failed</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            h1 { color: #dc3545; }
        </style>
    </head>
    <body>
        <h1>✗ Payment Failed</h1>
        <p>Your payment could not be processed. Please try again.</p>
        <a href="/">Back to Home</a>
    </body>
    </html>
    """


@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Xendit Invoice Payment</title>
        <style>
            body { font-family: Arial; max-width: 500px; margin: 50px auto; padding: 20px; }
            h2 { text-align: center; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 15px; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; margin-top: 10px; }
            button:hover { background: #0056b3; }
            .info { background: #e7f3ff; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h2>Create Payment Invoice</h2>
        
        <div class="info">
            <strong>📋 Multiple Payment Options</strong><br>
            The invoice checkout page will show:<br>
            • GCash<br>
            • PayMaya<br>
            • GrabPay<br>
            • ShopeePay<br>
            • Credit/Debit Cards
        </div>
        
        <input type="text" id="name" placeholder="Name" value="Juan Dela Cruz">
        <input type="email" id="email" placeholder="Email" value="customer@example.com">
        <input type="text" id="phone" placeholder="Phone" value="+639171234567">
        <input type="number" id="amount" placeholder="Amount" value="100">
        <input type="text" id="description" placeholder="Description" value="Product Purchase">
        
        <button onclick="createInvoice()">Create Invoice & Proceed to Payment</button>
        
        <script>
            function createInvoice() {
                const data = {
                    name: document.getElementById('name').value,
                    email: document.getElementById('email').value,
                    phone_number: document.getElementById('phone').value,
                    amount: document.getElementById('amount').value,
                    description: document.getElementById('description').value
                };
                
                fetch('/pay', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.invoice_url) {
                        // Redirect to Xendit's hosted invoice page
                        window.location.href = data.invoice_url;
                    } else {
                        alert('Error: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(err => alert('Error: ' + err));
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)