# QuantumDS

## Overview

> 해당 프로젝트는 Quantum Drive의 부속 호스팅 서버를 위한 코드입니다.
> <br>
> 파일 시스템을 호스팅하고 기초적인 클라우드 서비스의 동작을 위한 파일 암호화와 아키텍처를 구성했습니다.
> 파일 시스템은 Linux 상을 기반으로 합니다.

---

## Tech Stack

| Category | Technology |
|---|---|
| **Framework** | FastAPI |
| **Runtime** | Python 3.7+, Uvicorn (ASGI) |
| **Image Processing** | Pillow (PIL), CairoSVG |
| **Document Handling** | PyMuPDF (fitz), pdf2image, python-pptx, python-docx |
| **Video Processing** | MoviePy |
| **External Tool** | LibreOffice (headless, document → PDF conversion) |
| **Storage** | Filesystem (`/data/quantumDrive/files`) |
| **Serialization** | Pickle + Base64 |

---

## Architecture

```
QuantumDS/
├── server.py           # FastAPI app entry point, middleware, router registration
├── config/
│   └── serverCfg.py   # Server configuration (base path, CORS origins, IP whitelist)
├── modules/
│   ├── tree.py         # Tree data structure for file hierarchy navigation
│   └── utils.py        # Media processing utilities (thumbnail, preview, conversion)
└── routers/
    ├── user.py         # User workspace management
    ├── file.py         # File upload / download / preview / thumbnail
    └── trash.py        # Trash (soft delete), restore, permanent delete
```

### Layers

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │  server.py
│   (CORS Middleware, Router Registration) │
├──────────────┬──────────────────────────┤
│  /user       │  /file        │  /trash  │  routers/
├──────────────┴──────────────────────────┤
│     Business Logic & Utilities          │  modules/
│   (Tree, Thumbnail, Preview, Convert)   │
├─────────────────────────────────────────┤
│         Filesystem Storage              │
│   /data/quantumDrive/files/{userHash}/  │
│     ├── root/   temp/   trash/          │
└─────────────────────────────────────────┘
```

### Storage Layout

```
/data/quantumDrive/files/
└── {userHash}/
    ├── root/               # Primary file storage
    ├── temp/               # Temporary processing workspace
    └── trash/
        ├── {trashID}.tar.gz    # Compressed deleted files
        └── {trashID}.tree      # Serialized path tree (base64)
```

---

## Design

### Router-based Domain Separation
도메인별로 라우터를 분리하여 관심사를 독립적으로 관리합니다 (`user`, `file`, `trash`).

### Tree Data Structure
계층형 파일 경로를 탐색하기 위해 `Node`/`Tree` 클래스를 직접 구현했습니다. 휴지통 복원 시 원래 경로 구조를 그대로 재현하는 데 활용됩니다.

### Streaming Response
대용량 파일 다운로드 시 65KB 청크 단위 `StreamingResponse`를 사용하여 메모리 사용을 최소화합니다.

### Format Adapter
`match-case` 패턴으로 파일 확장자에 따라 적절한 변환 핸들러를 동적으로 선택합니다. 지원 포맷:
- **Image**: JPEG, JPG, PNG, GIF
- **Video**: MP4, AVI, MKV, WEBM, WMV, MOV (1초 프레임 추출)
- **Document**: PDF, PPTX, PPT, DOCX, DOC (LibreOffice → PDF → Image)
- **Vector**: SVG (CairoSVG → PNG)

### Soft Delete with Archive
파일 삭제 시 즉시 제거하지 않고 `tar.gz`로 압축 + 경로 트리를 직렬화하여 `trash/`에 보관합니다. 복원 시 원래 위치로 재배치합니다.

---

## API Endpoints

### User (`/user`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/user/` | 사용자 프로필 이미지 조회 |
| POST | `/user/` | 사용자 워크스페이스 생성 |
| PUT | `/user/` | 프로필 이미지 업데이트 |
| DELETE | `/user/` | 전체 워크스페이스 삭제 |

### File (`/file`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/file/` | 파일 다운로드 (streaming) |
| POST | `/file/` | 파일 업로드 |
| DELETE | `/file/` | 파일 삭제 |
| GET | `/file/thumbnail` | 썸네일 생성 (128×128 PNG) |
| GET | `/file/preview` | 문서 페이지 미리보기 (offset / limit) |

### Trash (`/trash`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/trash/` | 휴지통 메타데이터 조회 |
| POST | `/trash/` | 파일을 휴지통으로 이동 |
| PUT | `/trash/` | 파일 복원 |
| DELETE | `/trash/` | 항목 영구 삭제 또는 전체 비우기 |

---

## Getting Started

### Prerequisites

```bash
# Python 3.7+
pip install fastapi uvicorn pillow python-multipart requests
pip install python-pptx python-docx pdf2image PyMuPDF cairosvg moviepy

# LibreOffice (document conversion)
sudo apt install libreoffice   # Ubuntu/Debian
```

### Configuration

[config/serverCfg.py](config/serverCfg.py)에서 환경에 맞게 수정합니다.

```python
BASE_PATH = "/data/quantumDrive/files"   # 파일 저장 경로

origins = [                               # CORS 허용 출처
    "http://localhost:5300",
]

allowed_ips = [...]                       # IP 화이트리스트
```

### Run

```bash
python server.py
```

서버는 `http://0.0.0.0:5299`에서 실행됩니다.

또는 Uvicorn을 직접 사용할 수 있습니다.

```bash
uvicorn server:app --host 0.0.0.0 --port 5299 --reload
```
