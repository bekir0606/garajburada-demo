#!/usr/bin/env python3
"""
Garajburada.com Production Server
Bu script production ortamında FastAPI sunucusunu başlatır.
"""

import uvicorn
import os
import sys

def main():
    # Production ayarları
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))  # Railway port'u
    workers = int(os.getenv("WORKERS", 1))
    
    print(f"🚗 Garajburada.com Production Server başlatılıyor...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"👥 Workers: {workers}")
    print(f"🌐 URL: http://{host}:{port}")
    print(f"📊 Admin Panel: http://{host}:{port}/admin")
    print(f"📈 API Docs: http://{host}:{port}/docs")
    
    # Platform port kontrolü
    if port == 8000:
        print("🔧 Platform port'u kullanılıyor: 8000")
    
    # Uvicorn ile sunucuyu başlat
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,  # Production'da reload kapalı
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 