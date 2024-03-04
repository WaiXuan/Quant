import numpy as np

class Indicator():
    
    def ema(src, timeperiod):
        alpha = 2 / (timeperiod + 1)
        ema = np.zeros_like(src, dtype=np.float64)
        ema[0] = src[0]
        
        for i in range(1, len(src)):
            ema[i] = alpha * src[i] + (1 - alpha) * ema[i - 1]

        return ema