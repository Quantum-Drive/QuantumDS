import os
import io
import base64
import cairosvg
import subprocess
import uuid
import shutil

import fitz
from pptx import Presentation
from docx import Document
from pdf2image import convert_from_path as pdf2imageConvert
from PIL import Image
from moviepy.editor import VideoFileClip

async def thumbnail(img: Image.Image, size=(128, 128), quality=85):
  img.thumbnail(size)
  imgIO = io.BytesIO()
  img.save(imgIO, format="png", quality=quality)
  imgIO.seek(0)
  
  return imgIO

async def clipVideo(videoPath: str, time: float = 1.0):
  with VideoFileClip(videoPath) as clip:
    frame = clip.get_frame(time)
    img = Image.fromarray(frame)
    
    return img
  
async def pdf2Image(pdfPath: str, offset=0, limit=1e9):
  lImgs = []
  
  pdfDocument = fitz.open(pdfPath)
  pdfLast = min(offset+limit, pdfDocument.page_count)
  
  for i in range(offset, pdfLast):
    page = pdfDocument.load_page(i)
    
    pixmap = page.get_pixmap()
    bImage = pixmap.tobytes('png')
    img = Image.open(io.BytesIO(bImage))

    lImgs.append(img)
  return lImgs, -1 if i >= pdfDocument.page_count-1 else i+1

async def svg2Image(svgPath: str):
  with open(svgPath, 'rb') as f:
    dataSVG = f.read()
    
  return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=dataSVG)))

async def documentPreview(file_path: str, temp_path: str, extension: str, offset=0, limit=1e9):
  temp_path = os.path.join(temp_path, str(uuid.uuid4()))
  with open(os.devnull, 'w') as devnull:
    subprocess.run([
      "libreoffice",
      "--headless",
      "--convert-to", "pdf",
      "--outdir", temp_path,
      file_path
    ], stdout=devnull, stderr=devnull, check=True)
  
  pdf_path = os.path.join(temp_path, f"{os.path.basename(file_path)}.pdf")
  file_name = os.path.basename(file_path)
  images, nxt = await pdf2Image(pdf_path, offset=offset, limit=limit)
  try:
    shutil.rmtree(temp_path)
  except:
    pass
  return images, nxt

def getImageMode(colorspace) -> str:
  if colorspace.name == 'DeviceRGB':
      return 'RGB'
  elif colorspace.name == 'DeviceGray':
      return 'L'  # 'L' 모드는 그레이스케일
  elif colorspace.name == 'DeviceCMYK':
      return 'CMYK'
  else:
      raise ValueError(f"Unsupported colorspace: {colorspace.name}")

def byte2base64(b: bytes) -> str:
  return base64.b64encode(b).decode()