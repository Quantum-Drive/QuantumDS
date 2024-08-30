import os
import base64
import tarfile

from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, Query, Form, Response
from fastapi.responses import StreamingResponse

from config.serverCfg import BASE_PATH, USER_ROOT_PATH, TEMP_PATH, TRASH_PATH

router = APIRouter(prefix="/trash", tags=["trash"])

@router.get("/")
async def trashGet(userHash: str = Query(...),
                   trashID: str = Query(...)):
  sTrashPath = os.path.join(BASE_PATH, userHash, TRASH_PATH)
  if not os.path.exists(os.path.join(sTrashPath, f"{trashID}.tree")):
    raise HTTPException(status_code=404, detail="File not found")
  
  with open(os.path.join(sTrashPath, f"{trashID}.tree"), "rb") as f:
    data = f.read()
  
  return Response(content=base64.b64encode(data).decode())

@router.post("/")
async def trashPost(userHash: str = Query(...),
                    trashID: int = Form(...),
                    lFiles: list[str] = Form(...),
                    treePickle: str = Form(...)):
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH)
  sTrashPath = os.path.join(BASE_PATH, userHash, TRASH_PATH)
  if os.path.exists(os.path.join(sTrashPath, f"{trashID}.tree")):
    raise HTTPException(status_code=409, detail="File already exists")
  
  with open(
    os.path.join(sTrashPath, f"{trashID}.tree"), 
    "wb") as f:
    f.write(base64.b64decode(treePickle))
  
  with tarfile.open(os.path.join(sTrashPath, f"{trashID}.tar.gz"), "w:gz") as tar:
    for file in lFiles:
      if not os.path.exists(os.path.join(sPath, file)):
        continue
      tar.add(os.path.join(sPath, file), arcname=file)
  
  for file in lFiles:
    print(os.path.join(sPath, file))
    if not os.path.exists(os.path.join(sPath, file)):
      continue
    os.remove(os.path.join(sPath, file))
  
  return Response(status_code=201)


@router.put("/")
async def trashRestore(userHash: str = Query(...),
                       trashID: str = Form(...),
                       lPrevFiles: list[str] = Form(...),
                       lNewFiles: list[str] = Form(...)):
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH)
  sTempPath = os.path.join(BASE_PATH, userHash, TEMP_PATH)
  sTrashPath = os.path.join(BASE_PATH, userHash, TRASH_PATH)
  if not os.path.exists(os.path.join(sTrashPath, f"{trashID}.tar.gz")):
    raise HTTPException(status_code=404, detail="File not found")
  
  with tarfile.open(os.path.join(sTrashPath, f"{trashID}.tar.gz"), "r:gz") as tar:
    tar.extractall(sTempPath)
  os.remove(os.path.join(sTrashPath, f"{trashID}.tar.gz"))
  
  for prevFile, newFile in zip(lPrevFiles, lNewFiles):
    if not os.path.exists(os.path.join(sTempPath, prevFile)):
      continue
    os.rename(os.path.join(sTempPath, prevFile), os.path.join(sPath, newFile))

  os.remove(os.path.join(sTrashPath, f"{trashID}.tree"))
  
  return Response(status_code=201)


@router.delete("/")
async def trashDelete(userHash: str = Query(...),
                      trashID: Optional[str] = Form(None)):
  sTrashPath = os.path.join(BASE_PATH, userHash, TRASH_PATH)
  if trashID is None:
    for filename in os.listdir(sTrashPath):
      os.remove(os.path.join(sTrashPath, filename))
    return Response(status_code=204)
  
  if not os.path.exists(os.path.join(sTrashPath, f"{trashID}.tar.gz")):
    raise HTTPException(status_code=404, detail="File not found")
  
  os.remove(os.path.join(sTrashPath, f"{trashID}.tar.gz"))
  os.remove(os.path.join(sTrashPath, f"{trashID}.tree"))
  return Response(status_code=204)

