# FaceID — Sistema de Reconhecimento Facial

Projeto acadêmico de reconhecimento facial usando **DeepFace** + **FastAPI** + **SQLite**.

---

## Estrutura do Projeto

```
face_recognition_project/
├── app/
│   ├── __init__.py
│   ├── main.py          ← API FastAPI (rotas)
│   ├── models.py        ← Modelos do banco (SQLAlchemy)
│   ├── database.py      ← Conexão SQLite
│   ├── crud.py          ← Operações no banco
│   └── recognition.py  ← Lógica DeepFace
├── templates/
│   └── index.html       ← Frontend completo
├── faces/               ← Fotos cadastradas (criado automaticamente)
├── run.py               ← Ponto de entrada
├── requirements.txt
├── render.yaml          ← Config deploy Render.com
└── Procfile
```

---

## Instalação Local (PyCharm)

### 1. Clonar / abrir o projeto no PyCharm

### 2. Criar ambiente virtual
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

> A primeira instalação do DeepFace é pesada (~1GB de modelos). Tenha paciência.

### 4. Rodar o servidor
```bash
python run.py
```

### 5. Acessar no navegador
```
http://localhost:8000
```

---

## API — Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Interface web |
| `POST` | `/api/register` | Cadastrar pessoa (form-data: name, file) |
| `POST` | `/api/recognize` | Reconhecer por upload de foto |
| `POST` | `/api/recognize/base64` | Reconhecer por base64 (câmera) |
| `GET` | `/api/persons` | Listar pessoas cadastradas |
| `DELETE` | `/api/persons/{id}` | Remover pessoa |
| `GET` | `/api/logs` | Histórico de reconhecimentos |

### Documentação automática (Swagger):
```
http://localhost:8000/docs
```

---

## Deploy Gratuito — Render.com

### Passo a passo:

1. **Criar conta em** [render.com](https://render.com) (gratuito)

2. **Subir para GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
   git push -u origin main
   ```

3. **No Render:**
   - New → Web Service
   - Conecte seu repositório GitHub
   - O `render.yaml` já configura tudo automaticamente
   - Clique em **Deploy**

4. **URL pública** será gerada:
   ```
   https://faceid-reconhecimento-facial.onrender.com
   ```

> No plano gratuito do Render, o servidor hiberna após 15 min de inatividade. No primeiro acesso pode demorar ~1 min para "acordar".

---

## Tecnologias

| Lib | Função |
|-----|--------|
| **DeepFace** | Detecção e comparação de rostos |
| **FastAPI** | API REST moderna em Python |
| **SQLite + SQLAlchemy** | Banco de dados local |
| **Uvicorn** | Servidor ASGI |
| **Jinja2** | Templates HTML |

### Modelos DeepFace disponíveis (edite `recognition.py`):
- `Facenet` ← padrão (bom custo-benefício)
- `Facenet512` ← mais preciso, mais lento
- `ArcFace` ← excelente para produção
- `VGG-Face` ← pioneiro, pesado
- `DeepFace` ← modelo original

---

## Como funciona o sistema de confiança

O DeepFace calcula a **distância coseno** entre os embeddings faciais (vetores numéricos que representam o rosto).

```
distância coseno: 0.0 = idêntico | 1.0 = completamente diferente

confiança (%) = (1 - distância) × 100
```

| Confiança | Interpretação |
|-----------|---------------|
| ≥ 75% | Match seguro |
| 50–74% | Match incerto |
| < 50% | Não reconhecido |

O limiar padrão é `0.40` (cosine), ajustável em `recognition.py`.

---

## Banco de Dados

SQLite gerado automaticamente em `faceid.db` com três tabelas:

- **persons** — nome, data de cadastro
- **photos** — caminho das fotos por pessoa
- **recognition_logs** — histórico de reconhecimentos com timestamp e confiança
