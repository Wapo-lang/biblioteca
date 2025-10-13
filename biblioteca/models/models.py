from odoo import models, fields, api

class Libro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'Gestión de Libros'
    _rec_name = 'firstname'
    
    firstname = fields.Char(string='Nombre Libro', required=True)
    author = fields.Many2one('biblioteca.autor', string='Autor Libro', required=True)
    value = fields.Integer(string='Número de Ejemplares')
    value2 = fields.Float(compute="_value_pc", store=True, string='Valor Computado')
    description = fields.Text(string='Descripción')

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100 if record.value else 0.0


class Autor(models.Model):
    _name = 'biblioteca.autor'
    _description = 'Gestión de Autores'

    firstname = fields.Char(string='Nombre', required=True)
    lastname = fields.Char(string='Apellido', required=True)
    display_name = fields.Char(string='Nombre Completo', compute='_compute_display', store=True)

    @api.depends('firstname', 'lastname')
    def _compute_display(self):
        for record in self:
            record.display_name = f"{record.firstname} {record.lastname}"
