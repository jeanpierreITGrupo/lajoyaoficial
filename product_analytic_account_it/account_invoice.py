# -*- coding: utf-8 -*-
import pprint
import itertools
import openerp.addons.decimal_precision as dp

from lxml import etree

from openerp.osv import osv
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare

class account_invoice_line(models.Model):
	_inherit = "account.invoice.line"	
	
	def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, company_id=None, context=None):
		res_prod = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom_id, qty, name, type, partner_id, fposition_id, price_unit, currency_id=currency_id, company_id=company_id, context=context)
		product = self.pool.get('product.product').browse(cr, uid, product, context)
		#raise osv.except_osv('Alerta',product.analytic_account_id.id)
		res_prod['value'].update({'account_analytic_id': product.analytic_account_id.id})
		print 'HEREEEE'
		pprint.pprint(res_prod)
		return res_prod
	
	'''
	@api.multi
	def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
			partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
			company_id=None):
		context = self._context
		company_id = company_id if company_id is not None else context.get('company_id', False)
		self = self.with_context(company_id=company_id, force_company=company_id)

		if not partner_id:
			raise except_orm(_('No Partner Defined!'), _("You must first select a partner!"))
		if not product:
			if type in ('in_invoice', 'in_refund'):
				return {'value': {}, 'domain': {'product_uom': []}}
			else:
				return {'value': {'price_unit': 0.0}, 'domain': {'product_uom': []}}

		values = {}

		print 'values', values
		part = self.env['res.partner'].browse(partner_id)
		fpos = self.env['account.fiscal.position'].browse(fposition_id)

		if part.lang:
			self = self.with_context(lang=part.lang)
		product = self.env['product.product'].browse(product)

		values['name'] = product.partner_ref
		print 'values', values
		values['account_analytic_id'] = product.analytic_account_id.id
		print 'values', values
		
		if type in ('out_invoice', 'out_refund'):
			account = product.property_account_income or product.categ_id.property_account_income_categ
		else:
			account = product.property_account_expense or product.categ_id.property_account_expense_categ
		account = fpos.map_account(account)
		if account:
			values['account_id'] = account.id

		if type in ('out_invoice', 'out_refund'):
			taxes = product.taxes_id or account.tax_ids
			if product.description_sale:
				values['name'] += '\n' + product.description_sale
		else:
			taxes = product.supplier_taxes_id or account.tax_ids
			if product.description_purchase:
				values['name'] += '\n' + product.description_purchase

		taxes = fpos.map_tax(taxes)
		values['invoice_line_tax_id'] = taxes.ids

		if type in ('in_invoice', 'in_refund'):
			values['price_unit'] = price_unit or product.standard_price
		else:
			values['price_unit'] = product.lst_price

		values['uos_id'] = product.uom_id.id
		if uom_id:
			uom = self.env['product.uom'].browse(uom_id)
			if product.uom_id.category_id.id == uom.category_id.id:
				values['uos_id'] = uom_id

		domain = {'uos_id': [('category_id', '=', product.uom_id.category_id.id)]}

		company = self.env['res.company'].browse(company_id)
		currency = self.env['res.currency'].browse(currency_id)

		if company and currency:
			if company.currency_id != currency:
				if type in ('in_invoice', 'in_refund'):
					values['price_unit'] = product.standard_price
				values['price_unit'] = values['price_unit'] * currency.rate

			if values['uos_id'] and values['uos_id'] != product.uom_id.id:
				values['price_unit'] = self.env['product.uom']._compute_price(
					product.uom_id.id, values['price_unit'], values['uos_id'])
		print 'values', values
		#raise osv.except_osv('Alerta', values)
		
		return {'value': values, 'domain': domain}
	
	'''
	'''
	@api.multi
	def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, 
						  currency_id=False, company_id=None):
		res = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type, partner_id, 
																  fposition_id, price_unit, currency_id, company_id)
		product = self.env['product.product'].browse(product)
		#raise osv.except_osv('Alerta',product.analytic_account_id.id)
		res['value'].update({'account_analytic_id': product.analytic_account_id.id})
		#pprint(res['value'])
		raise osv.except_osv('Alerta', res)
		return res
	'''