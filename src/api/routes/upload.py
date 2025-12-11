import os
import shutil
from typing import Any, Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/registry/upload", tags=["upload"])

class UploadResponse(BaseModel):
    filename: str
    filepath: str
    size: int
    content_type: str

@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the server's data staging area.
    """
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Sanitize filename (basic)
    filename = os.path.basename(file.filename)
    filepath = os.path.join(upload_dir, filename)
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = os.path.getsize(filepath)
        
        return {
            "filename": filename,
            "filepath": os.path.abspath(filepath),
            "size": file_size,
            "content_type": file.content_type or "application/octet-stream"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
