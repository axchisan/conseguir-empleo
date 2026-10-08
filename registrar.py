"""Registra una postulación enviada en la base de datos (Neon).

Uso:
  .venv/bin/python registrar.py li:<jobId> <canal> <cv> [notas]
  .venv/bin/python registrar.py nueva "<empresa>" "<titulo>" <area> <fuente> <canal> <cv> [url] [notas]
"""
import sys
from datetime import date, timedelta

from db import conectar

hoy = date.today()
seguimiento = hoy + timedelta(days=5)

with conectar() as db:
    if sys.argv[1] == "nueva":
        _, _, empresa, titulo, categoria, fuente, canal, cv, *resto = sys.argv
        url = resto[0] if resto and resto[0] else None
        notas = resto[1] if len(resto) > 1 else None
        db.execute("INSERT INTO empresas(nombre) VALUES(%s) ON CONFLICT (nombre) DO NOTHING", (empresa,))
        eid = db.execute("SELECT id FROM empresas WHERE nombre=%s", (empresa,)).fetchone()["id"]
        oferta_id = db.execute("INSERT INTO ofertas(empresa_id,titulo,categoria,fuente,url) VALUES(%s,%s,%s,%s,%s) RETURNING id",
                               (eid, titulo, categoria, fuente, url)).fetchone()["id"]
    else:
        externo, canal, cv, *resto = sys.argv[1:]
        notas = resto[0] if resto else None
        oferta_id = db.execute("SELECT id FROM ofertas WHERE externo_id=%s", (externo,)).fetchone()["id"]

    pid = db.execute("""INSERT INTO postulaciones(oferta_id,canal,cv_usado,estado,fecha_envio,proximo_seguimiento,notas)
                        VALUES(%s,%s,%s,'enviada',%s,%s,%s) RETURNING id""",
                     (oferta_id, canal, cv, hoy, seguimiento, notas)).fetchone()["id"]
    db.commit()
print(f"postulación {pid} registrada (oferta {oferta_id})")
