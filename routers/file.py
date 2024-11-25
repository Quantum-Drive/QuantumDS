import os
import base64
import shutil
import io
import pickle
import uuid

from PIL import Image
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, Query, File
from fastapi.responses import StreamingResponse, Response, FileResponse

from config.serverCfg import BASE_PATH, USER_ROOT_PATH, TEMP_PATH

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
                           extension: str = Query(...)):
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, fileID)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="File not found")
  if os.path.isdir(sPath):
    raise HTTPException(status_code=400, detail="Path is a directory")
  
  match(extension):
    case "jpeg"|"jpg"|"png"|"gif":
      image = Image.open(sPath)
    case "mp4"|"avi"|"mkv"|"webm"|"wmv"|"mov":
      image = await utils.clipVideo(sPath)
    case "svg":
      image = await utils.svg2Image(sPath)
    case "pdf":
      image, _ = await utils.pdf2Image(sPath, limit=1)
      image = image[0]
    case "pptx"|"ppt"|"docx"|"doc"|"hwp":
      tmp_path = os.path.join(BASE_PATH, userHash, TEMP_PATH)
      image, _ = await utils.documentPreview(sPath, tmp_path, extension, limit=1)
      image = image[0]
    case "audio":
      raise HTTPException(status_code=400, detail="Not Implemented")
    case _:
      raise HTTPException(status_code=400, detail="Invalid format")
  
  thumbnailIO = await utils.thumbnail(image)
  headers = {"Content-Disposition": f"inline; filename={os.path.basename(sPath)}.png"}
  return StreamingResponse(thumbnailIO, media_type=f"image/png", status_code=200, headers=headers)

@router.get("/preview")
async def filePreviewGet(userHash: str = Query(...),
                        fileID: str = Query(...),
                        extension: str = Query(...),
                        offset: int = Query(0),
                        limit: int = Query(None)):
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, fileID)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="File not found")
  if os.path.isdir(sPath):
    raise HTTPException(status_code=400, detail="Path is a directory")
  
  match(extension):
    case "jpeg"|"jpg"|"png"|"gif":
      images = [Image.open(sPath)]
    case "mp4"|"avi"|"mkv"|"webm"|"wmv"|"mov":
      images = [await utils.clipVideo(sPath)]
      extension = "png"
    case "svg":
      images = [await utils.svg2Image(sPath)]
    case "pdf":
      if limit:
        images, _ = await utils.pdf2Image(sPath, offset=offset, limit=limit)
      else:
        images, _ = await utils.pdf2Image(sPath, offset=offset)
      extension = "png"
    case "pptx"|"ppt"|"docx"|"doc":
      tmp_path = os.path.join(BASE_PATH, userHash, TEMP_PATH)
      if limit:
        images, _ = await utils.documentPreview(sPath, tmp_path, extension, offset=offset, limit=limit)
      else:
        images, _ = await utils.documentPreview(sPath, tmp_path, extension, offset=offset)
      extension = "png"
    case _:
      raise HTTPException(status_code=400, detail="Invalid format")
  
  
  async def chunk_generator(data: bytes):
    dataIO = io.BytesIO(data)
    while chunk := dataIO.read(65536):
      yield chunk
  
  headers = {"Content-Disposition": f"attachment; filename={fileID}"}
  return StreamingResponse(chunk_generator(pickle.dumps(images)), status_code=200, media_type="application/octet-stream", headers=headers)
