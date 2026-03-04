# app/routers/vapi.py
import json
from fastapi import APIRouter, Request
from app.services import booking_service, rag_service


router = APIRouter()


@router.post('/webhook')
async def vapi_webhook(request: Request):
    payload    = await request.json()
    event_type = payload.get('message', {}).get('type')
    biz_id     = payload.get('call', {}).get('metadata', {}).get('business_id', '')


    if event_type == 'assistant-request':
        return build_assistant_config(biz_id)


    elif event_type == 'function-call':
        return await handle_function_call(payload, biz_id)


    elif event_type == 'end-of-call-report':
        print('Transcript:', payload.get('transcript', ''))
        return {'status': 'stored'}


    return {'status': 'ignored'}




def build_assistant_config(business_id: str) -> dict:
    """Return the full Vapi assistant config with all callable tools."""
    return {
        'assistant': {
            'model': {
                'provider': 'openai', 'model': 'gpt-4o',
                'systemPrompt': (
                    'You are a friendly booking receptionist for a cleaning company. '
                    'Help customers book services, answer questions, and schedule appointments. '
                    f'Business ID: {business_id}'
                )
            },
            'tools': [
                build_tool('check_availability', 'Check available time slots',
                    {'date': 'string', 'service_type': 'string', 'duration_minutes': 'integer'},
                    ['date', 'service_type', 'duration_minutes']),
                build_tool('get_price_estimate', 'Calculate a cleaning quote',
                    {'bedrooms': 'integer', 'bathrooms': 'integer', 'service_type': 'string'},
                    ['bedrooms', 'bathrooms', 'service_type']),
                build_tool('create_booking', 'Confirm and create a booking',
                    {'client_name': 'string', 'client_phone': 'string',
                     'client_address': 'string', 'slot_start': 'string',
                     'technician_id': 'string', 'price': 'number'},
                    ['client_name', 'client_phone', 'client_address',
                     'slot_start', 'technician_id', 'price']),
                build_tool('lookup_faq', 'Search SOPs and FAQs',
                    {'query': 'string'}, ['query']),
            ]
        }
    }




def build_tool(name, desc, props, required):
    return {'type': 'function', 'function': {
        'name': name, 'description': desc,
        'parameters': {
            'type': 'object',
            'properties': {k: {'type': v} for k, v in props.items()},
            'required': required
        }
    }}




async def handle_function_call(payload: dict, biz_id: str) -> dict:
    func = payload.get('message', {}).get('functionCall', {})
    name = func.get('name')
    args = json.loads(func.get('parameters', '{}'))


    if name == 'check_availability':
        slots = booking_service.check_availability(
            args['date'], args['service_type'], args['duration_minutes'], biz_id)
        return {'result': slots}


    elif name == 'get_price_estimate':
        price = booking_service.calculate_price(
            args.get('bedrooms',2), args.get('bathrooms',1),
            args.get('sqft',1000), args['service_type'], [], biz_id)
        return {'result': {'price': price}}


    elif name == 'create_booking':
        result = await booking_service.create_booking(
            {'full_name': args['client_name'], 'phone': args['client_phone'],
             'address': args['client_address']},
            {'start': args['slot_start'], 'technician_id': args['technician_id']},
            args['price'], biz_id)
        return {'result': result}


    elif name == 'lookup_faq':
        answer = await rag_service.lookup_faq(args['query'], biz_id)
        return {'result': answer}


    return {'result': 'Unknown function'}

