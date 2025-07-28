-- Garajburada.com Database Schema
-- Admin Panel, Moderator Panel ve Premium İlanlar için kapsamlı veritabanı yapısı
-- Güncelleme Tarihi: 2025-01-25

-- Users Tablosu (Genişletilmiş)
CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Email TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    Name TEXT,
    Phone TEXT,
    Role TEXT DEFAULT 'user' CHECK (Role IN ('superadmin', 'admin', 'moderator', 'user')),
    Status TEXT DEFAULT 'active' CHECK (Status IN ('active', 'inactive', 'pending', 'banned')),
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastLogin DATETIME,
    ListingCount INTEGER DEFAULT 0,
    IsPremium BOOLEAN DEFAULT 0,
    ProfileImage TEXT,
    Address TEXT,
    City TEXT,
    Country TEXT DEFAULT 'Türkiye',
    EmailVerified BOOLEAN DEFAULT 0,
    PhoneVerified BOOLEAN DEFAULT 0,
    TwoFactorEnabled BOOLEAN DEFAULT 0,
    LoginAttempts INTEGER DEFAULT 0,
    LastLoginAttempt DATETIME,
    AccountLocked BOOLEAN DEFAULT 0,
    LockedUntil DATETIME
);

-- Listings Tablosu (Genişletilmiş)
CREATE TABLE IF NOT EXISTS Listings (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    Title TEXT NOT NULL,
    Brand TEXT,
    Model TEXT,
    Year INTEGER,
    Price REAL,
    Currency TEXT DEFAULT 'TRY',
    Description TEXT,
    Category TEXT,
    Condition TEXT CHECK (Condition IN ('new', 'used', 'refurbished')),
    Location TEXT,
    City TEXT,
    Images TEXT, -- JSON array of image URLs
    IsUrgent BOOLEAN DEFAULT 0,
    IsFeatured BOOLEAN DEFAULT 0,
    IsPremium BOOLEAN DEFAULT 0,
    Status TEXT DEFAULT 'active' CHECK (Status IN ('active', 'inactive', 'pending', 'sold', 'expired')),
    Views INTEGER DEFAULT 0,
    Favorites INTEGER DEFAULT 0,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt DATETIME,
    ContactPhone TEXT,
    ContactEmail TEXT,
    ContactName TEXT,
    TechnicalDetails TEXT, -- JSON object for technical specifications
    Features TEXT, -- JSON array of features
    FOREIGN KEY(UserId) REFERENCES Users(Id)
);

-- Payments Tablosu
CREATE TABLE IF NOT EXISTS Payments (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    ListingId INTEGER,
    Amount REAL NOT NULL,
    Currency TEXT DEFAULT 'TRY',
    PaymentMethod TEXT CHECK (PaymentMethod IN ('credit_card', 'bank_transfer', 'paypal', 'stripe')),
    Status TEXT DEFAULT 'pending' CHECK (Status IN ('pending', 'completed', 'failed', 'refunded', 'cancelled')),
    TransactionId TEXT,
    PaymentDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Description TEXT,
    InvoiceNumber TEXT,
    TaxAmount REAL DEFAULT 0,
    CommissionAmount REAL DEFAULT 0,
    StripePaymentIntentId TEXT,
    RefundAmount REAL DEFAULT 0,
    RefundDate DATETIME,
    RefundReason TEXT,
    FOREIGN KEY(UserId) REFERENCES Users(Id),
    FOREIGN KEY(ListingId) REFERENCES Listings(Id)
);

-- Messages Tablosu (Genişletilmiş)
CREATE TABLE IF NOT EXISTS Messages (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    FromUserId INTEGER NOT NULL,
    ToUserId INTEGER NOT NULL,
    ListingId INTEGER,
    Subject TEXT,
    Message TEXT NOT NULL,
    MessageType TEXT DEFAULT 'text' CHECK (MessageType IN ('text', 'image', 'file', 'system')),
    IsRead BOOLEAN DEFAULT 0,
    ReadAt DATETIME,
    SentAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    DeletedBySender BOOLEAN DEFAULT 0,
    DeletedByReceiver BOOLEAN DEFAULT 0,
    Attachments TEXT, -- JSON array of attachment URLs
    Priority TEXT DEFAULT 'normal' CHECK (Priority IN ('low', 'normal', 'high', 'urgent')),
    FOREIGN KEY(FromUserId) REFERENCES Users(Id),
    FOREIGN KEY(ToUserId) REFERENCES Users(Id),
    FOREIGN KEY(ListingId) REFERENCES Listings(Id)
);

-- Favorites Tablosu
CREATE TABLE IF NOT EXISTS Favorites (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    ListingId INTEGER NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    Notes TEXT,
    FOREIGN KEY(UserId) REFERENCES Users(Id),
    FOREIGN KEY(ListingId) REFERENCES Listings(Id),
    UNIQUE(UserId, ListingId)
);

-- System Logs Tablosu (Genişletilmiş)
CREATE TABLE IF NOT EXISTS SystemLogs (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER,
    UserEmail TEXT,
    Action TEXT NOT NULL,
    Module TEXT NOT NULL,
    Level TEXT DEFAULT 'info' CHECK (Level IN ('debug', 'info', 'warning', 'error', 'critical')),
    Message TEXT,
    Details TEXT, -- JSON object for additional details
    IpAddress TEXT,
    UserAgent TEXT,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    SessionId TEXT,
    RequestId TEXT,
    ExecutionTime REAL, -- in milliseconds
    StatusCode INTEGER,
    FOREIGN KEY(UserId) REFERENCES Users(Id)
);

-- Settings Tablosu
CREATE TABLE IF NOT EXISTS Settings (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    SettingKey TEXT UNIQUE NOT NULL,
    SettingValue TEXT,
    SettingType TEXT DEFAULT 'string' CHECK (SettingType IN ('string', 'integer', 'boolean', 'json', 'array')),
    Category TEXT DEFAULT 'general',
    Description TEXT,
    IsPublic BOOLEAN DEFAULT 0,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Time Management Tablosu
CREATE TABLE IF NOT EXISTS TimeSettings (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Timezone TEXT DEFAULT 'UTC+3',
    TimeFormat TEXT DEFAULT '24',
    DateFormat TEXT DEFAULT 'DD/MM/YYYY',
    WeekStart TEXT DEFAULT 'monday',
    Language TEXT DEFAULT 'tr',
    AutoSync BOOLEAN DEFAULT 1,
    SyncFrequency TEXT DEFAULT 'daily',
    NtpServer TEXT DEFAULT 'time.windows.com',
    LastSync DATETIME,
    LastSyncStatus TEXT DEFAULT 'success',
    LastSyncOffset REAL DEFAULT 0,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance Mode Tablosu
CREATE TABLE IF NOT EXISTS MaintenanceMode (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    IsEnabled BOOLEAN DEFAULT 0,
    StartTime DATETIME,
    EndTime DATETIME,
    Message TEXT DEFAULT 'Site bakımda olduğu için geçici olarak erişilemiyor. Lütfen daha sonra tekrar deneyiniz.',
    Theme TEXT DEFAULT 'default',
    AdminAccess TEXT DEFAULT 'allowed',
    WhitelistIPs TEXT, -- JSON array of IP addresses
    EnabledBy TEXT,
    EnabledAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    DisabledAt DATETIME,
    DisabledBy TEXT
);

-- Reports Tablosu
CREATE TABLE IF NOT EXISTS Reports (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    ReporterId INTEGER NOT NULL,
    ReportedUserId INTEGER,
    ReportedListingId INTEGER,
    ReportType TEXT CHECK (ReportType IN ('user', 'listing', 'message', 'payment', 'system')),
    Reason TEXT NOT NULL,
    Description TEXT,
    Status TEXT DEFAULT 'pending' CHECK (Status IN ('pending', 'investigating', 'resolved', 'dismissed')),
    AssignedTo INTEGER,
    Priority TEXT DEFAULT 'normal' CHECK (Priority IN ('low', 'normal', 'high', 'urgent')),
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    ResolvedAt DATETIME,
    ResolvedBy INTEGER,
    Resolution TEXT,
    Evidence TEXT, -- JSON array of evidence files
    FOREIGN KEY(ReporterId) REFERENCES Users(Id),
    FOREIGN KEY(ReportedUserId) REFERENCES Users(Id),
    FOREIGN KEY(ReportedListingId) REFERENCES Listings(Id),
    FOREIGN KEY(AssignedTo) REFERENCES Users(Id),
    FOREIGN KEY(ResolvedBy) REFERENCES Users(Id)
);

-- Analytics Tablosu
CREATE TABLE IF NOT EXISTS Analytics (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Date DATE NOT NULL,
    Metric TEXT NOT NULL,
    Value REAL NOT NULL,
    Category TEXT,
    Details TEXT, -- JSON object for additional data
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(Date, Metric, Category)
);

-- Backups Tablosu
CREATE TABLE IF NOT EXISTS Backups (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    BackupType TEXT CHECK (BackupType IN ('full', 'incremental', 'differential')),
    FilePath TEXT NOT NULL,
    FileSize INTEGER,
    Status TEXT DEFAULT 'running' CHECK (Status IN ('running', 'completed', 'failed')),
    StartedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    CompletedAt DATETIME,
    Duration INTEGER, -- in seconds
    CreatedBy INTEGER,
    Description TEXT,
    Checksum TEXT,
    IsCompressed BOOLEAN DEFAULT 1,
    RetentionDays INTEGER DEFAULT 30,
    FOREIGN KEY(CreatedBy) REFERENCES Users(Id)
);

-- Scheduled Tasks Tablosu
CREATE TABLE IF NOT EXISTS ScheduledTasks (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    TaskName TEXT NOT NULL,
    TaskType TEXT CHECK (TaskType IN ('backup', 'cleanup', 'sync', 'report', 'maintenance')),
    CronExpression TEXT,
    IsActive BOOLEAN DEFAULT 1,
    LastRun DATETIME,
    NextRun DATETIME,
    Status TEXT DEFAULT 'idle' CHECK (Status IN ('idle', 'running', 'completed', 'failed')),
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Notifications Tablosu
CREATE TABLE IF NOT EXISTS Notifications (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    Title TEXT NOT NULL,
    Message TEXT NOT NULL,
    Type TEXT DEFAULT 'info' CHECK (Type IN ('info', 'success', 'warning', 'error')),
    IsRead BOOLEAN DEFAULT 0,
    ReadAt DATETIME,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt DATETIME,
    ActionUrl TEXT,
    ActionText TEXT,
    FOREIGN KEY(UserId) REFERENCES Users(Id)
);

-- API Keys Tablosu
CREATE TABLE IF NOT EXISTS ApiKeys (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    KeyName TEXT NOT NULL,
    ApiKey TEXT UNIQUE NOT NULL,
    Permissions TEXT, -- JSON array of permissions
    IsActive BOOLEAN DEFAULT 1,
    LastUsed DATETIME,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt DATETIME,
    FOREIGN KEY(UserId) REFERENCES Users(Id)
);

-- Sessions Tablosu
CREATE TABLE IF NOT EXISTS Sessions (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    SessionToken TEXT UNIQUE NOT NULL,
    IpAddress TEXT,
    UserAgent TEXT,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt DATETIME,
    LastActivity DATETIME DEFAULT CURRENT_TIMESTAMP,
    IsActive BOOLEAN DEFAULT 1,
    FOREIGN KEY(UserId) REFERENCES Users(Id)
);

-- Premium Listings Tablosu (Yeni)
CREATE TABLE IF NOT EXISTS PremiumListings (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    ListingId INTEGER NOT NULL,
    UserId INTEGER NOT NULL,
    PremiumType TEXT NOT NULL CHECK (PremiumType IN ('Premium', 'Premium Plus')),
    Amount REAL NOT NULL,
    PaymentStatus TEXT DEFAULT 'pending' CHECK (PaymentStatus IN ('pending', 'approved', 'failed', 'refunded')),
    ContentStatus TEXT DEFAULT 'pending' CHECK (ContentStatus IN ('pending', 'approved', 'rejected', 'revision_requested')),
    StartDate DATETIME,
    EndDate DATETIME,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    ApprovedBy INTEGER, -- Admin/Moderator ID
    ApprovedAt DATETIME,
    RejectionReason TEXT,
    RevisionNotes TEXT,
    IsActive BOOLEAN DEFAULT 1,
    FOREIGN KEY(ListingId) REFERENCES Listings(Id),
    FOREIGN KEY(UserId) REFERENCES Users(Id),
    FOREIGN KEY(ApprovedBy) REFERENCES Users(Id)
);

-- Premium Features Tablosu (Yeni)
CREATE TABLE IF NOT EXISTS PremiumFeatures (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    PremiumType TEXT NOT NULL CHECK (PremiumType IN ('Premium', 'Premium Plus')),
    FeatureName TEXT NOT NULL,
    FeatureDescription TEXT,
    IsActive BOOLEAN DEFAULT 1,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Premium Pricing Tablosu (Yeni)
CREATE TABLE IF NOT EXISTS PremiumPricing (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    PremiumType TEXT NOT NULL CHECK (PremiumType IN ('Premium', 'Premium Plus')),
    Duration INTEGER NOT NULL, -- Gün cinsinden
    Price REAL NOT NULL,
    Currency TEXT DEFAULT 'TRY',
    IsActive BOOLEAN DEFAULT 1,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Content Moderation Tablosu (Yeni)
CREATE TABLE IF NOT EXISTS ContentModeration (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    ListingId INTEGER NOT NULL,
    ModeratorId INTEGER NOT NULL,
    Action TEXT NOT NULL CHECK (Action IN ('approve', 'reject', 'request_revision')),
    Reason TEXT,
    Notes TEXT,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ListingId) REFERENCES Listings(Id),
    FOREIGN KEY(ModeratorId) REFERENCES Users(Id)
);

-- User Activity Logs Tablosu (Yeni)
CREATE TABLE IF NOT EXISTS UserActivityLogs (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    Action TEXT NOT NULL,
    Details TEXT,
    IpAddress TEXT,
    UserAgent TEXT,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(UserId) REFERENCES Users(Id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON Users(Email);
CREATE INDEX IF NOT EXISTS idx_users_role ON Users(Role);
CREATE INDEX IF NOT EXISTS idx_users_status ON Users(Status);
CREATE INDEX IF NOT EXISTS idx_listings_userid ON Listings(UserId);
CREATE INDEX IF NOT EXISTS idx_listings_status ON Listings(Status);
CREATE INDEX IF NOT EXISTS idx_listings_category ON Listings(Category);
CREATE INDEX IF NOT EXISTS idx_payments_userid ON Payments(UserId);
CREATE INDEX IF NOT EXISTS idx_payments_status ON Payments(Status);
CREATE INDEX IF NOT EXISTS idx_messages_fromuserid ON Messages(FromUserId);
CREATE INDEX IF NOT EXISTS idx_messages_touserid ON Messages(ToUserId);
CREATE INDEX IF NOT EXISTS idx_systemlogs_userid ON SystemLogs(UserId);
CREATE INDEX IF NOT EXISTS idx_systemlogs_level ON SystemLogs(Level);
CREATE INDEX IF NOT EXISTS idx_systemlogs_timestamp ON SystemLogs(Timestamp);
CREATE INDEX IF NOT EXISTS idx_reports_status ON Reports(Status);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON Analytics(Date);
CREATE INDEX IF NOT EXISTS idx_backups_status ON Backups(Status);
CREATE INDEX IF NOT EXISTS idx_notifications_userid ON Notifications(UserId);
CREATE INDEX IF NOT EXISTS idx_notifications_isread ON Notifications(IsRead);
CREATE INDEX IF NOT EXISTS idx_sessions_userid ON Sessions(UserId);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON Sessions(SessionToken);

-- Premium Listings Indexes
CREATE INDEX IF NOT EXISTS idx_premiumlistings_listingid ON PremiumListings(ListingId);
CREATE INDEX IF NOT EXISTS idx_premiumlistings_userid ON PremiumListings(UserId);
CREATE INDEX IF NOT EXISTS idx_premiumlistings_paymentstatus ON PremiumListings(PaymentStatus);
CREATE INDEX IF NOT EXISTS idx_premiumlistings_contentstatus ON PremiumListings(ContentStatus);
CREATE INDEX IF NOT EXISTS idx_premiumlistings_premiumtype ON PremiumListings(PremiumType);
CREATE INDEX IF NOT EXISTS idx_premiumlistings_enddate ON PremiumListings(EndDate);

-- Content Moderation Indexes
CREATE INDEX IF NOT EXISTS idx_contentmoderation_listingid ON ContentModeration(ListingId);
CREATE INDEX IF NOT EXISTS idx_contentmoderation_moderatorid ON ContentModeration(ModeratorId);
CREATE INDEX IF NOT EXISTS idx_contentmoderation_action ON ContentModeration(Action);
CREATE INDEX IF NOT EXISTS idx_contentmoderation_createdat ON ContentModeration(CreatedAt);

-- User Activity Logs Indexes
CREATE INDEX IF NOT EXISTS idx_useractivitylogs_userid ON UserActivityLogs(UserId);
CREATE INDEX IF NOT EXISTS idx_useractivitylogs_action ON UserActivityLogs(Action);
CREATE INDEX IF NOT EXISTS idx_useractivitylogs_createdat ON UserActivityLogs(CreatedAt);
