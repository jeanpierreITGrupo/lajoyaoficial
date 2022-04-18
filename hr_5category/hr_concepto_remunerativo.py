# -*- coding: utf-8 -*-
from openerp import models, fields, api
class hr_concepto_remunerativo_line(models.Model):
	_inherit = 'hr.concepto.remunerativo.line'

	incoming_type = fields.Selection([('ordinary','Ingreso ordinario'),('extraordinary','Ingreso extraordinario')],'Tipo de ingreso')