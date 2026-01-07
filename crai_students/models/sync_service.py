# -*- coding: utf-8 -*-
import json
import requests
import unicodedata
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

# ---------------------------
# Normalización determinista
# ---------------------------
def normalize_code(val: str) -> str:
    """Mayúsculas, sin tildes, espacios -> _, solo A-Z0-9_ (sin truncar)."""
    if not val:
        return ""
    val = ''.join(c for c in unicodedata.normalize('NFKD', val) if not unicodedata.combining(c))
    val = val.upper().strip()
    val = re.sub(r'\s+', '_', val)
    val = re.sub(r'[^A-Z0-9_]', '', val)
    val = re.sub(r'_+', '_', val)
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
        """
        IrConfig = self.env["ir.config_parameter"].sudo()
        raw = (IrConfig.get_param("crai_students.career_current_faculty_map") or "").strip()
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            return {normalize_code(k): normalize_name(v) for k, v in data.items() if v}
        except Exception:
            return {}

    # -------------------------
    # Catálogos (Campus/Fac/Car)
    # -------------------------
    def _ensure_site(self, sed_descripcion):
        Site = self.env["crai.site"].sudo()
        name = (sed_descripcion or "").strip() or "SIN SEDE"
        code = normalize_code(name) or "SEDE"
        site = Site.search([("name", "=", name)], limit=1)
        if not site:
            site = Site.create({"name": name, "code": code})
        return site

    def _ensure_campus(self, cam_descripcion, site):
        Campus = self.env["crai.campus"].sudo()
        if not cam_descripcion:
            return None
        name = (cam_descripcion or "").strip()
        code = normalize_code(name) or "CAMPUS"
        domain = [("code", "=", code)]
        if site:
            domain.append(("site_id", "=", site.id))
        campus = Campus.search(domain, limit=1)
        if not campus:
            campus = Campus.create({"name": name, "code": code, "site_id": site.id})
        else:
            if campus.name != name:
                campus.write({"name": name})
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
            if career.name != name:
                career.write({"name": name})
        return career

    # =========================
    # INGESTA PRINCIPAL
    # =========================
    @api.model
    def run_ingest(self, dry_run=False, update_existing=False):
        """Punto de entrada principal para la ingesta."""
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
        
        if dry_run:
            # Usar cursor independiente para dry_run
            return self._run_with_new_cursor(items, update_existing)
        else:
            # Modo normal con el cursor actual
            return self._process_items(items, update_existing, dry_run=False)

    def _run_with_new_cursor(self, items, update_existing):
        """Ejecuta el proceso en un cursor nuevo y lo descarta (para dry_run)."""
        new_cr = None
        
        try:
            # Crear nuevo cursor
            new_cr = self.pool.cursor()
            # Crear nuevo environment
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            # Obtener el servicio en el nuevo environment
            service = new_env['crai.students.ingest.service']
            
            # Procesar items CON MANEJO DE ERRORES POR ITEM
            result = service._process_items_safe(items, update_existing, new_cr)
            
            # IMPORTANTE: Siempre hacer rollback en dry_run
            new_cr.rollback()
            
            return result
            
        except Exception as e:
            _logger.exception("Error crítico durante dry-run")
            if new_cr:
                try:
                    new_cr.rollback()
                except:
                    pass
            # Retornar resultado con error
            return {
                "total": len(items),
                "create": 0,
                "update": 0,
                "skip": 0,
                "errors": len(items)
            }
        finally:
            # Cerrar el cursor
            if new_cr:
                try:
                    new_cr.close()
                except:
                    pass

    def _process_items_safe(self, items, update_existing, cursor):
        """Procesa items con savepoints individuales para aislar errores."""
        Student = self.env["crai.student"].sudo()

        total = len(items)
        create = 0
        update = 0
        skip = 0
        errors = 0

        # Prefetch de estudiantes existentes
        existing = Student.search_read([("number_id", "!=", False)], ["id", "number_id"])
        existing_map = {r["number_id"]: r["id"] for r in existing if r.get("number_id")}

        career_to_current_faculty = self._get_current_faculty_map()

        # IMPORTANTE: Procesar cada item en su propio savepoint
        for row in items:
            cedula = (row.get("cedula") or "").strip()
            
            # Usar savepoint para aislar errores de cada fila
            try:
                with cursor.savepoint():
                    nombre = (row.get("nombres_apellidos") or "").strip()
                    correo = (row.get("correo_institucional") or "").strip()
                    sede = (row.get("sed_descripcion") or "").strip()
                    campus_desc = (row.get("cam_descripcion") or "").strip()
                    fac_desc = (row.get("fac_descripcion") or "").strip()
                    car_desc = (row.get("car_descripcion") or "").strip()
                    discap = row.get("discapacidad")
                    tipo = row.get("tipo_discapacidad")

                    if not cedula:
                        skip += 1
                        continue

                    # Crear/obtener catálogos
                    site = self._ensure_site(sede)
                    campus_rec = self._ensure_campus(campus_desc, site)

                    car_code_norm = normalize_code(car_desc)
                    mapped_fac_name = career_to_current_faculty.get(car_code_norm)
                    if mapped_fac_name:
                        faculty_effective = self._ensure_faculty(mapped_fac_name)
                    else:
                        faculty_effective = self._ensure_faculty(fac_desc)
                    career_rec = self._ensure_career(car_desc, faculty_effective)

                    has_dis, dis_type = self._norm_discapacidad(discap, tipo)

                    # EXISTE -> actualizar
                    if cedula in existing_map:
                        if update_existing:
                            stu = Student.browse(existing_map[cedula])
                            vals_update = {}

                            new_name = nombre or correo or cedula
                            if stu.name != new_name:
                                vals_update["name"] = new_name
                            if (stu.email or False) != (correo or False):
                                vals_update["email"] = correo or False
                            if "site_id" in Student._fields and (stu.site_id.id or False) != (site.id if site else False):
                                vals_update["site_id"] = site and site.id
                            if (stu.campus_id.id or False) != (campus_rec.id if campus_rec else False):
                                vals_update["campus_id"] = campus_rec and campus_rec.id
                            if (stu.faculty_id.id or False) != (faculty_effective.id if faculty_effective else False):
                                vals_update["faculty_id"] = faculty_effective and faculty_effective.id
                            if (stu.career_id.id or False) != (career_rec.id if career_rec else False):
                                vals_update["career_id"] = career_rec and career_rec.id
                            if bool(getattr(stu, "has_disability", False)) != bool(has_dis):
                                vals_update["has_disability"] = bool(has_dis)
                            if (getattr(stu, "disability_type", False) or False) != (dis_type or False):
                                vals_update["disability_type"] = dis_type or False

                            if vals_update:
                                stu.write(vals_update)
                                update += 1
                            else:
                                skip += 1
                        else:
                            skip += 1
                        continue

                    # NUEVO -> crear
                    vals_create = {
                        "name": nombre or correo or cedula,
                        "number_id": cedula,
                        "email": correo or False,
                        "campus_id": campus_rec and campus_rec.id,
                        "faculty_id": faculty_effective and faculty_effective.id,
                        "career_id": career_rec and career_rec.id,
                        "has_disability": bool(has_dis),
                        "disability_type": dis_type or False,
                        "external_source": "umet_api",
                        "external_ref": cedula,
                        "active": True,
                    }
                    if "site_id" in Student._fields:
                        vals_create["site_id"] = site and site.id

                    Student.create(vals_create)
                    create += 1

            except Exception as e:
                errors += 1
                _logger.error("Error procesando fila (cedula=%s): %s", cedula, str(e))
                # El savepoint hace rollback automático en caso de error
                continue

        return {
            "total": total,
            "create": create,
            "update": update,
            "skip": skip,
            "errors": errors
        }

    def _process_items(self, items, update_existing, dry_run):
        """Procesa los items de la API (modo normal, SIN savepoints)."""
        Student = self.env["crai.student"].sudo()

        total = len(items)
        create = 0
        update = 0
        skip = 0
        errors = 0

        # Prefetch de estudiantes existentes
        existing = Student.search_read([("number_id", "!=", False)], ["id", "number_id"])
        existing_map = {r["number_id"]: r["id"] for r in existing if r.get("number_id")}

        career_to_current_faculty = self._get_current_faculty_map()

        for row in items:
            try:
                cedula = (row.get("cedula") or "").strip()
                nombre = (row.get("nombres_apellidos") or "").strip()
                correo = (row.get("correo_institucional") or "").strip()
                sede = (row.get("sed_descripcion") or "").strip()
                campus_desc = (row.get("cam_descripcion") or "").strip()
                fac_desc = (row.get("fac_descripcion") or "").strip()
                car_desc = (row.get("car_descripcion") or "").strip()
                discap = row.get("discapacidad")
                tipo = row.get("tipo_discapacidad")

                if not cedula:
                    skip += 1
                    continue

                # Crear/obtener catálogos
                site = self._ensure_site(sede)
                campus_rec = self._ensure_campus(campus_desc, site)

                car_code_norm = normalize_code(car_desc)
                mapped_fac_name = career_to_current_faculty.get(car_code_norm)
                if mapped_fac_name:
                    faculty_effective = self._ensure_faculty(mapped_fac_name)
                else:
                    faculty_effective = self._ensure_faculty(fac_desc)
                career_rec = self._ensure_career(car_desc, faculty_effective)

                has_dis, dis_type = self._norm_discapacidad(discap, tipo)

                # EXISTE -> actualizar
                if cedula in existing_map:
                    if update_existing:
                        stu = Student.browse(existing_map[cedula])
                        vals_update = {}

                        new_name = nombre or correo or cedula
                        if stu.name != new_name:
                            vals_update["name"] = new_name
                        if (stu.email or False) != (correo or False):
                            vals_update["email"] = correo or False
                        if "site_id" in Student._fields and (stu.site_id.id or False) != (site.id if site else False):
                            vals_update["site_id"] = site and site.id
                        if (stu.campus_id.id or False) != (campus_rec.id if campus_rec else False):
                            vals_update["campus_id"] = campus_rec and campus_rec.id
                        if (stu.faculty_id.id or False) != (faculty_effective.id if faculty_effective else False):
                            vals_update["faculty_id"] = faculty_effective and faculty_effective.id
                        if (stu.career_id.id or False) != (career_rec.id if career_rec else False):
                            vals_update["career_id"] = career_rec and career_rec.id
                        if bool(getattr(stu, "has_disability", False)) != bool(has_dis):
                            vals_update["has_disability"] = bool(has_dis)
                        if (getattr(stu, "disability_type", False) or False) != (dis_type or False):
                            vals_update["disability_type"] = dis_type or False

                        if vals_update:
                            stu.write(vals_update)
                            update += 1
                        else:
                            skip += 1
                    else:
                        skip += 1
                    continue

                # NUEVO -> crear
                vals_create = {
                    "name": nombre or correo or cedula,
                    "number_id": cedula,
                    "email": correo or False,
                    "campus_id": campus_rec and campus_rec.id,
                    "faculty_id": faculty_effective and faculty_effective.id,
                    "career_id": career_rec and career_rec.id,
                    "has_disability": bool(has_dis),
                    "disability_type": dis_type or False,
                    "external_source": "umet_api",
                    "external_ref": cedula,
                    "active": True,
                }
                if "site_id" in Student._fields:
                    vals_create["site_id"] = site and site.id

                Student.create(vals_create)
                create += 1

            except Exception as e:
                errors += 1
                _logger.exception("Error procesando fila (cedula=%s)", cedula)
                continue

        return {
            "total": total,
            "create": create,
            "update": update,
            "skip": skip,
            "errors": errors
        }

    # cron entrypoint
    @api.model
    def cron_ingest_students_every_3_months(self):
        """Tarea programada para importar estudiantes."""
        self.run_ingest(dry_run=False, update_existing=True)
        return True