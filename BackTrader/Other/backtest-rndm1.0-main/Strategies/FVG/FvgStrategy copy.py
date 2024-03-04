# 引入必要的模組或函數
from Utils import num_func as nf

# 定義FvgStrategy類別
class FvgStrategy():

    # 設定一個類別層級的常數FVG_DELTA_THRESHOLD
  FVG_DELTA_THRESHOLD = 1.5

  # 初始化方法，建立一個fvg_tracker字典用於追蹤交易策略的數據
  def __init__(self):
    self.fvg_tracker = {
      'delta_p': [],
      'delta_n': [],
    }

  # cycle_chunk方法用於處理一個數據區間(chunk)
  def cycle_chunk(self, chunk):
    # 重設fvg_tracker
    self.reset_fvg_tracker()
    self.chunk = chunk
    # 在過去60個數據點中遍歷，每次取3個相鄰的點
    for i in range(-60, 1, 1):
      try:
        # 呼叫get_movement_delta方法，計算價格變動情況
        self.get_movement_delta(chunk, i)
      except Exception as e:
        pass
    # 移除無效的fvg交易區間
    self.remove_invalidated_fvg_zones()
    # 返回fvg_tracker，其中包含檢測到的有效交易區間

  # 重設fvg_tracker，清空之前的數據
  def reset_fvg_tracker(self):
    self.fvg_tracker = {
      'delta_p': [],
      'delta_n': [],
    }

  # 移除無效的fvg交易區間
  def remove_invalidated_fvg_zones(self):
    # 遍歷delta_p和delta_n中的fvg交易區間
    for idx, x in enumerate(self.fvg_tracker['delta_p']):
      self.fvg_tracker['delta_p'][idx]['fvg_invalidated'] = False
      for i in range(x['fvg_chunk_index'], 1, 1):
        if self.chunk.close[i] < x['fvg_low']:
          # 將fvg標記為無效
          self.fvg_tracker['delta_p'][idx]['fvg_invalidated'] = True
          break
    for idx, x in enumerate(self.fvg_tracker['delta_n']):
      self.fvg_tracker['delta_n'][idx]['fvg_invalidated'] = False
      for i in range(x['fvg_chunk_index'], 1, 1):
        if self.chunk.close[i] > x['fvg_high']:
          # 將fvg標記為無效
          self.fvg_tracker['delta_n'][idx]['fvg_invalidated'] = True
          break

  # 計算價格變動情況
  def get_movement_delta(self, chunk, index) -> int:
    # 檢測是否符合牛市fvg條件
    if chunk.high[index] < chunk.low[index+2] and chunk.high[index] > chunk.open[index+1] and chunk.low[index+2] < chunk.close[index+1]:
      if nf.pct_delta(chunk.high[index], chunk.low[index+2]) >= self.FVG_DELTA_THRESHOLD:
        self.fvg_tracker['delta_p'].append({
          'fvg_high': chunk.low[index+2],
          'fvg_low': chunk.high[index],
          'fvg_timestamp': chunk.datetime.datetime(index),
          'fvg_chunk_index': index+2
        })
    # 檢測是否符合熊市fvg條件
    if chunk.low[index] > chunk.high[index+2] and chunk.low[index] < chunk.open[index+1] and chunk.high[index+2] > chunk.close[index+1]:
      if nf.pct_delta(chunk.high[index+2], chunk.low[index]) >= self.FVG_DELTA_THRESHOLD:
        self.fvg_tracker['delta_n'].append({
          'fvg_high': chunk.low[index],
          'fvg_low': chunk.high[index+2],
          'fvg_timestamp': chunk.datetime.datetime(index),
          'fvg_chunk_index': index+2
        })

  # 找到最接近的熊市fvg交易區間
  def nearest_delta_n_fvg(self):
    nearest_p_fvg = None
    nearest_p_fvg_distance = 99999
    for x in self.fvg_tracker['delta_n']:
      if not x['fvg_invalidated'] and (x['fvg_low']-self.chunk.close[0]) < nearest_p_fvg_distance:
        nearest_p_fvg = x
    return nearest_p_fvg

  # 找到最接近的牛市fvg交易區間
  def nearest_delta_p_fvg(self):
    nearest_n_fvg = None
    nearest_n_fvg_distance = 99999
    for x in self.fvg_tracker['delta_p']:
      if not x['fvg_invalidated'] and (self.chunk.close[0]-x['fvg_low']) < nearest_n_fvg_distance:
        nearest_n_fvg = x
    return nearest_n_fvg

  # 執行做空交易
  def short(self):
    fvg = self.nearest_delta_n_fvg()
    acceptance = False
    if fvg is not None and self.chunk.close[0] < fvg['fvg_low']:
      if fvg['fvg_low'] < self.chunk.open[-1] and fvg['fvg_low'] < self.chunk.close[-1]:
        acceptance = True
    return {
      'fvg': fvg,
    }