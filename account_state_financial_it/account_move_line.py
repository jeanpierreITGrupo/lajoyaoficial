# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_move_line(models.Model):
	_inherit = 'account.move.line'

	@api.one
	def get_fefectivo(self):
		self.fefectivo_id = self.account_id.fefectivo_id.id

	fefectivo_id = fields.Many2one('account.config.efective',string ="F. Efectivo",compute="get_fefectivo",store=False)