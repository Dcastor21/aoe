# app/services/cv_service.py
import httpx
from app.database import supabase
from app.config import settings
from app.services.twilio_service import send_sms


async def run_cv_pipeline(job_id: str):
    """
    Full QA pipeline:
    1. Fetch all 'after' photos for this job
    2. Run CleanVision audit on each (blur, duplicates, exposure)
    3. Run Tiliter scoring on each (cleanliness 1-5)
    4. Write results back to job_photos and aggregate to jobs
    5. Alert owner if average score < 3.5
    """
    photos = supabase.table('job_photos').select('*') \
        .eq('job_id', job_id).eq('photo_type', 'after').execute()


    if not photos.data:
        return


    scores = []
    for photo in photos.data:
        signed = supabase.storage.from_('photos') \
            .create_signed_url(photo['storage_path'], 3600)
        url = signed['signedURL']


        audit  = await run_cleanvision_audit(url)
        score  = await get_tiliter_score(url)


        supabase.table('job_photos').update({
            'cv_audit_result': audit,
            'cleanliness_score': score
        }).eq('id', photo['id']).execute()


        scores.append(score)


    avg = round(sum(scores) / len(scores), 1)
    supabase.table('jobs').update(
        {'cleanliness_score': int(avg)}).eq('id', job_id).execute()


    if avg < 3.5:
        print(f'QA ALERT: Job {job_id} scored {avg}/5')
        # TODO: look up owner phone from businesses table and send_sms()




async def run_cleanvision_audit(image_url: str) -> dict:
    """
    Check image quality using CleanVision library.
    In production: download the image to a temp file, then use Imagelab.
    """
    # Simplified — see CleanVision docs for full implementation
    return {
        'is_blurry': False, 'is_dark': False,
        'is_duplicate': False, 'low_information': False
    }




async def get_tiliter_score(image_url: str) -> int:
    """Call Tiliter API to get cleanliness score (1-5)."""
    async with httpx.AsyncClient() as c:
        r = await c.post(
            'https://api.tiliter.com/v1/cleanliness',
            headers={'Authorization': f'Bearer {settings.tiliter_api_key}'},
            json={'image_url': image_url}
        )
        return r.json().get('score', 3)

