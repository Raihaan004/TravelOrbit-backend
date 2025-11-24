import razorpay
from app.config import settings

class RazorpayService:
    def __init__(self):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise ValueError("Razorpay credentials not configured")
        
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    def create_order(self, amount: float, currency: str = "INR", receipt: str = None, notes: dict = None):
        """
        Create a Razorpay order.
        Amount should be in major units (e.g. Rupees), this function converts it to paise.
        """
        data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {}
        }
        return self.client.order.create(data=data)

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str):
        """
        Verify the payment signature returned by Razorpay checkout.
        """
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        return self.client.utility.verify_payment_signature(params_dict)

razorpay_service = None

def get_razorpay_service():
    global razorpay_service
    if razorpay_service is None:
        try:
            razorpay_service = RazorpayService()
        except ValueError:
            # Return None or handle gracefully if credentials are missing during startup
            # For now, we'll let it fail when accessed if not configured
            pass
    return razorpay_service
