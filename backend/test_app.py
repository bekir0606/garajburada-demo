#!/usr/bin/env python3
"""
Garajburada.com Test App
Railway deployment test için basit FastAPI uygulaması
"""

from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="Garajburada.com Test", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Garajburada.com Test çalışıyor!", "status": "success"}

@app.get("/api/test")
def test_api():
    return {"message": "Garajburada.com API Test çalışıyor!", "status": "success"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Uygulama çalışıyor"}

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚗 Garajburada.com Test App başlatılıyor...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🌐 URL: http://{host}:{port}")
    print(f"📊 Health: http://{host}:{port}/health")
    print(f"📈 API Test: http://{host}:{port}/api/test")
    
    uvicorn.run(app, host=host, port=port, log_level="info") 