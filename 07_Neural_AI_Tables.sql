-- ============================================================
-- Neural AI Tables for IncentiveHouse ERP
-- Run against IHE_ERP database on SQL Server
-- ============================================================

-- 1. NeuralNode - AI model registry
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NeuralNode' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.NeuralNode (
        id INT IDENTITY(1,1) PRIMARY KEY,
        organ VARCHAR(50) NOT NULL,
        cell VARCHAR(50) NOT NULL,
        name VARCHAR(200) NOT NULL,
        description TEXT NULL,
        model_type VARCHAR(50) DEFAULT 'default',
        status VARCHAR(20) DEFAULT 'active',
        last_trained DATETIME NULL,
        accuracy FLOAT NULL,
        training_count INT DEFAULT 0,
        model_data VARBINARY(MAX) NULL,
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_NeuralNode_Organ ON dbo.NeuralNode(organ);
    CREATE INDEX IX_NeuralNode_Cell ON dbo.NeuralNode(cell);
END;

-- 2. NeuralPrediction - prediction log + human feedback
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NeuralPrediction' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.NeuralPrediction (
        id INT IDENTITY(1,1) PRIMARY KEY,
        node_id INT NULL,
        organ VARCHAR(50) NOT NULL,
        cell VARCHAR(50) NOT NULL,
        prediction_id VARCHAR(200) NULL,
        input_data TEXT NULL,
        output_data TEXT NULL,
        confidence FLOAT NULL,
        actual_outcome VARCHAR(500) NULL,
        feedback_text TEXT NULL,
        feedback_rating INT NULL,
        created_at DATETIME DEFAULT GETDATE()
    );
END;

-- 3. NeuralFeatureStore - computed features for ML
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NeuralFeatureStore' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.NeuralFeatureStore (
        id INT IDENTITY(1,1) PRIMARY KEY,
        feature_group VARCHAR(100) NOT NULL,
        feature_name VARCHAR(200) NOT NULL,
        feature_value FLOAT NULL,
        feature_json TEXT NULL,
        entity_id VARCHAR(100) NULL,
        computed_at DATETIME DEFAULT GETDATE(),
        expires_at DATETIME NULL
    );
    CREATE INDEX IX_NFS_Group ON dbo.NeuralFeatureStore(feature_group);
END;

-- 4. NeuralTrainingHistory - training run log
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NeuralTrainingHistory' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.NeuralTrainingHistory (
        id INT IDENTITY(1,1) PRIMARY KEY,
        node_id INT NOT NULL,
        training_date DATETIME DEFAULT GETDATE(),
        samples INT DEFAULT 0,
        features INT DEFAULT 0,
        accuracy FLOAT NULL,
        loss FLOAT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        model_data VARBINARY(MAX) NULL,
        metrics_json VARCHAR(2000) NULL,
        duration_seconds FLOAT NULL
    );
    CREATE INDEX IX_NTH_NodeId ON dbo.NeuralTrainingHistory(node_id);
END;

-- 5. NeuralMemory - long-term memory store for AI assistant
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NeuralMemory' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.NeuralMemory (
        id INT IDENTITY(1,1) PRIMARY KEY,
        memory_key VARCHAR(200) NOT NULL UNIQUE,
        memory_type VARCHAR(50) DEFAULT 'insight',
        organ VARCHAR(50) NULL,
        cell VARCHAR(50) NULL,
        content TEXT NULL,
        importance FLOAT DEFAULT 0.5,
        access_count INT DEFAULT 0,
        is_active BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE(),
        last_accessed_at DATETIME NULL
    );
    CREATE INDEX IX_NM_Key ON dbo.NeuralMemory(memory_key);
END;

-- Seed 4 neural nodes
IF NOT EXISTS (SELECT * FROM dbo.NeuralNode WHERE organ = 'finance' AND cell = 'cashflow')
    INSERT INTO dbo.NeuralNode (organ, cell, name, description, model_type, status)
    VALUES ('finance', 'cashflow', 'Cash Flow Predictor',
            'Predicts 30-day cash position using GradientBoostingRegressor',
            'gradient_boosting', 'active');

IF NOT EXISTS (SELECT * FROM dbo.NeuralNode WHERE organ = 'sales' AND cell = 'churn')
    INSERT INTO dbo.NeuralNode (organ, cell, name, description, model_type, status)
    VALUES ('sales', 'churn', 'Client Churn Predictor',
            'Predicts client churn probability using RandomForestClassifier',
            'random_forest', 'active');

IF NOT EXISTS (SELECT * FROM dbo.NeuralNode WHERE organ = 'events' AND cell = 'overrun')
    INSERT INTO dbo.NeuralNode (organ, cell, name, description, model_type, status)
    VALUES ('events', 'overrun', 'PNR Overrun Predictor',
            'Predicts PNR budget overrun using GradientBoostingRegressor',
            'gradient_boosting', 'active');

IF NOT EXISTS (SELECT * FROM dbo.NeuralNode WHERE organ = 'finance' AND cell = 'anomaly')
    INSERT INTO dbo.NeuralNode (organ, cell, name, description, model_type, status)
    VALUES ('finance', 'anomaly', 'Transaction Anomaly Detector',
            'Detects anomalous bank transactions using IsolationForest',
            'isolation_forest', 'active');

PRINT 'Neural AI tables created and seeded successfully.';
