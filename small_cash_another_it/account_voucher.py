# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import osv, fields
from openerp.tools.translate import _

class account_voucher(osv.osv):
	_name='account.voucher'
	_inherit='account.voucher'

	def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
		vals = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context)
		if journal_id:
			journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context)
			vals['value']['hide_small'] = journal.is_small_cash
		#vals['value']['small_cash'] = False
		#vals['value']['rendicion'] = False
		#vals['value']['reference'] = False
		print 'SALIO'
		return vals
	
	def onchange_journal_voucher(self, cr, uid, ids, line_ids=False, tax_id=False, price=0.0, partner_id=False, journal_id=False, ttype=False, company_id=False, context=None):
		default = super(account_voucher, self).onchange_journal_voucher(self, cr, uid, ids, line_ids, tax_id, price, partner_id, journal_id, ttype, company_id, context)
		print 'SALIO VOUCHER'
		if journal_id:
			journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context)
			if journal_id.is_small_cash:
				default['value']['hide_small'] = True
		return default
		
	def _is_hide_small(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for voucher in self.browse(cr, uid, ids, context=context):
			val = voucher.journal_id.is_small_cash
			res[voucher.id] = val
		return res
	
	def onchange_small_cash(self, cr, uid, ids, small_cash=False, context=None):
		result = {}
		print 'INTRO CHANGE'
		if small_cash:
			rendicion_obj = self.pool.get('small.cash.another').browse(cr, uid, small_cash, context=context)
			print 'name:', rendicion_obj.name
			result = {'value': {
				'reference': rendicion_obj.name,
				}
			}
		return result
	
	_columns={
		'small_cash': fields.many2one('small.cash.another', 'Caja Chica', readonly=True, domain=[('state','=','done'),], states={'draft':[('readonly',False)]}),
		'hide_small': fields.function(_is_hide_small, string="Is Hide Small", type="boolean"),
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
					if voucher.journal_id.is_small_cash:
						if voucher.small_cash.id == False: 
							raise osv.except_osv('Acción Inválida!', 'Debe seleccionar una caja chica con la cual pagar.')
						
						#self.pool.get('account.voucher').write(cr, uid, [voucher.id], {'reference': voucher.small_cash.name})
						
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

						print(last.move_id.id)

						#Agregamos la referencia de la rendicion a las lineas de asiento contable

						cuentas = [
							voucher.journal_id.default_debit_account_id.id,
						]

						self.pool.get('account.move').write(cr,uid,[voucher.move_id.id],{'small_cash_id':voucher.small_cash.id})
						for move_line in last.move_id.line_id:
							#vals = {'rendicion_id': voucher.rendicion.id}
							vals = {}
							if move_line.account_id.id in cuentas:
								#partner_id = voucher.rendicion.partner_id.id
								vals.update({'small_cash_id': voucher.small_cash.id})
								#vals.update({'small_cash_id': voucher.small_cash.id, 'nro_comprobante': voucher.small_cash.name})
							'''
							else:
								if voucher.invoice.id != False:
									vals.update({'nro_comprobante': voucher.invoice.supplier_invoice_number})
							'''
							self.pool.get('account.move.line').write(cr, uid, [move_line.id], vals, context)
						return True
					else:
						super(account_voucher,self).action_move_line_create(cr, uid, ids, context)
						return True
				else:
					super(account_voucher,self).action_move_line_create(cr, uid, ids, context)
					voucher_tmp = self.browse(cr,uid,ids[0],context)

					#print(voucher.rendicion.id)
					print('EXEC')
					if voucher.small_cash.id != False:
						cuentas = [
							voucher.journal_id.default_debit_account_id.id,
						]

						#Agregamos la referencia de la rendicion a las lineas de asiento contable
						self.pool.get('account.move').write(cr,uid,[voucher.move_id.id],{'small_cash_id':voucher.small_cash.id})
						for move_line in voucher_tmp.move_id.line_id:
							#vals = {'rendicion_id': voucher.rendicion.id}
							vals = {}
							if move_line.account_id.id in cuentas:
								#partner_id = voucher.rendicion.partner_id.id
								vals.update({'small_cash_id': voucher.small_cash.id})
								#vals.update({'small_cash_id': voucher.small_cash.id, 'nro_comprobante': voucher.small_cash.name})
							'''
							else:
								if voucher.invoice.id != False:
									vals.update({'nro_comprobante': voucher.invoice.supplier_invoice_number})
							'''
							self.pool.get('account.move.line').write(cr, uid, [move_line.id], vals, context)
					return True
			else:
				raise osv.except_osv('Acción Inválida!', 'El monto a pagar no puede ser 0.00.')
		return True

account_voucher()