# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

#Orden de Compra
#class purchase_order(models.Model):
#	_inherit = 'purchase.order'
#
#	expedient_id = fields.Many2one('purchase.costing', "Expediente")

#	def action_picking_create(self, cr, uid, ids, context=None):
#		t = super(purchase_order,self).action_picking_create(cr, uid, ids, context)
#		picking_obj = self.pool.get('stock.picking').browse(cr,uid,t)
#		purchase_obj = self.pool.get('purchase.order').browse(cr,uid,ids)
#		for i in picking_obj.move_lines:
#			i.expedient_id = purchase_obj.expedient_id.id
#		return picking_obj.id

#	def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
#		res = super(purchase_order,self)._prepare_invoice(cr, uid, order, line_ids, context)
#		res['expedient_id'] = order.expedient_id.id
#		return res


#Movimiento de Almacén
#class stock_move(models.Model):
#	_inherit = 'stock.move'

#	expedient_id = fields.Many2one('purchase.costing', "Expediente")