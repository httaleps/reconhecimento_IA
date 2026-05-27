---
title: FaceID Reconhecimento Facial
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# FaceID — Sistema de Reconhecimento Facial

Sistema acadêmico de reconhecimento facial desenvolvido com DeepFace e FastAPI, com suporte a cadastro de rostos, reconhecimento em tempo real via câmera e histórico de identificações.

---

## Tecnologias Utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python 3.11 | Linguagem principal |
| FastAPI | API REST e servidor web |
| DeepFace | Detecção e reconhecimento facial |
| TensorFlow / Keras | Backend do modelo de IA |
| PostgreSQL | Banco de dados relacional |
| SQLAlchemy | ORM para acesso ao banco |
| Cloudinary | Armazenamento persistente de imagens |
| Uvicorn | Servidor ASGI |
| Jinja2 | Renderização de templates HTML |

---

## Funcionalidades

- Cadastro de pessoas com foto via upload ou câmera
- Reconhecimento facial em tempo real com porcentagem de confiança
- Suporte a rostos frontais e em perfil (detector RetinaFace)
- Histórico completo de reconhecimentos com timestamp
- Interface web responsiva sem dependência de frameworks frontend
- API REST documentada automaticamente via Swagger

---

## Estrutura do Projeto

```
.
├── app/
│   ├── main.py          # Rotas e inicialização da API
│   ├── models.py        # Modelos do banco de dados
│   ├── database.py      # Configuração da conexão
│   ├── crud.py          # Operações no banco
│   ├── recognition.py   # Lógica de reconhecimento facial
│   └── storage.py       # Integração com Cloudinary
├── templates/
│   └── index.html       # Interface web
├── static/              # Arquivos estáticos
├── Dockerfile           # Configuração para deploy
├── requirements.txt
└── run.py               # Ponto de entrada local
```

---

## Endpoints da API

| Método | Rota | Descricao |
|---|---|---|
| GET | / | Interface web |
| POST | /api/register | Cadastrar pessoa (form-data: name, file) |
| POST | /api/recognize | Reconhecer por upload de foto |
| POST | /api/recognize/base64 | Reconhecer por imagem base64 (câmera) |
| GET | /api/persons | Listar pessoas cadastradas |
| DELETE | /api/persons/{id} | Remover pessoa |
| GET | /api/logs | Histórico de reconhecimentos |

Documentação interativa disponível em `/docs` (Swagger UI).

---

## Como Executar Localmente

**Requisitos:** Python 3.11, pip

```bash
# 1. Criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Iniciar o servidor
python run.py

# 4. Acessar no navegador
# http://localhost:8000
```

Na primeira execução o DeepFace fara o download automatico dos modelos de IA (aproximadamente 200MB).

---

## Variaveis de Ambiente

Para deploy, configure as seguintes variaveis:

| Variavel | Descricao |
|---|---|
| DATABASE_URL | URL de conexao com o PostgreSQL |
| CLOUDINARY_CLOUD_NAME | Nome do cloud no Cloudinary |
| CLOUDINARY_API_KEY | Chave de API do Cloudinary |
| CLOUDINARY_API_SECRET | Segredo de API do Cloudinary |

---

## Sistema de Confianca

O reconhecimento utiliza distancia cosseno entre embeddings faciais gerados pelo modelo Facenet.

```
Confianca (%) = (1 - distancia_cosseno) x 100
```

| Faixa | Interpretacao |
|---|---|
| Acima de 75% | Identificacao confiavel |
| Entre 50% e 75% | Identificacao incerta |
| Abaixo de 50% | Nao reconhecido |

O limiar padrao e 0.40 (distancia cosseno), ajustavel em `app/recognition.py`.

---

## Autor

Desenvolvido como projeto academico para avaliacao em disciplina de Inteligencia Artificial.