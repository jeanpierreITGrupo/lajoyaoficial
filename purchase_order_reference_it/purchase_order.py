# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class purchase_order(models.Model):
	_inherit = 'purchase.order'

	reference = fields.Char("Descripción", size=30)