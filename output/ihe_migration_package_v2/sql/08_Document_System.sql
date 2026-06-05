-- ============================================================
-- Document System Tables for IncentiveHouse ERP
-- Run against IHE_ERP database on SQL Server
-- ============================================================

-- 1. DocumentModule - classification modules
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DocumentModule' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.DocumentModule (
        ModuleID INT IDENTITY(1,1) PRIMARY KEY,
        ModuleCode VARCHAR(50) NOT NULL UNIQUE,
        ModuleName VARCHAR(200) NOT NULL,
        Folder VARCHAR(500) NULL,
        Description TEXT NULL,
        Icon VARCHAR(50) NULL,
        DisplayOrder INT DEFAULT 0,
        IsActive BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_DM_Code ON dbo.DocumentModule(ModuleCode);
END;

-- 2. SupportingDocument - file registry
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SupportingDocument' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.SupportingDocument (
        DocumentID BIGINT IDENTITY(1,1) PRIMARY KEY,
        FileName VARCHAR(500) NOT NULL,
        FilePath VARCHAR(1000) NULL,
        FileSize BIGINT NULL,
        SHA256 VARCHAR(64) NULL,
        MimeType VARCHAR(100) NULL,
        ModuleCode VARCHAR(50) NULL,
        LinkedEntityType VARCHAR(50) NULL,
        LinkedEntityID VARCHAR(100) NULL,
        PNRNumber VARCHAR(50) NULL,
        Year INT NULL,
        Description TEXT NULL,
        Tags VARCHAR(500) NULL,
        Status VARCHAR(20) DEFAULT 'active',
        IsVerified BIT DEFAULT 0,
        Version INT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_SD_Module ON dbo.SupportingDocument(ModuleCode);
    CREATE INDEX IX_SD_Entity ON dbo.SupportingDocument(LinkedEntityType, LinkedEntityID);
    CREATE INDEX IX_SD_PNR ON dbo.SupportingDocument(PNRNumber);
END;

PRINT 'Document system tables created successfully.';
