# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv

class account_invoice_tax(models.Model):
	_inherit='account.invoice.tax'

	@api.multi
	def amount_change(self, amount, currency_id=False, company_id=False, date_invoice=False):
		company = self.env['res.company'].browse(company_id)
		if currency_id and company.currency_id:
			currency = self.env['res.currency'].browse(currency_id)
			currency = currency.with_context(date=date_invoice or fields.Date.context_today(self))
			amount = currency.compute(amount, company.currency_id, round=False)
		return {'value': {'tax_amount': amount}}
