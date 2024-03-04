/****************************************************************
** Desc: 新增Veags交易紀錄
*****************************************************************
USE [Quantitative]
GO

DECLARE	@return_value int

EXEC	@return_value = [Trade].[usp_InsertVeags]
		@Symbol = N'ETHUSD',
		@AccountName = NULL,
		@TimeFrame = NULL,
		@OrderId = NULL,
		@Side = NULL,
		@Price = NULL,
		@TotalValue = NULL,
		@Reason = NULL,
		@Action = NULL,
		@OrderCase = NULL,
		@ProfitPercent = NULL,
		@ProfitSizePercent = NULL,
		@LossPercent = NULL,
		@IsLeveRage = NULL

SELECT	'Return Value' = @return_value

GO
*****************************************************************
** Change History
** 2023/10/22   KAO   First Release
*****************************************************************/
CREATE PROCEDURE [Trade].[usp_InsertVeags]
	@Symbol				VARCHAR(20),
	@AccountName		VARCHAR(20),
	@TimeFrame			VARCHAR(4),
	@OrderId			VARCHAR(50),
	@Side				VARCHAR(4),
	@Price				DECIMAL(11, 2),
	@TotalValue			DECIMAL(9, 2),
	@Reason				NVARCHAR(30),
	@Action				NVARCHAR(30),
	@OrderCase			INT,
	@ProfitPrice		DECIMAL(6, 4),
	@ProfitPercent		DECIMAL(6, 4),
	@ProfitSizePercent	DECIMAL(4, 2),
	@LossPrice			DECIMAL(6, 4),
	@LossPercent		DECIMAL(4, 2),
	@IsLeveRage			INT
AS

	SET NOCOUNT ON;

	DECLARE @Error INT;
	SET @Error = 0;

	BEGIN TRY	

	INSERT INTO [Trade].[Vegas]
			   (Symbol,
				AccountName,
				TimeFrame,
				OrderId,
				Side,
				Price,
				TotalValue,
				Reason,
				Action,
				OrderCase,
				ProfitPrice,
				ProfitPercent,
				ProfitSizePercent,
				LossPrice,
				LossPercent,
				IsLeveRage
				)
     VALUES
           (@Symbol,
			@AccountName,
			@TimeFrame,
			@OrderId,
			@Side,
			@Price,
			@TotalValue,
			@Reason,
			@Action,
			@OrderCase,
			@ProfitPrice,
			@ProfitPercent,
			@ProfitSizePercent,
			@LossPrice,
			@LossPercent,
			@IsLeveRage
			)
	END TRY
	BEGIN CATCH
		SET @Error = ERROR_NUMBER();
	END CATCH

	SET NOCOUNT OFF;

RETURN @Error;