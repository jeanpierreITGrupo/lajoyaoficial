# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import openerp.addons.decimal_precision as dp

class stock_warehouse_orderpoint(models.Model):
	_inherit = 'stock.warehouse.orderpoint'

	max_min = fields.Integer(u'Días Max-Min')
	estimated_rotation = fields.Integer(u'Rotación Estimada')