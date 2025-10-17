from odoo import models, fields, api
from datetime import datetime, timedelta


class Libro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'Gestión de Libros'
    _rec_name = 'firstname'
    
    firstname = fields.Char(string='Nombre Libro', required=True)
    author = fields.Many2one('biblioteca.autor', string='Autor Libro', required=True)
    isbn = fields.Char(string='ISBN')
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


class BibliotecaMulta(models.Model):
    _name='biblioteca.multa'
    _description='biblioteca.multa'
    codigo_multa=fields.Char(string='Código de la multa')
    monto=fields.Float(string='Valor a pagar')
    motivo=fields.Selection(selection=[('retraso','Retraso'),
                                        ('daño','Daño'),
                                        ('perdida','Perdida')],string='Causa de la multa')
    pago=fields.Selection(selection=[('pendiente','Pendiente'),
                                     ('saldada','Saldada')],string='Pago de la multa')
    
    
class BibliotecaPrestamos(models.Model):
    _name= 'biblioteca.prestamo'
    _description='biblioteca.prestamo'
    _rec_name='fecha_max'
    name=fields.Char(required=True)
    fecha_prestamo=fields.Datetime(default=datetime.now(),string='Fecha de prestamo' )
    libro= fields.Many2one('biblioteca.libro',string='Titulo de libro')
    fecha_devolucion=fields.Datetime()
    multa_bol=fields.Boolean(Default=False)
    multa=fields.Float()
    estado=fields.Selection([('b','Borrador'),('p','Prestado'),('m','Multa'),('d','Devuelto')]
                           ,string='Estado', default='b')
    personal=fields.Many2one('res.users',string='Persona que presto el libro',
                            default=lambda self: self.env.uid)
    fecha_max=fields.Datetime(compute='_compute_fecha_devo' ,string='Fecha Maxima de devolucion')
   
    def write(self,vals):
       seq=self.env.ref('biblioteca.sequence_codigo_prestamos').next_by_code('biblioteca.prestamo')
       vals ['name']=seq
       return super(BibliotecaPrestamos,self).write(vals)
   
    def generar_prestamo(self):
        print("Generando prestamo")
        self.write({'estado':'p'}) 
        
    @api.depends('fecha_max' , 'fecha_prestamo' )
    def _compute_fecha_devo(self):
        for record in self:
            record.fecha_max=record.fecha_prestamo + timedelta(days=2)

