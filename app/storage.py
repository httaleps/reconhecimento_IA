import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import requests
import tempfile

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

CLOUDINARY_ENABLED = bool(os.environ.get("CLOUDINARY_CLOUD_NAME"))


def upload_face(filepath: str, person_name: str) -> dict:
    """Faz upload da foto para o Cloudinary."""
    if not CLOUDINARY_ENABLED:
        return {"url": filepath, "public_id": None}

    folder = f"faceid/{person_name.strip().lower().replace(' ', '_')}"
    result = cloudinary.uploader.upload(
        filepath,
        folder=folder,
        resource_type="image"
    )
    return {
        "url": result["secure_url"],
        "public_id": result["public_id"]
    }


def download_face_tmp(cloudinary_url: str) -> str:
    """Baixa foto do Cloudinary para arquivo temporário e retorna o caminho."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    response = requests.get(cloudinary_url, timeout=15)
    tmp.write(response.content)
    tmp.close()
    return tmp.name


def delete_face(public_id: str):
    """Remove foto do Cloudinary."""
    if CLOUDINARY_ENABLED and public_id:
        cloudinary.uploader.destroy(public_id)


def sync_faces_from_cloudinary(faces_dir: str):
    """
    Baixa todas as fotos do Cloudinary para a pasta local faces/.
    Chamado no startup para o DeepFace ter acesso às imagens.
    """
    if not CLOUDINARY_ENABLED:
        return

    os.makedirs(faces_dir, exist_ok=True)
    try:
        result = cloudinary.api.resources(
            type="upload",
            prefix="faceid/",
            max_results=500
        )
        for resource in result.get("resources", []):
            public_id = resource["public_id"]
            url = resource["secure_url"]
            # Reconstrói estrutura de pastas: faces/nome/arquivo.jpg
            parts = public_id.replace("faceid/", "").split("/")
            if len(parts) < 2:
                continue
            person_folder = os.path.join(faces_dir, parts[0])
            os.makedirs(person_folder, exist_ok=True)
            local_path = os.path.join(person_folder, parts[1] + ".jpg")
            if not os.path.exists(local_path):
                img_data = requests.get(url, timeout=15).content
                with open(local_path, "wb") as f:
                    f.write(img_data)
        print(f"Sincronizado {len(result.get('resources', []))} fotos do Cloudinary")
    except Exception as e:
        print(f"Erro ao sincronizar Cloudinary: {e}")