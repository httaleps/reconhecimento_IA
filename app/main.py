from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
import uvicorn
import os
import shutil
import base64
import uuid
from datetime import datetime
from app.database import SessionLocal, engine
from app import models, crud
from app.recognition import recognize_face, register_face

# Cria as tabelas no banco
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FaceID API",
    description="Sistema de reconhecimento facial acadêmico com DeepFace",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/faces", StaticFiles(directory="faces"), name="faces")
templates = Jinja2Templates(directory="templates")

os.makedirs("faces", exist_ok=True)


# ─── FRONTEND ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ─── API: CADASTRO ───────────────────────────────────────────────────────────

@app.post("/api/register", summary="Cadastrar novo rosto")
async def register(
    name: str = Form(..., description="Nome do indivíduo"),
    file: UploadFile = File(..., description="Foto do rosto (jpg/png)")
):
    """
    Cadastra um novo rosto no sistema.
    - Salva a imagem na pasta /faces/{name}/
    - Persiste no banco de dados
    """
    db = SessionLocal()
    try:
        # Valida extensão
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(status_code=400, detail="Formato inválido. Use JPG ou PNG.")

        # Cria pasta do indivíduo
        person_dir = os.path.join("faces", name.strip().lower().replace(" ", "_"))
        os.makedirs(person_dir, exist_ok=True)

        # Salva arquivo
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(person_dir, filename)

        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        # Valida se há rosto na imagem via DeepFace
        result = register_face(filepath, name)
        if not result["success"]:
            os.remove(filepath)
            raise HTTPException(status_code=422, detail=result["message"])

        # Persiste no banco
        person = crud.get_or_create_person(db, name)
        photo = crud.create_photo(db, person.id, filepath, filename)

        return {
            "success": True,
            "message": f"✅ {name} cadastrado com sucesso!",
            "person_id": person.id,
            "photo_id": photo.id,
            "filepath": filepath
        }
    finally:
        db.close()


# ─── API: RECONHECIMENTO ─────────────────────────────────────────────────────

@app.post("/api/recognize", summary="Reconhecer rosto")
async def recognize(
    file: UploadFile = File(..., description="Foto para reconhecimento")
):
    """
    Tenta reconhecer o rosto na imagem enviada comparando com o banco cadastrado.
    Retorna nome, confiança e detalhes do match.
    """
    # Salva temporariamente
    tmp_path = f"/tmp/{uuid.uuid4().hex}.jpg"
    with open(tmp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        result = recognize_face(tmp_path, db_path="faces")
        return result
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/recognize/base64", summary="Reconhecer rosto via base64 (câmera)")
async def recognize_base64(payload: dict):
    """
    Reconhece rosto a partir de imagem em base64 (captura da webcam).
    """
    image_data = payload.get("image", "")
    if "," in image_data:
        image_data = image_data.split(",")[1]

    tmp_path = f"/tmp/{uuid.uuid4().hex}.jpg"
    with open(tmp_path, "wb") as f:
        f.write(base64.b64decode(image_data))

    try:
        result = recognize_face(tmp_path, db_path="faces")
        return result
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─── API: LISTAGEM ───────────────────────────────────────────────────────────

@app.get("/api/persons", summary="Listar pessoas cadastradas")
async def list_persons():
    db = SessionLocal()
    try:
        persons = crud.get_all_persons(db)
        return {
            "total": len(persons),
            "persons": [
                {
                    "id": p.id,
                    "name": p.name,
                    "photo_count": len(p.photos),
                    "created_at": p.created_at.isoformat(),
                    "photos": [
                        {"id": ph.id, "path": ph.filepath, "filename": ph.filename}
                        for ph in p.photos
                    ]
                }
                for p in persons
            ]
        }
    finally:
        db.close()


@app.delete("/api/persons/{person_id}", summary="Remover pessoa cadastrada")
async def delete_person(person_id: int):
    db = SessionLocal()
    try:
        person = crud.get_person(db, person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        # Remove arquivos
        folder = os.path.join("faces", person.name.strip().lower().replace(" ", "_"))
        if os.path.exists(folder):
            shutil.rmtree(folder)

        crud.delete_person(db, person_id)
        return {"success": True, "message": f"{person.name} removido com sucesso"}
    finally:
        db.close()


@app.get("/api/logs", summary="Histórico de reconhecimentos")
async def get_logs():
    db = SessionLocal()
    try:
        logs = crud.get_recognition_logs(db)
        return {
            "total": len(logs),
            "logs": [
                {
                    "id": l.id,
                    "person_name": l.person_name,
                    "confidence": l.confidence,
                    "recognized": l.recognized,
                    "timestamp": l.timestamp.isoformat()
                }
                for l in logs
            ]
        }
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
