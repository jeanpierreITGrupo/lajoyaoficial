# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
class stock_move(osv.osv):
	_name='stock.move'
	_inherit='stock.move'
	_columns={
		'invoice_id':fields.many2one('account.invoice','Factura'),
		'analitic_id':fields.many2one('account.analytic.account','Cta. Analitica'),
	}
	def set_invoice(self,cr,uid,ids,context=None):

		try:
			dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock.move.invoice', 'view_sm_add_invoice_form')
		except ValueError, e:
			view_id = False
		return {
				'type': 'ir.actions.act_window',
				'res_model': 'stock.move.invoice',
				'view_mode': 'form',
				'view_type': 'form',
				'view_id': view_id,
				'context': context,
				'target': 'new',
			}
	def copy(self, cr, uid, id, default=None, context=None):
		if not default:
			default = {}
		default.update({'invoice_id':False})
		return super(stock_move, self).copy(cr, uid, id, default, context=context)	
stock_move()


class stock_move_invoice(osv.osv_memory):
	_name ='stock.move.invoice'
	_columns={
		'invoice_id':fields.many2one('account.invoice','Factura relacionada')
		}
	
	def set_invoice(self,cr,uid,ids,context=None):
		return False
stock_move_invoice()