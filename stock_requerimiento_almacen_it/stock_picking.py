# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	is_req = fields.Boolean('Es Albarán de Requerimiento', default=False)

	@api.one
	def compute_check_req(self):
		self.check_req =  self.env['res.users'].has_group('stock_requerimiento_almacen_it.group_stock_picking_req') 
	check_req = fields.Boolean('check requerimiento', compute="compute_check_req")

	@api.one
	def compute_check_mark_as_todo(self):
		if self.state not in ['draft']:
			self.check_mark_as_todo = True
		else:
			if not self.env['res.users'].has_group('stock_requerimiento_almacen_it.group_confirm_button'):
				self.check_mark_as_todo = True
			else:
				self.check_mark_as_todo = False
		print self.check_mark_as_todo
	check_mark_as_todo = fields.Boolean('check mark as todo', compute="compute_check_mark_as_todo")

	@api.model
	def default_get(self,fields):
		t = super(stock_picking,self).default_get(fields)
		if 'req_action' in self.env.context:
			t['is_req'] = True
		return t