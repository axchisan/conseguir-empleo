"""Recalcula el encaje de las ofertas de LinkedIn ya guardadas (útil tras cambiar "encaje" en perfil.json)."""

from buscar_linkedin import encaje
from db import conectar, perfil

p = perfil()
db = conectar()
filas = db.execute("SELECT id, titulo, descripcion, requisitos, num_postulantes, categoria FROM ofertas "
                   "WHERE fuente='linkedin'").fetchall()
for f in filas:
    d = {"titulo": f["titulo"] or "", "desc": f["descripcion"] or "",
         "nivel": (f["requisitos"] or "").split(" | ")[0], "num": f["num_postulantes"]}
    db.execute("UPDATE ofertas SET encaje=%s WHERE id=%s", (encaje(d, f["categoria"], p), f["id"]))
db.commit()
print(f"{len(filas)} ofertas recalculadas")
