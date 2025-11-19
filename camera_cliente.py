import cv2
import numpy as np
import requests
import time
import os
from collections import deque

API_URL_POST = "http://127.0.0.1:8000/ingest"
API_URL_GET  = "http://127.0.0.1:8000/status"
SNAPSHOT_DIR = "snapshots"

def main():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Não foi possível abrir a câmera.")
        return

    ret, prev = cap.read()
    if not ret:
        print("Não foi possível ler o primeiro frame.")
        return

    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (9, 9), 0)

    rtt_hist = deque(maxlen=100)

    # para guardar as ultimas metricas calculadas
    last_upload_ms   = None
    last_proc_ms     = None
    last_download_ms = None
    last_rtt_ms      = None

    detecting = False

    print("ESPACO = iniciar/pausar deteccao")
    print("G      = capturar imagem + GET /status")
    print("ESC    = sair")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if not detecting:
            cv2.putText(
                frame, "PRESSIONE ESPACO PARA INICIAR",
                (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 0, 255), 2, cv2.LINE_AA
            )
            cv2.imshow("Reactive Cam -> API", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 32:      # ESPACO
                detecting = True
            elif key == 27:    # ESC
                break
            elif key == ord('g'):
                # mesmo pausado, permitir snapshot simples (sem POST/GET)
                ts = time.time()
                fname = os.path.join(SNAPSHOT_DIR, f"snapshot_{int(ts)}.jpg")
                cv2.imwrite(fname, frame)
                print(f"[SNAPSHOT] Imagem salva (modo pausado): {fname}")
            continue

        # ---------- PROCESSAMENTO DO FRAME (detec/POST) ----------
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (9, 9), 0)

        diff = cv2.absdiff(gray_blur, prev_gray)
        motion_level = float(np.mean(diff))
        prev_gray = gray_blur

        brightness = float(np.mean(gray))

        if brightness > 140:
            ilum = "Claro"
        elif brightness < 80:
            ilum = "Escuro"
        else:
            ilum = "Ilum. media"

        mov = "Movimento" if motion_level > 8 else "Parado"
        caption = f"{ilum} | {mov}"

        cv2.putText(
            frame, caption, (16, 32),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA
        )

        t_client_send = time.time()
        try:
            resp = requests.post(
                API_URL_POST,
                json={
                    "sent_ts": t_client_send,
                    "caption": caption,
                    "aux": {
                        "brightness": brightness,
                        "motion_level": motion_level
                    }
                },
                timeout=0.5
            )
            t_client_recv = time.time()

            resp.raise_for_status()
            data = resp.json()

            server_recv_ts = data["server_recv_ts"]
            server_send_ts = data["server_send_ts"]

            upload_ms   = (server_recv_ts - t_client_send) * 1000.0
            proc_ms     = (server_send_ts - server_recv_ts) * 1000.0
            download_ms = (t_client_recv - server_send_ts) * 1000.0
            rtt_ms      = (t_client_recv - t_client_send) * 1000.0

            rtt_hist.append(rtt_ms)
            rtt_avg_ms = float(np.mean(rtt_hist))

            # guarda ultimas metricas
            last_upload_ms   = upload_ms
            last_proc_ms     = proc_ms
            last_download_ms = download_ms
            last_rtt_ms      = rtt_ms

            cv2.putText(
                frame,
                f"RTT: {rtt_ms:.1f} ms (media {rtt_avg_ms:.1f} ms)",
                (16, 64),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA
            )
            cv2.putText(
                frame,
                f"UP: {upload_ms:.1f} | PROC: {proc_ms:.1f} | DOWN: {download_ms:.1f} ms",
                (16, 96),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2, cv2.LINE_AA
            )

        except Exception as e:
            cv2.putText(
                frame,
                f"Erro API: {type(e).__name__}",
                (16, 64),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA
            )

        cv2.imshow("Reactive Cam -> API", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 32:      # ESPACO
            detecting = not detecting
        elif key == 27:    # ESC
            break
        elif key == ord('g'):
            # ---------- AQUI ENTRA O SNAPSHOT + GET ----------
            ts = time.time()
            fname = os.path.join(SNAPSHOT_DIR, f"snapshot_{int(ts)}.jpg")
            cv2.imwrite(fname, frame)

            print(f"\n[SNAPSHOT] Imagem salva: {fname}")

            # faz GET /status para pegar infos da API
            try:
                s_resp = requests.get(API_URL_GET, timeout=0.5)
                s_resp.raise_for_status()
                status_data = s_resp.json()
                print("[OPERADOR GET] Resposta da API:")
                print(status_data)
            except Exception as e:
                print(f"[OPERADOR GET] Erro no GET /status: {type(e).__name__}")

            # mostra também as infos locais (caption/metricas)
            print("[INFOS LOCAIS]")
            print(f"caption       = {caption}")
            print(f"brightness    = {brightness:.2f}")
            print(f"motion_level  = {motion_level:.2f}")
            print(f"upload_ms     = {last_upload_ms}")
            print(f"proc_ms       = {last_proc_ms}")
            print(f"download_ms   = {last_download_ms}")
            print(f"rtt_ms        = {last_rtt_ms}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
