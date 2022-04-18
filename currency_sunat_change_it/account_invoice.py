# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

import openerp.addons.decimal_precision as dp
from openerp.tools import float_round, float_is_zero, float_compare


class account_invoice(models.Model):
	_inherit = 'account.invoice'
	currency_rate_auto = fields.Float('Tipo de Cambio Sunat',digits=(16,3))
	currency_rate_mod = fields.Float('Tipo de Cambio Personalizado',digits=(16,3))
	
	@api.one
	def recalcule_tcsunat(self):
		#res_currency_id = self.env['res.company'].search([])[0].currency_id
		res_currency_id = self.env['main.parameter'].search([])[0].currency_id
		if self.date_invoice:
			pass
		else:
			self.write({})
			import datetime
			self.date_invoice = str(datetime.datetime.today())
		if self.date_invoice:
			self.write({})
			data = 0.0
			print "entro"
			for inv in self:
				t = False
				for i in res_currency_id.rate_ids:
					if str(i.date_sunat)[:10] == str(self.date_invoice)[:10]:
						data = i.type_sale
						t = True
				if t == False:
					data = 1
				self.write({'currency_rate_auto': data})		
				self.currency_rate_auto = data
		else:
			raise osv.except_osv('Alerta','No Tiene Fecha la Factura')


	@api.one
	def button_reset_taxes(self):
		t = super(account_invoice,self).button_reset_taxes()
		self.recalcule_tcsunat()
		return t

	@api.multi
	def finalize_invoice_move_lines(self,move_lines):
		t = super(account_invoice,self).finalize_invoice_move_lines(move_lines)
		rate_tmp = self.currency_rate_auto
		if self.currency_rate_mod != 0:
			rate_tmp= self.currency_rate_mod
			print "SOY YO JP"
			for line in t:
				linea = line[2]
				if linea['currency_id']:
					if linea["amount_currency"] >0:

						linea['debit'] = linea['amount_currency'] * rate_tmp
						
						if linea['tax_amount'] > 0:
							linea['tax_amount'] = linea['amount_currency'] * rate_tmp

					if linea["amount_currency"] <0:
						
						linea['credit']= linea['amount_currency'] * rate_tmp* -1
						
						if linea['tax_amount']<0:
							linea['tax_amount'] = linea['amount_currency'] * rate_tmp* -1
		return t


	@api.one
	def action_number(self):
		for inv in self:
			rate_tmp = inv.currency_rate_auto
			if inv.currency_rate_mod != 0:
				rate_tmp= inv.currency_rate_mod
			self._cr.execute(""" UPDATE account_move_line SET currency_rate_it=%s WHERE move_id=%s """,(rate_tmp, inv.move_id.id))
			#esto es el ultimo cambio hecho

			"""
			linea__mov_act =self.env['account.move'].search([('id','=',inv.move_id.id)])[0]
			linea__mov_act.button_cancel()

			for t in inv.move_id.line_id:		
				if t.currency_id:				

					if t.amount_currency >0:
						linea_act =self.env['account.move.line'].search([('id','=',t.id)])[0]
						linea_act.debit = float_round(value=float(t.amount_currency * rate_tmp ), precision_rounding=2)
						print "linea 1",linea_act.debit
						#self._cr.execute("" UPDATE account_move_line SET debit=%s WHERE id=%s "",("%0.2f"%(t.amount_currency * rate_tmp), t.id))
						
						if t.tax_amount > 0:
							#self._cr.execute("" UPDATE account_move_line SET tax_amount=%s WHERE id=%s "",("%0.2f"%(t.amount_currency * rate_tmp), t.id))
							
							linea_act.tax_amount = float_round(value=float(t.amount_currency * rate_tmp) , precision_rounding=2)
							#linea_act.tax_amount = t.amount_currency * rate_tmp
							print "linea 2",linea_act.tax_amount
					else:
						print "antes",t.amount_currency * rate_tmp * -1
						linea_act =self.env['account.move.line'].search([('id','=',t.id)])[0]
						tmp_linea= t.amount_currency * rate_tmp* -1
						linea_act.credit = float_round( value=float(tmp_linea), precision_rounding=2)
							
						print "linea 3",linea_act.credit

						#self._cr.execute("" UPDATE account_move_line SET credit=%s WHERE id=%s "",("%0.2f"%(t.amount_currency * rate_tmp * -1), t.id))
						
						if t.tax_amount > 0:
							#self._cr.execute("" UPDATE account_move_line SET tax_amount=%s WHERE id=%s "",("%0.2f"%(t.amount_currency * rate_tmp * -1), t.id))
							linea_act.tax_amount = float_round(value=float(t.amount_currency * rate_tmp* -1) , precision_rounding=2)
							print "linea 4",linea_act.tax_amount

			linea__mov_act.button_validate()
			"""
		t = super(account_invoice,self).action_number()
		return t

	def invoice_pay_customer(self, cr, uid, ids, context=None):
		t = super(account_invoice,self).invoice_pay_customer(cr, uid, ids, context)
		print "confe"
		if not ids: return []
		inv = self.browse(cr, uid, ids[0], context=context)	
		rate_tmp = inv.currency_rate_auto
		if inv.currency_rate_mod != 0:
			rate_tmp= inv.currency_rate_mod
		t['context']['currency_rate_it'] = rate_tmp
		return t


class account_voucher(models.Model):
	_inherit= 'account.voucher'

	@api.multi
	def proforma_voucher(self):
		t = super(account_voucher,self).proforma_voucher()
		if self.move_id:
			tt = self.env['main.parameter'].search([])[0]
			print "------------ esta fregado"
			print self.date
			oml = self.env['res.currency.rate'].search([ ('currency_id','=',tt.currency_id.id),('name','=',self.date) ])
			tipocambio = 0
			if len(oml)> 0:
				tipocambio = oml[0].type_sale

			for i in self.move_id.line_id:
				i.currency_rate_it = tipocambio
		return t