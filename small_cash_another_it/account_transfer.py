# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class account_transfer(models.Model):
	_inherit = 'account.transfer'
	
	@api.onchange('origen_amount', 'origen_journal_id', 'destiny_journal_id', 'destiny_exchange', 'date')
	def _refund_amount(self):
		if self.origen_journal_id:
			#print 'ORIGIN'
			self.origin_hide = self.origen_journal_id.is_small_cash
		if self.destiny_journal_id:
			#print 'DESTINY'
			self.destiny_hide = self.destiny_journal_id.is_small_cash
		return super(account_transfer, self)._refund_amount()
	
	origin_hide = fields.Boolean('Origin Hide', default=False)
	destiny_hide = fields.Boolean('Destiny Hide', default=False)
	small_cash_origin_id = fields.Many2one('small.cash.another', 'Nro Caja Chica Origen')
	small_cash_destiny_id = fields.Many2one('small.cash.another', 'Nro Caja Chica Destino')
	
	@api.multi
	def aprove(self):
		x = super(account_transfer, self).aprove()
		"""print 'HERE XD'
		if self.origen_journal_id.is_small_cash or self.destiny_journal_id.is_small_cash:
			for move in self.done_move:
				for line in move.line_id:
					if self.origen_journal_id.is_small_cash:
						if line.account_id.id == self.origen_journal_id.default_debit_account_id.id:
							line.write({'small_cash_id': self.small_cash_origin_id.id})
					if self.destiny_journal_id.is_small_cash:
						print 'line.account_id', line.account_id.id
						print 'self.destiny_journal_id.default_debit_account_id', self.destiny_journal_id.default_debit_account_id.id
						if line.account_id.id == self.destiny_journal_id.default_debit_account_id.id:
							print 'small_cash_id', self.small_cash_destiny_id.id
							line.write({'small_cash_id': self.small_cash_destiny_id.id})
		"""

		if  self.origen_journal_id.is_small_cash:
			for line in self.move_move_1_id.line_id:
				if line.account_id.id == self.origen_journal_id.default_debit_account_id.id:
					line.write({'small_cash_id': self.small_cash_origin_id.id})
		if self.destiny_journal_id.is_small_cash:
			for line in self.move_move_2_id.line_id:
				if line.account_id.id == self.destiny_journal_id.default_debit_account_id.id:
					line.write({'small_cash_id': self.small_cash_destiny_id.id})	

		return x
		
		'''
		flag = True
		while flag:
			try:
				exec(raw_input('Comete Esta:'))
			except Exception as es:
				print 'Te Webiaste:', es
		
		'''
		#raise osv.except_osv('Alerta!', 'EX')