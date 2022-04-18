# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

#Orden de Compra

class account_move(models.Model):
	_inherit = 'account.move'

	period_origin_id = fields.Many2one('account.period','Periodo Origen')

	@api.onchange("date")
	def onchange_date_asiento(self):
		per_id = False
		periodos = self.env['account.period'].search([('date_start','<=',self.date),('date_stop','>=',self.date)])
		for i in periodos:
			if '00/' not in i.code:
				per_id = i.id
		self.period_origin_id = per_id



class account_invoice(models.Model):
	_inherit = "account.invoice"

	period_origin_id = fields.Many2one('account.period','Periodo Origen')
	
	@api.multi
	def onchange_payment_term_date_invoice(self, payment_term_id, date_invoice):
		t = super(account_invoice,self).onchange_payment_term_date_invoice(payment_term_id, date_invoice)

		per_id = False
		periodos = self.env['account.period'].search([('date_start','<=',date_invoice),('date_stop','>=',date_invoice)])
		for i in periodos:
			if '00/' not in i.code:
				per_id = i.id
		t['value']['period_origin_id'] = per_id
		return t


	@api.multi
	def invoice_validate(self):
		t = super(account_invoice,self).invoice_validate()
		for i in self:
			if i.move_id.id:
				i.move_id.period_origin_id = i.period_origin_id.id
		return t


class account_voucher(models.Model):
	_inherit = "account.voucher"

	period_origin_id = fields.Many2one('account.period','Periodo Origen')

	

	def onchange_date(self, cr, uid, ids, date, currency_id, payment_rate_currency_id, amount, company_id, context=None):
		t= super(account_voucher,self).onchange_date( cr, uid, ids, date, currency_id, payment_rate_currency_id, amount, company_id, context)
		period_ids = self.pool.get('account.period').search(cr,uid,[('date_stop','>=',date),('date_start','<=',date)] )
		period_obj = self.pool.get('account.period').browse(cr,uid,period_ids)
		per_id = False
		for i in period_obj:
			if '00/' not in i.code:
				per_id = i.id

			t['value']['period_origin_id'] = per_id
		return t


	@api.multi
	def proforma_voucher(self):
		t = super(account_voucher,self).proforma_voucher()
		for i in self:
			if i.move_id.id:
				i.move_id.period_origin_id = i.period_origin_id.id		
		return t
	