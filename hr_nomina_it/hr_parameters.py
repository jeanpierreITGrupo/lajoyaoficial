# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class hr_parameters(models.Model):
	_name = 'hr.parameters'
	_rec_name = 'name'
	
	name        = fields.Char('Nombre')
	monto       = fields.Float('Monto')
	num_tipo    = fields.Integer('Tipo')
	concepto_id = fields.Many2one('hr.lista.conceptos', 'Concepto')