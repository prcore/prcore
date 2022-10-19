from fastapi import APIRouter, File

router = APIRouter()


@router.post("/event-log/")
def upload_event_log(file: bytes = File()):
    return {"file_size": len(file)}
