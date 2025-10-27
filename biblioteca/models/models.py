from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import requests
import logging


_logger = logging.getLogger(__name__)

class Libro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'Gestión de Libros'
    _rec_name = 'firstname'
    
    firstname = fields.Char(string='Nombre Libro', required=True)
    author = fields.Many2one('biblioteca.autor', string='Autor Libro')
    isbn = fields.Char(string='ISBN')
    value = fields.Integer(string='Número de Ejemplares')
    value2 = fields.Float(compute="_value_pc", store=True, string='Valor Computado')
    description = fields.Text(string='Descripción')
    openlibrary_description = fields.Text(string='Descripción (Open Library)')

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100 if record.value else 0.0

    @api.onchange('isbn')
    def _onchange_isbn_fetch_data(self):
        if self.isbn:
            
            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{self.isbn}&format=json&jscmd=data"
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                book_key = f"ISBN:{self.isbn}"
                
                if book_key in data:
                    book_info = data[book_key]
                    

                    title = book_info.get('title')
                    if title:
                        self.firstname = title

                    author_name = None
                    authors = book_info.get('authors')
                    if authors and isinstance(authors, list):
                        author_name = authors[0].get('name')
                    if author_name:
                        AuthorModel = self.env['biblioteca.autor']
                        author_record = AuthorModel.search([('firstname', '=', author_name)], limit=1)
                        if not author_record:
                            author_record = AuthorModel.create({'firstname': author_name, 'lastname': ''})
                        self.author = author_record.id


                    description = None
                    if 'description' in book_info:
                        if isinstance(book_info['description'], dict):
                            description = book_info['description'].get('value')
                        else:
                            description = book_info['description']
                    elif 'notes' in book_info:
                        description = book_info['notes']
                    self.openlibrary_description = description or "No se encontró descripción detallada en Open Library."
                else:
                    self.openlibrary_description = f"ISBN {self.isbn} no encontrado en Open Library."
                    
            except requests.exceptions.RequestException as e:
                self.openlibrary_description = "Error al conectar con Open Library. Verifique la conexión."
                _logger.error(f"Error en la petición a Open Library: {e}")
            except Exception as e:
                self.openlibrary_description = "Error al procesar los datos de Open Library o al gestionar el autor."
                _logger.error(f"Error general: {e}")
        else:
            self.openlibrary_description = False
            self.firstname = False
            self.author = False

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
    
class BibliotecaUsuario(models.Model):
    _name = 'biblioteca.usuario'
    _description = 'Gestión de Usuarios de la Biblioteca'
    _rec_name = 'nombre_completo'

    nombre = fields.Char(string='Nombre', required=True)
    apellido = fields.Char(string='Apellido', required=True)
    cedula = fields.Char(string='Cédula', required=True)
    telefono = fields.Char(string='Teléfono')
    correo = fields.Char(string='Correo electrónico')
    direccion = fields.Char(string='Dirección')
    nombre_completo = fields.Char(string='Nombre completo', compute='_compute_nombre_completo', store=True)

    @api.depends('nombre', 'apellido')
    def _compute_nombre_completo(self):
        for record in self:
            record.nombre_completo = f"{record.nombre} {record.apellido}"

    @api.constrains('correo')
    def _check_correo(self):
        for rec in self:
            if rec.correo and '@' not in rec.correo:
                raise ValidationError('Ingrese un correo electrónico válido.')

    @api.constrains('cedula')
    def _check_cedula(self):
        for rec in self:
            # Puedes reutilizar el validador de cédula de tu clase CedulaEcuador
            valido, msg = CedulaEcuador._validar_cedula_ecuador(rec.cedula or '')
            if not valido:
                raise ValidationError(f'Cédula: {msg}')

  
       
class BibliotecaPrestamos(models.Model):
    _name= 'biblioteca.prestamo'
    _description='biblioteca.prestamo'
    _rec_name='fecha_max'
    name=fields.Char(required=True)
    usuario = fields.Many2one('biblioteca.usuario', string='Usuario', required=True)
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
            
def _cron_multas(self):
    prestamos = self.env['biblioteca.prestamo'].search([('estado', '=', 'p'), 
                                                       ('fecha_max', '<', datetime.now())])
    
    for prestamo in prestamos:
        prestamo.write({'estado': 'm', 'multa_bol': True, 'multa': 1.0})
    prestamos = self.env['biblioteca.prestamo'].search([('estado','=', 'm')])
    for prestamo in prestamos:
        days = (datetime.now() - prestamo.fecha_max).days
        prestamo.write({'multa': days,})
        

class CedulaEcuador(models.Model):
    _name = 'biblioteca.cedula'
    _description = 'Verificador de Cédula Ecuatoriana'
    _rec_name = 'cedula'

    cedula = fields.Char(string='Cédula', required=True)
    es_valida = fields.Boolean(string='Cédula válida', compute='_compute_validez', store=True)
    mensaje = fields.Char(string='Mensaje de validación', compute='_compute_validez', store=True)

    @api.depends('cedula')
    def _compute_validez(self):
        for rec in self:
            valido, msg = self._validar_cedula_ecuador(rec.cedula or '')
            rec.es_valida = valido
            rec.mensaje = msg

    @staticmethod
    def _validar_cedula_ecuador(cedula: str):
        cedula = (cedula or '').strip()
        if not cedula.isdigit():
            return False, "La cédula debe contener solo dígitos."
        if len(cedula) != 10:
            return False, "La cédula debe tener 10 dígitos."
        prov = int(cedula[:2])
        if prov < 1 or prov > 24:
            return False, "Código de provincia inválido."
        tercer = int(cedula[2])
        if tercer >= 6:
            return False, "Tercer dígito inválido para cédula natural."
        digitos = list(map(int, cedula))
        coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        total = 0
        for i in range(9):
            prod = digitos[i] * coef[i]
            if prod >= 10:
                prod -= 9
            total += prod
        dig_verificador = (10 - (total % 10)) % 10
        if dig_verificador == digitos[9]:
            return True, "Cédula válida."
        return False, "Dígito verificador inválido."

    @api.constrains('cedula')
    def _check_cedula(self):
        for rec in self:
            valido, msg = self._validar_cedula_ecuador(rec.cedula or '')
            if not valido:
                raise ValidationError(msg)

