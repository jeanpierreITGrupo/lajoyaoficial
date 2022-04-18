# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv


class main_parameter(models.Model):
	_inherit = 'main.parameter'

	journal_distribucion_pagos = fields.Many2one('account.journal', 'Diario de Distribución de Gastos')



class distribucion_gastos(models.Model):
	_name = 'distribucion.gastos'

	codigo = fields.Char('Código',size=2,required=True)
	descripcion = fields.Char('Descripción',size=200,required=True)
	distribucion_lines = fields.One2many('distribucion.gastos.linea','distribucion_gastos_id','Lineas de Distribución')

	_rec_name = 'codigo'

class distribucion_gastos_linea(models.Model):
	_name = 'distribucion.gastos.linea'

	distribucion_gastos_id = fields.Many2one('distribucion.gastos','Distribución Gastos')
	cuenta = fields.Many2one('account.account','Cuenta',required=True)
	porcentaje = fields.Float('Porcentaje',required=True,digits=(12,2))
	analitica = fields.Many2one('account.analytic.account','Cuenta Analítica')


class account_invoice_line(models.Model):
	_inherit='account.invoice.line'

	distribucion_gasto_id = fields.Many2one('distribucion.gastos','DIS')


class account_invoice(models.Model):
	_inherit = 'account.invoice'


	@api.one
	def get_estado_buttom_distrib(self):
		if self.state in ('open','paid'):
			if self.move_distribucion_id.id:
				self.ver_estado_buttom_distrib= 1
			else:
				self.ver_estado_buttom_distrib= 2
		else:
			self.ver_estado_buttom_distrib= 3

	move_distribucion_id = fields.Many2one('account.move','Asiento Dis. Gastos',copy=False)
	name_move_distribucion = fields.Char('Nombre Distribucion')
	diario_move_distribucion = fields.Many2one('account.journal','Diario Distribucion')
	periodo_move_distribucion = fields.Many2one('account.period', 'Periodo Distribucion')

	ver_estado_buttom_distrib = fields.Integer('ver estado distrib', compute='get_estado_buttom_distrib')

	@api.multi
	def action_cancel(self):

		if self.move_distribucion_id.id:
			if self.move_distribucion_id.state != 'draft':
				self.move_distribucion_id.button_cancel()
			self.move_distribucion_id.unlink()
		return super(account_invoice,self).action_cancel()


	@api.multi
	def remove_distribucion_gastos(self):
		if self.move_distribucion_id.id:
			if self.move_distribucion_id.state != 'draft':
				self.move_distribucion_id.button_cancel()
			self.move_distribucion_id.unlink()
		return True

	@api.multi
	def create_distribucion_gastos(self):
		m = self.env['main.parameter'].search([])[0]
		if not m.journal_distribucion_pagos.id:
			raise osv.except_osv('Alerta!', "No esta configurada el diario de Distribucion de Gastos en Parametros.")

		flag_ver = True
		data = {
			'journal_id': m.journal_distribucion_pagos.id,
			'ref':(self.number if self.number else 'Borrador'),
			'period_id': self.period_id.id,
			'date': self.date_invoice,
		}
		if self.name_move_distribucion and self.diario_move_distribucion.id == m.journal_distribucion_pagos.id and self.periodo_move_distribucion.id == self.period_id.id:
			data['name']= self.name_move_distribucion
			flag_ver = False
		else:
			self.diario_move_distribucion= m.journal_distribucion_pagos.id
			self.periodo_move_distribucion = self.period_id.id
			flag_ver = True
		lines = []

		for i in self.invoice_line:
			if i.distribucion_gasto_id.id:
				tamanio = len(i.distribucion_gasto_id.distribucion_lines)
				acum = 0
				tmp_pos = 1
				price_act = i.price_subtotal
				if self.currency_id.name == 'PEN':
					pass
				else:
					if self.currency_rate_auto != 0:
						price_act = price_act * self.currency_rate_auto
					else:
						price_act = price_act

				for j in i.distribucion_gasto_id.distribucion_lines:
					if tmp_pos == tamanio:
						line_cc = (0,0,{
							'account_id': j.cuenta.id,
							'debit': price_act - acum ,
							'credit':0,
							'name':'Distribución de Gasto',
							'analytic_account_id' : j.analitica.id,
							'nro_comprobante': self.supplier_invoice_number,
							'type_document_id': self.type_document_id.id,
							})
						lines.append(line_cc)
					else:
						line_cc = (0,0,{
							'account_id': j.cuenta.id,
							'debit': float("%0.2f"%( (float(j.porcentaje) / float(100.0))*price_act )),
							'credit':0,
							'name':'Distribución de Gasto',
							'analytic_account_id' : j.analitica.id,
							'nro_comprobante': self.supplier_invoice_number,
							'type_document_id': self.type_document_id.id,
							})
						acum += float("%0.2f"%( (float(j.porcentaje) / float(100.0))*price_act ))
						lines.append(line_cc)
						tmp_pos +=1
					print "---adentro: ",lines
				line_cc = (0,0,{
						'account_id': i.account_id.id,
						'credit': price_act,
						'debit':0,
						'name':'Distribución de Gasto',
						'nro_comprobante': self.supplier_invoice_number,
						'type_document_id': self.type_document_id.id,
					})
				lines.append(line_cc)
				
		if len(lines) == 0:
			raise osv.except_osv('Alerta!', "No hay lineas con Distribución de Gastos.")
		data['line_id'] = lines
		tt = self.env['account.move'].create(data)
		if tt.state =='draft':
			tt.button_validate()
		self.move_distribucion_id = tt.id

		if flag_ver:
			self.name_move_distribucion = tt.name
		return True