from fastapi import FastAPI
from pydantic import BaseModel
from time import time, sleep

app = FastAPI()

last_event = None  # guarda o ultimo evento recebido

class Event(BaseModel):
    sent_ts: float
    caption: str
    aux: dict | None = None

@app.post("/ingest")
def ingest(ev: Event):
    global last_event

    server_recv_ts = time()
    # sleep(0.02)  # simular processamento, se quiser
    server_send_ts = time()

    last_event = {
        "sent_ts": ev.sent_ts,
        "caption": ev.caption,
        "aux": ev.aux,
        "server_recv_ts": server_recv_ts,
        "server_send_ts": server_send_ts,
    }

    return {
        "server_recv_ts": server_recv_ts,
        "server_send_ts": server_send_ts,
        "echo_caption": ev.caption,
    }

@app.get("/status")
def get_status():
    if last_event is None:
        return {"status": "ok", "message": "Nenhum evento recebido ainda."}

    return {
        "status": "ok",
        "message": "Ultimo evento registrado:",
        "last_event": last_event
    }
