import os
import base64
import shutil

from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, Form, Query, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from config.serverCfg import allowed_ips, origins
from routers import user, file, trash

app = FastAPI()

app.include_router(user.router)
app.include_router(file.router)
app.include_router(trash.router)

@app.middleware("http")
def checkIPMiddleware(request: Request, call_next):
  host = request.client.host
  print(host)
  if host not in allowed_ips:
    raise HTTPException(status_code=403, detail="Not allowed")
  return call_next(request)

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)



if __name__ == "__main__":
  import uvicorn
  uvicorn.run('server:app', host="0.0.0.0", port=5299, reload=True)