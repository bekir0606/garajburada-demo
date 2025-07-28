from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import jwt
from passlib.context import CryptContext
import os

# FastAPI app oluştur
app = FastAPI(title="Garajburada.com API", version="1.0.0")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Veritabanı bağlantısı
DATABASE_URL = "sqlite:///./database/database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Güvenlik
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT ayarları
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Veritabanı bağlantısı için dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Kullanıcı doğrulama
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Şifre hash'leme
def hash_password(password: str):
    return pwd_context.hash(password)

# Şifre doğrulama
def verify_password(plain_password: str, hashed_password: str):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        # Eğer bcrypt hash'i değilse, basit hash ile kontrol et
        import hashlib
        simple_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return simple_hash == hashed_password

# JWT token oluşturma
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Test endpoint
@app.get("/api/test")
def test_api():
    return {"message": "Garajburada.com API çalışıyor!", "status": "success"}

# Statik dosyaları servis et
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Ana sayfa
@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")

# Admin paneli
@app.get("/admin")
def admin_panel():
    return FileResponse("frontend/admin.html")

# Basit admin paneli
@app.get("/simple-admin")
def simple_admin():
    return FileResponse("frontend/simple_admin.html")

# Süresi biten ilanları getir
@app.get("/api/admin/expired-listings")
def get_expired_listings(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Kullanıcının rolünü kontrol et
        cursor.execute("SELECT Role FROM Users WHERE Email = ?", (current_user,))
        user_role = cursor.fetchone()
        
        if not user_role or user_role[0] not in ['superadmin', 'admin', 'moderator']:
            raise HTTPException(status_code=403, detail="Yetkisiz erişim")
        
        # Süresi biten ilanları getir
        query = """
        SELECT 
            l.Id,
            l.Title,
            l.Price,
            l.Status,
            l.CreatedAt,
            l.ExpiresAt,
            u.Email as UserEmail,
            u.Name as UserName
        FROM Listings l
        JOIN Users u ON l.UserId = u.Id
        WHERE l.ExpiresAt IS NOT NULL 
        AND l.ExpiresAt <= datetime('now', '+1 day')
        ORDER BY l.ExpiresAt ASC
        """
        
        cursor.execute(query)
        expired_listings = cursor.fetchall()
        
        listings = []
        for listing in expired_listings:
            expires_at = datetime.strptime(listing[5], '%Y-%m-%d %H:%M:%S') if listing[5] else None
            days_left = (expires_at - datetime.now()).days if expires_at else 0
            
            listings.append({
                "id": listing[0],
                "title": listing[1],
                "price": f"₺{listing[2]:,.0f}" if listing[2] else "Fiyat belirtilmemiş",
                "status": listing[3],
                "created_at": listing[4],
                "expires_at": listing[5],
                "user_email": listing[6],
                "user_name": listing[7],
                "days_left": days_left
            })
        
        conn.close()
        return {"listings": listings, "count": len(listings)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# İlan süresini uzat
@app.put("/api/admin/listings/{listing_id}/extend")
def extend_listing_expiry(listing_id: int, days: int, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Kullanıcının rolünü kontrol et
        cursor.execute("SELECT Role FROM Users WHERE Email = ?", (current_user,))
        user_role = cursor.fetchone()
        
        if not user_role or user_role[0] not in ['superadmin', 'admin', 'moderator']:
            raise HTTPException(status_code=403, detail="Yetkisiz erişim")
        
        # İlanın mevcut süresini kontrol et
        cursor.execute("SELECT ExpiresAt FROM Listings WHERE Id = ?", (listing_id,))
        current_expiry = cursor.fetchone()
        
        if not current_expiry:
            raise HTTPException(status_code=404, detail="İlan bulunamadı")
        
        # Yeni bitiş tarihini hesapla
        if current_expiry[0]:
            new_expiry = datetime.strptime(current_expiry[0], '%Y-%m-%d %H:%M:%S') + timedelta(days=days)
        else:
            new_expiry = datetime.now() + timedelta(days=days)
        
        # İlan süresini güncelle
        cursor.execute(
            "UPDATE Listings SET ExpiresAt = ?, UpdatedAt = ? WHERE Id = ?",
            (new_expiry.strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), listing_id)
        )
        
        conn.commit()
        conn.close()
        
        return {"message": f"İlan süresi {days} gün uzatıldı", "new_expiry": new_expiry.strftime('%Y-%m-%d %H:%M:%S')}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# Süresi biten ilanları toplu uzat
@app.put("/api/admin/listings/extend-all-expired")
def extend_all_expired_listings(days: int, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Kullanıcının rolünü kontrol et
        cursor.execute("SELECT Role FROM Users WHERE Email = ?", (current_user,))
        user_role = cursor.fetchone()
        
        if not user_role or user_role[0] not in ['superadmin', 'admin']:
            raise HTTPException(status_code=403, detail="Yetkisiz erişim")
        
        # Süresi biten tüm ilanları bul
        cursor.execute("""
            SELECT Id FROM Listings 
            WHERE ExpiresAt IS NOT NULL 
            AND ExpiresAt <= datetime('now')
        """)
        expired_listings = cursor.fetchall()
        
        if not expired_listings:
            return {"message": "Süresi biten ilan bulunamadı", "updated_count": 0}
        
        # Tüm süresi biten ilanları uzat
        updated_count = 0
        for listing in expired_listings:
            cursor.execute(
                "UPDATE Listings SET ExpiresAt = datetime(ExpiresAt, '+{} days'), UpdatedAt = ? WHERE Id = ?".format(days),
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), listing[0])
            )
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        return {"message": f"{updated_count} ilanın süresi {days} gün uzatıldı", "updated_count": updated_count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# Kullanıcı kayıt
@app.post("/api/register")
def register(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    city: str = Form(...)
):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # E-posta kontrolü
        cursor.execute("SELECT * FROM Users WHERE Email = ?", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı!")
        
        # Yeni kullanıcı oluştur
        hashed_password = hash_password(password)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO Users (Email, Password, Name, Phone, Role, Status, City, IsPremium, CreatedAt, LastLogin)
            VALUES (?, ?, ?, ?, 'user', 'pending', ?, 0, ?, ?)
        """, (email, hashed_password, name, phone, city, current_time, current_time))
        
        conn.commit()
        conn.close()
        
        return {"message": "Kayıt başarılı! Admin onayı bekleniyor.", "status": "success"}
        
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# Kullanıcı girişi
@app.post("/api/login")
def login(email: str = Form(...), password: str = Form(...)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Users WHERE Email = ?", (email,))
        user = cursor.fetchone()
        
        if user and verify_password(password, user[2]):  # user[2] = password
            # Kullanıcı durumunu kontrol et
            if user[5] == 'pending':  # user[5] = status
                raise HTTPException(status_code=403, detail="Hesabınız henüz onaylanmadı!")
            
            # Son giriş zamanını güncelle
            cursor.execute("UPDATE Users SET LastLogin = ? WHERE Email = ?", 
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email))
            conn.commit()
            
            # JWT token oluştur
            access_token = create_access_token(data={"sub": email})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user[0],
                    "email": user[1],
                    "name": user[3],
                    "role": user[5],
                    "status": user[6]
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Kullanıcılar
@app.get("/api/admin/users")
def get_users(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, Email, Name, Phone, Role, Status, CreatedAt, LastLogin, 
                   ListingCount, IsPremium, City, Country
            FROM Users 
            ORDER BY CreatedAt DESC
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "email": row[1],
                "name": row[2],
                "phone": row[3],
                "role": row[4],
                "status": row[5],
                "createdAt": row[6],
                "lastLogin": row[7],
                "listingCount": row[8],
                "isPremium": bool(row[9]),
                "city": row[10],
                "country": row[11]
            })
        
        return {"users": users, "total": len(users)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - İlanlar
@app.get("/api/admin/listings")
def get_listings(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.Id, l.Title, l.Brand, l.Model, l.Year, l.Price, l.Currency,
                   l.Status, l.Views, l.Favorites, l.CreatedAt, l.UpdatedAt,
                   u.Email as UserEmail, u.Name as UserName
            FROM Listings l
            JOIN Users u ON l.UserId = u.Id
            ORDER BY l.CreatedAt DESC
        """)
        
        listings = []
        for row in cursor.fetchall():
            listings.append({
                "id": row[0],
                "title": row[1],
                "brand": row[2],
                "model": row[3],
                "year": row[4],
                "price": row[5],
                "currency": row[6],
                "status": row[7],
                "views": row[8],
                "favorites": row[9],
                "createdAt": row[10],
                "updatedAt": row[11],
                "userEmail": row[12],
                "userName": row[13]
            })
        
        return {"listings": listings, "total": len(listings)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Ödemeler
@app.get("/api/admin/payments")
def get_payments(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.Id, p.Amount, p.Currency, p.PaymentMethod, p.Status,
                   p.TransactionId, p.PaymentDate, p.Description, p.InvoiceNumber,
                   u.Email as UserEmail, u.Name as UserName
            FROM Payments p
            JOIN Users u ON p.UserId = u.Id
            ORDER BY p.PaymentDate DESC
        """)
        
        payments = []
        for row in cursor.fetchall():
            payments.append({
                "id": row[0],
                "amount": row[1],
                "currency": row[2],
                "paymentMethod": row[3],
                "status": row[4],
                "transactionId": row[5],
                "paymentDate": row[6],
                "description": row[7],
                "invoiceNumber": row[8],
                "userEmail": row[9],
                "userName": row[10]
            })
        
        return {"payments": payments, "total": len(payments)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Mesajlar
@app.get("/api/admin/messages")
def get_messages(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.Id, m.Subject, m.Message, m.MessageType, m.IsRead, m.SentAt, m.Priority,
                   u1.Email as FromEmail, u1.Name as FromName,
                   u2.Email as ToEmail, u2.Name as ToName
            FROM Messages m
            JOIN Users u1 ON m.FromUserId = u1.Id
            JOIN Users u2 ON m.ToUserId = u2.Id
            ORDER BY m.SentAt DESC
        """)
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "subject": row[1],
                "message": row[2],
                "messageType": row[3],
                "isRead": bool(row[4]),
                "sentAt": row[5],
                "priority": row[6],
                "fromEmail": row[7],
                "fromName": row[8],
                "toEmail": row[9],
                "toName": row[10]
            })
        
        return {"messages": messages, "total": len(messages)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Sistem Logları
@app.get("/api/admin/logs")
def get_logs(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, UserEmail, Action, Module, Level, Message, IpAddress, Timestamp
            FROM SystemLogs
            ORDER BY Timestamp DESC
            LIMIT 100
        """)
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "id": row[0],
                "userEmail": row[1],
                "action": row[2],
                "module": row[3],
                "level": row[4],
                "message": row[5],
                "ipAddress": row[6],
                "timestamp": row[7]
            })
        
        return {"logs": logs, "total": len(logs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Ayarlar
@app.get("/api/admin/settings")
def get_settings(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT SettingKey, SettingValue, SettingType, Category, Description FROM Settings")
        
        settings = {}
        for row in cursor.fetchall():
            settings[row[0]] = {
                "value": row[1],
                "type": row[2],
                "category": row[3],
                "description": row[4]
            }
        
        return {"settings": settings}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Zaman Ayarları
@app.get("/api/admin/time-settings")
def get_time_settings(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM TimeSettings LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            return {
                "timezone": row[1],
                "timeFormat": row[2],
                "dateFormat": row[3],
                "weekStart": row[4],
                "language": row[5],
                "autoSync": bool(row[6]),
                "syncFrequency": row[7],
                "ntpServer": row[8],
                "lastSync": row[9],
                "lastSyncStatus": row[10],
                "lastSyncOffset": row[11]
            }
        else:
            return {"error": "Zaman ayarları bulunamadı"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Bakım Modu
@app.get("/api/admin/maintenance")
def get_maintenance_mode(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM MaintenanceMode LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            return {
                "isEnabled": bool(row[1]),
                "startTime": row[2],
                "endTime": row[3],
                "message": row[4],
                "theme": row[5],
                "adminAccess": row[6],
                "whitelistIPs": row[7],
                "enabledBy": row[8],
                "enabledAt": row[9]
            }
        else:
            return {"isEnabled": False}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Raporlar
@app.get("/api/admin/reports")
def get_reports(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.Id, r.ReportType, r.Reason, r.Description, r.Status, r.Priority, r.CreatedAt,
                   u1.Email as ReporterEmail, u1.Name as ReporterName,
                   u2.Email as ReportedEmail, u2.Name as ReportedName
            FROM Reports r
            JOIN Users u1 ON r.ReporterId = u1.Id
            LEFT JOIN Users u2 ON r.ReportedUserId = u2.Id
            ORDER BY r.CreatedAt DESC
        """)
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                "id": row[0],
                "reportType": row[1],
                "reason": row[2],
                "description": row[3],
                "status": row[4],
                "priority": row[5],
                "createdAt": row[6],
                "reporterEmail": row[7],
                "reporterName": row[8],
                "reportedEmail": row[9],
                "reportedName": row[10]
            })
        
        return {"reports": reports, "total": len(reports)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Yedekler
@app.get("/api/admin/backups")
def get_backups(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, BackupType, FilePath, FileSize, Status, StartedAt, CompletedAt,
                   Duration, Description, Checksum, IsCompressed, RetentionDays
            FROM Backups
            ORDER BY StartedAt DESC
        """)
        
        backups = []
        for row in cursor.fetchall():
            backups.append({
                "id": row[0],
                "backupType": row[1],
                "filePath": row[2],
                "fileSize": row[3],
                "status": row[4],
                "startedAt": row[5],
                "completedAt": row[6],
                "duration": row[7],
                "description": row[8],
                "checksum": row[9],
                "isCompressed": bool(row[10]),
                "retentionDays": row[11]
            })
        
        return {"backups": backups, "total": len(backups)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Admin paneli - Analitikler
@app.get("/api/admin/analytics")
def get_analytics(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Toplam kullanıcı sayısı
        cursor.execute("SELECT COUNT(*) FROM Users")
        total_users = cursor.fetchone()[0]
        
        # Aktif kullanıcı sayısı
        cursor.execute("SELECT COUNT(*) FROM Users WHERE Status = 'active'")
        active_users = cursor.fetchone()[0]
        
        # Toplam ilan sayısı
        cursor.execute("SELECT COUNT(*) FROM Listings")
        total_listings = cursor.fetchone()[0]
        
        # Aktif ilan sayısı
        cursor.execute("SELECT COUNT(*) FROM Listings WHERE Status = 'active'")
        active_listings = cursor.fetchone()[0]
        
        # Toplam ödeme tutarı
        cursor.execute("SELECT SUM(Amount) FROM Payments WHERE Status = 'completed'")
        total_revenue = cursor.fetchone()[0] or 0
        
        # Bugünkü ödemeler
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM Payments WHERE DATE(PaymentDate) = ?", (today,))
        today_payments = cursor.fetchone()[0]
        
        return {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalListings": total_listings,
            "activeListings": active_listings,
            "totalRevenue": total_revenue,
            "todayPayments": today_payments
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Kullanıcı durumu güncelleme
@app.put("/api/admin/users/{user_id}/status")
def update_user_status(user_id: int, status: str, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Kullanıcı rolünü kontrol et
        cursor.execute("SELECT Role FROM Users WHERE Email = ?", (current_user,))
        user_role = cursor.fetchone()
        
        if not user_role or user_role[0] not in ['superadmin', 'admin']:
            raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok!")
        
        cursor.execute("UPDATE Users SET Status = ? WHERE Id = ?", (status, user_id))
        conn.commit()
        
        return {"message": "Kullanıcı durumu güncellendi", "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Kullanıcı rolü güncelleme
@app.put("/api/admin/users/{user_id}/role")
def update_user_role(user_id: int, role: str, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Kullanıcı rolünü kontrol et
        cursor.execute("SELECT Role FROM Users WHERE Email = ?", (current_user,))
        user_role = cursor.fetchone()
        
        if not user_role or user_role[0] != 'superadmin':
            raise HTTPException(status_code=403, detail="Bu işlem için superadmin yetkisi gerekli!")
        
        # Geçerli roller
        valid_roles = ['user', 'moderator', 'admin', 'superadmin']
        if role not in valid_roles:
            raise HTTPException(status_code=400, detail="Geçersiz rol!")
        
        cursor.execute("UPDATE Users SET Role = ? WHERE Id = ?", (role, user_id))
        conn.commit()
        
        return {"message": f"Kullanıcı rolü {role} olarak güncellendi", "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# İlan durumu güncelleme
@app.put("/api/admin/listings/{listing_id}/status")
def update_listing_status(listing_id: int, status: str, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("UPDATE Listings SET Status = ? WHERE Id = ?", (status, listing_id))
        conn.commit()
        
        return {"message": "İlan durumu güncellendi", "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Rapor durumu güncelleme
@app.put("/api/admin/reports/{report_id}/status")
def update_report_status(report_id: int, status: str, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("UPDATE Reports SET Status = ? WHERE Id = ?", (status, report_id))
        conn.commit()
        
        return {"message": "Rapor durumu güncellendi", "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Bakım modu güncelleme
@app.put("/api/admin/maintenance")
def update_maintenance_mode(is_enabled: bool, message: str = None, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        if is_enabled:
            cursor.execute("""
                UPDATE MaintenanceMode SET IsEnabled = ?, Message = ?, EnabledBy = ?, EnabledAt = ?
                WHERE Id = 1
            """, (True, message, current_user, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        else:
            cursor.execute("""
                UPDATE MaintenanceMode SET IsEnabled = ?, DisabledBy = ?, DisabledAt = ?
                WHERE Id = 1
            """, (False, current_user, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        
        return {"message": "Bakım modu güncellendi", "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Zaman ayarları güncelleme
@app.put("/api/admin/time-settings")
def update_time_settings(timezone: str, time_format: str, date_format: str, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE TimeSettings SET Timezone = ?, TimeFormat = ?, DateFormat = ?, UpdatedAt = ?
            WHERE Id = 1
        """, (timezone, time_format, date_format, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        
        return {"message": "Zaman ayarları güncellendi", "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Premium Listings Endpoints
@app.get("/api/premium-listings")
def get_premium_listings():
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pl.*, l.Title, l.Price, l.Description, u.Email as UserEmail
            FROM PremiumListings pl
            JOIN Listings l ON pl.ListingId = l.Id
            JOIN Users u ON pl.UserId = u.Id
            WHERE pl.IsActive = 1
            ORDER BY pl.CreatedAt DESC
        """)
        
        columns = [description[0] for description in cursor.description]
        premium_listings = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return {"premium_listings": premium_listings, "status": "success"}
    except Exception as e:
        return {"message": f"Hata: {str(e)}", "status": "error"}

@app.get("/api/premium-listings/pending")
def get_pending_premium_listings(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pl.*, l.Title, l.Price, l.Description, u.Email as UserEmail
            FROM PremiumListings pl
            JOIN Listings l ON pl.ListingId = l.Id
            JOIN Users u ON pl.UserId = u.Id
            WHERE pl.IsActive = 1 AND (pl.PaymentStatus = 'pending' OR pl.ContentStatus = 'pending')
            ORDER BY pl.CreatedAt ASC
        """)
        
        columns = [description[0] for description in cursor.description]
        pending_listings = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return {"pending_listings": pending_listings, "status": "success"}
    except Exception as e:
        return {"message": f"Hata: {str(e)}", "status": "error"}

@app.put("/api/premium-listings/{premium_id}/approve-payment")
def approve_premium_payment(premium_id: int, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE PremiumListings 
            SET PaymentStatus = 'approved', ApprovedBy = ?, ApprovedAt = ?, UpdatedAt = ?
            WHERE Id = ?
        """, (get_user_id(current_user), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), premium_id))
        
        conn.commit()
        conn.close()
        
        return {"message": "Premium ödeme onaylandı", "status": "success"}
    except Exception as e:
        return {"message": f"Hata: {str(e)}", "status": "error"}

@app.put("/api/premium-listings/{premium_id}/approve-content")
def approve_premium_content(premium_id: int, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE PremiumListings 
            SET ContentStatus = 'approved', ApprovedBy = ?, ApprovedAt = ?, UpdatedAt = ?
            WHERE Id = ?
        """, (get_user_id(current_user), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), premium_id))
        
        conn.commit()
        conn.close()
        
        return {"message": "Premium içerik onaylandı", "status": "success"}
    except Exception as e:
        return {"message": f"Hata: {str(e)}", "status": "error"}

@app.put("/api/premium-listings/{premium_id}/reject")
def reject_premium_listing(premium_id: int, reason: str, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE PremiumListings 
            SET PaymentStatus = 'failed', ContentStatus = 'rejected', 
                RejectionReason = ?, ApprovedBy = ?, ApprovedAt = ?, UpdatedAt = ?
            WHERE Id = ?
        """, (reason, get_user_id(current_user), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), premium_id))
        
        conn.commit()
        conn.close()
        
        return {"message": "Premium ilan reddedildi", "status": "success"}
    except Exception as e:
        return {"message": f"Hata: {str(e)}", "status": "error"}

# Content Moderation Endpoints
@app.get("/api/moderation/pending")
def get_pending_moderation(current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.*, u.Email as UserEmail, pl.PremiumType, pl.Amount
            FROM Listings l
            JOIN Users u ON l.UserId = u.Id
            LEFT JOIN PremiumListings pl ON l.Id = pl.ListingId
            WHERE l.Status = 'pending' OR (pl.ContentStatus = 'pending' AND pl.PaymentStatus = 'approved')
            ORDER BY l.CreatedAt ASC
        """)
        
        columns = [description[0] for description in cursor.description]
        pending_listings = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return {"pending_listings": pending_listings, "status": "success"}
    except Exception as e:
        return {"message": f"Hata: {str(e)}", "status": "error"}

@app.post("/api/moderation/{listing_id}/approve")
def approve_listing_content(listing_id: int, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Update listing status
        cursor.execute("""
            UPDATE Listings 
            SET Status = 'active', UpdatedAt = ?
            WHERE Id = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), listing_id))
        
        # Update premium listing content status if exists
        cursor.execute("""
            UPDATE PremiumListings 
            SET ContentStatus = 'approved', ApprovedBy = ?, ApprovedAt = ?, UpdatedAt = ?
            WHERE ListingId = ?
        """, (get_user_id(current_user), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), listing_id))
        
        # Log moderation action
        cursor.execute("""
            INSERT INTO ContentModeration (ListingId, ModeratorId, Action, CreatedAt)
            VALUES (?, ?, 'approve', ?)
        """, (listing_id, get_user_id(current_user), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        conn.close()
        
        return {"message": "İlan içeriği onaylandı", "status": "success"}
    except Exception as e:
        return {"message": f"Hata: {str(e)}", "status": "error"}

@app.post("/api/moderation/{listing_id}/reject")
def reject_listing_content(listing_id: int, reason: str, current_user: str = Depends(verify_token)):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Update listing status
        cursor.execute("""
            UPDATE Listings 
            SET Status = 'inactive', UpdatedAt = ?
            WHERE Id = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), listing_id))
        
        # Update premium listing content status if exists
        cursor.execute("""
            UPDATE PremiumListings 
            SET ContentStatus = 'rejected', RejectionReason = ?, ApprovedBy = ?, ApprovedAt = ?, UpdatedAt = ?
            WHERE ListingId = ?
        """, (reason, get_user_id(current_user), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), listing_id))
        
        # Log moderation action
        cursor.execute("""
            INSERT INTO ContentModeration (ListingId, ModeratorId, Action, Reason, CreatedAt)
            VALUES (?, ?, 'reject', ?, ?)
        """, (listing_id, get_user_id(current_user), reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        conn.close()
        
        return {"message": "İlan içeriği reddedildi", "status": "success"}
    except Exception as e:
        return {"message": f"Hata: {str(e)}", "status": "error"}

# Helper function to get user ID
def get_user_id(email: str):
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
        user = cursor.fetchone()
        
        conn.close()
        return user[0] if user else None
    except Exception as e:
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)