# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class main_parameter(models.Model):
	_inherit = 'main.parameter'
	
	currency_id = fields.Many2one('res.currency', 'Divisa Extranjera')
	