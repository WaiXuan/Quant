CREATE TABLE [Record].[Vegas] (
    [Symbol]    VARCHAR (20)   NOT NULL,
    [TimeFrame] VARCHAR (2)    NULL,
    [RowOpen]   DECIMAL (9, 2) NULL,
    [RowHigh]   DECIMAL (9, 2) NULL,
    [RowLow]    DECIMAL (9, 2) NULL,
    [RowClose]  DECIMAL (9, 2) NULL,
    [Ema12]     DECIMAL (9, 2) NULL,
    [Ema144]    DECIMAL (9, 2) NULL,
    [Ema169]    DECIMAL (9, 2) NULL,
    [Ema576]    DECIMAL (9, 2) NULL,
    [Ema676]    DECIMAL (9, 2) NULL,
    [Adosc]     DECIMAL (9, 2) NULL,
    [Rsi]       DECIMAL (9, 2) NULL,
    [Obv]       DECIMAL (9, 2) NULL,
    [VolumeOsc] DECIMAL (9, 2) NULL,
    [KDJ_K]     DECIMAL (9, 2) NULL,
    [KDJ_D]     DECIMAL (9, 2) NULL,
    [KDJ_J]     DECIMAL (9, 2) NULL,
    [CreateDT]  DATETIME       CONSTRAINT [DF_Vegas_CreateDT] DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Vegas] PRIMARY KEY CLUSTERED ([CreateDT] ASC, [Symbol] ASC)
);

