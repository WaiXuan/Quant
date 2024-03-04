CREATE TABLE [Trade].[Vegas] (
    [Symbol]            VARCHAR (20)    NULL,
    [AccountName]       VARCHAR (20)    NULL,
    [TimeFrame]         VARCHAR (4)     NULL,
    [OrderId]           VARCHAR (50)    NULL,
    [Side]              VARCHAR (4)     NULL,
    [Price]             DECIMAL (11, 4) NULL,
    [TotalValue]        DECIMAL (9, 2)  NULL,
    [Reason]            NVARCHAR (30)   NULL,
    [Action]            NVARCHAR (30)   NULL,
    [OrderCase]         INT             NULL,
    [ProfitPrice]       DECIMAL (6, 4)  NULL,
    [ProfitPercent]     DECIMAL (6, 4)  NULL,
    [ProfitSizePercent] DECIMAL (4, 2)  NULL,
    [LossPrice]         DECIMAL (6, 4)  NULL,
    [LossPercent]       DECIMAL (4, 2)  NULL,
    [IsLeveRage]        INT             NULL,
    [CreateDT]          DATETIME        CONSTRAINT [DF_Vegas_CreateDT] DEFAULT (getdate()) NULL
);

