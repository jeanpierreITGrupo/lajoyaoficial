# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.multi
	def action_number(self):
		t = super(account_invoice,self).action_number()
		self.write({})
		for inv in self:
			if inv.supplier_invoice_number:
				print 'number', inv.supplier_invoice_number
				inv.write({'number': inv.supplier_invoice_number})
			elif inv.serie_id:
				name = self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, inv.serie_id.sequence_id.id)
				inv.write({'number': name, 'supplier_invoice_number': name})
			print 'new_number', inv.number
		return t
	
	@api.onchange('serie_id')
	def _onchange_serie_id(self):
		print 'type', self.type
		if self.type in ['out_invoice', 'out_refund']:
			self.supplier_invoice_number = ""
		else:
			super (account_invoice, self)._onchange_serie_id()