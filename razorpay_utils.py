import os
import razorpay
from flask import url_for, request

# Initialize Razorpay client
def get_razorpay_client():
    """
    Initialize and return a Razorpay client instance
    """
    key_id = os.environ.get("RAZORPAY_KEY_ID", "")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    
    if not key_id or not key_secret:
        # Log warning that keys are not set
        print("Warning: Razorpay keys are not set. Payment functionality will be limited.")
        return None
    
    return razorpay.Client(auth=(key_id, key_secret))

def create_razorpay_order(amount, currency="INR", receipt=None):
    """
    Create a Razorpay order
    
    Args:
        amount: Amount in paise (INR) or cents (other currencies)
        currency: Currency code (default: INR)
        receipt: Receipt number for reference
        
    Returns:
        order_id or None on failure
    """
    client = get_razorpay_client()
    if not client:
        return None
    
    try:
        data = {
            "amount": amount * 100,  # Convert to paise
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1  # Auto-capture payment
        }
        order = client.order.create(data=data)
        return order["id"]
    except Exception as e:
        print(f"Error creating Razorpay order: {e}")
        return None

def verify_razorpay_payment(payment_id, order_id, signature):
    """
    Verify the Razorpay payment signature
    
    Args:
        payment_id: Razorpay payment ID
        order_id: Razorpay order ID
        signature: Razorpay signature
        
    Returns:
        True if signature is valid, False otherwise
    """
    client = get_razorpay_client()
    if not client:
        return False
    
    try:
        client.utility.verify_payment_signature({
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        })
        return True
    except Exception as e:
        print(f"Payment verification failed: {e}")
        return False

def generate_razorpay_checkout_data(order_id, amount, user_name, campaign_title, user_email):
    """
    Generate data needed for Razorpay checkout
    
    Args:
        order_id: Razorpay order ID
        amount: Amount in rupees
        user_name: Name of the donor
        campaign_title: Title of the campaign
        user_email: Email of the donor
        
    Returns:
        Dictionary with checkout data
    """
    key_id = os.environ.get("RAZORPAY_KEY_ID", "")
    
    return {
        "key": key_id,
        "amount": int(amount * 100),
        "currency": "INR",
        "name": "Sahyog",
        "description": f"Donation for {campaign_title}",
        "order_id": order_id,
        "prefill": {
            "name": user_name,
            "email": user_email
        },
        "theme": {
            "color": "#0d6efd"
        }
    }