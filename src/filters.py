import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi, fftconvolve

# ---------------------------------------------------------------------
# 1. Reducción de ruido
# ---------------------------------------------------------------------
def design_noise_filter(cutoff=100, sample_rate=44100, order=4):
    """
    Filtro pasa-altos Butterworth para eliminar ruido de baja frecuencia
    (zumbido eléctrico, ruido de ventiladores, etc).
    Ecuación de diferencias: y[n] = sum(b_k x[n-k]) - sum(a_k y[n-k])
    """
    nyq = 0.5 * sample_rate
    b, a = butter(order, cutoff / nyq, btype="highpass")
    return b, a

def apply_noise_reduction(x, b, a, zi=None):
    """
    Aplica el filtro de ruido manteniendo el estado acústico (zi) 
    para evitar 'clicks' o 'pops' entre bloques de audio en tiempo real.
    """
    y, zf = lfilter(b, a, x, zi=zi if zi is not None else lfilter_zi(b, a) * x[0])
    return y, zf


# ---------------------------------------------------------------------
# 2. Ecualizador de 3 bandas
# ---------------------------------------------------------------------
def design_eq_bands(sample_rate=44100):
    """
    Devuelve 3 filtros (b, a): graves, medios, agudos.
    Cada banda es un sistema LTI independiente; la salida final es la
    suma ponderada por las ganancias de los sliders.
    """
    nyq = 0.5 * sample_rate
    low_b, low_a = butter(2, 300 / nyq, btype="lowpass")
    mid_b, mid_a = butter(2, [300 / nyq, 3000 / nyq], btype="bandpass")
    high_b, high_a = butter(2, 3000 / nyq, btype="highpass")
    return {"low": (low_b, low_a), "mid": (mid_b, mid_a), "high": (high_b, high_a)}

def apply_eq(x, bands, gains):
    """
    Aplica las ganancias (0.0 a 2.0) a cada banda LTI de forma independiente.
    """
    y = np.zeros_like(x)
    for band_name, (b, a) in bands.items():
        y += gains.get(band_name, 1.0) * lfilter(b, a, x)
    return y


# ---------------------------------------------------------------------
# 3. Delay
# ---------------------------------------------------------------------
class DelayEffect:
    """
    Ecuación de diferencias directa: y[n] = x[n] + g * x[n - D]
    Se implementa con un buffer circular para no recalcular todo el historial.
    """
    def __init__(self, delay_samples, feedback_gain=0.4, sample_rate=44100):
        self.delay_samples = delay_samples
        self.g = feedback_gain
        self.buffer = np.zeros(delay_samples)
        self.index = 0

    def process(self, x):
        y = np.zeros_like(x)
        for n, sample in enumerate(x):
            delayed = self.buffer[self.index]
            y[n] = sample + self.g * delayed
            # Actualizamos el buffer con el nuevo eco (Feedback)
            self.buffer[self.index] = sample + self.g * delayed
            self.index = (self.index + 1) % self.delay_samples
        return y


# ---------------------------------------------------------------------
# 4. Reverb (Overlap-Add)
# ---------------------------------------------------------------------
class ReverbEffect:
    """
    Reverb por convolución con algoritmo Overlap-Add para tiempo real.
    y[n] = x[n] * h[n] (convolución).
    
    A diferencia de np.convolve (que recorta la cola entre bloques), esta clase
    guarda el "excedente" acústico en `self.tail` y lo suma suavemente 
    al inicio del siguiente bloque.
    """
    def __init__(self, reverb_time=0.25, sample_rate=44100):
        self.reverb_length = int(reverb_time * sample_rate)
        t_rev = np.linspace(0, 1.0, self.reverb_length)
        
        # Generamos una respuesta acústica (Ruido aleatorio con decaimiento exponencial)
        # Esto imita cómo rebota el sonido en una habitación real
        self.ir = np.random.randn(self.reverb_length) * np.exp(-t_rev * 7)
        self.ir = self.ir / np.max(np.abs(self.ir)) * 0.25 
        self.ir[0] = 1.0 
        
        # Memoria interna para la cola superpuesta (Overlap-Add)
        self.tail = np.zeros(self.reverb_length - 1)

    def process(self, x):
        # Asegurarnos de que procesamos en Mono (1 canal)
        if x.ndim > 1: 
            x = x[:, 0]
            
        # 1. Convolución rápida (Fast Fourier Convolution)
        # fftconvolve es vital aquí porque procesar miles de muestras con convolve estándar congelaría el PC.
        y_conv = fftconvolve(x, self.ir, mode='full')
        N = len(x)
        
        # 2. Extraer el segmento exacto que pide la tarjeta (N muestras)
        y_out = y_conv[:N].copy()
        
        # 3. Sumar la cola acústica (eco) del bloque anterior
        n_tail = min(N, len(self.tail))
        y_out[:n_tail] += self.tail[:n_tail]
        
        # 4. Guardar la nueva cola "sobrante" para el siguiente bloque de audio
        new_tail = y_conv[N:]
        old_tail_leftover = self.tail[N:] if len(self.tail) > N else np.zeros(0)
        
        max_len = max(len(new_tail), len(old_tail_leftover))
        self.tail = np.zeros(max_len)
        self.tail[:len(new_tail)] += new_tail
        self.tail[:len(old_tail_leftover)] += old_tail_leftover
        
        return y_out