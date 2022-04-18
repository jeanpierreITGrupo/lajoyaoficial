# -*- coding: utf-8 -*-
from openerp import models, fields, api
import base64
from openerp.osv import osv

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.one
	def button_borrar_analytic_lines(self):
		for i in self.invoice_line:
			i.write({
				'account_analytic_id': False,
				'analytics_id': False,
			})