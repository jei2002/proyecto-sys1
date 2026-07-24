"""
gui.py
------
Interfaz gráfica: botones para cada función, sliders/perillas para
parámetros, y dos gráficas en vivo (forma de onda + espectro FFT).

Placeholder de estructura. Implementación completa en Fase 4, una vez
que audio_io.py, filters.py y pitch_robot.py estén integrados en main.py.
"""

from PyQt5 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("proyecto-sys1 — Restauración y ambientación de voz")

        # TODO Fase 4:
        # - Botones: Grabar, Reproducir, Activar/Desactivar cada efecto
        # - Sliders: ganancia EQ (graves/medios/agudos), pitch (semitonos),
        #   frecuencia portadora (robot), delay time, mezcla reverb
        # - pyqtgraph.PlotWidget x2: forma de onda y espectro, actualizados
        #   en tiempo real desde analysis.py


def run_app():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
