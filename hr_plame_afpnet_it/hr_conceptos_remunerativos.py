# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class hr_concepto_remunerativo_line(models.Model):
	_inherit = 'hr.concepto.remunerativo.line'

	sunat_code = fields.Char("Código SUNAT", size=4)
