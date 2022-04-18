# -*- coding: utf-8 -*-

import time
from lxml import etree
import pprint
from openerp import models, fields, api
from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw
import openerp

class account_invoice(models.Model):
	_inherit= 'account.invoice'

	def invoice_pay_customer(self, cr, uid, ids, context=None):
		t = super(account_invoice,self).invoice_pay_customer(cr, uid, ids, context)

		if not ids: return []
		inv = self.browse(cr, uid, ids[0], context=context)
		if inv.supplier_invoice_number:
			t['context']['default_nro_comprobante_invoice'] = inv.supplier_invoice_number
		if inv.amount_total:
			t['context']['default_total_dialog'] = inv.amount_total
		if inv.residual:
			t['context']['default_saldo_dialog'] = inv.residual
		if inv.currency_id:
			t['context']['default_divisa_dialog'] = inv.currency_id.id
		if inv.date_invoice:
			t['context']['default_date_dialog'] = inv.date_invoice
		if inv.type_document_id:
			t['context']['default_type_document_dialog'] = inv.type_document_id.id
		t['context']['default_invoice_type'] = t['context']['invoice_type'] 
		#import pprint
		#pprint.pprint(t)
		return t


class account_voucher(models.Model):
	_inherit = 'account.voucher'
	means_payment_id = fields.Many2one('it.means.payment',string ="Medio de Pago",index = True,ondelete='restrict')
	invoice_dialog_id = fields.Many2one('account.invoice',string="temporal_data")

	nro_comprobante_invoice = fields.Char(string="Comprobante")
	total_dialog = fields.Float(string="Total")
	saldo_dialog = fields.Float(string="Saldo")
	divisa_dialog = fields.Many2one('res.currency',string="Moneda")
	date_dialog = fields.Date(string="Fecha Factura")
	type_document_dialog = fields.Many2one('it.type.document','Tipo de Documento')

	invoice_type = fields.Char('Tipo Factura',size=50)

	tipo_de_cambio_detalle = fields.Float('Tipo de Cambio',digits=(12,3), default=1)
	saldo_mn_detalle = fields.Float('Saldo Soles',digits=(12,2))
	saldo_me_detalle = fields.Float('Saldo Dolares',digits=(12,2))
	divisa_related_dialog = fields.Char('Divisa Dialog',related='divisa_dialog.name')

	###type_sale

	def cancel_voucher(self, cr, uid, ids, context=None):
		reconcile_pool = self.pool.get('account.move.reconcile')
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		for voucher in self.browse(cr, uid, ids, context=context):
			voucher.write({'nro_comprobante_invoice' : False})
		return super(account_voucher,self).cancel_voucher(cr,uid,ids,context)
	
	
	def onchange_date(self, cr, uid, ids, date, currency_id, payment_rate_currency_id, amount, company_id, context=None):
		t= super(account_voucher,self).onchange_date( cr, uid, ids, date, currency_id, payment_rate_currency_id, amount, company_id, context)
		return t
		res_currency_rate_list = self.pool.get('res.currency.rate').search(cr,uid,[('currency_id.name','=','USD'),('name','=',date)],context=context)
		if res_currency_rate_list and len(res_currency_rate_list)>0:
			t['value']['tipo_de_cambio_detalle'] = self.pool.get('res.currency.rate').browse(cr,uid, res_currency_rate_list[0]).type_sale
			data = self.browse(cr,uid,ids,context=context)
			if 'invoice_id' in context:
				t['value']['saldo_mn_detalle'] = (self.pool.get('account.invoice').browse(cr,uid,context['invoice_id'],context).residual) * (self.pool.get('res.currency.rate').browse(cr,uid, res_currency_rate_list[0]).type_sale)
				t['value']['saldo_me_detalle'] = (self.pool.get('account.invoice').browse(cr,uid,context['invoice_id'],context).residual) / (self.pool.get('res.currency.rate').browse(cr,uid, res_currency_rate_list[0]).type_sale)
		else:
			t['value']['tipo_de_cambio_detalle'] = 1
			if 'invoice_id' in context:
				t['value']['saldo_mn_detalle'] = (self.pool.get('account.invoice').browse(cr,uid,context['invoice_id'],context).residual)
				t['value']['saldo_me_detalle'] = (self.pool.get('account.invoice').browse(cr,uid,context['invoice_id'],context).residual)

		return t

	def button_proforma_voucher(self, cr, uid, ids, context=None):
		if 'invoice_id' in context:
			invoice = self.pool.get('account.invoice').browse(cr,uid,context['invoice_id'],context)
			data = {
			'invoice_dialog_id':invoice.id,
			'nro_comprobante_invoice':invoice.supplier_invoice_number,
			'total_dialog':invoice.amount_total,
			'saldo_dialog':invoice.residual,
			'divisa_dialog':invoice.currency_id.id,
			'date_dialog':invoice.date_invoice,
			'type_document_dialog':invoice.type_document_id.id,
			}
			#import pprint
			#pprint.pprint(data)
			self.write(cr,uid,ids,data,context=context)
		t = super(account_voucher,self).button_proforma_voucher(cr, uid, ids, context)
		self.recalcule_all(cr,uid,ids,context)
		return t
	
	def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
		t = super(account_voucher,self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency, current_currency, context)
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		if voucher.means_payment_id and voucher.journal_id.default_debit_account_id.id == t['account_id']:
			t['means_payment_id'] = voucher.means_payment_id.id
		if voucher.name:
			t['name'] = voucher.name
		return t
		

	def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
		t = super(account_voucher,self).writeoff_move_line_get(cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context)
		if t == {}:
			return {}

		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		if voucher.means_payment_id  and voucher.journal_id.default_debit_account_id.id == t['account_id']:
			t['means_payment_id'] = voucher.means_payment_id.id
		if voucher.name:
			t['name'] = voucher.name
		return t

	def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
		'''
		Create one account move line, on the given account move, per voucher line where amount is not 0.0.
		It returns Tuple with tot_line what is total of difference between debit and credit and
		a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

		:param voucher_id: Voucher id what we are working with
		:param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
		:param move_id: Account move wher those lines will be joined.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
		:rtype: tuple(float, list of int)
		'''
		if context is None:
			context = {}
		move_line_obj = self.pool.get('account.move.line')
		currency_obj = self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		tot_line = line_total
		rec_lst_ids = []

		date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
		ctx = context.copy()
		ctx.update({'date': date})
		voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
		voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
		ctx.update({
			'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
			'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
		prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
		for line in voucher.line_ids:
			#create one move line per voucher line where amount is not 0.0
			# AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
			if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
				continue
			# convert the amount set on the voucher line into the currency of the voucher's company
			# this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
			amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
			# if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
			# currency rate difference
			if line.amount == line.amount_unreconciled:
				if not line.move_line_id:
					raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
				sign = line.type =='dr' and -1 or 1
				currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
			else:
				currency_rate_difference = 0.0
			move_line = {
				'journal_id': voucher.journal_id.id,
				'period_id': voucher.period_id.id,
				'name': line.name or '/',
				'account_id': line.account_id.id,
				'move_id': move_id,
				'partner_id': voucher.partner_id.id,
				'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
				'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
				'quantity': 1,
				'credit': 0.0,
				'debit': 0.0,
				'date': voucher.date
			}
			if amount < 0:
				amount = -amount
				if line.type == 'dr':
					line.type = 'cr'
				else:
					line.type = 'dr'

			if (line.type=='dr'):
				tot_line += amount
				move_line['debit'] = amount
			else:
				tot_line -= amount
				move_line['credit'] = amount

			if voucher.tax_id and voucher.type in ('sale', 'purchase'):
				move_line.update({
					'account_tax_id': voucher.tax_id.id,
				})

			# compute the amount in foreign currency
			foreign_currency_diff = 0.0
			amount_currency = False
			if line.move_line_id:
				# We want to set it on the account move line as soon as the original line had a foreign currency
				if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
					# we compute the amount in that foreign currency.
					if line.move_line_id.currency_id.id == current_currency:
						# if the voucher and the voucher line share the same currency, there is no computation to do
						sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
						amount_currency = sign * (line.amount)
					else:
						# if the rate is specified on the voucher, it will be used thanks to the special keys in the context
						# otherwise we use the rates of the system
						amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
				if line.amount == line.amount_unreconciled:
					foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)

			move_line['amount_currency'] = amount_currency
			# aqui comienza modificacion actual ( Version Final )
			if voucher.type_document_id:
				move_line['type_document_id'] = voucher.type_document_id.id
			if voucher.means_payment_id  and voucher.journal_id.default_debit_account_id.id == move_line['account_id']:
				move_line['means_payment_id'] = voucher.means_payment_id.id
			if voucher.name:
				move_line['name'] = voucher.name
			
			if line.nro_comprobante:
				move_line['nro_comprobante'] = line.nro_comprobante
			
			if voucher.nro_comprobante_invoice:
				move_line['nro_comprobante'] = voucher.nro_comprobante_invoice
				

			voucher_line = move_line_obj.create(cr, uid, move_line)
			rec_ids = [voucher_line, line.move_line_id.id]
			
			if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
				# Change difference entry in company currency
				exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
				new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
				move_line_obj.create(cr, uid, exch_lines[1], context)
				rec_ids.append(new_id)

			if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
				# Change difference entry in voucher currency
				move_line_foreign_currency = {
					'journal_id': line.voucher_id.journal_id.id,
					'period_id': line.voucher_id.period_id.id,
					'name': _('change')+': '+(line.name or '/'),
					'account_id': line.account_id.id,
					'move_id': move_id,
					'partner_id': line.voucher_id.partner_id.id,
					'currency_id': line.move_line_id.currency_id.id,
					'amount_currency': -1 * foreign_currency_diff,
					'quantity': 1,
					'credit': 0.0,
					'debit': 0.0,
					'date': line.voucher_id.date,
				}
				if voucher.type_document_id:
					move_line_foreign_currency['type_document_id'] = voucher.type_document_id.id

				if voucher.means_payment_id and line.voucher_id.journal_id.default_debit_account_id.id == move_line_foreign_currency['account_id']:
					move_line_foreign_currency['means_payment_id'] = voucher.means_payment_id.id
				if line.nro_comprobante:
					move_line_foreign_currency['nro_comprobante'] = line.nro_comprobante
					
				
				if voucher.name:
					move_line_foreign_currency['name'] = voucher.name

				new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
				rec_ids.append(new_id)
			if line.move_line_id.id:
				rec_lst_ids.append(rec_ids)

			
		return (tot_line, rec_lst_ids)
