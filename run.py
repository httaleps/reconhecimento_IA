"""
Ponto de entrada principal — rode este arquivo no PyCharm ou terminal.
    python run.py
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,          # hot-reload durante desenvolvimento
        log_level="info"
    )
