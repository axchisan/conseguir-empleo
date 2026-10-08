"""Conexión a la base de datos de postulaciones (Postgres en Neon).

La cadena de conexión sale de la variable DATABASE_URL o del archivo .env del proyecto.
Ejecutarlo directamente crea las tablas: .venv/bin/python db.py
"""
import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

RAIZ = Path(__file__).resolve().parent

ESQUEMA = """
CREATE TABLE IF NOT EXISTS empresas (
  id SERIAL PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, sector TEXT, ciudad TEXT,
  web TEXT, portal_empleo TEXT, notas TEXT, creado TIMESTAMP DEFAULT (now() AT TIME ZONE 'America/Bogota'));
CREATE TABLE IF NOT EXISTS contactos (
  id SERIAL PRIMARY KEY, empresa_id INTEGER REFERENCES empresas(id), nombre TEXT, cargo TEXT,
  email TEXT, telefono TEXT, linkedin TEXT, fuente TEXT, notas TEXT,
  creado TIMESTAMP DEFAULT (now() AT TIME ZONE 'America/Bogota'));
CREATE TABLE IF NOT EXISTS ofertas (
  id SERIAL PRIMARY KEY, empresa_id INTEGER REFERENCES empresas(id), titulo TEXT NOT NULL,
  categoria TEXT, ciudad TEXT, modalidad TEXT, salario TEXT, url TEXT, fuente TEXT, publicada TEXT,
  num_postulantes INTEGER, encaje INTEGER CHECK (encaje BETWEEN 0 AND 100), requisitos TEXT,
  creado TIMESTAMP DEFAULT (now() AT TIME ZONE 'America/Bogota'),
  externo_id TEXT UNIQUE, descripcion TEXT, emails TEXT, url_aplicar TEXT);
CREATE TABLE IF NOT EXISTS postulaciones (
  id SERIAL PRIMARY KEY, oferta_id INTEGER REFERENCES ofertas(id), contacto_id INTEGER REFERENCES contactos(id),
  canal TEXT, cv_usado TEXT, carta TEXT,
  estado TEXT DEFAULT 'preparada' CHECK (estado IN ('preparada','enviada','vista','respuesta','entrevista','rechazada','oferta','descartada')),
  fecha_envio DATE, proximo_seguimiento DATE, notas TEXT,
  creado TIMESTAMP DEFAULT (now() AT TIME ZONE 'America/Bogota'));
CREATE TABLE IF NOT EXISTS eventos (
  id SERIAL PRIMARY KEY, postulacion_id INTEGER REFERENCES postulaciones(id), tipo TEXT, detalle TEXT,
  fecha TIMESTAMP DEFAULT (now() AT TIME ZONE 'America/Bogota'));
"""


def _url():
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    env = RAIZ / ".env"
    if env.exists():
        for linea in env.read_text().splitlines():
            if linea.startswith("DATABASE_URL="):
                return linea.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("Falta DATABASE_URL en el archivo .env (ver CLAUDE.md, paso 3)")


def conectar():
    return psycopg.connect(_url(), row_factory=dict_row, autocommit=False)


def perfil():
    """Datos de la persona que busca empleo (perfil.json, nunca se sube al repo)."""
    archivo = RAIZ / "perfil.json"
    if not archivo.exists():
        raise RuntimeError("Falta perfil.json: cópialo de perfil.ejemplo.json y llénalo (ver CLAUDE.md, paso 2)")
    return json.loads(archivo.read_text(encoding="utf-8"))


if __name__ == "__main__":
    with conectar() as db:
        db.execute(ESQUEMA)
        db.commit()
    print("Tablas listas")
