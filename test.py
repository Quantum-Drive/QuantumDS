from fastapi import FastAPI, HTTPException
import requests
from fastapi.responses import StreamingResponse
from io import BytesIO

app = FastAPI()

@app.get("/download/")
async def download_file(url: str):
    try:
        # 원격 파일을 가져오기 위해 requests.get() 사용
        response = requests.get(url)
        response.raise_for_status()  # 요청이 성공하지 않으면 예외 발생

        # 파일 내용을 바이트 스트림으로 변환
        file_stream = BytesIO(response.content)

        # 파일명을 추출하거나 기본 파일명 설정
        file_name = url.split("/")[-1] or "downloaded_file"

        # StreamingResponse로 파일 전달
        return StreamingResponse(file_stream, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={file_name}"})
    except requests.exceptions.RequestException as e:
        # 요청이 실패했을 때 예외 처리
        raise HTTPException(status_code=400, detail=f"Failed to download file: {str(e)}")
      
if __name__ == "__main__":
  import uvicorn
  uvicorn.run("test:app", host="0.0.0.0", port=5299, reload=True)