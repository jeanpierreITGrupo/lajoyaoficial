# -*- coding: utf-8 -*-

from openerp import models, fields, api ,  _

class account_move(models.Model):
	_inherit = 'account.move'

	@api.one
	def write(self,vals):
		if 'period_id' in vals or 'journal_id' in vals:
			vals['name'] = '/'
		return super(account_move,self).write(vals)

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	period_verifi_change_id = fields.Many2one('account.period','Periodo Modify', copy=False)
	journal_verifi_change_id = fields.Many2one('account.journal','Journal Modify', copy=False)

	@api.multi
	def action_move_create(self):

		if self.journal_verifi_change_id.id:
			print "primer if"
			if self.journal_id:
				print "segundo if"
				if self.journal_id.id != self.journal_verifi_change_id.id:
					"""
					if self.internal_number:
						print "tercer if"
						data_move= {
							'journal_id': self.journal_id.id,
							'date': self.date_invoice,
							'period_id': self.period_id.id,
							'name': self.internal_number,
						}
						new_null = self.env['account.move'].create(data_move)
						data_move_line={
							'move_id': new_null.id,
							'name': 'ANULADO',
							'account_id': self.journal_id.default_debit_account_id.id,
							'debit':0,
							'credit':0,
						}
						new_null_line= self.env['account.move.line'].create(data_move_line)
						new_null.write({ 'line_id': [(4,new_null_line.id )] })
					"""
					self.internal_number= False
					self.write( {'internal_number':False })
					self.journal_verifi_change_id = self.journal_id
					self.write( {'journal_verifi_change_id':self.journal_id.id})

		if self.period_verifi_change_id.id:
			print "primer if"
			if self.period_id:
				print "segundo if"
				if self.period_id.id != self.period_verifi_change_id.id:
					"""
					if self.internal_number:
						print "tercer if"
						data_move= {
							'journal_id': self.journal_id.id,
							'date': self.date_invoice,
							'period_id': self.period_id.id,
							'name': self.internal_number,
						}
						new_null = self.env['account.move'].create(data_move)
						data_move_line={
							'move_id': new_null.id,
							'name': 'ANULADO',
							'account_id': self.journal_id.default_debit_account_id.id,
							'debit':0,
							'credit':0,
						}
						new_null_line= self.env['account.move.line'].create(data_move_line)
						new_null.write({ 'line_id': [(4,new_null_line.id )] })
					"""
					self.internal_number= False
					self.write( {'internal_number':False })
					self.period_verifi_change_id = self.period_id
					self.write( {'period_verifi_change_id':self.period_id.id})
					
		t = super(account_invoice,self).action_move_create()

		if self.period_verifi_change_id.id==False or self.period_verifi_change_id.id==None:
			print "if unico"
			self.period_verifi_change_id = self.period_id
			self.write( {'period_verifi_change_id':self.period_id.id})

		if self.journal_verifi_change_id.id==False or self.journal_verifi_change_id.id==None:
			print "if unico"
			self.journal_verifi_change_id = self.journal_id
			self.write( {'journal_verifi_change_id':self.journal_id.id})
		return t


class account_voucher(models.Model):
	_inherit='account.voucher'


	period_verifi_change_id = fields.Many2one('account.period','Periodo Modify')
	
	@api.multi
	def proforma_voucher(self):
		if self.period_verifi_change_id==False or self.period_verifi_change_id==None:
			self.period_verifi_change_id = self.period_id
		else:
			if self.period_id:
				if self.period_id.id != self.period_verifi_change_id.id:
					self.number= False
					self.write( {'number':False })
					self.period_verifi_change_id = self.period_id
					self.write( {'period_verifi_change_id':self.period_id.id})
		t = super(account_voucher,self).proforma_voucher()
		return t
	