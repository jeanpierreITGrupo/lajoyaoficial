# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	optative_ple = fields.Boolean('Anotación optativa para PLE')


	dec_reg_type_document_id = fields.Many2one('it.type.document', string="Tipo de Documento",ondelete='restrict')
	dec_reg_nro_comprobante = fields.Char('Comprobante', size=30)
	dec_mod_type_document_id = fields.Many2one('it.type.document', string="Tipo de Documento",ondelete='restrict')
	dec_mod_nro_comprobante = fields.Char('Comprobante', size=30)
	
	com_det_date = fields.Date('Fecha')
	com_det_amount =fields.Float('Monto', digits=(12,2))
	com_det_number = fields.Char('Número', size=50)
	com_det_date_maturity = fields.Date('Fecha Vencimiento')
	com_det_type_change = fields.Float('Tipo de Cambio', digits=(16,3))
	com_det_currency = fields.Many2one('res.currency', string="Moneda")


	@api.model
	def create(self,vals):
		t = super(account_invoice,self).create(vals)
		if t.payment_term.id and t.date_invoice:
			elem = t.onchange_payment_term_date_invoice(t.payment_term.id,t.date_invoice)['value']['date_due']
			self._cr.execute(""" UPDATE account_invoice SET date_due=%s WHERE id=%s """,( elem, t.id))
		return t

	@api.one
	def write(self,vals):
		t = super(account_invoice,self).write(vals)
		self.refresh()
		if self.payment_term.id and self.date_invoice:
			elem = self.onchange_payment_term_date_invoice(self.payment_term.id,self.date_invoice)['value']['date_due']
			self._cr.execute(""" UPDATE account_invoice SET date_due=%s WHERE id=%s """,( elem, self.id))

		for inv in self:
			if inv.move_id.id:
				j = inv.optative_ple
				if j:
					j= 'true'
				else:
					j= 'false'
				self._cr.execute(""" UPDATE account_move SET optative_ple=%s WHERE id=%s """,( j, inv.move_id.id))

				if inv.code_operation:
					self._cr.execute(""" UPDATE account_move SET com_det_code_operation=%s WHERE id=%s """,(inv.code_operation, inv.move_id.id))
				if inv.date:
					self._cr.execute(""" UPDATE account_move SET com_det_date=%s WHERE id=%s """,(inv.date, inv.move_id.id))
				if inv.amount:
					self._cr.execute(""" UPDATE account_move SET com_det_amount=%s WHERE id=%s """,(inv.amount, inv.move_id.id))
				if inv.voucher_number:
					self._cr.execute(""" UPDATE account_move SET com_det_number=%s WHERE id=%s """,(inv.voucher_number, inv.move_id.id))
				
				if inv.currency_rate_mod:
					self._cr.execute(""" UPDATE account_move SET com_det_type_change=%s WHERE id=%s """,(inv.currency_rate_mod, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET com_det_type_change=%s WHERE id=%s """,(inv.currency_rate_auto, inv.move_id.id))
				if inv.currency_id:
					self._cr.execute(""" UPDATE account_move SET com_det_currency=%s WHERE id=%s """,(inv.currency_id.id, inv.move_id.id))
				
				if inv.type_document_id:
					self._cr.execute(""" UPDATE account_move SET dec_reg_type_document_id=%s WHERE id=%s """,(inv.type_document_id.id, inv.move_id.id))
				if inv.supplier_invoice_number:
					self._cr.execute(""" UPDATE account_move SET dec_reg_nro_comprobante=%s WHERE id=%s """,(inv.supplier_invoice_number, inv.move_id.id))
				if inv.date_due:
					self._cr.execute(""" UPDATE account_move SET com_det_date_maturity=%s WHERE id=%s """,(inv.date_due, inv.move_id.id))

				if inv.tipo_tasa_percepcion:
					self._cr.execute(""" UPDATE account_move SET dec_percep_tipo_tasa_percepcion=%s WHERE id=%s """,(inv.tipo_tasa_percepcion, inv.move_id.id))

				if inv.numero_serie:
					self._cr.execute(""" UPDATE account_move SET dec_percep_numero_serie=%s WHERE id=%s """,(inv.numero_serie, inv.move_id.id))
				if inv.account_ids:
					
					if inv.account_ids[0].tipo_doc:
						self._cr.execute(""" UPDATE account_move SET dec_mod_type_document_id=%s WHERE id=%s """,(inv.account_ids[0].tipo_doc.id, inv.move_id.id))
					if inv.account_ids[0].comprobante:
						self._cr.execute(""" UPDATE account_move SET dec_mod_nro_comprobante=%s WHERE id=%s """,(inv.account_ids[0].comprobante, inv.move_id.id))
					if inv.account_ids[0].fecha:
						self._cr.execute(""" UPDATE account_move SET dec_mod_fecha=%s WHERE id=%s """,(inv.account_ids[0].fecha, inv.move_id.id))
					if inv.account_ids[0].base_imponible:
						self._cr.execute(""" UPDATE account_move SET dec_mod_base_imponible=%s WHERE id=%s """,(inv.account_ids[0].base_imponible, inv.move_id.id))
					if inv.account_ids[0].igv:
						self._cr.execute(""" UPDATE account_move SET dec_mod_igv=%s WHERE id=%s """,(inv.account_ids[0].igv, inv.move_id.id))
					if inv.account_ids[0].perception:
						self._cr.execute(""" UPDATE account_move SET dec_mod_total=%s WHERE id=%s """,(inv.account_ids[0].perception, inv.move_id.id))			
		return t



	@api.one
	def action_number(self):
		t = super(account_invoice,self).action_number()
		self.write({})

		data = 0.0
		
		if self.type == 'in_invoice':
			rpt_optative=0
			for i in self.invoice_line:
				for j in i.invoice_line_tax_id:
					if j.tax_code_id:
						if (j.tax_code_id.record_shop== '4' or j.tax_code_id.record_shop=='6') and rpt_optative <=0:
							rpt_optative=-1
						else:
							rpt_optative=1

			rpt_fin_optative = True if rpt_optative ==-1 else False
			self.optative_ple = rpt_fin_optative
			self.write({'optative_ple': rpt_fin_optative})

		for inv in self:
			tmp_divisa = self.env['res.currency'].search([('name','=','USD')])[0]
			for i in tmp_divisa.rate_ids:
				if str(i.date_sunat)[:10] == str(self.date_invoice)[:10]:
					data = i.type_sale
			self.write({'currency_rate_auto': data})

		for inv in self:
			j = inv.optative_ple
			if j:
				j= 'true'
			else:
				j= 'false'
			self._cr.execute(""" UPDATE account_move SET optative_ple=%s WHERE id=%s """,( j, inv.move_id.id))

			if inv.code_operation:
				self._cr.execute(""" UPDATE account_move SET com_det_code_operation=%s WHERE id=%s """,(inv.code_operation, inv.move_id.id))
			if inv.date:
				self._cr.execute(""" UPDATE account_move SET com_det_date=%s WHERE id=%s """,(inv.date, inv.move_id.id))
			if inv.amount:
				self._cr.execute(""" UPDATE account_move SET com_det_amount=%s WHERE id=%s """,(inv.amount, inv.move_id.id))
			if inv.voucher_number:
				self._cr.execute(""" UPDATE account_move SET com_det_number=%s WHERE id=%s """,(inv.voucher_number, inv.move_id.id))
			
			if inv.currency_rate_mod:
				self._cr.execute(""" UPDATE account_move SET com_det_type_change=%s WHERE id=%s """,(inv.currency_rate_mod, inv.move_id.id))
			else:
				self._cr.execute(""" UPDATE account_move SET com_det_type_change=%s WHERE id=%s """,(inv.currency_rate_auto, inv.move_id.id))
			if inv.currency_id:
				self._cr.execute(""" UPDATE account_move SET com_det_currency=%s WHERE id=%s """,(inv.currency_id.id, inv.move_id.id))
			
			if inv.type_document_id:
				self._cr.execute(""" UPDATE account_move SET dec_reg_type_document_id=%s WHERE id=%s """,(inv.type_document_id.id, inv.move_id.id))
			if inv.supplier_invoice_number:
				self._cr.execute(""" UPDATE account_move SET dec_reg_nro_comprobante=%s WHERE id=%s """,(inv.supplier_invoice_number, inv.move_id.id))
			if inv.date_due:
				self._cr.execute(""" UPDATE account_move SET com_det_date_maturity=%s WHERE id=%s """,(inv.date_due, inv.move_id.id))
			
			if inv.tipo_tasa_percepcion:
				self._cr.execute(""" UPDATE account_move SET dec_percep_tipo_tasa_percepcion=%s WHERE id=%s """,(inv.tipo_tasa_percepcion, inv.move_id.id))

			if inv.numero_serie:
				self._cr.execute(""" UPDATE account_move SET dec_percep_numero_serie=%s WHERE id=%s """,(inv.numero_serie, inv.move_id.id))
			if inv.account_ids:
				
				if inv.account_ids[0].tipo_doc:
					self._cr.execute(""" UPDATE account_move SET dec_mod_type_document_id=%s WHERE id=%s """,(inv.account_ids[0].tipo_doc.id, inv.move_id.id))
				if inv.account_ids[0].comprobante:
					self._cr.execute(""" UPDATE account_move SET dec_mod_nro_comprobante=%s WHERE id=%s """,(inv.account_ids[0].comprobante, inv.move_id.id))
				if inv.account_ids[0].fecha:
					self._cr.execute(""" UPDATE account_move SET dec_mod_fecha=%s WHERE id=%s """,(inv.account_ids[0].fecha, inv.move_id.id))
			
			
		return t


	def invoice_pay_customer(self, cr, uid, ids, context=None):
		t = super(account_invoice,self).invoice_pay_customer(cr, uid, ids, context)

		if not ids: return []
		inv = self.browse(cr, uid, ids[0], context=context)
		if inv.type_document_id:
			t['context']['type_document_id'] = inv.type_document_id.id
		if inv.supplier_invoice_number:
			t['context']['nro_comprobante'] = inv.supplier_invoice_number
		return t
