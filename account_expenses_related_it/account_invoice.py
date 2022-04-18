# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	gastovinculado_name= fields.Char('name_vinculado',size=200)

	@api.one
	def flag_check(self):
		if self.expense_related_id:
			self.flag_expense_related=True
		else:
			self.flag_expense_related=False


	expense_related_id = fields.Many2one('account.expense.related', string="Gastos Vinculado")
	flag_expense_related = fields.Boolean('flag',compute="flag_check")

	_defaults = {
	"flag_expense_related" : False,
	}

	
	@api.multi
	def redirec_expente_related(self):
		if self.expense_related_id:
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			view_ref = mod_obj.get_object_reference('account', 'invoice_supplier_form')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )
			res= {
				"type": "ir.actions.act_window",
				"res_model": "account.expense.related",
				"view_type": "form",
				"view_mode": "form",
				"target": "current",
				"res_id": self.expense_related_id.id,
			}
			print res
			return res




	@api.multi
	def create_expente_related(self):
		valor_ammount= self.amount_untaxed
		if self.currency_id.name == "USD":
			cambio_moneda = 0
			if self.currency_rate_auto != 0:
				cambio_moneda = self.currency_rate_auto
			if self.currency_rate_mod != 0:
				cambio_moneda = self.currency_rate_mod
			if cambio_moneda ==0:
				raise osv.except_osv( 'Alerta!', "El Cambio de Moneda No esta configurado (No esta configurado la Moneda para la Fecha, o la factura no fue Validada")	
			valor_ammount = valor_ammount * cambio_moneda

		name_vinculado_tmp = ""
		if self.gastovinculado_name:
			name_vinculado_tmp = self.gastovinculado_name
		else:
			obj_seq_vincu = self.env['main.parameter'].search([])[0].sequence_gvinculado
			if obj_seq_vincu:
				name_vinculado_tmp = self.env['ir.sequence'].next_by_id(obj_seq_vincu.id)
				self.write({'gastovinculado_name':name_vinculado_tmp})
				self.gastovinculado_name = name_vinculado_tmp
			else:
				raise osv.except_osv( 'Alerta!', "Gastos Vinculado no tiene configurado una Secuencia")	
			 

		expense_related = {
			'period_id': self.period_id.id,
			'date': self.date_invoice,
			'partner_id': self.partner_id.id,
			'currency_id': self.currency_id.id,
			'journal_id':self.journal_id.id,
			'invoice_id':self.id,
			'state':  'draft',
			'amount_untaxed' : valor_ammount,
			'type_document_id': self.type_document_id.id,
			'nro_comprobante': self.supplier_invoice_number,
			'name': name_vinculado_tmp,
		}
			
		t =self.env['account.expense.related'].create(expense_related)
		self.expense_related_id = t.id
		
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		view_ref = mod_obj.get_object_reference('account', 'invoice_supplier_form')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		res= {
			"type": "ir.actions.act_window",
			"res_model": "account.expense.related",
			"view_type": "form",
			"view_mode": "form",
			"target": "current",
			"res_id": t.id,
		}
		print res
		return res



	@api.one
	@api.v8
	def unlink(self):
		if self.expense_related_id:
			raise osv.except_osv( 'Alerta!', "No se puede elimnar con un Gasto Vinculado Existente")
		else:
			return super(account_invoice,self).unlink()
