# -*- coding: utf-8 -*-

import time
from lxml import etree

from openerp import models, fields, api
from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw
import openerp


class account_voucher(models.Model):
	_inherit = 'account.voucher'
	type_document_id = fields.Many2one('it.type.document', string="Tipo de Documento",index=True,ondelete='restrict')

	def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
		t = super(account_voucher,self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency, current_currency, context)
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		#if voucher.type_document_id:
		#	t['type_document_id'] = voucher.type_document_id.id
		if voucher.reference:
			t['nro_comprobante'] = voucher.reference
		return t
		

	def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
		t = super(account_voucher,self).writeoff_move_line_get(cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context)
		if t == {}:
			return {}

		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		if voucher.type_document_id:
			t['type_document_id'] = voucher.type_document_id.id
		if voucher.reference:
			t['nro_comprobante'] = voucher.reference
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
			if voucher.type_document_id:
				move_line['type_document_id'] = voucher.type_document_id.id

			if voucher.reference:
				move_line['nro_comprobante'] = voucher.reference
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

				if voucher.reference:
					move_line_foreign_currency['nro_comprobante'] = voucher.reference
					
				new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
				rec_ids.append(new_id)
			if line.move_line_id.id:
				rec_lst_ids.append(rec_ids)

			
		return (tot_line, rec_lst_ids)

	@api.multi
	def add_nro_comprobante(self, entrada):
		t= entrada
		if 'value' in t:
			if 'line_cr_ids' in t['value']:
				for i in t['value']['line_cr_ids']:
					if 'move_line_id' in i:
						m = self.env['account.move.line'].search([('id','=',i['move_line_id'])])
						rpta = ''
						type_d_i = None
						if m.nro_comprobante:
							rpta = m.nro_comprobante
						if m.type_document_id:
							type_d_i = m.type_document_id.id
						i['nro_comprobante'] = str(rpta)
						i['type_document_line_id'] = type_d_i

			if 'line_dr_ids' in t['value']:
				for i in t['value']['line_dr_ids']:
					if 'move_line_id' in i:
						m = self.env['account.move.line'].search([('id','=',i['move_line_id'])])
						rpta = ''
						type_d_i = None
						if m.nro_comprobante:
							rpta = m.nro_comprobante
						if m.type_document_id:
							type_d_i = m.type_document_id.id
						i['nro_comprobante'] = str(rpta)
						i['type_document_line_id'] = type_d_i
		print "finalizo----------", t
		return t

	@api.one
	def add_nro_comprobante_without(self):
		for i in self.line_cr_ids:
			if i.move_line_id:
				m = self.env['account.move.line'].search([('id','=',i.move_line_id.id)])
				rpta = ''
				type_d_i = None
				if m.nro_comprobante:
					rpta = m.nro_comprobante
				if m.type_document_id:
					type_d_i = m.type_document_id.id
				i['nro_comprobante'] = str(rpta)
				i['type_document_line_id'] = type_d_i

		for i in self.line_dr_ids:
			if i.move_line_id:
				m = self.env['account.move.line'].search([('id','=',i.move_line_id.id)])
				rpta = ''
				type_d_i = None
				if m.nro_comprobante:
					rpta = m.nro_comprobante
				if m.type_document_id:
					type_d_i = m.type_document_id.id
				i['nro_comprobante'] = str(rpta)
				i['type_document_line_id'] = type_d_i
		return True

	@api.multi
	def recalcule_all(self):
		contador = 0
		if self.line_cr_ids:
			for i in self.line_cr_ids:
				if self._context['type'] == 'receipt':
					contador += i.amount
				else:
					contador -= i.amount
				if i.amount== 0:
					self.env['account.voucher.line'].search([('id','=',i.id)]).unlink()
		if self.line_dr_ids:
			for i in self.line_dr_ids:
				if self._context['type'] == 'receipt':
					contador -= i.amount
				else:
					contador += i.amount
				if i.amount== 0:
					self.env['account.voucher.line'].search([('id','=',i.id)]).unlink()
		self.amount = contador
		self.add_nro_comprobante_without()


	@api.multi
	def onchange_partner_id(self, partner_id, journal_id, amount, currency_id, ttype, date):
		t = super(account_voucher,self).onchange_partner_id(partner_id, journal_id, amount, currency_id, ttype, date)
		print "entre----------------"
		print t
		return self.add_nro_comprobante(t)
	
	@api.multi
	def onchange_amount(self, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id):
		t = super(account_voucher,self).onchange_amount( amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id)
		import pprint
		pprint.pprint(t)
		return self.add_nro_comprobante(t)

	@api.multi
	def onchange_journal(self, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id):
		t = super(account_voucher,self).onchange_journal(journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id)
		return t


class account_voucher_line(models.Model):
	_inherit = 'account.voucher.line'

	nro_comprobante = fields.Char('Comprobante', size=30)
	type_document_line_id = fields.Many2one('it.type.document','Tipo de Documento',ondelete='restrict')
	periodo_id = fields.Many2one('account.period',related='move_line_id.period_id',readonly=True,string='Periodo')
'''
    def recompute_payment_rate(self, cr, uid, ids, vals, currency_id, date, ttype, journal_id, amount, context=None):
        if context is None:
            context = {}
        #on change of the journal, we need to set also the default value for payment_rate and payment_rate_currency_id
        currency_obj = self.pool.get('res.currency')
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        company_id = journal.company_id.id
        payment_rate = 1.0
        currency_id = currency_id or journal.company_id.currency_id.id
        payment_rate_currency_id = currency_id
        ctx = context.copy()
        ctx.update({'date': date})
        o2m_to_loop = False
        if ttype == 'receipt':
            o2m_to_loop = 'line_cr_ids'
        elif ttype == 'payment':
            o2m_to_loop = 'line_dr_ids'
        if o2m_to_loop and 'value' in vals and o2m_to_loop in vals['value']:
            for voucher_line in vals['value'][o2m_to_loop]:
                if not isinstance(voucher_line, dict):
                    continue
                if voucher_line['currency_id'] != currency_id:
                    # we take as default value for the payment_rate_currency_id, the currency of the first invoice that
                    # is not in the voucher currency
                    payment_rate_currency_id = voucher_line['currency_id']
                    tmp = currency_obj.browse(cr, uid, payment_rate_currency_id, context=ctx).rate
                    payment_rate = tmp / currency_obj.browse(cr, uid, currency_id, context=ctx).rate
                    break
        vals['value'].update({
            'payment_rate': payment_rate,
            'currency_id': currency_id,
            'payment_rate_currency_id': payment_rate_currency_id
        })
        #read the voucher rate with the right date in the context
        voucher_rate = self.pool.get('res.currency').read(cr, uid, [currency_id], ['rate'], context=ctx)[0]['rate']
        ctx.update({
            'voucher_special_currency_rate': payment_rate * voucher_rate,
            'voucher_special_currency': payment_rate_currency_id})
        res = self.onchange_rate(cr, uid, ids, payment_rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        for key in res.keys():
            vals[key].update(res[key])
        return vals'''