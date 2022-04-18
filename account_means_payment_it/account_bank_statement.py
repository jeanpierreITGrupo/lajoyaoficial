# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_bank_statement(models.Model):
	_inherit = 'account.bank.statement'
	means_payment_id = fields.Many2one('it.means.payment',string ="Medio de Pago",index = True,ondelete='restrict')
	
	def _prepare_bank_move_line(self, cr, uid, st_line, move_id, amount, company_currency_id, context=None):
		t = super(account_bank_statement,self)._prepare_bank_move_line(cr, uid, st_line, move_id, amount, company_currency_id, context)
		t['means_payment_id'] = st_line.statement_id.means_payment_id.id
		return t