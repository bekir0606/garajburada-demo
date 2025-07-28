#!/usr/bin/env python3
"""
Railway Database Setup
Railway ortamında SQLite database'ini oluşturur.
"""

import sqlite3
import os

def setup_database():
    # Database dizinini oluştur
    os.makedirs('database', exist_ok=True)
    
    # Database bağlantısı
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    # Users tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Email TEXT UNIQUE NOT NULL,
        Password TEXT NOT NULL,
        Name TEXT NOT NULL,
        Phone TEXT,
        City TEXT,
        Role TEXT DEFAULT 'user',
        Status TEXT DEFAULT 'active',
        CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Listings tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Listings (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        UserId INTEGER,
        Title TEXT NOT NULL,
        Description TEXT,
        Price REAL,
        Status TEXT DEFAULT 'active',
        CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
        ExpiresAt DATETIME,
        FOREIGN KEY (UserId) REFERENCES Users (Id)
    )
    ''')
    
    # Admin kullanıcısı oluştur
    cursor.execute('''
    INSERT OR IGNORE INTO Users (Email, Password, Name, Role) 
    VALUES (?, ?, ?, ?)
    ''', ('admin@garajburada.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.', 'Admin', 'superadmin'))
    
    # Demo kullanıcısı oluştur
    cursor.execute('''
    INSERT OR IGNORE INTO Users (Email, Password, Name, Role) 
    VALUES (?, ?, ?, ?)
    ''', ('demo@garajburada.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.', 'Demo User', 'user'))
    
    # Demo ilanları oluştur
    cursor.execute('''
    INSERT OR IGNORE INTO Listings (UserId, Title, Description, Price, Status) 
    VALUES (?, ?, ?, ?, ?)
    ''', (2, 'Demo Araç İlanı', 'Bu bir demo ilanıdır.', 50000, 'active'))
    
    conn.commit()
    conn.close()
    
    print("✅ Railway database başarıyla oluşturuldu!")

if __name__ == "__main__":
    setup_database() 