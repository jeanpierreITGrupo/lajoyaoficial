# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
import datetime 
from datetime import timedelta

class sale_order(models.Model):
	_inherit = 'sale.order'

	ingoing_date = fields.Date("Fecha de Recepción")
	limit_date = fields.Date("Fecha Entrega Cliente")

	def action_button_confirm(self, cr, uid, ids, context=None):
		t = super(sale_order,self).action_button_confirm(cr, uid, ids)
		sale = self.pool.get('sale.order').browse(cr,uid,ids)
		if sale.limit_date:
			for picking in sale.picking_ids:
				picking.write({
					'min_date':datetime.datetime.strptime(str(sale.limit_date), '%Y-%m-%d')+timedelta(days=1),
					'date':sale.date_order,
					})
		return t


class stock_picking(models.Model):
	_inherit = 'stock.picking'

	outgoing_date = fields.Date("Fecha de Despacho", readonly=[('state','=','done')])