from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.database import supabase
from app.services.cv_service import run_cv_pipeline
import time


router = APIRouter()


@router.post('/{job_id}/photos')
async def upload_photos(
    job_id: str,
    photo_type: str,  # 'before' or 'after'
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    """
    Upload photos to Supabase Storage.
    If photo_type is 'after', the CV pipeline runs asynchronously.
    BackgroundTasks means the API responds immediately while scoring runs in the background.
    """
    job = supabase.table('jobs').select('business_id') \
        .eq('id', job_id).single().execute()
    biz_id = job.data['business_id']
    paths = []


    for file in files:
        content   = await file.read()
        timestamp = int(time.time())
        path = f'photos/{biz_id}/{job_id}/{photo_type}_{timestamp}_{file.filename}'


        supabase.storage.from_('photos').upload(path, content)
        supabase.table('job_photos').insert({
            'job_id': job_id,
            'photo_type': photo_type,
            'storage_path': path
        }).execute()
        paths.append(path)


    if photo_type == 'after':
        # Non-blocking: respond to client immediately, score in background
        background_tasks.add_task(run_cv_pipeline, job_id)


    return {'uploaded': len(paths), 'paths': paths}

