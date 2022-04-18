# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv

class desembolso_personal(models.Model):
	_inherit = 'desembolso.personal'
	
	hide = fields.Boolean('Hide', default=False)
	small_cash_id = fields.Many2one('small.cash.another', 'Nro Caja Chica')
	
	@api.onchange('caja_banco')
	def onchange_caja_banco(self):
		if self.caja_banco:
			self.hide = self.caja_banco.is_small_cash

	@api.multi
	def entregar_button(self):
		x = super(desembolso_personal, self).entregar_button()
		if self.caja_banco.is_small_cash:
			if self.move_id:
				for line in self.move_id.line_id:
					if line.account_id.id == self.caja_banco.default_debit_account_id.id:
						line.write({'small_cash_id': self.small_cash_id.id})
		return x
	
class desembolso_personal_wizard(models.Model):
	_inherit ='desembolso.personal.wizard'

	@api.onchange('metodo_pago')
	def onchange_metodo_pago(self):
		if self.metodo_pago:
			self.hide = self.metodo_pago.is_small_cash
	
	hide = fields.Boolean('Hide', default=False)
	small_cash_id = fields.Many2one('small.cash.another', 'Nro Caja Chica')
	
	@api.multi
	def do_rebuild(self):
		move = super(desembolso_personal_wizard, self).do_rebuild()
		if self.metodo_pago.is_small_cash:
			if move:
				for line in move.line_id:
					if line.account_id.id == self.metodo_pago.default_debit_account_id.id:
						line.write({'small_cash_id': self.small_cash_id.id})
		return move