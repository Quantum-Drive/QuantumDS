import os
import base64
import shutil

from fastapi import APIRouter, HTTPException, Response, Query, Form

from modules import utils
from config.serverCfg import BASE_PATH, USER_ROOT_PATH, TEMP_PATH, TRASH_PATH

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/")
async def userImageGet(userHash: str = Query(...), extension: str = Query(None)):
  sPath = os.path.join(BASE_PATH, userHash)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="Directory not found")
  if not extension:
    raise HTTPException(status_code=400, detail="Extension not specified")
  
  try:
    with open(os.path.join(sPath, "profile"), "rb") as f:
      return Response(status_code=200, content=f.read())
  except FileNotFoundError:
    raise HTTPException(status_code=404, detail="File not found")

@router.post("/")
async def userPost(userHash: str = Query(...)):
  sPath = os.path.join(BASE_PATH, userHash)
  if os.path.exists(sPath):
    raise HTTPException(status_code=409, detail="Directory already exists")
  os.makedirs(os.path.join(sPath, USER_ROOT_PATH))
  os.makedirs(os.path.join(sPath, TEMP_PATH))
  os.makedirs(os.path.join(sPath, TRASH_PATH))
  return Response(status_code=201)

@router.put("/")
async def userImageUpdate(userHash: str = Query(...), image: bytes = Form(None)):
  sPath = os.path.join(BASE_PATH, userHash)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="Directory not found")
  if not image:
    try:
      os.remove(os.path.join(sPath, "profile"))
    except FileNotFoundError:
      pass
    return Response(status_code=204)
  
  with open(os.path.join(sPath, "profile"), "wb") as f:
    f.write(image)
  return Response(status_code=201)

@router.delete("/")
async def userDelete(userHash: str = Query(...)):
  sPath = os.path.join(BASE_PATH, userHash)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="Directory not found")
  shutil.rmtree(sPath)
  return Response(status_code=204)