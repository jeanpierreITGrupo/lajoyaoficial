# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv


class egreso_trabajador(models.Model):
	_name = 'egreso.trabajador'

	name = fields.Char(required=True, string="Concepto",size=100)
	cta_soles = fields.Many2one('account.account', string="Cta. Soles")
	cta_dolares = fields.Many2one('account.account', string="Cta. Dolares")

class desembolso_personal(models.Model):
	_name = 'desembolso.personal'

	@api.one
	def saldo_deuda_calculate(self):
		ele = self
		rpta = 0
		for i in self.env['account.move.line'].search([('partner_id','=',self.personal.id),('nro_comprobante','=',self.name)]):
			if self.caja_banco.currency.id: 
				rpta += i.amount_currency
			else:
				rpta += i.debit
				rpta -= i.credit

		ele.saldo_deuda = rpta

	@api.one
	def saldo_pagado_calculate(self):
		self.saldo_pagado = self.monto_entregado - self.saldo_deuda

	@api.one
	def desembolso_line_calculate(self):
		ele = self
		rpta = []		
		rpta2 = []
		if self.move_id.id:
			ttt =self.env['account.move.line'].search([('partner_id','=',self.personal.id),('nro_comprobante','=',self.name),('move_id','=',self.move_id.id)])[0]
			rpta.append(ttt.id)
		for i in self.env['account.move.line'].search([('partner_id','=',self.personal.id),('nro_comprobante','=',self.name),('move_id','!=',self.move_id.id)]).sorted(key=lambda r: r.date):
			rpta2.append(i.id)
		ele.desembolso_lines = (rpta2[::-1] + rpta)[::-1]


	name = fields.Char('Nombre',size=200)
	state = fields.Selection([('draft','Borrador'), ('done','Entregado'), ('cancel','Cancelado')], 'Estado', readonly=True, copy=False, default='draft')
	tipo_egreso = fields.Many2one('egreso.trabajador','Tipo de Egreso')
	fecha_entrega = fields.Date('Fecha de Entrega')
	personal = fields.Many2one('res.partner', domain="[('employee','=',True)]",string='Personal')
	caja_banco = fields.Many2one('account.journal','Caja o Banco', domain="[('type','=',['cash','bank'])]")
	medio_pago = fields.Many2one('it.means.payment','Medio de Pago')
	comprobante_nro= fields.Char('Comprobante Nro.',size=200,copy=False)
	memoria = fields.Char('Memoria',size=200)
	fecha_ven = fields.Date('Fecha Vencimiento')
	monto_entregado = fields.Float('Monto Entregado', digits=(12,2))
	saldo_deuda = fields.Float('Saldo Deuda',digits=(12,2),compute='saldo_deuda_calculate')
	saldo_pagado = fields.Float('Saldo Pagado', digits=(12,2),compute='saldo_pagado_calculate')
	desembolso_lines = fields.Many2many('account.move.line','Lineas Desembolso',compute='desembolso_line_calculate', readonly="1")
	periodo_id = fields.Many2one('account.period','Periodo')
	move_id = fields.Many2one('account.move','Asiento', copy=False)


	@api.one
	def unlink(self):
		if len(self.desembolso_lines)>0:
			raise osv.except_osv('Alerta!', 'No puede eliminar este Desembolso porque existen Lineas referenciadas al mismo.')
		return super(desembolso_personal,self).unlink()

	@api.one
	def write(self,vals):
		fechita = None

		if 'fecha_entrega' in vals:
			fechita = vals['fecha_entrega']
		else:
			fechita = self.fecha_entrega

		periodo = self.env['account.period'].search([('code','=', str( fechita[5:7])+'/'+ str( fechita[:4])  )])
		if not periodo:
			raise osv.except_osv('Alerta!','No existe el periodo para esta fecha.')
		vals['periodo_id'] = periodo.id
		return super(desembolso_personal,self).write(vals)

	@api.model
	def create(self,vals):
		if 'fecha_entrega' in vals:
			periodo = self.env['account.period'].search([('code','=', str(vals['fecha_entrega'][5:7])+'/'+ str(vals['fecha_entrega'][:4])  )])
			if not periodo:
				raise osv.except_osv('Alerta!','No existe el periodo para esta fecha.')
			vals['periodo_id'] = periodo.id

		t = super(desembolso_personal,self).create(vals)
		if self.env['main.parameter'].search([])[0].sequence_desembolso_personal.id:
			secuencia_name = self.env['ir.sequence'].next_by_id( self.env['main.parameter'].search([])[0].sequence_desembolso_personal.id)
			t.name = secuencia_name
		else:
			raise osv.except_osv('Alerta!', 'Falta consigurar la secuencia para el Desembolso Personal')
		return t


	@api.multi
	def entregar_button(self):
		l1 = l2 = {}
		if self.caja_banco.currency.id:
			if not len(self.env['res.currency.rate'].search([('name','=',self.fecha_entrega),('currency_id','=',self.caja_banco.currency.id)])) >0:
				raise osv.except_osv('Alerta!','No existe tipo de cambio para la fecha colocada')
			tipo_cambio = self.env['res.currency.rate'].search([('name','=',self.fecha_entrega),('currency_id','=',self.caja_banco.currency.id)])[0].type_sale

			if not self.tipo_egreso.cta_dolares.id:
				raise osv.except_osv('Alerta!','No existe configurado la cuenta en Dolares.')
			l1 = {
				'name': self.memoria,
				'debit': float( "%0.2f"%(self.monto_entregado * tipo_cambio)),
				'credit': 0,
				'nro_comprobante': self.name,
				'account_id': self.tipo_egreso.cta_dolares.id,
				'partner_id': self.personal.id,
				'date': self.fecha_entrega,
				'date_maturity': self.fecha_ven,
				'currency_id': self.caja_banco.currency.id,
				'amount_currency': float( "%0.2f"%self.monto_entregado),
				'currency_rate_it': tipo_cambio,
			}

			l2 = {
				'name': self.memoria,
				'debit': 0,
				'credit': float( "%0.2f"%(self.monto_entregado * tipo_cambio)),
				'nro_comprobante': self.comprobante_nro,
				'account_id': self.caja_banco.default_debit_account_id.id,
				'partner_id': self.personal.id,
				'date': self.fecha_entrega,
				'currency_id': self.caja_banco.currency.id,
				'amount_currency': float( "%0.2f"%(-self.monto_entregado)),
				'currency_rate_it': tipo_cambio,
			}
		else:
			l1 = {
				'name': self.memoria,
				'debit': float( "%0.2f"%(self.monto_entregado )),
				'credit': 0,
				'nro_comprobante': self.name,
				'account_id': self.tipo_egreso.cta_soles.id,
				'partner_id': self.personal.id,
				'date': self.fecha_entrega,
				'date_maturity': self.fecha_ven,
			}

			l2 = {
				'name': self.memoria,
				'debit': 0,
				'credit': float( "%0.2f"%(self.monto_entregado )),
				'nro_comprobante': self.comprobante_nro,
				'account_id': self.caja_banco.default_debit_account_id.id,
				'partner_id': self.personal.id,
				'date': self.fecha_entrega,
			}

		periodo = self.env['account.period'].search([('code','=', str(self.fecha_entrega[5:7])+'/'+ str(self.fecha_entrega[:4])  )])
		if not periodo:
			raise osv.except_osv('Alerta!','No existe el periodo para esta fecha.')

		move = self.env['account.move'].create({
			'ref': self.comprobante_nro,
			'line_id': [(0, 0, l2), (0, 0, l1)],
			'journal_id': self.caja_banco.id,
			'period_id': periodo[0].id,
			'date': self.fecha_entrega,
		})

		self.move_id = move
		self.state='done'



	@api.multi
	def cancelar_button(self):
		self.state='cancel'
		if self.move_id.state=='posted':
			self.move_id.button_cancel()

		self.move_id.unlink()


	@api.multi
	def borrador_button(self):
		self.state='draft'


	@api.multi
	def pagar_button(self):
		return {
			'name': 'Desembolso Personal Pago',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'desembolso.personal.wizard',
			'views': [(False, 'form')],
			'target': 'new',
			'context': {'desembolso_id':self.id},
		}

	@api.multi
	def conciliacion_button(self):
		ids_lines = []
		for i in self.desembolso_lines:
			ids_lines.append(i.id)
		return {
			'name':'Conciliación',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.move.line.reconcile',
			'views': [(False, 'form')],
			'target': 'new',
			'context': {'active_ids':ids_lines},
		}


	@api.multi
	def desconciliacion_button(self):
		ids_lines = []
		for i in self.desembolso_lines:
			ids_lines.append(i.id)
		return {
			'name':'Conciliación',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.unreconcile',
			'views': [(False, 'form')],
			'target': 'new',
			'context': {'active_ids':ids_lines},
		}



class desembolso_personal_wizard(models.Model):
	_name ='desembolso.personal.wizard'

	fecha = fields.Date('Fecha')
	metodo_pago = fields.Many2one('account.journal','Caja o Banco', domain="[('type','=',['cash','bank'])]")
	medio_pago = fields.Many2one('it.means.payment','Medio de Pago')

	monto = fields.Float('Monto',digits=(12,2))
	memoria = fields.Char('Memoria',size=200)
	flujo_efectivo = fields.Many2one('account.config.efective','Flujo de Efectivo')

	@api.multi
	def do_rebuild(self):
		padre = self.env['desembolso.personal'].search([('id','=',self.env.context['desembolso_id'])])[0]

		l1 = l2 = {}
		if self.metodo_pago.currency.id:
			if not len(self.env['res.currency.rate'].search([('name','=',self.fecha),('currency_id','=',self.metodo_pago.currency.id)])) >0:
				raise osv.except_osv('Alerta!','No existe tipo de cambio para la fecha colocada')
			tipo_cambio = self.env['res.currency.rate'].search([('name','=',self.fecha),('currency_id','=',self.metodo_pago.currency.id)])[0].type_sale

			if not padre.tipo_egreso.cta_dolares.id:
				raise osv.except_osv('Alerta!','No existe configurado la cuenta en Dolares.')
			l1 = {
				'name': self.memoria,
				'debit': 0,
				'credit': float( "%0.2f"%(self.monto * tipo_cambio)),
				'nro_comprobante': padre.name,
				'account_id': padre.tipo_egreso.cta_dolares.id,
				'partner_id': padre.personal.id,
				'date': self.fecha,
				'currency_id': self.metodo_pago.currency.id,
				'amount_currency': -float( "%0.2f"%self.monto),
				'means_payment_id':self.medio_pago.id,
				'fefectivo_id': self.flujo_efectivo.id,
				'currency_rate_it': tipo_cambio,
			}

			l2 = {
				'name': self.memoria,
				'debit': float( "%0.2f"%(self.monto * tipo_cambio)),
				'credit': 0,
				'nro_comprobante': padre.comprobante_nro, 
				'account_id': self.metodo_pago.default_debit_account_id.id,
				'partner_id': padre.personal.id,
				'date': self.fecha,
				'currency_id': self.metodo_pago.currency.id,
				'amount_currency': float( "%0.2f"%(self.monto)),
				'currency_rate_it': tipo_cambio,
			}
		elif padre.caja_banco.currency.id:
			if not len(self.env['res.currency.rate'].search([('name','=',self.fecha),('currency_id','=',padre.caja_banco.currency.id)])) >0:
				raise osv.except_osv('Alerta!','No existe tipo de cambio para la fecha colocada')

			if self.env['res.currency.rate'].search([('name','=',self.fecha),('currency_id','=',padre.caja_banco.currency.id)])[0].type_sale == 0:
				raise osv.except_osv('Alerta!','Tipo de Cambio igual a Cero no es permitido')
			tipo_cambio = self.env['res.currency.rate'].search([('name','=',self.fecha),('currency_id','=',padre.caja_banco.currency.id)])[0].type_sale

			if not padre.tipo_egreso.cta_dolares.id:
				raise osv.except_osv('Alerta!','No existe configurado la cuenta en Dolares.')
			l1 = {
				'name': self.memoria,
				'debit': 0,
				'credit': float( "%0.2f"%(self.monto)),
				'nro_comprobante': padre.name,
				'account_id': padre.tipo_egreso.cta_dolares.id,
				'partner_id': padre.personal.id,
				'date': self.fecha,
				'currency_id': padre.caja_banco.currency.id,
				'amount_currency': -float( "%0.2f"%( float(self.monto)/tipo_cambio)),
				'means_payment_id':self.medio_pago.id,
				'fefectivo_id': self.flujo_efectivo.id,
				'currency_rate_it': tipo_cambio,
			}

			l2 = {
				'name': self.memoria,
				'debit': float( "%0.2f"%(self.monto)),
				'credit': 0,
				'nro_comprobante': padre.comprobante_nro, 
				'account_id': self.metodo_pago.default_debit_account_id.id,
				'partner_id': padre.personal.id,
				'date': self.fecha,
				'currency_id': padre.caja_banco.currency.id,
				'amount_currency': float( "%0.2f"%( float(self.monto)/tipo_cambio)),
				'currency_rate_it': tipo_cambio,
			}

		else:
			l1 = {
				'name': self.memoria,
				'debit': 0,
				'credit': float( "%0.2f"%(self.monto )),
				'nro_comprobante': padre.name,
				'account_id': padre.tipo_egreso.cta_soles.id,
				'partner_id': padre.personal.id,
				'date': self.fecha,
				'means_payment_id':self.medio_pago.id,
				'fefectivo_id': self.flujo_efectivo.id,
			}

			l2 = {
				'name': self.memoria,
				'debit': float( "%0.2f"%(self.monto)),
				'credit': 0,
				'nro_comprobante': padre.comprobante_nro, 
				'account_id': self.metodo_pago.default_debit_account_id.id,
				'partner_id': padre.personal.id,
				'date': self.fecha,
			}

		periodo = self.env['account.period'].search([('code','=', str(self.fecha[5:7])+'/'+ str(self.fecha[:4])  )])
		if not periodo:
			raise osv.except_osv('Alerta!','No existe el periodo para esta fecha.')

		move = self.env['account.move'].create({
			'ref': padre.name,
			'line_id': [(0, 0, l1), (0, 0, l2)],
			'journal_id': self.metodo_pago.id,
			'period_id': periodo[0].id,
			'date': self.fecha,
		})
		if move.state=='draft':
			move.button_validate()

		return move

class main_parameter(models.Model):
	_inherit = 'main.parameter'

	sequence_desembolso_personal = fields.Many2one('ir.sequence','Secuencia de Desembolso Personal')

