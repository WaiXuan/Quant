/****************************************************************
** Desc: 新增Veags策略K線資訊
*****************************************************************
USE [Quantitative]
GO

DECLARE	@return_value int

EXEC	@return_value = [Record].[usp_InsertVeags]
		@Symbol = N'ETHUSDT',
		@TimeFrame = NULL,
		@RowOpen = NULL,
		@RowHigh = NULL,
		@RowLow = NULL,
		@RowClose = NULL,
		@Ema12 = NULL,
		@Ema144 = NULL,
		@Ema169 = NULL,
		@Ema576 = NULL,
		@Ema676 = NULL,
		@Adosc = NULL,
		@Rsi = NULL,
		@Obv = NULL,
		@VolumeOsc = NULL,
		@KDJ_K = NULL,
		@KDJ_D = NULL,
		@KDJ_J = NULL

SELECT	'Return Value' = @return_value

GO

*****************************************************************
** Change History
** 2023/10/22   KAO   First Release
*****************************************************************/
CREATE PROCEDURE [Record].[usp_InsertVeags]
	@Symbol		VARCHAR(20),
	@TimeFrame	VARCHAR(2),
	@RowOpen	DECIMAL(9, 2),
	@RowHigh	DECIMAL(9, 2),
	@RowLow		DECIMAL(9, 2),
	@RowClose	DECIMAL(9, 2),
	@Ema12		DECIMAL(9, 2),
	@Ema144		DECIMAL(9, 2),
	@Ema169		DECIMAL(9, 2),
	@Ema576		DECIMAL(9, 2),
	@Ema676		DECIMAL(9, 2),
	@Adosc		DECIMAL(9, 2),
	@Rsi		DECIMAL(9, 2),
	@Obv		DECIMAL(9, 2),
	@VolumeOsc	DECIMAL(9, 2),
	@KDJ_K		DECIMAL(9, 2),
	@KDJ_D		DECIMAL(9, 2),
	@KDJ_J		DECIMAL(9, 2)
AS

	SET NOCOUNT ON;

	DECLARE @Error INT;
	SET @Error = 0;

	BEGIN TRY	

	INSERT INTO [Record].[Vegas]
           ([Symbol]
           ,[TimeFrame]
           ,[RowOpen]
           ,[RowHigh]
           ,[RowLow]
           ,[RowClose]
           ,[Ema12]
           ,[Ema144]
           ,[Ema169]
           ,[Ema576]
           ,[Ema676]
           ,[Adosc]
           ,[Rsi]
           ,[Obv]
           ,[VolumeOsc]
           ,[KDJ_K]
           ,[KDJ_D]
           ,[KDJ_J]
			)
     VALUES
           (@Symbol,
			@TimeFrame,
			@RowOpen,
			@RowHigh,
			@RowLow,
			@RowClose,
			@Ema12,
			@Ema144,
			@Ema169,
			@Ema576,
			@Ema676,
			@Adosc,
			@Rsi,
			@Obv,
			@VolumeOsc,
			@KDJ_K,
			@KDJ_D,
			@KDJ_J
			)
	END TRY
	BEGIN CATCH
		SET @Error = ERROR_NUMBER();
	END CATCH

	SET NOCOUNT OFF;

RETURN @Error;