# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class purchase_order_line(osv.osv):
	_name='purchase.order.line'
	_inherit='purchase.order.line'
	
	def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order=False, fiscal_position_id=False, date_planned=False, name=False, price_unit=False, state='draft', context=None):
		res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order, fiscal_position_id, date_planned, name, price_unit, state, context)
		product = self.pool.get('product.product').browse(cr, uid, product_id, context)
		#raise osv.except_osv('Alerta',product.analytic_account_id.id)
		res['value'].update({'account_analytic_id': product.analytic_account_id.id})
		return res
	
purchase_order_line()		