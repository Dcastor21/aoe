# app/services/booking_service.py
from app.database import supabase
from app.services.stripe_service import create_payment_intent
from app.services.twilio_service import send_sms


def check_availability(date: str, service_type: str,
                        duration_minutes: int, business_id: str) -> list:
    """Return open time slots by finding technicians not yet booked on this date."""
    techs = supabase.table('technicians').select('id, availability') \
        .eq('business_id', business_id).eq('is_active', True).execute()


    booked = supabase.table('jobs').select('technician_id') \
        .eq('business_id', business_id) \
        .gte('scheduled_at', f'{date}T00:00:00') \
        .lte('scheduled_at', f'{date}T23:59:59') \
        .neq('status', 'cancelled').execute()


    booked_ids = {j['technician_id'] for j in booked.data}
    slots = []
    for tech in techs.data:
        if tech['id'] not in booked_ids:
            slots.append({
                'start': f'{date}T08:00:00',
                'end': f'{date}T17:00:00',
                'technician_id': tech['id']
            })
    return slots




def calculate_price(bedrooms: int, bathrooms: int, sqft: int,
                     service_type: str, extras: list, business_id: str) -> float:
    """Apply the tenant's JSONB pricing rules to compute a quote."""
    biz = supabase.table('businesses').select('pricing_config') \
        .eq('id', business_id).single().execute()
    cfg = biz.data['pricing_config']


    price = cfg.get('base_rate', 100)
    price += bedrooms  * cfg.get('per_bedroom', 25)
    price += bathrooms * cfg.get('per_bathroom', 20)
    price *= cfg.get('service_multipliers', {}).get(service_type, 1.0)
    return round(price, 2)




async def create_booking(client_details: dict, slot: dict,
                          price: float, business_id: str) -> dict:
    """Full booking: upsert client → create job → charge deposit → send SMS."""
    # 1. Upsert client
    client = supabase.table('clients').upsert({
        'business_id': business_id,
        'full_name': client_details['full_name'],
        'phone': client_details['phone'],
        'address': client_details['address'],
    }, on_conflict='business_id,phone').execute()
    client_id = client.data[0]['id']


    # 2. Create Stripe authorization hold (30% deposit)
    deposit = round(price * 0.30, 2)
    pi = await create_payment_intent(int(deposit * 100), business_id)


    # 3. Insert job record
    job = supabase.table('jobs').insert({
        'business_id': business_id,
        'client_id': client_id,
        'technician_id': slot['technician_id'],
        'status': 'confirmed',
        'service_type': 'standard_clean',
        'scheduled_at': slot['start'],
        'quoted_price': price,
        'deposit_amount': deposit,
        'stripe_payment_intent_id': pi['id']
    }).execute()
    job_id = job.data[0]['id']
    code   = job_id[:8].upper()


    # 4. Confirm SMS to client
    await send_sms(client_details['phone'],
        f"Hi {client_details['full_name']}! Cleaning confirmed {slot['start'][:10]}. "
        f"Quote: ${price}. Deposit: ${deposit}. Code: {code}")


    return {'job_id': job_id, 'confirmation_code': code}

