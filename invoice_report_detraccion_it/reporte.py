# -*- coding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import datetime
from datetime import datetime
import decimal
import calendar

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.one
	def get_monto_detraccion(self):
		param = self.env['main.parameter'].search([])[0].account_detracciones.id
		if self.move_detraccion_id.id:
			for k in self.move_detraccion_id.line_id:
				if k.account_id.id == param:
					self.monto_detraccion = k.debit + k.credit
		else:
			self.monto_detraccion = 0

	monto_detraccion = fields.Float('Monto Detraccion',digits=(12,2),compute="get_monto_detraccion")