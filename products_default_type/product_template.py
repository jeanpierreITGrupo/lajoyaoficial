# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api

class product_template(models.Model):
	_inherit = 'product.template'

	type = fields.Selection(default='product')