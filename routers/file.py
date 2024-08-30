import os
import base64
import shutil

from PIL import Image
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, Query, File
from fastapi.responses import StreamingResponse, Response, FileResponse

from config.serverCfg import BASE_PATH, USER_ROOT_PATH

from modules import *

from . import trash

router = APIRouter(prefix="/file", tags=["file"])


@router.get("/")
async def fileGet(userHash: str = Query(...),
                  fileID: str = Query(...)):
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, fileID)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="File not found")
  if os.path.isdir(sPath):
    raise HTTPException(status_code=400, detail="Path is a directory")
  
  def stream():
    with open(sPath, "rb") as f:
      while data := f.read(65536):
        yield data
  
  headers = {"Content-Disposition": f"attachment; filename={fileID}"}
  return StreamingResponse(stream(), media_type="application/octet-stream", headers=headers)


@router.post("/")
async def filePost(userHash: str = Query(...),
                   fileID: str = Query(...),
                   file: Optional[UploadFile] = File(None)):
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, fileID)
  if os.path.exists(sPath):
    raise HTTPException(status_code=409, detail="File already exists")
  with open(sPath, "wb") as f:
    shutil.copyfileobj(file.file, f)
  return Response(status_code=201)


@router.delete("/")
async def fileDelete(userHash: str = Query(...),
                     fileID: str = Query(...)):
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, fileID)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="File not found")
  os.remove(sPath)
  return Response(status_code=204)


@router.get("/thumbnail")
async def fileThumbnailGet(userHash: str = Query(...),
                           fileID: str = Query(...),
                           description: str = Query(...)):
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, fileID)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="File not found")
  if os.path.isdir(sPath):
    raise HTTPException(status_code=400, detail="Path is a directory")
  
  match(description):
    case "image":
      image = Image.open(sPath)
    case "video":
      image = await utils.clipVideo(sPath)
    case "pdf":
      image, _ = await utils.pdf2Image(sPath, limit=1)
      image = image[0]
    case "document":
      raise HTTPException(status_code=400, detail="Not Implemented")
    case "audio":
      raise HTTPException(status_code=400, detail="Not Implemented")
    case _:
      raise HTTPException(status_code=400, detail="Invalid format")
  
  thumbnailIO = await utils.thumbnail(image)
  headers = {"Content-Disposition": f"inline; filename={os.path.basename(sPath)}.png"}
  return StreamingResponse(thumbnailIO, media_type=f"image/png", status_code=200, headers=headers)
