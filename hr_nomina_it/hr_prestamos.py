# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class hr_prestamos(models.Model):
	_name = 'hr.prestamos'

	fecha = fields.Date('Fecha Prestamo')
	monto = fields.Float('Monto',digits=(12,2))
	employee = fields.Many2one('hr.employee','Trabajador')
