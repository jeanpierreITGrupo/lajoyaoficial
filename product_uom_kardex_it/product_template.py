# -*- coding: utf-8 -*-

from openerp import models, fields, api

class product_template(models.Model):
	_inherit = 'product.template'
	
	unidad_kardex = fields.Many2one('product.uom',string="Unidad de Producto Kardex")