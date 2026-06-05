-- IHE-ERP Full Schema DDL
-- Run this first to create all 26 tables in dbo schema
-- Then run 07_Neural_AI_Tables.sql and 08_Document_System.sql for neural+doc tables

-- Master tables
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Currency' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.Currency (
    CurrencyCode VARCHAR(3) PRIMARY KEY,
    CurrencyName VARCHAR(50) NOT NULL,
    Symbol VARCHAR(5) NULL,
    IsBaseCurrency BIT DEFAULT 0
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Client' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.Client (
    ClientCode VARCHAR(10) PRIMARY KEY,
    ClientName VARCHAR(200) NOT NULL,
    TaxID VARCHAR(50) NULL,
    TaxRegisterNo VARCHAR(50) NULL,
    Address VARCHAR(500) NULL,
    Telephone VARCHAR(50) NULL,
    Email VARCHAR(200) NULL,
    ContactPerson VARCHAR(200) NULL,
    PostingAccount VARCHAR(20) NULL,
    ExpenseAccount VARCHAR(20) NULL,
    PaymentTerms VARCHAR(100) NULL,
    IsActive BIT DEFAULT 1
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Vendor' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.Vendor (
    VendorCode VARCHAR(10) PRIMARY KEY,
    VendorName VARCHAR(200) NOT NULL,
    TaxID VARCHAR(50) NULL,
    TaxRegisterNo VARCHAR(50) NULL,
    Address VARCHAR(500) NULL,
    Telephone VARCHAR(50) NULL,
    Email VARCHAR(200) NULL,
    Branch VARCHAR(100) NULL,
    BankName VARCHAR(100) NULL,
    IBAN VARCHAR(50) NULL,
    EGPAccountNo VARCHAR(50) NULL,
    USDAccountNo VARCHAR(50) NULL,
    VendorType VARCHAR(50) NULL,
    PostingAccount VARCHAR(20) NULL,
    ExpenseAccount VARCHAR(20) NULL,
    PaymentTerms VARCHAR(100) NULL,
    IsActive BIT DEFAULT 1
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Employee' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.Employee (
    EmployeeCode VARCHAR(10) PRIMARY KEY,
    EmployeeName VARCHAR(200) NOT NULL,
    EmployeeType VARCHAR(20) NOT NULL,
    PostingAccount VARCHAR(20) NULL,
    ExpenseAccount VARCHAR(20) NULL,
    IsActive BIT DEFAULT 1
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Bank' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.Bank (
    BankCode VARCHAR(10) PRIMARY KEY,
    BankName VARCHAR(200) NOT NULL,
    GLAccount VARCHAR(20) NULL,
    IsActive BIT DEFAULT 1
);

-- Service category tables
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ServiceMainCategory' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.ServiceMainCategory (
    MainCategoryCode VARCHAR(10) PRIMARY KEY,
    MainCategoryName VARCHAR(100) NOT NULL,
    DisplayOrder INT NULL
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ServiceSubCategory' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.ServiceSubCategory (
    SubCategoryCode VARCHAR(20) PRIMARY KEY,
    MainCategoryCode VARCHAR(10) NOT NULL REFERENCES dbo.ServiceMainCategory(MainCategoryCode),
    SubCategoryName VARCHAR(200) NOT NULL,
    DefaultVendorCode VARCHAR(10) NULL,
    GLAccount VARCHAR(20) NULL
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ServiceType' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.ServiceType (
    ServiceTypeCode VARCHAR(10) PRIMARY KEY,
    ServiceName VARCHAR(200) NOT NULL,
    CostAccount VARCHAR(20) NULL,
    SubCategoryCode VARCHAR(20) NULL REFERENCES dbo.ServiceSubCategory(SubCategoryCode)
);

-- Chart of Accounts
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ChartOfAccounts' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.ChartOfAccounts (
    AccountCode VARCHAR(20) PRIMARY KEY,
    AccountName VARCHAR(200) NOT NULL,
    AccountType VARCHAR(50) NOT NULL,
    ParentAccount VARCHAR(20) NULL,
    IsControlAccount BIT DEFAULT 0,
    CurrencyCode VARCHAR(3) NULL
);

-- PNR / Event management
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PNRMaster' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.PNRMaster (
    PNRNumber VARCHAR(50) PRIMARY KEY,
    ClientCode VARCHAR(10) NULL REFERENCES dbo.Client(ClientCode),
    EventName VARCHAR(500) NULL,
    EventStartDate DATE NULL,
    EventEndDate DATE NULL,
    JobFolder VARCHAR(200) NULL,
    Year INT NULL,
    Status VARCHAR(20) NULL,
    CurrencyCode VARCHAR(3) NULL
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ClientEmployee' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.ClientEmployee (
    EmployeeID INT IDENTITY(1,1) PRIMARY KEY,
    ClientCode VARCHAR(10) NOT NULL REFERENCES dbo.Client(ClientCode),
    EmployeeName VARCHAR(200) NOT NULL,
    Position VARCHAR(100) NULL,
    Email VARCHAR(200) NULL,
    Phone VARCHAR(50) NULL
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PNRBudgetLineItem' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.PNRBudgetLineItem (
    LineItemID BIGINT IDENTITY(1,1) PRIMARY KEY,
    Year INT NULL,
    JobFolder VARCHAR(500) NULL,
    FileName VARCHAR(500) NULL,
    SheetName VARCHAR(200) NULL,
    RowNumber INT NULL,
    MainCategoryCode VARCHAR(10) NULL,
    SubCategoryCode VARCHAR(20) NULL,
    ClientCode VARCHAR(10) NULL,
    Description TEXT NULL,
    Quantity NUMERIC(18,2) NULL,
    UnitPrice NUMERIC(18,2) NULL,
    Amount NUMERIC(18,2) NULL,
    CurrencyCode VARCHAR(3) NULL,
    C1 VARCHAR(500) NULL, C2 VARCHAR(500) NULL, C3 VARCHAR(500) NULL,
    C4 VARCHAR(500) NULL, C5 VARCHAR(500) NULL, C6 VARCHAR(500) NULL,
    C7 VARCHAR(500) NULL, C8 VARCHAR(500) NULL, C9 VARCHAR(500) NULL,
    C10 VARCHAR(500) NULL, C11 VARCHAR(500) NULL, C12 VARCHAR(500) NULL,
    C13 VARCHAR(500) NULL, C14 VARCHAR(500) NULL, C15 VARCHAR(500) NULL,
    C16 VARCHAR(500) NULL, C17 VARCHAR(500) NULL, C18 VARCHAR(500) NULL,
    C19 VARCHAR(500) NULL, C20 VARCHAR(500) NULL,
    IsHeaderRow BIT DEFAULT 0
);

-- Sales
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SalesInvoice' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.SalesInvoice (
    InvoiceID INT IDENTITY(1,1) PRIMARY KEY,
    InvoiceNumber VARCHAR(50) NULL,
    PNRNumber VARCHAR(50) NULL REFERENCES dbo.PNRMaster(PNRNumber),
    ClientCode VARCHAR(10) NULL REFERENCES dbo.Client(ClientCode),
    EventName VARCHAR(500) NULL,
    InvoiceDate DATE NULL,
    DueDate DATE NULL,
    TotalValue NUMERIC(18,2) NULL,
    CollectedAmount NUMERIC(18,2) NULL,
    PaymentStatus VARCHAR(20) NULL,
    CurrencyCode VARCHAR(3) NULL
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SalesInvoiceLine' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.SalesInvoiceLine (
    InvoiceLineID INT IDENTITY(1,1) PRIMARY KEY,
    InvoiceID INT NOT NULL REFERENCES dbo.SalesInvoice(InvoiceID),
    ServiceTypeCode VARCHAR(10) NULL REFERENCES dbo.ServiceType(ServiceTypeCode),
    LineAmount NUMERIC(18,2) NULL
);

-- Purchase
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PurchaseVoucher' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.PurchaseVoucher (
    VoucherID INT IDENTITY(1,1) PRIMARY KEY,
    VoucherNumber VARCHAR(50) NULL,
    DocumentNumber VARCHAR(50) NULL,
    PNRNumber VARCHAR(50) NULL REFERENCES dbo.PNRMaster(PNRNumber),
    EventName VARCHAR(500) NULL,
    InvoiceDate DATE NULL,
    TotalValue NUMERIC(18,2) NULL,
    CurrencyCode VARCHAR(3) NULL
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PurchaseVoucherLine' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.PurchaseVoucherLine (
    VoucherLineID INT IDENTITY(1,1) PRIMARY KEY,
    VoucherID INT NOT NULL REFERENCES dbo.PurchaseVoucher(VoucherID),
    ServiceTypeCode VARCHAR(10) NULL REFERENCES dbo.ServiceType(ServiceTypeCode),
    VendorCode VARCHAR(10) NULL REFERENCES dbo.Vendor(VendorCode),
    ItemNarration TEXT NULL,
    Quantity NUMERIC(18,2) NULL,
    NoOfNights INT NULL,
    UnitPrice NUMERIC(18,2) NULL,
    SubTotal NUMERIC(18,2) NULL,
    VATAmount NUMERIC(18,2) NULL
);

-- Banking
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'BankTransaction' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.BankTransaction (
    TransactionID INT IDENTITY(1,1) PRIMARY KEY,
    TransactionDate DATE NOT NULL,
    Payee VARCHAR(200) NULL,
    DocumentType VARCHAR(100) NULL,
    DocumentNumber VARCHAR(50) NULL,
    Withdrawal NUMERIC(18,2) NULL,
    Deposit NUMERIC(18,2) NULL,
    RunningBalance NUMERIC(18,2) NULL,
    TransactionType VARCHAR(50) NULL,
    JVNumber VARCHAR(50) NULL,
    Narration TEXT NULL,
    DrAccount VARCHAR(20) NULL,
    CrAccount VARCHAR(20) NULL,
    FromSubCategory VARCHAR(200) NULL,
    ToSubCategory VARCHAR(200) NULL,
    BankCode VARCHAR(10) NULL REFERENCES dbo.Bank(BankCode),
    CurrencyCode VARCHAR(3) DEFAULT 'EGP'
);

-- Journal Voucher
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'JournalVoucher' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.JournalVoucher (
    JVNumber VARCHAR(50) PRIMARY KEY,
    JVDate DATE NULL,
    Narration TEXT NULL,
    TotalDebit NUMERIC(18,2) NULL,
    TotalCredit NUMERIC(18,2) NULL
);

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'JournalVoucherLine' AND schema_id = SCHEMA_ID('dbo'))
CREATE TABLE dbo.JournalVoucherLine (
    JVLineID INT IDENTITY(1,1) PRIMARY KEY,
    JVNumber VARCHAR(50) NOT NULL REFERENCES dbo.JournalVoucher(JVNumber),
    AccountCode VARCHAR(20) NULL,
    DebitAmount NUMERIC(18,2) NULL,
    CreditAmount NUMERIC(18,2) NULL,
    Narration TEXT NULL,
    PNRNumber VARCHAR(50) NULL REFERENCES dbo.PNRMaster(PNRNumber)
);

PRINT 'IHE-ERP base schema created successfully. 19 IHE tables created.';
