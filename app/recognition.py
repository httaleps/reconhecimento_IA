import os
import traceback
from deepface import DeepFace

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACES_DIR = os.environ.get("FACES_DIR", os.path.join(BASE_DIR, "faces"))
MODEL_NAME = "Facenet"
DETECTOR = "retinaface"
DISTANCE_METRIC = "cosine"

# Limiar de confiança: abaixo disso = rostos diferentes
THRESHOLD = 0.40  # cosine: quanto menor, mais parecido. 0.40 é conservador


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACES_DIR = os.environ.get("FACES_DIR", os.path.join(BASE_DIR, "faces"))

MODEL_NAME = "Facenet"
DETECTOR = "retinaface"
DISTANCE_METRIC = "cosine"
THRESHOLD = 0.40


def register_face(filepath: str, name: str) -> dict:
    from deepface import DeepFace  # ← import lazy aqui
    try:
        faces = DeepFace.extract_faces(
            img_path=filepath,
            detector_backend=DETECTOR,
            enforce_detection=False,
            align=True
        )
        valid_faces = [f for f in faces if f.get("confidence", 0) > 0.3]
        if not valid_faces:
            return {"success": False, "message": "Nenhum rosto detectado."}
        return {"success": True, "message": f"Rosto detectado ({len(valid_faces)} rosto(s))", "face_count": len(valid_faces)}
    except Exception as e:
        return {"success": False, "message": f"Erro ao processar imagem: {str(e)}"}


def recognize_face(img_path: str, db_path: str = None) -> dict:
    from deepface import DeepFace  # ← import lazy aqui
    from app.database import SessionLocal
    from app import crud

    if db_path is None:
        db_path = FACES_DIR

    db = SessionLocal()
    try:
        image_extensions = (".jpg", ".jpeg", ".png", ".webp")
        all_images = [
            f for root, dirs, files in os.walk(db_path)
            for f in files if f.lower().endswith(image_extensions)
        ]
        if not all_images:
            return {"recognized": False, "message": "Nenhum rosto cadastrado.", "confidence": 0.0, "person": None}

        results = DeepFace.find(
            img_path=img_path,
            db_path=db_path,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR,
            distance_metric=DISTANCE_METRIC,
            enforce_detection=True,
            silent=True
        )

        if not results or results[0].empty:
            crud.create_recognition_log(db, "Desconhecido", 0.0, False)
            return {"recognized": False, "message": "Rosto não reconhecido.", "confidence": 0.0, "person": None}

        df = results[0]
        distance_col = [c for c in df.columns if "distance" in c.lower()]
        if not distance_col:
            return {"recognized": False, "message": "Erro ao processar resultado.", "confidence": 0.0}

        df_sorted = df.sort_values(distance_col[0])
        best = df_sorted.iloc[0]
        distance = float(best[distance_col[0]])
        confidence = round(max(0.0, min(1.0, 1.0 - distance)) * 100, 2)

        parts = best["identity"].replace("\\", "/").split("/")
        person_folder = parts[-2] if len(parts) >= 2 else "desconhecido"
        person_name = person_folder.replace("_", " ").title()
        recognized = distance <= THRESHOLD

        persons = crud.get_all_persons(db)
        person_id = next((p.id for p in persons if p.name.lower().replace(" ", "_") == person_folder.lower()), None)

        crud.create_recognition_log(db, person_name if recognized else "Desconhecido", confidence, recognized, person_id if recognized else None)

        if recognized:
            return {"recognized": True, "person": person_name, "confidence": confidence, "distance": round(distance, 4), "message": f"✅ {person_name} ({confidence}%)"}
        else:
            return {"recognized": False, "person": None, "confidence": confidence, "distance": round(distance, 4), "message": f"❌ Não reconhecido (melhor: {person_name}, {confidence}%)"}

    except Exception as e:
        if "Face could not be detected" in str(e) or "No face detected" in str(e):
            return {"recognized": False, "message": "Nenhum rosto detectado na câmera.", "confidence": 0.0, "person": None}
        crud.create_recognition_log(db, "Erro", 0.0, False)
        return {"recognized": False, "message": f"Erro: {str(e)}", "confidence": 0.0, "person": None}
    finally:
        db.close()
