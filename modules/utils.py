import io

import fitz
from PIL import Image
from moviepy.editor import VideoFileClip

async def thumbnail(img: Image.Image, size=(128, 128), quality=85) -> Image.Image:
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
    bImage = pixmap.tobytes()
    img = Image.frombytes(pixmap.colorspace, pixmap.size, bImage)

    lImgs.append(img)
  return lImgs, -1 if i >= pdfDocument.page_count-1 else i+1
    