# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_account(models.Model):
	_inherit = 'account.account'

	analytic_account_id = fields.Many2one('account.analytic.account',string='Cuenta Analitica')
	analytic_distribution_id = fields.Many2one('account.analytic.plan.instance',string='Distribucion Analitica')

class product_template(models.Model):
	_inherit = 'product.template'

	analytic_distribution_id = fields.Many2one('account.analytic.plan.instance',string='Distribucion Analitica')	

class account_invoice_line(models.Model):
	_inherit = 'account.invoice.line'


	@api.multi
	def onchange_account_id(self, product_id, partner_id, inv_type, fposition_id, account_id):
		t = super(account_invoice_line,self).onchange_account_id(product_id, partner_id, inv_type, fposition_id, account_id)
		

		if account_id:
			account_act = self.env['account.account'].search([('id','=',account_id)])[0]

			if 'value' in t:
				if account_act.analytic_account_id.id:
					t['value']['account_analytic_id'] = account_act.analytic_account_id.id
				if account_act.analytic_distribution_id.id:
					t['value']['analytics_id'] = account_act.analytic_distribution_id.id
				print "estoy aki"
				print t

		if product_id:
			product_act = self.env['product.product'].search([('id','=',product_id)])[0]
			if 'value' in t:
				if product_act.analytic_account_id.id:
					t['value']['account_analytic_id'] = product_act.analytic_account_id.id
				if product_act.analytic_distribution_id.id:
					t['value']['analytics_id'] = product_act.analytic_distribution_id.id
		print "final",t
		return t


	@api.multi
	def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, company_id=None):
		
		t = super(account_invoice_line,self).product_id_change(product, uom_id, qty, name, type, partner_id, fposition_id, price_unit, currency_id, company_id)
		if product:
			product_act = self.env['product.product'].search([('id','=',product)])[0]
			if 'value' in t:
				if product_act.analytic_account_id.id:
					t['value']['account_analytic_id'] = product_act.analytic_account_id.id
				if product_act.analytic_distribution_id.id:
					t['value']['analytics_id'] = product_act.analytic_distribution_id.id
		return t


class purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'

	
	def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order=False, fiscal_position_id=False, date_planned=False, name=False, price_unit=False, state='draft',context=None):
		t = super(purchase_order_line,self).onchange_product_id(cr,uid,ids,pricelist_id, product_id, qty, uom_id, partner_id, date_order, fiscal_position_id, date_planned, name, price_unit, state,context)
		print "--------------gg",product_id
		if product_id:
			product_act_id = self.pool.get('product.product').search(cr,uid,[('id','=',product_id)])
			print product_act_id
			product_act = self.pool.get('product.product').browse(cr,uid,product_act_id,context)
			if 'value' in t:
				if product_act.analytic_account_id.id:
					t['value']['account_analytic_id'] = product_act.analytic_account_id.id
				if product_act.analytic_distribution_id.id:
					t['value']['analytics_id'] = product_act.analytic_distribution_id.id
		return t