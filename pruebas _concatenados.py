import cv2
import threading
import easyocr
import time

# Inicializa EasyOCR (gpu=True si tienes GPU compatible)
lector = easyocr.Reader(['en'], gpu=False)

# Variables globales
rectangulos_rois = []       # Lista de ROI: (x, y, w, h)
numeros_detectados = []     # Números detectados por ROI
confianzas = []             # Confiabilidad por ROI
seleccionando = False
punto_inicio = None
punto_actual = None
procesando = False
bloqueo = threading.Lock()
ultimos_valores = []  # Lista paralela a numeros_detectados

# Archivo de registro
log_file = "registro_ocr.txt"

def registrar_evento_ocr_completo(lista_textos):
    """Guarda la línea completa de números detectados, igual a la que aparece en pantalla"""
    texto_total = " ".join([t for t in lista_textos if t.strip().isdigit()])
    if texto_total:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Numeros detectados: {texto_total}\n")

def esta_dentro_roi(x, y, roi):
    rx, ry, rw, rh = roi
    return rx <= x <= rx + rw and ry <= y <= ry + rh

def callback_mouse(event, x, y, flags, param):
    global seleccionando, punto_inicio, punto_actual

    if event == cv2.EVENT_LBUTTONDOWN:
        seleccionando = True
        punto_inicio = (x, y)
        punto_actual = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE and seleccionando:
        punto_actual = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        seleccionando = False
        x1, y1 = punto_inicio
        x2, y2 = punto_actual
        x_min, y_min = min(x1, x2), min(y1, y2)
        w, h = abs(x2 - x1), abs(y2 - y1)
        if w > 10 and h > 10:
            with bloqueo:
                rectangulos_rois.append((x_min, y_min, w, h))
                numeros_detectados.append("")
                confianzas.append(0.0)
                ultimos_valores.append(None)

    elif event == cv2.EVENT_RBUTTONDOWN:
        with bloqueo:
            for i, roi in enumerate(rectangulos_rois):
                if esta_dentro_roi(x, y, roi):
                    rectangulos_rois.pop(i)
                    numeros_detectados.pop(i)
                    confianzas.pop(i)
                    ultimos_valores.pop(i) 
                    break

def ocr_thread(frame, rois):
    global numeros_detectados, confianzas, procesando, ultimos_valores
    temp_numeros = []
    temp_confianzas = []

    for roi in rois:
        x, y, w, h = roi
        roi_img = frame[y:y+h, x:x+w]
        roi_rgb = cv2.cvtColor(roi_img, cv2.COLOR_BGR2RGB)
        resultados = lector.readtext(roi_rgb, detail=1, allowlist='0123456789')

        texto = ""
        confianza = 0.0
        if resultados:
            texto = "".join([res[1] for res in resultados if res[1].isdigit()])
            confianza = sum([res[2] for res in resultados]) / len(resultados)

        temp_numeros.append(texto)
        temp_confianzas.append(confianza)

    with bloqueo:
        numeros_detectados = temp_numeros
        confianzas = temp_confianzas
        registrar_evento_ocr_completo(temp_numeros)
        procesando = False

        # Validación de salto de valor
        for i, nuevo_valor in enumerate(temp_numeros):
            if nuevo_valor.isdigit():
                nuevo_valor_int = int(nuevo_valor)
                anterior = ultimos_valores[i]
                if anterior is not None:
                    diferencia = abs(nuevo_valor_int - anterior)
                    if nuevo_valor_int <= anterior:
                        print(f"[ALERTA ROI {i}] Valor menor o igual que el anterior ({anterior} -> {nuevo_valor_int})")
                    if diferencia > 5:
                        print(f"[ALERTA ROI {i}] Salto demasiado grande ({anterior} -> {nuevo_valor_int})")
                ultimos_valores[i] = nuevo_valor_int
            else:
                # Si no es un número válido, no actualizar
                print(f"[ALERTA ROI {i}] Valor no numérico detectado: '{nuevo_valor}'")

def main():
    global procesando
    video_path = r"video\shinhan.mov"
    cap = cv2.VideoCapture(video_path)
  # Cambiar a 0 si deseas usar la cámara predeterminada
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    cv2.namedWindow("Video")
    cv2.setMouseCallback("Video", callback_mouse)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        with bloqueo:
            if rectangulos_rois and not procesando:
                procesando = True
                frame_copy = frame.copy()
                t = threading.Thread(target=ocr_thread, args=(frame_copy, rectangulos_rois.copy()))
                t.start()

            for i, roi in enumerate(rectangulos_rois):
                x, y, w, h = roi
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if i < len(confianzas):
                    texto_conf = f"{confianzas[i]*100:.1f}%"
                    cv2.putText(frame, texto_conf, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            texto_total = "Numeros detectados: " + " ".join(
                [t for t in numeros_detectados if t.strip().isdigit()]
            )
            cv2.putText(frame, texto_total, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if seleccionando and punto_inicio and punto_actual:
            cv2.rectangle(frame, punto_inicio, punto_actual, (255, 0, 0), 2)

        cv2.imshow("Video", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()