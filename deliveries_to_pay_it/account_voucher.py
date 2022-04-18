# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import osv, fields
from openerp.tools.translate import _

class account_voucher(osv.osv):
	_name='account.voucher'
	_inherit='account.voucher'

	def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
		if context is None:
			context = {}
		if not journal_id:
			return False
		journal_pool = self.pool.get('account.journal')
		journal = journal_pool.browse(cr, uid, journal_id, context=context)
		if ttype in ('sale', 'receipt'):
			account_id = journal.default_debit_account_id
		elif ttype in ('purchase', 'payment'):
			account_id = journal.default_credit_account_id
		else:
			account_id = journal.default_credit_account_id or journal.default_debit_account_id
		tax_id = False
		if account_id and account_id.tax_ids:
			tax_id = account_id.tax_ids[0].id

		vals = {'value':{} }
		vals['value']['hide'] = journal.is_fixer
		if ttype in ('sale', 'purchase'):
			vals = self.onchange_price(cr, uid, ids, line_ids, tax_id, partner_id, context)
			vals['value'].update({'tax_id':tax_id,'amount': amount})
		currency_id = False
		if journal.currency:
			currency_id = journal.currency.id
		else:
			currency_id = journal.company_id.currency_id.id

		period_ids = self.pool['account.period'].find(cr, uid, context=dict(context, company_id=company_id))
		vals['value'].update({
			'currency_id': currency_id,
			'payment_rate_currency_id': currency_id,
			'period_id': period_ids and period_ids[0] or False
		})
		#in case we want to register the payment directly from an invoice, it's confusing to allow to switch the journal 
		#without seeing that the amount is expressed in the journal currency, and not in the invoice currency. So to avoid
		#this common mistake, we simply reset the amount to 0 if the currency is not the invoice currency.
		if context.get('payment_expected_currency') and currency_id != context.get('payment_expected_currency'):
			vals['value']['amount'] = 0
			amount = 0
		if partner_id:
			res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
			for key in res.keys():
				vals[key].update(res[key])
		return vals
	
	def onchange_journal_voucher(self, cr, uid, ids, line_ids=False, tax_id=False, price=0.0, partner_id=False, journal_id=False, ttype=False, company_id=False, context=None):
		"""price
		Returns a dict that contains new values and context

		@param partner_id: latest value from user input for field partner_id
		@param args: other arguments
		@param context: context arguments, like lang, time zone

		@return: Returns a dict which contains new values, and context
		"""
		default = {
			'value':{},
		}

		if not partner_id or not journal_id:
			return default

		partner_pool = self.pool.get('res.partner')
		journal_pool = self.pool.get('account.journal')

		journal = journal_pool.browse(cr, uid, journal_id, context=context)
		partner = partner_pool.browse(cr, uid, partner_id, context=context)
		
		if journal.is_fixer:
			default['value']['hide'] = True
			return default
		
		account_id = False
		tr_type = False
		if journal.type in ('sale','sale_refund'):
			account_id = partner.property_account_receivable.id
			tr_type = 'sale'
		elif journal.type in ('purchase', 'purchase_refund','expense'):
			account_id = partner.property_account_payable.id
			tr_type = 'purchase'
		else:
			if not journal.default_credit_account_id or not journal.default_debit_account_id:
				raise osv.except_osv(_('Error!'), _('Please define default credit/debit accounts on the journal "%s".') % (journal.name))
			if ttype in ('sale', 'receipt'):
				account_id = journal.default_debit_account_id.id
			elif ttype in ('purchase', 'payment'):
				account_id = journal.default_credit_account_id.id
			else:
				account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
			tr_type = 'receipt'

		default['value']['account_id'] = account_id
		default['value']['type'] = ttype or tr_type

		vals = self.onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, time.strftime('%Y-%m-%d'), price, ttype, company_id, context)
		default['value'].update(vals.get('value'))

		return default

	def _is_hide(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for voucher in self.browse(cr, uid, ids, context=context):
			val = voucher.journal_id.is_fixer
			res[voucher.id] = val
		return res
	'''
	def _get_payment_type_selection (self, cr, uid, context=None):
		bt_obj = self.pool.get('base.element')
		return bt_obj.get_as_selection(cr, uid, 'PE.SUNAT.TABLA_01', context=context) 
	'''
	def _get_invoice_id(self, cr, uid, context=None):
		if context is None:
			context= {}
		return context.get('invoice_id', False)
	
	def onchange_rendicion(self, cr, uid, ids, rendicion=False, context=None):
		result = {}
		print 'INTRO CHANGE'
		if rendicion:
			rendicion_obj = self.pool.get('deliveries.to.pay').browse(cr, uid, rendicion, context=context)
			print 'name:', rendicion_obj.name
			result = {'value': {
				'reference': rendicion_obj.name,
				}
			}
		return result
	
	_columns={
		'rendicion': fields.many2one('deliveries.to.pay', 'Rendicion', readonly=True, domain=[('state','=','delivered'),], states={'draft':[('readonly',False)]}),
		'hide': fields.function(_is_hide, string="Is Hide", type="boolean"),
		'invoice': fields.many2one('account.invoice', 'Account Invoice'),
	}
	
	_defaults={
		'invoice': _get_invoice_id,
	}
	
		
	def action_move_line_create(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		
		parametro_id = self.pool.get('main.parameter').search(cr, uid, [])
		parametro = self.pool.get('main.parameter').browse(cr, uid, parametro_id[0],context)
		for voucher in self.browse(cr, uid, ids, context=context):
			#if voucher.amount != 0.00:
			if True:
				if voucher.invoice.id != False:
					if voucher.journal_id.is_fixer:
						if voucher.rendicion.id == False: 
							raise osv.except_osv('Acción Inválida!', 'Debe seleccionar una rendicion con la cual pagar.')
						
						if voucher.rendicion.done_date == False: 
							raise osv.except_osv('Acción Inválida!', 'Debe establecer una fecha de rendicion.')
						
						self.pool.get('account.voucher').write(cr, uid, [voucher.id], {'reference': voucher.rendicion.name})
						
						super(account_voucher,self).action_move_line_create(cr, uid, ids, context)
						invoice_tmp = self.pool.get('account.invoice').browse(cr,uid,[voucher.invoice.id],context)[0]

						'''
						account_move = self.pool.get('account.move').search(cr, uid, [('name','=',voucher.invoice.supplier_invoice_number),('date_stop','>=',fixer.deliver_date)])
						self.pool.get('account.period').search(cr,uid,[('date_start','<=',fixer.deliver_date),('date_stop','>=',fixer.deliver_date)])
						'''
						last_id = 0
						last = None
						for payment in invoice_tmp.payment_ids:
							if payment.id > last_id:
								last_id = payment.id
								last = payment

						#print(last.move_id.id)

						#Agregamos la referencia de la rendicion a las lineas de asiento contable

						cuentas = [
							parametro.deliver_account_mn.id, 
							parametro.deliver_account_me.id, 
							parametro.loan_account_mn.id, 
							parametro.loan_account_me.id, 
						]

						for move_line in last.move_id.line_id:
							vals = {'rendicion_id': voucher.rendicion.id}
							if move_line.account_id.id in cuentas:
								partner_id = voucher.rendicion.partner_id.id
								vals.update({'partner_id': partner_id, 'nro_comprobante': voucher.rendicion.name})
							'''
							else:
								if voucher.invoice.id != False:
									vals.update({'nro_comprobante': voucher.invoice.supplier_invoice_number})
							'''
							self.pool.get('account.move.line').write(cr, uid, [move_line.id], vals, context)
							self.pool.get('account.move').write(cr, uid, [last.move_id.id], {'rendicion_id': voucher.rendicion.id}, context)

						rendicion_tmp = self.pool.get('deliveries.to.pay')
						rendicion_tmp.write(cr, uid, voucher.rendicion.id, {'done_move': [(4, last.move_id.id)]})
						return True
					else:
						super(account_voucher,self).action_move_line_create(cr, uid, ids, context)
						return True
				else:
					super(account_voucher,self).action_move_line_create(cr, uid, ids, context)
					voucher_tmp = self.browse(cr,uid,ids[0],context)

					#print(voucher.rendicion.id)
					print('EJECUTE')
					print(voucher.rendicion.id)
					print(voucher_tmp.move_id)
					print(voucher_tmp.move_id.id)

					if voucher.rendicion.id != False:
						cuentas = [
							parametro.deliver_account_mn.id, 
							parametro.deliver_account_me.id, 
							parametro.loan_account_mn.id, 
							parametro.loan_account_me.id, 
						]

						#Agregamos la referencia de la rendicion a las lineas de asiento contable
						for move_line in voucher_tmp.move_id.line_id:
							vals = {'rendicion_id': voucher.rendicion.id}
							if move_line.account_id.id in cuentas:
								partner_id = voucher.rendicion.partner_id.id
								vals.update({'partner_id': partner_id, 'nro_comprobante': voucher.rendicion.name})
							'''
							else:
								if voucher.invoice.id != False:
									vals.update({'nro_comprobante': voucher.invoice.supplier_invoice_number})
							'''
							self.pool.get('account.move.line').write(cr, uid, [move_line.id], vals, context)
							self.pool.get('account.move').write(cr, uid, [voucher_tmp.move_id.id], {'rendicion_id': voucher.rendicion.id}, context)

						rendicion_tmp = self.pool.get('deliveries.to.pay')
						rendicion_tmp.write(cr, uid, voucher.rendicion.id, {'done_move': [(4, voucher_tmp.move_id.id)]})
					return True
			else:
				raise osv.except_osv('Acción Inválida!', 'El monto a pagar no puede ser 0.00.')
		return True

account_voucher()