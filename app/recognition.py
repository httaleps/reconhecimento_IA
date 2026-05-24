import os
import traceback
from deepface import DeepFace
from app.database import SessionLocal
from app import crud

# Modelo padrão — pode trocar por "Facenet512", "ArcFace", "VGG-Face"
MODEL_NAME = "Facenet"
DETECTOR = "retinaface"
DISTANCE_METRIC = "cosine"

# Limiar de confiança: abaixo disso = rostos diferentes
THRESHOLD = 0.40  # cosine: quanto menor, mais parecido. 0.40 é conservador


def register_face(filepath: str, name: str) -> dict:
    try:
        faces = DeepFace.extract_faces(
            img_path=filepath,
            detector_backend=DETECTOR,
            enforce_detection=False,
            align=True               # ← normaliza rotação do rosto
        )

        valid_faces = [f for f in faces if f.get("confidence", 0) > 0.3]

        if not valid_faces:
            return {"success": False, "message": "Nenhum rosto detectado. Tente uma foto com melhor iluminação."}

        return {
            "success": True,
            "message": f"Rosto detectado com sucesso ({len(valid_faces)} rosto(s))",
            "face_count": len(valid_faces)
        }
    except Exception as e:
        return {"success": False, "message": f"Erro ao processar imagem: {str(e)}"}


def recognize_face(img_path: str, db_path: str = "faces") -> dict:
    """
    Compara o rosto da imagem com todos os cadastrados em db_path.
    Retorna o match mais próximo acima do limiar de confiança.
    """
    db = SessionLocal()
    try:
        # Verifica se há rostos cadastrados
        if not os.path.exists(db_path) or not os.listdir(db_path):
            return {
                "recognized": False,
                "message": "Nenhum rosto cadastrado no sistema.",
                "confidence": 0.0,
                "person": None
            }

        # DeepFace.find retorna uma lista de DataFrames (um por rosto encontrado)
        results = DeepFace.find(
            img_path=img_path,
            db_path=db_path,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR,
            distance_metric=DISTANCE_METRIC,
            enforce_detection=True,
            silent=True
        )

        # Sem resultados
        if not results or results[0].empty:
            crud.create_recognition_log(db, "Desconhecido", 0.0, False)
            return {
                "recognized": False,
                "message": "Rosto não reconhecido.",
                "confidence": 0.0,
                "person": None
            }

        df = results[0]
        distance_col = [c for c in df.columns if "distance" in c.lower()]
        if not distance_col:
            return {"recognized": False, "message": "Erro ao processar resultado.", "confidence": 0.0}

        # Ordena pelo menor distance (mais parecido)
        df_sorted = df.sort_values(distance_col[0])
        best = df_sorted.iloc[0]
        distance = float(best[distance_col[0]])

        # Converte distance em porcentagem de confiança (cosine: 0=idêntico, 1=oposto)
        confidence = max(0.0, min(1.0, 1.0 - distance))
        confidence_pct = round(confidence * 100, 2)

        # Extrai nome da pasta
        identity_path = best["identity"]
        # Estrutura: faces/{nome}/{arquivo.jpg}
        parts = identity_path.replace("\\", "/").split("/")
        if len(parts) >= 2:
            person_folder = parts[-2]
            person_name = person_folder.replace("_", " ").title()
        else:
            person_name = "Desconhecido"

        recognized = distance <= THRESHOLD

        # Busca ID da pessoa no banco
        persons = crud.get_all_persons(db)
        person_id = None
        for p in persons:
            if p.name.lower().replace(" ", "_") == person_folder.lower():
                person_id = p.id
                break

        # Registra log
        crud.create_recognition_log(
            db,
            person_name=person_name if recognized else "Desconhecido",
            confidence=confidence_pct,
            recognized=recognized,
            person_id=person_id if recognized else None
        )

        if recognized:
            return {
                "recognized": True,
                "person": person_name,
                "confidence": confidence_pct,
                "distance": round(distance, 4),
                "threshold": THRESHOLD,
                "message": f"✅ Identificado: {person_name} ({confidence_pct}% de confiança)",
                "matched_image": identity_path
            }
        else:
            return {
                "recognized": False,
                "person": None,
                "confidence": confidence_pct,
                "distance": round(distance, 4),
                "threshold": THRESHOLD,
                "message": f"❌ Rosto não reconhecido (melhor match: {person_name}, {confidence_pct}%)"
            }

    except Exception as e:
        tb = traceback.format_exc()
        # Caso comum: nenhum rosto detectado na imagem da câmera
        if "Face could not be detected" in str(e) or "No face detected" in str(e):
            return {
                "recognized": False,
                "message": "Nenhum rosto detectado. Posicione o rosto na câmera.",
                "confidence": 0.0,
                "person": None
            }
        crud.create_recognition_log(db, "Erro", 0.0, False)
        return {
            "recognized": False,
            "message": f"Erro no reconhecimento: {str(e)}",
            "confidence": 0.0,
            "person": None,
            "traceback": tb
        }
    finally:
        db.close()
