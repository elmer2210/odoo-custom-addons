from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CraiStudent(models.Model):
    _name = "crai.student"
    _description = "CRAI Student (canonical)"
    _order = "name"
    _rec_name = "display_name"

    # Identidad
    name = fields.Char("Nombres y apellidos", required=True, index=True)
    display_name = fields.Char("Nombre a mostrar", compute="_compute_display_name", store=True)
    number_id = fields.Char("Cédula", required=True, index=True)
    email = fields.Char("Correo institucional")

    # Barcode = Cédula (espejo)
    barcode = fields.Char(
        "Código de barras",
        compute="_compute_barcode",
        store=True,
        readonly=True,
        help="Espejo de la cédula, se mantiene por compatibilidad."
    )

    # Vínculos CRAI
    campus_id = fields.Many2one("crai.campus", string="Sede", required=True, index=True)
    faculty_id = fields.Many2one("crai.faculty", string="Facultad")
    career_id = fields.Many2one("crai.career", string="Carrera")

    # Accesibilidad
    has_disability = fields.Boolean("Tiene discapacidad")
    disability_type = fields.Selection([
        ("visual", "Visual"),
        ("auditiva", "Auditiva"),
        ("motora", "Motora"),
        ("intelectual", "Intelectual"),
        ("psicosocial", "Psicosocial"),
        ("otra", "Otra"),
    ], string="Tipo de discapacidad")

    # Traza de sincronización
    external_ref = fields.Char("Referencia externa", index=True)
    external_source = fields.Char("Fuente externa")

    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("number_id_unique", "unique(number_id)", "La cédula ya existe."),
        ("external_pair_unique", "unique(external_ref, external_source)", "La referencia externa ya está asignada."),
    ]

    @api.depends("name")
    def _compute_display_name(self):
        for r in self:
            r.display_name = r.name

    @api.depends("number_id")
    def _compute_barcode(self):
        for r in self:
            r.barcode = (r.number_id or "").strip()

    @api.constrains("career_id", "faculty_id")
    def _check_career_faculty(self):
        for rec in self:
            if rec.career_id and rec.faculty_id and rec.career_id.faculty_id != rec.faculty_id:
                raise ValidationError(_("La carrera seleccionada no pertenece a la facultad indicada."))

    # --------- API estable para otros módulos ----------
    @api.model
    def find_by_document(self, number_id):
        """Búsqueda por cédula."""
        doc = (number_id or "").strip()
        if not doc:
            return self.browse()
        return self.search([("number_id", "=", doc)], limit=1)

    @api.model
    def find_by_barcode(self, barcode):
        """Compatibilidad: busca por 'barcode' pero realmente usa cédula."""
        return self.find_by_document(barcode)

    @api.model
    def upsert_from_external(self, vals, source_name, ext_id):
        """Upsert canónico: si llega barcode y no number_id, asumimos que barcode=cedula."""
        vals = dict(vals or {})
        # Normalizar: si no mandan number_id pero sí barcode, lo usamos como cédula
        if not vals.get("number_id") and vals.get("barcode"):
            vals["number_id"] = vals["barcode"]

        # Por coherencia, jamás permitimos que barcode != number_id
        if vals.get("barcode") and vals.get("number_id") and vals["barcode"] != vals["number_id"]:
            vals["barcode"] = vals["number_id"]

        student = self.search([("external_ref", "=", ext_id), ("external_source", "=", source_name)], limit=1)
        vals.update({"external_ref": ext_id, "external_source": source_name})
        if student:
            student.write(vals)
            return student
        return self.create(vals)
