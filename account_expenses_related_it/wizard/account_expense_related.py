# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
class account_expense_related(models.Model):
	_name = 'account.expense.related'


	period_id = fields.Many2one('account.period', string='Periodo' ,required=False)
	date = fields.Date('Fecha',required=False)
	partner_id = fields.Many2one('res.partner', string='Proveedor',domain="[('supplier','=',True)]",required=False)
	currency_id = fields.Many2one('res.currency',string='Moneda',required=False)
	total_weight = fields.Float('Peso Total', digits=(12,2),required=False)
	amount_untaxed = fields.Float('Monto a Prorratear', digits=(12,2),required=False)
	invoice_id = fields.Many2one('account.invoice',string='Factura',required=False)
	lines_id = fields.One2many('account.expense.related.line','expense_related_id',string='Facturas',required=False)
	name = fields.Char('Nombre',size=50)
	state = fields.Selection([('draft','Borrador'), ('closed','Asentado')], 'Estado', copy=False,required=False)
	type_document_id = fields.Many2one('it.type.document',string='Tipo de Documento')
	nro_comprobante = fields.Char('Número de Comprobante')

	_defaults = {
	'state':'draft',
	'name':'Gasto Vinculado'
	}

	@api.one
	@api.v8
	def calculate(self):

		if self.invoice_id.currency_id.name == "USD":
			cambio_moneda = 0
			if self.invoice_id.currency_rate_auto != 0:
				cambio_moneda = self.invoice_id.currency_rate_auto
			if self.invoice_id.currency_rate_mod != 0:
				cambio_moneda = self.invoice_id.currency_rate_mod
			if cambio_moneda==0:
				raise osv.except_osv( 'Alerta!', "El Cambio de Moneda No esta configurado (No esta configurado la Moneda para la Fecha, o la factura no fue Validada")	
			self.amount_untaxed = self.invoice_id.amount_untaxed * cambio_moneda
		pesoT = self.total_weight
		tmp = 0
		for i in self.lines_id:
			tmp+= i.amount
		if pesoT != tmp:
			raise osv.except_osv( 'Alerta!', "Las cantidades en las Lineas no suman el Peso Total Configurado")
		if pesoT == 0:
			raise osv.except_osv( 'Alerta!', "No se puede realizar un Gasto Vinculado con Peso Total Cero")
		if self.amount_untaxed == 0:
			raise osv.except_osv( 'Alerta!', "No se puede realizar un Gasto Vinculado con Monto a Prorratear Cero")

		prorrateo_acum = 0
		equivalence_acum = 0
		for i in self.lines_id:
			if i == self.lines_id[len(self.lines_id)-1]:
				i.prorrateo = 1 - prorrateo_acum
				i.equivalence = self.amount_untaxed - equivalence_acum
			else:
				i.prorrateo = float(i.amount)/pesoT
				i.equivalence = i.prorrateo * self.amount_untaxed

			prorrateo_acum += i.prorrateo
			equivalence_acum += i.equivalence
		return True

	@api.multi
	@api.v8
	def factura_show(self):
		if self.invoice_id:
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			view_ref = mod_obj.get_object_reference('account', 'invoice_supplier_form')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )
			res= {
				"type": "ir.actions.act_window",
				"res_model": "account.invoice",
				"view_type": "form",
				"view_mode": "form",
				"target": "current",
				"res_id": self.invoice_id.id,
			}

			print res
			return res
		

class account_expense_related_line(models.Model):
	_name = 'account.expense.related.line'

	expense_related_id = fields.Many2one('account.expense.related', string='ID')
	invoice_id = fields.Many2one('account.invoice', domain="[('type','=','in_invoice'),('state','in',('open','paid'))]",string='Facturas')
	partner_id = fields.Many2one('res.partner', domain="[('supplier','=',True)]",string='Proveedor')
	location_id = fields.Many2one('stock.location',string='Almacén destino')
	product_id = fields.Many2one('product.product',string='Producto', required=False)
	amount = fields.Float('Cantidad', digits=(12,2))
	prorrateo = fields.Float('Prorrateo', digits=(12,6))
	equivalence = fields.Float('Equivalente', digits=(12,2))
