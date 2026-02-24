# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CraiDonationBook(models.Model):
    _name = "crai.donation.book"
    _description = "Libro de Donación"
    _order = "sequence, id"
    
    # ===============================
    # CAMPOS PRINCIPALES
    # ===============================
    
    donation_id = fields.Many2one(
        "crai.donation",
        string="Donación",
        required=True,
        ondelete="cascade",
        index=True
    )
    
    sequence = fields.Integer(
        string="Secuencia",
        default=10
    )
    
    title = fields.Char(
        string="Título del Libro",
        required=True
    )
    
    author = fields.Char(
        string="Autor",
        required=True
    )
    
    isbn = fields.Char(
        string="ISBN",
        help="Número internacional estándar del libro"
    )
    
    publisher = fields.Char(
        string="Editorial"
    )
    
    publication_year = fields.Integer(
        string="Año de Publicación"
    )
    
    edition = fields.Char(
        string="Edición"
    )
    
    quantity = fields.Integer(
        string="Cantidad",
        required=True,
        default=1
    )
    
    cost = fields.Float(
        string="Costo Unitario",
        digits=(16, 2),
        help="Costo por unidad (requerido para donaciones de estudiantes)"
    )
    
    total_cost = fields.Float(
        string="Costo Total",
        compute="_compute_total_cost",
        store=True,
        digits=(16, 2)
    )
    
    condition = fields.Selection(
        [
            ("new", "Nuevo"),
            ("very_good", "Muy Bueno"),
            ("good", "Bueno"),
            ("acceptable", "Aceptable")
        ],
        string="Estado del Libro",
        required=True,
        default="new"
    )
    
    notes = fields.Text(
        string="Observaciones"
    )
    
    # ===============================
    # CAMPOS RELACIONADOS
    # ===============================
    
    donation_type = fields.Selection(
        related="donation_id.donation_type",
        store=True,
        readonly=True
    )
    
    campus_id = fields.Many2one(
        "crai.campus",
        string="Campus (Sede)",
        related="donation_id.campus_id",
        store=True,
        readonly=True
    )
    
    approval_date = fields.Datetime(
        string="Fecha de Aprobación",
        related="donation_id.approval_date",
        store=True,
        readonly=True
    )
    
    state = fields.Selection(
        related="donation_id.state",
        string="Estado de Donación",
        store=True,
        readonly=True
    )

    # ===============================
    # COMPUTED FIELDS
    # ===============================
    
    @api.depends("quantity", "cost")
    def _compute_total_cost(self):
        """Calcula el costo total (cantidad × costo unitario)"""
        for record in self:
            record.total_cost = record.quantity * record.cost
    
    # ===============================
    # CONSTRAINTS Y VALIDACIONES
    # ===============================
    
    @api.constrains("quantity")
    def _check_quantity(self):
        """Valida que la cantidad sea mayor a cero"""
        for record in self:
            if record.quantity < 1:
                raise ValidationError(
                    _("La cantidad debe ser al menos 1.")
                )
    
    @api.constrains("cost", "donation_type")
    def _check_cost_for_student_donations(self):
        """Valida que las donaciones de estudiantes tengan costo"""
        for record in self:
            if (
                record.donation_type in ("individual", "group")
                and record.donation_id.state in ("submitted", "approved", "certificate_issued")
                and record.cost <= 0
            ):
                raise ValidationError(
                    _("Los libros de donaciones de estudiantes deben tener un costo mayor a cero.")
                )
    
    @api.constrains("publication_year")
    def _check_publication_year(self):
        """Valida que el año de publicación sea razonable"""
        for record in self:
            if record.publication_year:
                current_year = fields.Date.today().year
                if record.publication_year < 1500 or record.publication_year > current_year + 1:
                    raise ValidationError(
                        _("El año de publicación debe estar entre 1500 y %s.") % (current_year + 1)
                    )
    
    # ===============================
    # ONCHANGE METHODS
    # ===============================
    
    @api.onchange("quantity", "cost")
    def _onchange_compute_total(self):
        """Actualiza el total cuando cambia cantidad o costo"""
        # El compute ya lo maneja, pero esto da feedback inmediato en UI
        pass
    
    # ===============================
    # MÉTODOS AUXILIARES
    # ===============================
    
    def name_get(self):
        """Formato de visualización del libro"""
        result = []
        for record in self:
            name = f"{record.title} - {record.author}"
            if record.isbn:
                name += f" (ISBN: {record.isbn})"
            result.append((record.id, name))
        return result
