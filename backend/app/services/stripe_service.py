# app/services/stripe_service.py
import stripe
from app.config import settings


stripe.api_key = settings.stripe_secret_key


async def create_payment_intent(amount_cents: int, business_id: str) -> dict:
    """
    Create a manual-capture PaymentIntent.
    capture_method='manual' means: place an authorization hold now,
    but do NOT take money until we explicitly call capture().
    This is perfect for deposits — authorize at booking, capture at job completion.
    """
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency='usd',
        capture_method='manual',
        metadata={'business_id': business_id}
    )
    return {'id': intent.id, 'client_secret': intent.client_secret}




async def capture_payment(payment_intent_id: str) -> bool:
    """Capture a previously authorized deposit on job completion."""
    try:
        intent = stripe.PaymentIntent.capture(payment_intent_id)
        return intent.status == 'succeeded'
    except stripe.error.StripeError as e:
        print(f'Capture failed: {e}')
        return False

