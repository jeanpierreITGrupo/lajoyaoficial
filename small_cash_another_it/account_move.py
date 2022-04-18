# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class account_move(models.Model):
	_inherit = "account.move"
	
	hide = fields.Boolean('Hide', default=False)
	small_cash_id = fields.Many2one('small.cash.another', 'Nro Caja Chica')
	
	@api.onchange('journal_id')
	def onchange_journal_id(self):
		if self.journal_id:
			self.hide = self.journal_id.is_small_cash
	
	@api.model
	def create(self, vals):
		x = super(account_move, self).create(vals)
		if x.journal_id.is_small_cash:
			for line in x.line_id:
				if line.account_id.id == x.journal_id.default_debit_account_id.id:
					line.write({'small_cash_id': x.small_cash_id.id})
		return x
	
	@api.one
	def write(self, vals):
		x = super(account_move, self).write(vals)
		if self.journal_id.is_small_cash:
			for line in self.line_id:
				if line.account_id.id == self.journal_id.default_debit_account_id.id:
					line.write({'small_cash_id': self.small_cash_id.id})
		return x