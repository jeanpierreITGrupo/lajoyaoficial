# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class product_grupo(models.Model):
	_name = 'product.grupo'

	name = fields.Char('Grupo')

class product_template(models.Model):
	_inherit = 'product.template'
	
	grupo_product = fields.Many2one('product.grupo','Grupo')
