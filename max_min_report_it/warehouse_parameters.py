# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import openerp.addons.decimal_precision as dp

class warehouse_parameters(models.Model):
	_inherit = 'warehouse.parameters'

	s_rotation = fields.Integer(u'Día(s) de Rotación')
	s_warehouse_id = fields.Many2one('stock.warehouse', u'Almacén')
	s_user_ids = fields.Many2many('res.users','warehouse_user_rels','warehouse_id','user_id','Correos')
	
	f_rotation = fields.Integer(u'Día(s) de Rotación')
	f_warehouse_id = fields.Many2one('stock.warehouse', u'Almacén')
	f_user_ids = fields.Many2many('res.users','warehouse_user_relf','warehouse_id','user_id','Correos')