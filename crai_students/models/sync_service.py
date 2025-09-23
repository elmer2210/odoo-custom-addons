# -*- coding: utf-8 -*-
import json
import requests
import unicodedata
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError


# ---------------------------
# Normalización determinista
# ---------------------------
def normalize_code(val: str) -> str:
    """Mayúsculas, sin tildes, espacios -> _, solo A-Z0-9_ (sin truncar)."""
    if not val:
        return ""
    val = ''.join(c for c in unicodedata.normalize('NFKD', val) if not unicodedata.combining(c))
    val = val.upper().strip()
    val = re.sub(r'\s+', '_', val)           # espacios -> _
    val = re.sub(r'[^A-Z0-9_]', '', val)     # solo A-Z0-9_
    val = re.sub(r'_+', '_', val)            # colapsa múltiples _
    return val


def normalize_name(val: str) -> str:
    """Nombre limpio para mostrar (sin tocar demasiado)."""
    return (val or "").strip()


class CraiStudentsIngestService(models.AbstractModel):
    _name = "crai.students.ingest.service"
    _description = "Ingesta de estudiantes desde API GET (solo nuevos)"

    # --- mapeos auxiliares ---
    def _norm_discapacidad(self, discap, tipo):
        has = False if (str(discap or "")).strip().lower() in ("no", "0", "false", "n") else bool(discap)
        mapa = {
            "visual": "visual",
            "auditiva": "auditiva",
            "motora": "motora",
            "intelectual": "intelectual",
            "psicosocial": "psicosocial",
            "otra": "otra",
        }
        tipo_key = None
        if tipo:
            key = (str(tipo).strip().lower())
            for k in mapa:
                if k in key:
                    tipo_key = mapa[k]
                    break
        return has, tipo_key

    # -------------
    # Config helper
    # -------------
    def _get_current_faculty_map(self):
        """
        Lee JSON de Ajustes (ir.config_parameter):
        key: crai_students.career_current_faculty_map
        Ejemplo:
        {"DERECHO":"FACULTAD DE DERECHO","PSICOLOGIA CLINICA":"FACULTAD DE SALUD Y CULTURA FISICA"}
        """
        IrConfig = self.env["ir.config_parameter"].sudo()
        raw = (IrConfig.get_param("crai_students.career_current_faculty_map") or "").strip()
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            # normalizar claves a code normalizado
            return {normalize_code(k): normalize_name(v) for k, v in data.items() if v}
        except Exception:
            # si está mal formateado, lo ignoramos
            return {}

    # -------------------------
    # Catálogos (Campus/Fac/Car)
    # -------------------------
    def _ensure_campus(self, sed_descripcion):
        Campus = self.env["crai.campus"].sudo()
        name = normalize_name(sed_descripcion) or "SIN SEDE"
        code = normalize_code(name) or "CAMPUS"
        campus = Campus.search([("name", "=", name)], limit=1)
        if not campus:
            campus = Campus.create({"name": name, "code": code})
        return campus

    def _ensure_faculty(self, fac_descripcion):
        Faculty = self.env["crai.faculty"].sudo()
        if not fac_descripcion:
            return None
        name = normalize_name(fac_descripcion)
        code = normalize_code(name) or "FAC"
        faculty = Faculty.search([("name", "=", name)], limit=1)
        if not faculty:
            faculty = Faculty.create({"name": name, "code": code})
        return faculty

    def _ensure_career(self, car_descripcion, faculty):
        Career = self.env["crai.career"].sudo()
        if not car_descripcion:
            return None
        name = normalize_name(car_descripcion)
        code = normalize_code(name) or "CAR"

        # Busca por (faculty_id, code) -> evita colisiones globales
        domain = [("code", "=", code)]
        if faculty:
            domain.append(("faculty_id", "=", faculty.id))
        career = Career.search(domain, limit=1)

        if not career:
            vals = {"name": name, "code": code}
            if faculty:
                vals["faculty_id"] = faculty.id
            career = Career.create(vals)
        else:
            # Mantén el name “bonito” si cambió
            if career.name != name:
                career.write({"name": name})
        return career

    # =========================
    # INGESTA PRINCIPAL
    # =========================
    @api.model
    def run_ingest(self, dry_run=False):
        IrConfig = self.env["ir.config_parameter"].sudo()
        url = (IrConfig.get_param("crai_students.api_url") or "").strip()
        token = (IrConfig.get_param("crai_students.api_token") or "").strip()
        if not url:
            raise UserError(_("Configura la URL de la API en Ajustes (CRAI · Ingesta de Estudiantes)."))

        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.get(url, headers=headers, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            raise UserError(_("Error llamando API de estudiantes: %s") % e)

        items = (payload or {}).get("data") or []
        Student = self.env["crai.student"].sudo()

        total = len(items)
        create = 0
        skip = 0
        errors = 0

        # Prefetch existente por cédula (FIX: no construyas set de dicts)
        existing = Student.search_read(
            domain=[("number_id", "!=", False)],
            fields=["number_id"]
        )
        existing_docs = {r["number_id"] for r in existing if r.get("number_id")}

        # Mapa forzado de "carrera -> facultad actual"
        career_to_current_faculty = self._get_current_faculty_map()

        for row in items:
            # Aislar errores por fila (no tires toda la corrida)
            with self.env.cr.savepoint():
                try:
                    cedula = (row.get("cedula") or "").strip()
                    nombre = (row.get("nombres_apellidos") or "").strip()
                    correo = (row.get("correo_institucional") or "").strip()
                    sede = (row.get("sed_descripcion") or "").strip()

                    fac_desc = (row.get("fac_descripcion") or "").strip()
                    car_desc = (row.get("car_descripcion") or "").strip()

                    discap = row.get("discapacidad")
                    tipo = row.get("tipo_discapacidad")

                    if not cedula:
                        skip += 1
                        continue

                    # si ya existe esa cédula -> omitimos (no tocamos nada)
                    if cedula in existing_docs:
                        skip += 1
                        continue

                    # asegurar campus
                    campus = self._ensure_campus(sede)

                    # determinar facultad efectiva:
                    # 1) Si hay mapeo de facultad actual por carrera, úsalo (simplifica tu caso Derecho)
                    # 2) Si no, usa la que viene en la API
                    faculty_effective = None
                    car_code_norm = normalize_code(car_desc)
                    mapped_fac_name = career_to_current_faculty.get(car_code_norm)
                    if mapped_fac_name:
                        # Forzamos la facultad “actual”
                        faculty_effective = self._ensure_faculty(mapped_fac_name)
                    else:
                        # Respetamos lo que viene
                        faculty_effective = self._ensure_faculty(fac_desc)

                    # asegurar carrera con (faculty_effective, code)
                    career = self._ensure_career(car_desc, faculty_effective)

                    has_dis, dis_type = self._norm_discapacidad(discap, tipo)

                    vals = {
                        "name": nombre or correo or cedula,
                        "number_id": cedula,     # canónico
                        # barcode se computa = number_id en tu modelo
                        "email": correo or False,
                        "campus_id": campus.id,
                        "faculty_id": faculty_effective and faculty_effective.id,
                        "career_id": career and career.id,
                        "has_disability": has_dis,
                        "disability_type": dis_type,
                        "external_source": "umet_api",
                        "external_ref": cedula,  # llave externa estable en tu contexto
                        "active": True,
                    }

                    if not dry_run:
                        Student.create(vals)
                        existing_docs.add(cedula)  # evitar repetidos en la misma corrida

                    create += 1

                except Exception:
                    # registramos y seguimos
                    errors += 1
                    # El savepoint revierte SOLO esta fila
                    # (puedes agregar logs aquí si tienes _logger)
                    # _logger.exception("Fila con error: %s", row)
                    continue

        return {"total": total, "create": create, "skip": skip, "errors": errors}

    # cron entrypoint
    @api.model
    def cron_ingest_students_every_3_months(self):
        self.run_ingest(dry_run=False)
        return True
