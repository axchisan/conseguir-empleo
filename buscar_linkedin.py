"""Busca ofertas recientes en LinkedIn (API pública de invitado) y las guarda en la base.

Las búsquedas, ciudades y palabras clave salen de perfil.json ("areas" y "encaje").
Uso: .venv/bin/python buscar_linkedin.py [horas=24]
"""
import html
import re
import sys
import time
import urllib.parse
import urllib.request

from db import conectar, perfil

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"}
TITULO_SENIOR = re.compile(r"\b(sr|senior|ssr|semi ?senior|staff|lead|l[ií]der|arquitect\w*|manager|gerente|"
                           r"coordinador|director|principal|head|expert|experto)\b", re.I)


def get(url):
    req = urllib.request.Request(url, headers=UA)
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(3 * (intento + 1))
    return ""


def texto(h, clase):
    m = re.search(r'class="[^"]*' + re.escape(clase) + r'[^"]*"[^>]*>(.*?)</(?:a|h\d|span|div|figcaption)', h, re.S)
    return html.unescape(re.sub(r"<[^>]+>|\s+", " ", m.group(1))).strip() if m else ""


def ids_busqueda(kw, loc, segundos):
    ids = []
    for start in (0, 25):
        q = urllib.parse.urlencode({"keywords": kw, "location": loc, "f_TPR": f"r{segundos}", "start": start})
        h = get("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?" + q)
        nuevos = re.findall(r"urn:li:jobPosting:(\d+)", h)
        ids += nuevos
        if len(nuevos) < 10:
            break
        time.sleep(1.5)
    return ids


def detalle(jid):
    h = get(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}")
    if not h:
        return None
    m = re.search(r'show-more-less-html__markup[^>]*>(.*?)</div>', h, re.S)
    desc = html.unescape(re.sub(r"<br\s*/?>|</li>|</p>", "\n", m.group(1))) if m else ""
    desc = re.sub(r"<[^>]+>", "", desc).strip()
    aplicantes = texto(h, "num-applicants__caption")
    n = re.search(r"(\d+)", aplicantes)
    criterios = re.findall(r'description__job-criteria-text[^>]*>(.*?)</span>', h, re.S)
    criterios = [html.unescape(c).strip() for c in criterios]
    externo = re.search(r'id="applyUrl"[^>]*><!--"(.*?)"-->', h)
    return {
        "titulo": texto(h, "top-card-layout__title"),
        "empresa": texto(h, "topcard__org-name-link") or texto(h, "topcard__flavor"),
        "ciudad": texto(h, "topcard__flavor--bullet"),
        "publicada": texto(h, "posted-time-ago__text"),
        "num": int(n.group(1)) if n else None,
        "aplicantes_txt": aplicantes,
        "nivel": criterios[0] if criterios else "",
        "desc": desc,
        "emails": ";".join(sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+[a-z]", desc)))),
        "externo": html.unescape(externo.group(1)) if externo else "",
    }


def encaje(d, area, p=None):
    """Puntaje 0-100 de qué tanto encaja la oferta con el perfil."""
    p = p or perfil()
    reglas = p.get("encaje", {})
    t = (d["titulo"] + " " + d["desc"] + " " + d["nivel"]).lower()
    s = 40 + min(35, sum(v for k, v in reglas.get("positivas", {}).items() if k.lower() in t))
    s += sum(v for k, v in reglas.get("negativas", {}).items() if k.lower() in t)
    if TITULO_SENIOR.search(d["titulo"]) and not reglas.get("acepta_senior"):
        s -= 40
    if reglas.get("titulo_descarta") and re.search(reglas["titulo_descarta"], d["titulo"], re.I):
        s -= 25
    if reglas.get("titulo_afin") and re.search(reglas["titulo_afin"], d["titulo"], re.I):
        s += 10
    if not reglas.get("habla_ingles") and re.search(r"biling[uü]|english|ingl[eé]s (avanzado|b2|c1|fluido)|\bb2\b|\bc1\b", t):
        s -= 12
    if d["nivel"] in ("Sin experiencia", "Prácticas", "Entry level", "Internship"):
        s += 10
    if d["num"] is not None:
        s += 10 if d["num"] < 25 else (-5 if d["num"] >= 100 else 0)
    s += p.get("areas", {}).get(area, {}).get("ajuste_encaje", 0)
    return max(0, min(100, s))


def main():
    horas = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    p = perfil()
    db = conectar()
    vistos = {r["externo_id"] for r in db.execute("SELECT externo_id FROM ofertas WHERE externo_id IS NOT NULL")}
    candidatos = {}
    for area, conf in p["areas"].items():
        for kw in conf.get("busquedas_linkedin", []):
            for loc in p.get("ubicaciones_linkedin", ["Colombia"]):
                for jid in ids_busqueda(kw, loc, horas * 3600):
                    candidatos.setdefault(jid, area)
                time.sleep(1.5)
    nuevos = [j for j in candidatos if f"li:{j}" not in vistos]
    print(f"{len(candidatos)} ofertas encontradas, {len(nuevos)} nuevas")
    for jid in nuevos:
        d = detalle(jid)
        time.sleep(1.2)
        if not d or not d["titulo"]:
            continue
        area = candidatos[jid]
        empresa = d["empresa"] or "(desconocida)"
        db.execute("INSERT INTO empresas(nombre) VALUES(%s) ON CONFLICT (nombre) DO NOTHING", (empresa,))
        eid = db.execute("SELECT id FROM empresas WHERE nombre=%s", (empresa,)).fetchone()["id"]
        db.execute("""INSERT INTO ofertas(empresa_id,titulo,categoria,ciudad,url,fuente,publicada,num_postulantes,
                      encaje,requisitos,externo_id,descripcion,emails,url_aplicar)
                      VALUES(%s,%s,%s,%s,%s,'linkedin',%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (externo_id) DO NOTHING""",
                   (eid, d["titulo"], area, d["ciudad"], f"https://www.linkedin.com/jobs/view/{jid}", d["publicada"],
                    d["num"], encaje(d, area, p), d["nivel"] + " | " + d["aplicantes_txt"], f"li:{jid}", d["desc"],
                    d["emails"], d["externo"]))
        db.commit()
    for r in db.execute("""SELECT o.encaje, o.num_postulantes, o.publicada, o.titulo, e.nombre, o.ciudad, o.emails
                           FROM ofertas o JOIN empresas e ON e.id=o.empresa_id
                           WHERE o.fuente='linkedin' AND NOT EXISTS (SELECT 1 FROM postulaciones p WHERE p.oferta_id=o.id)
                           ORDER BY o.encaje DESC NULLS LAST, o.id DESC LIMIT 40"""):
        print(" | ".join("" if x is None else str(x) for x in r.values()))
    db.close()


if __name__ == "__main__":
    main()
