# 📷 OCR en Video en Tiempo Real con OpenCV y EasyOCR

Este proyecto permite detectar y leer números en tiempo real desde una cámara (o video) usando OpenCV y EasyOCR. El usuario puede seleccionar manualmente regiones de interés (ROIs) sobre la imagen para que el sistema extraiga los datos mediante reconocimiento óptico de caracteres (OCR).

---

## 🚀 Características

- Selección manual de zonas para lectura de texto.
- Reconocimiento automático de números en tiempo real.
- Alerta por cambios bruscos o inconsistencias en los valores detectados.
- Registro de resultados con marcas de tiempo.
- Interfaz visual para ver detecciones y niveles de confianza.

---

## 🧰 Requisitos

- Python 3.7 o superior
- Webcam conectada
- Dependencias:

```bash
pip install opencv-python easyocr
