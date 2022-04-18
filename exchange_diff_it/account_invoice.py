# -*- encoding: utf-8 -*-
from osv import osv, fields

class account_invoice(osv.osv):
	_name='account.invoice'
	_inherit='account.invoice'
	
	def action_move_create(self, cr, uid, ids, context=None):
		super(account_invoice, self).action_move_create(cr, uid, ids, context)
		for invoice in self.browse(cr, uid, ids, context):
			print 'invoice', invoice
			print 'line', invoice.move_id.line_id
			for move_line in invoice.move_id.line_id:
				if move_line.name == '/':
					self.pool.get('account.move.line').write(cr, uid, [move_line.id], {'name': invoice.move_id.name}, context)
		return True
		
account_invoice()