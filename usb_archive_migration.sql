-- USB Archive Integration — IncentiveHouse ERP
-- Run AFTER scanner: creates index, transaction link, audit tables
-- Compatible with SQL Server (dbo schema)

-- 1. USB Archive Index — every file scanned, deduplicated, typed
IF OBJECT_ID('dbo.usb_archive_index', 'U') IS NOT NULL DROP TABLE dbo.usb_archive_index;
CREATE TABLE dbo.usb_archive_index (
    FileID          INT IDENTITY(1,1) PRIMARY KEY,
    FileUUID        UNIQUEIDENTIFIER DEFAULT NEWID() NOT NULL,
    FilePath        NVARCHAR(1000) NOT NULL,
    FileName        NVARCHAR(255) NOT NULL,
    FileExtension   NVARCHAR(20) NULL,
    FileSize        BIGINT NULL,
    MD5Hash         NVARCHAR(32) NULL,
    DocumentType    NVARCHAR(50) NULL,       -- invoice, banking, payment, tax, etc.
    Category        NVARCHAR(50) NULL,       -- TRANSACTION_DOCUMENTS, MASTER_DATA, AUDIT_TRAIL, BACKUPS, REPORTS, UNCLASSIFIED
    TRNXNumber      NVARCHAR(50) NULL,       -- linked transaction number (optional)
    TRNXType        NVARCHAR(20) NULL,       -- BNK, INV, PUR, SAL, EVN, HR
    IsDuplicate     BIT DEFAULT 0,
    PrimaryFileID   INT NULL REFERENCES dbo.usb_archive_index(FileID),
    CreatedAt       DATETIME2 DEFAULT GETUTCDATE(),
    LastAccessedAt  DATETIME2 NULL,
    INDEX IX_usb_archive_md5 (MD5Hash),
    INDEX IX_usb_archive_type (DocumentType),
    INDEX IX_usb_archive_trnx (TRNXNumber, TRNXType),
    INDEX IX_usb_archive_category (Category)
);

-- 2. Transaction Documents — links files to specific business transactions
IF OBJECT_ID('dbo.transaction_documents', 'U') IS NOT NULL DROP TABLE dbo.transaction_documents;
CREATE TABLE dbo.transaction_documents (
    LinkID          INT IDENTITY(1,1) PRIMARY KEY,
    FileID          INT NOT NULL REFERENCES dbo.usb_archive_index(FileID),
    TRNXType        NVARCHAR(20) NOT NULL,   -- BANKING, SALES, PURCHASE, EVENTS, HR, etc.
    TRNXNumber      NVARCHAR(50) NOT NULL,   -- actual transaction number
    LinkedBy        NVARCHAR(100) NULL,
    LinkedAt        DATETIME2 DEFAULT GETUTCDATE(),
    Notes           NVARCHAR(500) NULL,
    INDEX IX_td_trnx (TRNXType, TRNXNumber),
    INDEX IX_td_file (FileID)
);

-- 3. Archive Audit Log — all access, move, delete operations
IF OBJECT_ID('dbo.archive_audit_log', 'U') IS NOT NULL DROP TABLE dbo.archive_audit_log;
CREATE TABLE dbo.archive_audit_log (
    AuditID         INT IDENTITY(1,1) PRIMARY KEY,
    Action          NVARCHAR(20) NOT NULL,   -- SCAN, UPLOAD, DOWNLOAD, LINK, UNLINK, DELETE, DEDUP
    FileID          INT NULL REFERENCES dbo.usb_archive_index(FileID),
    PerformedBy     NVARCHAR(100) NULL,
    Details         NVARCHAR(MAX) NULL,
    CreatedAt       DATETIME2 DEFAULT GETUTCDATE(),
    INDEX IX_audit_action (Action),
    INDEX IX_audit_time (CreatedAt)
);

-- 4. Unified View — transaction documents with full file metadata
IF OBJECT_ID('dbo.vw_transaction_documents', 'V') IS NOT NULL DROP VIEW dbo.vw_transaction_documents;
GO
CREATE VIEW dbo.vw_transaction_documents AS
SELECT
    td.LinkID,
    td.TRNXType,
    td.TRNXNumber,
    f.FileUUID,
    f.FileName,
    f.FileExtension,
    f.FileSize,
    f.DocumentType,
    f.Category,
    f.MD5Hash,
    f.FilePath,
    td.LinkedBy,
    td.LinkedAt,
    td.Notes
FROM dbo.transaction_documents td
JOIN dbo.usb_archive_index f ON td.FileID = f.FileID
WHERE f.IsDuplicate = 0 OR f.PrimaryFileID IS NULL;
GO

-- 5. Stored Procedure: Link file to transaction
IF OBJECT_ID('dbo.sp_link_file_to_transaction', 'P') IS NOT NULL DROP PROCEDURE dbo.sp_link_file_to_transaction;
GO
CREATE PROCEDURE dbo.sp_link_file_to_transaction
    @FileUUID       UNIQUEIDENTIFIER,
    @TRNXType       NVARCHAR(20),
    @TRNXNumber     NVARCHAR(50),
    @LinkedBy       NVARCHAR(100) = NULL,
    @Notes          NVARCHAR(500) = NULL
AS
BEGIN
    DECLARE @FileID INT;
    SELECT @FileID = FileID FROM dbo.usb_archive_index WHERE FileUUID = @FileUUID;
    IF @FileID IS NULL
        THROW 50000, 'File not found in archive index', 1;

    UPDATE dbo.usb_archive_index SET TRNXNumber = @TRNXNumber, TRNXType = @TRNXType WHERE FileID = @FileID;

    INSERT INTO dbo.transaction_documents (FileID, TRNXType, TRNXNumber, LinkedBy, Notes)
    VALUES (@FileID, @TRNXType, @TRNXNumber, @LinkedBy, @Notes);

    INSERT INTO dbo.archive_audit_log (Action, FileID, PerformedBy, Details)
    VALUES ('LINK', @FileID, @LinkedBy,
            CONCAT('Linked to ', @TRNXType, ' ', @TRNXNumber));
END;
GO

-- 6. Stored Procedure: Get all documents for a transaction
IF OBJECT_ID('dbo.sp_get_transaction_documents', 'P') IS NOT NULL DROP PROCEDURE dbo.sp_get_transaction_documents;
GO
CREATE PROCEDURE dbo.sp_get_transaction_documents
    @TRNXType   NVARCHAR(20),
    @TRNXNumber NVARCHAR(50)
AS
BEGIN
    SELECT * FROM dbo.vw_transaction_documents
    WHERE TRNXType = @TRNXType AND TRNXNumber = @TRNXNumber
    ORDER BY LinkedAt DESC;
END;
GO

PRINT 'USB Archive migration complete. Tables created: usb_archive_index, transaction_documents, archive_audit_log';
PRINT 'Views: vw_transaction_documents';
PRINT 'Stored Procedures: sp_link_file_to_transaction, sp_get_transaction_documents';
