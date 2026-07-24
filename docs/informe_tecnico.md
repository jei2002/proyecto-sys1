# Informe técnico — Sistema de restauración y ambientación de voz en tiempo real

## 1. Introducción
(Objetivo del proyecto, motivación, alcance)

## 2. Arquitectura del sistema
(Insertar diagrama de bloques: captura → filtrado → efectos → salida,
con análisis espectral y GUI en paralelo)

## 3. Fundamento teórico por módulo

### 3.1 Reducción de ruido ambiente
- Ecuación de diferencias
- Función de transferencia H(z)
- Justificación de la frecuencia de corte elegida

### 3.2 Ecualizador de 3 bandas
- Diseño de cada filtro (graves/medios/agudos)
- Diagrama de polos y ceros

### 3.3 Pitch shifting (afinador / "autotune")
- STFT, ventaneo, overlap-add
- Phase vocoder: por qué preserva el timbre al cambiar el tono

### 3.4 Efecto robot (modulación)
- Modulación en anillo
- Por qué este bloque NO es un sistema LTI (discusión de invarianza temporal)

### 3.5 Delay
- Ecuación de diferencias con retardo
- Relación con sistemas de eco

### 3.6 Reverb
- Convolución con respuesta al impulso
- Alternativa: modelo de Schroeder (comb + all-pass)

## 4. Interfaz gráfica
(Capturas de pantalla, descripción de controles)

## 5. Pruebas y resultados
(Grabaciones antes/después, espectrogramas comparativos)

## 6. Conclusiones

## 7. Referencias
