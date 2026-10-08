"""Panel de postulaciones (FastAPI) sobre Postgres en Neon. Corre local o desplegado en Vercel.

Variables de entorno: DATABASE_URL, PANEL_PASSWORD, SESSION_SECRET.
En local se leen del archivo .env de la raíz del proyecto.
"""
import hashlib
import hmac
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from psycopg.rows import dict_row

RAIZ = Path(__file__).resolve().parent
for env in (RAIZ / ".env", RAIZ.parent / ".env"):
    if env.exists():
        for linea in env.read_text().splitlines():
            clave, _, valor = linea.partition("=")
            if clave.strip() and _ and not linea.lstrip().startswith("#"):
                os.environ.setdefault(clave.strip(), valor.strip().strip('"'))
ESTADOS = ["preparada", "enviada", "vista", "respuesta", "entrevista", "rechazada", "oferta", "descartada"]
COOKIE = "panel_sesion"
TZ = ZoneInfo("America/Bogota")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def conectar():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def token():
    secreto = os.environ["SESSION_SECRET"].encode()
    return hmac.new(secreto, os.environ["PANEL_PASSWORD"].encode(), hashlib.sha256).hexdigest()


def autenticado(request: Request):
    return hmac.compare_digest(request.cookies.get(COOKIE, ""), token())


@app.middleware("http")
async def proteger(request: Request, call_next):
    ruta = request.url.path
    if ruta in ("/login", "/favicon.ico") or autenticado(request):
        return await call_next(request)
    if ruta.startswith("/api/"):
        return JSONResponse({"error": "no autenticado"}, status_code=401)
    return RedirectResponse("/login", status_code=303)


LOGIN = """<!doctype html><html lang=es><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Mis Postulaciones</title><style>
:root{--bg:#f4f2ee;--panel:#fffdf9;--ink:#1d1b18;--muted:#6f6a62;--line:#e3ded5;--accent:#1f5f4a;--bad:#9b2c2c}
@media (prefers-color-scheme:dark){:root{--bg:#161513;--panel:#1f1d1a;--ink:#ece8e1;--muted:#a39d93;--line:#34312c;--accent:#6fc4a3;--bad:#ec8d8d}}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font:15px -apple-system,system-ui,sans-serif;padding:16px}
form{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:28px;width:min(340px,100%)}
h1{font-size:20px;margin:0 0 4px}p{color:var(--muted);margin:0 0 18px;font-size:13px}
input{width:100%;box-sizing:border-box;font:inherit;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
button{margin-top:12px;width:100%;padding:10px;border:0;border-radius:8px;background:var(--accent);color:var(--panel);font:inherit;font-weight:600;cursor:pointer}
.err{color:var(--bad);font-size:13px;margin-top:10px}</style>
<form method=post action=/login><h1>Mis postulaciones</h1><p>Panel privado</p>
<input type=password name=password placeholder=Contraseña autofocus autocomplete=current-password>
<button>Entrar</button>__ERROR__</form></html>"""


@app.get("/login", response_class=HTMLResponse)
def login_form():
    return LOGIN.replace("__ERROR__", "")


@app.post("/login")
def login(request: Request, password: str = Form("")):
    if not hmac.compare_digest(password.encode(), os.environ["PANEL_PASSWORD"].encode()):
        return HTMLResponse(LOGIN.replace("__ERROR__", "<div class=err>Contraseña incorrecta</div>"), status_code=401)
    r = RedirectResponse("/", status_code=303)
    r.set_cookie(COOKIE, token(), max_age=60 * 60 * 24 * 90, httponly=True, secure=request.url.scheme == "https", samesite="lax")
    return r


@app.get("/", response_class=HTMLResponse)
def inicio():
    return (RAIZ / "index.html").read_text(encoding="utf-8")


def detalle(db, pid):
    p = db.execute("""
        SELECT p.*, o.titulo, o.categoria, o.ciudad, o.modalidad, o.salario, o.url, o.fuente, o.publicada,
               o.num_postulantes, o.encaje, o.requisitos, o.descripcion, o.emails, o.url_aplicar,
               e.id AS empresa_id, e.nombre AS empresa, e.web
        FROM postulaciones p JOIN ofertas o ON o.id = p.oferta_id JOIN empresas e ON e.id = o.empresa_id
        WHERE p.id = %s""", (pid,)).fetchone()
    if not p:
        raise HTTPException(404, "no existe")
    p["contactos"] = db.execute("SELECT * FROM contactos WHERE empresa_id = %s", (p["empresa_id"],)).fetchall()
    p["eventos"] = db.execute("SELECT * FROM eventos WHERE postulacion_id = %s ORDER BY fecha DESC", (pid,)).fetchall()
    return p


@app.get("/api/postulaciones")
def postulaciones():
    with conectar() as db:
        return db.execute("""
            SELECT p.id, p.estado, p.canal, p.cv_usado, p.fecha_envio, p.proximo_seguimiento, p.notas, p.creado,
                   o.id AS oferta_id, o.titulo, o.categoria, o.ciudad, o.url, o.fuente, o.num_postulantes, o.encaje,
                   e.id AS empresa_id, e.nombre AS empresa
            FROM postulaciones p JOIN ofertas o ON o.id = p.oferta_id JOIN empresas e ON e.id = o.empresa_id
            ORDER BY COALESCE(p.fecha_envio, p.creado::date) DESC, p.id DESC""").fetchall()


@app.get("/api/postulaciones/{pid}")
def postulacion(pid: int):
    with conectar() as db:
        return detalle(db, pid)


@app.patch("/api/postulaciones/{pid}")
async def editar(pid: int, request: Request):
    datos = await request.json()
    cambios = {k: (v or None) for k, v in datos.items() if k in ("estado", "notas", "proximo_seguimiento")}
    if "estado" in cambios and cambios["estado"] not in ESTADOS:
        raise HTTPException(400, "estado inválido")
    with conectar() as db:
        anterior = db.execute("SELECT estado FROM postulaciones WHERE id=%s", (pid,)).fetchone()
        if cambios:
            db.execute(f"UPDATE postulaciones SET {', '.join(k + '=%s' for k in cambios)} WHERE id=%s",
                       (*cambios.values(), pid))
        if "estado" in cambios and anterior and anterior["estado"] != cambios["estado"]:
            db.execute("INSERT INTO eventos(postulacion_id, tipo, detalle) VALUES(%s, 'estado', %s)",
                       (pid, f"{anterior['estado']} → {cambios['estado']}"))
        return detalle(db, pid)


@app.post("/api/postulaciones/{pid}/eventos")
async def evento(pid: int, request: Request):
    datos = await request.json()
    with conectar() as db:
        db.execute("INSERT INTO eventos(postulacion_id, tipo, detalle) VALUES(%s, %s, %s)",
                   (pid, datos.get("tipo") or "nota", datos.get("detalle") or ""))
        return detalle(db, pid)


@app.get("/api/ofertas")
def ofertas():
    with conectar() as db:
        return db.execute("""
            SELECT o.id, o.titulo, o.categoria, o.ciudad, o.url, o.fuente, o.publicada, o.num_postulantes, o.encaje,
                   o.emails, e.nombre AS empresa, substr(o.descripcion, 1, 600) AS resumen
            FROM ofertas o JOIN empresas e ON e.id = o.empresa_id
            WHERE NOT EXISTS (SELECT 1 FROM postulaciones p WHERE p.oferta_id = o.id)
            ORDER BY o.encaje DESC NULLS LAST, o.id DESC""").fetchall()


@app.post("/api/ofertas/{oid}/{accion}")
def accion_oferta(oid: int, accion: str):
    if accion not in ("preparar", "descartar"):
        raise HTTPException(404, "acción desconocida")
    estado, nota = (("descartada", "Descartada desde el panel") if accion == "descartar"
                    else ("preparada", "Marcada para postular desde el panel"))
    with conectar() as db:
        db.execute("INSERT INTO postulaciones(oferta_id, estado, notas) VALUES(%s, %s, %s)", (oid, estado, nota))
    return {"ok": True}


@app.get("/api/stats")
def stats():
    hoy = datetime.now(TZ).date()
    with conectar() as db:
        por_estado = {r["estado"]: r["n"] for r in db.execute(
            "SELECT estado, COUNT(*) AS n FROM postulaciones GROUP BY estado")}
        uno = lambda sql, *a: db.execute(sql, a).fetchone()["n"]
        return {
            "total": sum(por_estado.values()),
            "por_estado": por_estado,
            "hoy": uno("SELECT COUNT(*) AS n FROM postulaciones WHERE fecha_envio = %s", hoy),
            "ofertas_sin_postular": uno("SELECT COUNT(*) AS n FROM ofertas o WHERE NOT EXISTS "
                                        "(SELECT 1 FROM postulaciones p WHERE p.oferta_id = o.id)"),
            "hoy_fecha": hoy.isoformat(),
        }
