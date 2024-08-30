import os
import base64
import shutil

from fastapi import APIRouter, HTTPException, Response, Query

from config.serverCfg import BASE_PATH, USER_ROOT_PATH, TEMP_PATH, TRASH_PATH

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/")
async def userPost(userHash: str = Query(...)):
  sPath = os.path.join(BASE_PATH, userHash)
  if os.path.exists(sPath):
    raise HTTPException(status_code=409, detail="Directory already exists")
  os.makedirs(os.path.join(sPath, USER_ROOT_PATH))
  os.makedirs(os.path.join(sPath, TEMP_PATH))
  os.makedirs(os.path.join(sPath, TRASH_PATH))
  return Response(status_code=201)

@router.delete("/")
async def userDelete(userHash: str = Query(...)):
  sPath = os.path.join(BASE_PATH, userHash)
  if not os.path.exists(sPath):
    raise HTTPException(status_code=404, detail="Directory not found")
  shutil.rmtree(sPath)
  return Response(status_code=204)