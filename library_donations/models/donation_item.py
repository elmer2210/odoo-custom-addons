from odoo import models, fields


class LibraryDonationItem(models.Model):
    _name = 'library.donation.item'
    _description = 'Ítems de Donación'

    donation_id = fields.Many2one('library.donation', string="Donación", ondelete='cascade')
    title = fields.Char(string="Título", required=True)
    author = fields.Char(string="Autor/es")
    isbn =  fields.Char(string="ISBN")
    publisher = fields.Char(string="Editorial")
    edition = fields.Char(string="Edición")
    publication_year = fields.Char(string="Año de Publicación")
    cost = fields.Float(string="Costo")
