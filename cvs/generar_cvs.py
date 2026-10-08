"""Genera las variantes del CV en PDF (HTML -> Chrome/Edge en modo headless).

Los datos salen de cvs/cv.json (copia de cvs/cv.ejemplo.json, nunca se sube al repo).
Uso: .venv/bin/python cvs/generar_cvs.py
Cada variante sale en cvs/adaptados/<archivo>.pdf
"""
import html as h
import json
import pathlib
import shutil
import subprocess
import sys

AQUI = pathlib.Path(__file__).parent
SALIDA = AQUI / "adaptados"
NAVEGADORES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def navegador():
    for n in NAVEGADORES:
        if pathlib.Path(n).exists() or shutil.which(n):
            return n
    sys.exit("No encontré Chrome ni Edge para imprimir el PDF. Abre el .html generado y usa Imprimir → Guardar como PDF.")


def e(texto):
    return h.escape(str(texto or ""))


def li(items):
    return "".join(f"<li>{e(i)}</li>" for i in items)


def item(titulo, fechas, lugar, nota="", puntos=()):
    nota = f"<p class=ctx>{e(nota)}</p>" if nota else ""
    lista = f"<ul>{li(puntos)}</ul>" if puntos else ""
    return (f"<div class=item><div class=row><b>{e(titulo)}</b><span>{e(fechas)}</span></div>"
            f"<div class=sub>{e(lugar)}</div>{nota}{lista}</div>")


def pagina(d, v):
    habilidades = "".join(f"<div class=hab><b>{e(t)}</b><span>{e(x)}</span></div>" for t, x in v["habilidades"])
    exp = "".join(item(x["cargo"], x["fechas"], x["empresa"], x.get("contexto", ""), x.get("puntos", []))
                  for x in v["experiencia"])
    form = "".join(item(f["titulo"], f["fechas"], f["institucion"], f.get("nota", "")) for f in d["formacion"])
    cert = "".join(item(c["titulo"], c["fecha"], c["entidad"]) for c in d.get("certificaciones", []))
    idiomas = "".join(f"<p>{e(i)}</p>" for i in d.get("idiomas", []))
    nombre = "<br>".join(e(p) for p in d["nombre_lineas"])
    secc_cert = f"<h2>Certificaciones</h2>{cert}" if cert else ""
    return f"""<!doctype html><html lang=es><meta charset=utf-8><style>
@page {{ size: Letter; margin: 0 }}
* {{ box-sizing: border-box; margin: 0; padding: 0 }}
body {{ font: 9.6pt/1.38 "Helvetica Neue", Arial, sans-serif; color: #1d2433; display: grid; grid-template-columns: 2.35in 1fr; min-height: 11in }}
aside {{ background: #f1f4f8; padding: .55in .3in; }}
main {{ padding: .42in .42in .3in .38in }}
h1 {{ font-size: 21pt; line-height: 1.1; color: #10213f }}
.tit {{ font-size: 11.5pt; color: #1f5fa8; font-weight: 600; margin-top: 4px }}
.subt {{ font-size: 9pt; color: #5a6475; margin-top: 2px }}
h2 {{ font-size: 9.2pt; letter-spacing: .12em; text-transform: uppercase; color: #1f5fa8; border-bottom: 1.5px solid #c9d6e8; padding-bottom: 3px; margin: 12px 0 6px }}
aside h2 {{ margin-top: 20px }} aside h2:first-child {{ margin-top: 0 }}
aside p, aside div {{ font-size: 9pt }}
.hab {{ margin-bottom: 7px }} .hab b {{ display: block; font-size: 9pt }} .hab span {{ color: #4a5466 }}
.perfil {{ text-align: justify }}
.item {{ margin-bottom: 7px }}
.row {{ display: flex; justify-content: space-between; gap: 8px }} .row span {{ color: #5a6475; white-space: nowrap; font-size: 9pt }}
.sub {{ color: #4a5466; font-size: 9pt }} .ctx {{ font-style: italic; color: #4a5466; font-size: 9pt; margin-top: 2px }}
ul {{ margin: 4px 0 0 14px }} li {{ margin-bottom: 2px }}
.pie {{ margin-top: 14px; font-weight: 600; color: #10213f }}
</style><body>
<aside><h2>Contacto</h2>{''.join(f'<p>{e(c)}</p>' for c in d['contacto'])}
<h2>Habilidades</h2>{habilidades}
<h2>Idiomas</h2>{idiomas}</aside>
<main><h1>{nombre}</h1><div class=tit>{e(v['titulo'])}</div><div class=subt>{e(v['subtitulo'])}</div>
<h2>Perfil</h2><p class=perfil>{e(v['perfil'])}</p>
<h2>Experiencia</h2>{exp}<h2>Formación</h2>{form}{secc_cert}
<p class=pie>{e(d.get('pie', ''))}</p></main></body></html>"""


def main():
    archivo = AQUI / "cv.json"
    if not archivo.exists():
        sys.exit("Falta cvs/cv.json: cópialo de cvs/cv.ejemplo.json y llénalo con tus datos.")
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    SALIDA.mkdir(exist_ok=True)
    nav = navegador()
    for nombre, v in datos["variantes"].items():
        html_cv = SALIDA / f"{nombre}.html"
        html_cv.write_text(pagina(datos, v), encoding="utf-8")
        pdf = SALIDA / f"{nombre}.pdf"
        subprocess.run([nav, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", html_cv.as_uri()], check=True, capture_output=True)
        print(pdf)


if __name__ == "__main__":
    main()
