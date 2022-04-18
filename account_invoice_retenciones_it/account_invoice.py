# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv


class main_parameter(models.Model):
	_inherit = 'main.parameter'
	
	account_retenciones = fields.Many2one('account.account','Cuenta para Retenciones')
	diario_retenciones = fields.Many2one('account.journal','Diario para Retenciones')



class res_partner(models.Model):
	_inherit = 'res.partner'

	porcentaje_ret = fields.Float('Porcentaje Retención')

class create_retencion(models.Model):
	_name = 'create.retencion'

	fecha = fields.Date('Fecha')
	monto = fields.Float('Monto',digits=(12,2))

	@api.multi
	def generar(self):
		invoice = self.env['account.invoice'].search( [('id','=',self.env.context['invoice_id'])])[0]

		m = self.env['main.parameter'].search([])[0]
		if not m.diario_retenciones.id:
			raise osv.except_osv('Alerta!', "No esta configurada el diario de Retención en Parametros.")
		if not m.account_retenciones.id:
			raise osv.except_osv('Alerta!', "No esta configurada la cuenta de Retención en Parametros.")


		periodo_fecha_list = self.env['account.period'].search([('date_start','<=',self.fecha),('date_stop','>=',self.fecha)])

		periodo_fecha_fin = False
		for aol in periodo_fecha_list:
			if '00/' in aol.code:
				pass
			else:
				periodo_fecha_fin = aol

		if not periodo_fecha_fin:
			raise osv.except_osv('Alerta!','No se encuentra el periodo.')
		flag_ver = True
		data = {
			'journal_id': m.diario_retenciones.id,
			'ref':(invoice.number if invoice.number else 'Borrador'),
			'period_id': periodo_fecha_fin.id,
			'date': self.fecha,
		}
		if invoice.name_move_retencion and invoice.diario_move_retencion.id == m.diario_retenciones.id and invoice.periodo_move_retencion.id == invoice.period_id.id:
			data['name']= invoice.name_move_retencion
			flag_ver = False
		else:
			invoice.diario_move_retencion= m.diario_retenciones.id
			invoice.periodo_move_retencion = invoice.period_id.id
			flag_ver = True
		lines = []

		if invoice.currency_id.name == 'USD':

			line_cc = (0,0,{
				'account_id': invoice.account_id.id,
				'debit': self.monto * invoice.currency_rate_auto,
				'credit':0,
				'name':'PROVISION DE LA RETENCION',
				'partner_id': invoice.partner_id.id,
				'nro_comprobante': invoice.supplier_invoice_number,
				'type_document_id': invoice.type_document_id.id,
				'amount_currency': self.monto,
				'currency_rate_it': invoice.currency_rate_auto,
				'currency_id': invoice.currency_id.id,				
				})
			lines.append(line_cc)

			line_cc = (0,0,{
				'account_id': m.account_retenciones.id ,
				'debit': 0,
				'credit':self.monto * invoice.currency_rate_auto,
				'name':'PROVISION DE LA RETENCION',
				'partner_id': invoice.partner_id.id,
				'nro_comprobante': invoice.supplier_invoice_number,
				'currency_rate_it': invoice.currency_rate_auto,
				'type_document_id': invoice.type_document_id.id,
				})
			lines.append(line_cc)

		else:
			line_cc = (0,0,{
				'account_id': invoice.account_id.id,
				'debit': self.monto,
				'credit':0,
				'name':'PROVISION DE LA RETENCION',
				'partner_id': invoice.partner_id.id,
				'nro_comprobante': invoice.supplier_invoice_number,
				'type_document_id': invoice.type_document_id.id,
				})
			lines.append(line_cc)

			line_cc = (0,0,{
				'account_id': m.account_retenciones.id ,
				'debit': 0,
				'credit':self.monto,
				'name':'PROVISION DE LA RETENCION',
				'partner_id': invoice.partner_id.id,
				'nro_comprobante': invoice.supplier_invoice_number,
				'type_document_id': invoice.type_document_id.id,
				})
			lines.append(line_cc)


		data['line_id'] = lines
		tt = self.env['account.move'].create(data)
		if tt.state =='draft':
			tt.button_validate()
		invoice.move_retencion_id = tt.id

		if flag_ver:
			invoice.name_move_retencion = tt.name

		vals_data = {}
		ids_conciliar = []
		for i1 in tt.line_id:
			if i1.debit >0:
				ids_conciliar.append(i1.id)

		for i2 in invoice.move_id.line_id:
			if i2.account_id.id == invoice.account_id.id:
				ids_conciliar.append(i2.id)

		concile_move = self.with_context({'active_ids':ids_conciliar}).env['account.move.line.reconcile'].create(vals_data)
		concile_move.trans_rec_reconcile_partial_reconcile()

		self.env.cr.execute("""update account_invoice set sujeto_a_retencion = true where id =  """ + str(invoice.id) )
		self.env.cr.execute("""update account_move set sujeto_a_retencion = true where id =  """ + str(invoice.move_id.id) )
		return True




class account_invoice(models.Model):
	_inherit = 'account.invoice'

	name_move_retencion = fields.Char('nombre retencion')
	diario_move_retencion = fields.Many2one('account.journal','nombre diario')
	periodo_move_retencion = fields.Many2one('account.period','Periodo')


	@api.one
	def get_estado_buttom_retencion(self):
		if self.state in ('open','paid'):
			if self.move_retencion_id.id:
				self.ver_estado_buttom_retencion= 1
			else:
				self.ver_estado_buttom_retencion= 2
		else:
			self.ver_estado_buttom_retencion= 3


	move_retencion_id = fields.Many2one('account.move','Asiento Retención',copy=False)
	
	ver_estado_buttom_retencion = fields.Integer('ver estado distrib', compute='get_estado_buttom_retencion')

	@api.multi
	def action_cancel(self):

		vals_data = {}
		ids_conciliar = []
		for i1 in self.move_retencion_id.line_id:
			if i1.debit >0:
				ids_conciliar.append(i1.id)
		"""
		for i2 in self.move_id.line_id:
			if i2.account_id.id == self.account_id.id:
				ids_conciliar.append(i2.id)
		"""
		concile_move = self.with_context({'active_ids':ids_conciliar}).env['account.unreconcile'].create(vals_data)
		concile_move.trans_unrec()


		if self.move_retencion_id.id:
			if self.move_retencion_id.state != 'draft':
				self.move_retencion_id.button_cancel()
			self.move_retencion_id.unlink()
		return super(account_invoice,self).action_cancel()


	@api.multi
	def remove_retencion_gastos(self):

		vals_data = {}
		ids_conciliar = []
		for i1 in self.move_retencion_id.line_id:
			if i1.debit >0:
				ids_conciliar.append(i1.id)
		"""
		for i2 in self.move_id.line_id:
			if i2.account_id.id == self.account_id.id:
				ids_conciliar.append(i2.id)
		"""
		concile_move = self.with_context({'active_ids':ids_conciliar}).env['account.unreconcile'].create(vals_data)
		concile_move.trans_unrec()


		if self.move_retencion_id.id:
			if self.move_retencion_id.state != 'draft':
				self.move_retencion_id.button_cancel()
			self.move_retencion_id.unlink()
		return True

	@api.multi
	def create_retencion_gastos(self):

		context = {'invoice_id': self.id,'default_fecha': self.date_invoice ,'default_monto':self.amount_total * float(self.partner_id.porcentaje_ret)/100.0}
		return {
				'type': 'ir.actions.act_window',
				'name': "Generar Retención",
				'view_type': 'form',
				'view_mode': 'form',
				'context': context,
				'res_model': 'create.retencion',
				'target': 'new',
		}


