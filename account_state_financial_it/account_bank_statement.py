# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_bank_statement(models.Model):
	_inherit = 'account.bank.statement'
	fefectivo_id = fields.Many2one('account.config.efective',string ="F. Efectivo")
	
	def _prepare_bank_move_line(self, cr, uid, st_line, move_id, amount, company_currency_id, context=None):
		t = super(account_bank_statement,self)._prepare_bank_move_line(cr, uid, st_line, move_id, amount, company_currency_id, context)
		t['fefectivo_id'] = st_line.statement_id.fefectivo_id.id
		return t