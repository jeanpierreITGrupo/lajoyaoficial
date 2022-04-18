# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.osv import osv

class account_voucher_advance(models.Model):
	_name = 'account.voucher.advance'

	name = fields.Char('Pago Avanzado')
	fecha = fields.Date('Fecha')
	period_id = fields.Many2one('account.period','Periodo')
	caja = fields.Many2one('account.journal','Caja')
	flujo_caja = fields.Many2one('it.flujo.caja','Flujo de Caja')
	moneda = fields.Many2one('res.currency','Moneda de Pago')
	type_mov = fields.Selection([('ingreso','Ingreso'),('egreso','Egreso')],'Tipo de Movimiento')
	ref_pago = fields.Char('Ref. Pago',size=30)
	glosa = fields.Char('Glosa', size=200)
	partner_ids = fields.Many2many('res.partner','partner_voucher_advance_rel','advance_id','partner_id','Proveedores/Clientes')
	total = fields.Float('Total',digits=(12,2))
	tipo_cambio = fields.Float('Tipo de Cambio',digits=(12,3))

	line_ids = fields.One2many('account.voucher.advance.line','padre','Detalle')
	state = fields.Selection([('draft','Borrador'),('done','Asentado')],'Estado',default='draft')


	total_moneda = fields.Float(u'Total Moneda de la Compañia',digits=(12,2), compute="get_total_moneda")
	suma_total = fields.Float(u'Suma de los montos a pagar en moneda de la compañia',digits=(12,2), compute="get_suma_total")
	importe_desajuste = fields.Float(u'Importe de desajuste',digits=(12,2), compute="get_importe_desajuste")
	cuenta_desajuste = fields.Many2one('account.account','Cuenta de Desajuste')
	cuenta_analitica = fields.Many2one(u'account.analytic.account','Cuenta Analitica',digits=(12,2))

	move_id = fields.Many2one('account.move','Asiento')


	@api.model
	def create(self,vals):
		t = super(account_voucher_advance,self).create(vals)

		id_seq=self.env['ir.sequence'].search([('name', '=', 'pago avanzado it')])
		if len(id_seq) > 0:
			id_seq=id_seq[0]
		else:
			id_seq=self.env['ir.sequence'].create({'name': 'pago avanzado it', 'implementation': 'standard','active': True, 'prefix': 'PA-', 'padding': 4, 'number_increment': 1, 'number_next_actual': 1})
		t.write({'name': id_seq.next_by_id(id_seq.id)})
		return t



	@api.one
	def totalizar(self):
		for i in self.line_ids:
			if i.monto == 0:
				i.unlink()
		self.refresh()

		if 'nada' in self.env.context:
			pass
		else:
			self.total = self.suma_total


	@api.one
	def cancelar(self):
		self.state = 'draft'
		if self.move_id.id:
			if self.move_id.state != 'draft':
				self.move_id.button_cancel()
			self.move_id.unlink()


	@api.one
	def get_total_moneda(self):
		self.total_moneda  = self.total

	@api.one
	def get_suma_total(self):
		suma = 0
		for i in self.line_ids:
			suma += i.monto

		self.suma_total = suma

	@api.one
	def get_importe_desajuste(self):
		self.importe_desajuste = self.total_moneda - self. suma_total


	@api.one
	def traer_datos(self):
		for i in self.line_ids:
			i.unlink()
			
		
		periodo_inicial = self.env['account.period'].search([('code','=','00/'+ self.period_id.fiscalyear_id.name)])[0].id

		generar = self.env['saldo.comprobante.periodo.wizard'].create({
			'fiscal_id':self.period_id.fiscalyear_id.id,
			'periodo_ini':periodo_inicial,
			'periodo_fin':self.period_id.id,
			'mostrar':'pantalla',
			'check':False,
			'empresa':False,
			'cuenta':False,
			'tipo':'A pagar' if self.type_mov == 'egreso' else 'A cobrar',
			})
		generar.do_rebuild()



		for line in self.env['saldo.comprobante.periodo'].search([]):
			if line.saldo > 0 and self.type_mov == 'ingreso':
				partner_act = self.env['res.partner'].search([('type_number','=',line.ruc)])[0].id if len( self.env['res.partner'].search([('type_number','=',line.ruc)]) )>0 else False
				if partner_act and partner_act in self.partner_ids.ids:
					dato = {
						'periodo': self.env['account.period'].search([('code','=',line.periodo)])[0].id,
						'fecha_emision':line.fecha_emision,
						'empresa': partner_act,
						'ruc':line.ruc,
						'cuenta':self.env['account.account'].search([('code','=',line.code)])[0].id,
						'tipo':line.tipo,
						'nro_comprobante':line.nro_comprobante,
						'saldo_mn':line.saldo,
						'type_document_id':self.env['it.type.document'].search([('code','=',line.tipo)])[0].id if len (self.env['it.type.document'].search([('code','=',line.tipo)]) ) >0 else False,
						'divisa':self.env['res.currency'].search([('name','=',line.divisa)])[0].id if len (self.env['res.currency'].search([('name','=',line.divisa)]) ) >0 else False,
						'saldo_me':line.amount_currency,
						'padre':self.id,
						}
					self.env['account.voucher.advance.line'].create(dato)

			if line.saldo < 0 and self.type_mov == 'egreso':
				partner_act = self.env['res.partner'].search([('type_number','=',line.ruc)])[0].id if len( self.env['res.partner'].search([('type_number','=',line.ruc)]) )>0 else False
				if partner_act and partner_act in self.partner_ids.ids:
					dato = {
						'periodo': self.env['account.period'].search([('code','=',line.periodo)])[0].id,
						'fecha_emision':line.fecha_emision,
						'empresa': partner_act,
						'ruc':line.ruc,
						'cuenta':self.env['account.account'].search([('code','=',line.code)])[0].id,
						'tipo':line.tipo,
						'nro_comprobante':line.nro_comprobante,
						'saldo_mn':-line.saldo,
						'type_document_id':self.env['it.type.document'].search([('code','=',line.tipo)])[0].id if len (self.env['it.type.document'].search([('code','=',line.tipo)]) ) >0 else False,
						'divisa':self.env['res.currency'].search([('name','=',line.divisa)])[0].id if len (self.env['res.currency'].search([('name','=',line.divisa)]) ) >0 else False,
						'saldo_me':-line.amount_currency,
						'padre':self.id,
						}
					self.env['account.voucher.advance.line'].create(dato)


	@api.one
	def generar_asiento(self):
		self.with_context({'nada':1}).totalizar()
		if len(self.line_ids)==0:
			raise  osv.except_osv(_('Alerta!'), _("No contiene lineas de Detalle a pagar."))

		asiento = {
			'journal_id':self.caja.id,
			'period_id':self.period_id.id,
			'period_origin_id':self.period_id.id,
			'date':self.fecha,
			'ref':self.ref_pago,
			'period_modify_ple':self.period_id.id,
			'ple_diariomayor':'1',
			'ple_venta':'1',
			'ple_compra':'1',
		}
		move_t = self.env['account.move'].create(asiento)
		self.move_id = move_t.id

		for i in self.line_ids:
			linea = {
				'name':'PAGO DE DIVERSAS FACTURAS',
				'partner_id':i.empresa.id,
				'nro_comprobante':i.nro_comprobante,
				'account_id':i.cuenta.id,
				'type_document_id':i.type_document_id.id,
				'debit': float("%.2f"%( (i.monto*self.tipo_cambio if self.caja.currency.id else i.monto) if self.type_mov == 'egreso' else 0 )),
				'credit':float("%.2f"%( 0 if self.type_mov == 'egreso' else (i.monto*self.tipo_cambio if self.caja.currency.id else i.monto) )),
				'analytic_account_id':False,
				'amount_currency':float("%.2f"%( ( (1 if self.type_mov == 'egreso' else -1) * ((i.monto if self.caja.currency.id else i.monto / self.tipo_cambio) if self.tipo_cambio != 0 else 0) ) if i.divisa.id else 0 )),
				'currency_id':i.divisa.id,
				'currency_rate_it':self.tipo_cambio if i.divisa.id else 0,
				'flujo_caja_id':self.flujo_caja.id,
				'move_id':move_t.id,
			}
			self.env['account.move.line'].create(linea)
		
		linea_f = {
			'name':'PAGO DE DIVERSAS FACTURAS',
			'partner_id':False,
			'nro_comprobante':self.ref_pago,
			'account_id':self.caja.default_debit_account_id.id,
			'type_document_id':False,
			'debit': float("%.2f"%( (self.total*self.tipo_cambio if self.caja.currency.id else self.total) if self.type_mov == 'ingreso' else 0 )),
			'credit':float("%.2f"%( 0 if self.type_mov == 'ingreso' else (self.total*self.tipo_cambio if self.caja.currency.id else self.total) )),
			'analytic_account_id':False,
			'amount_currency':float("%.2f"%( ( (1 if self.type_mov == 'ingreso' else -1) * ((self.total if self.caja.currency.id else 0 )  ) )  )),
			'currency_id':self.caja.currency.id,
			'currency_rate_it':self.tipo_cambio if self.caja.currency.id else 0,
			'flujo_caja_id':self.flujo_caja.id,
			'move_id':move_t.id,
		}
		self.env['account.move.line'].create(linea_f)
		

		if self.importe_desajuste != 0:
			if not self.cuenta_desajuste.id:
				raise osv.except_osv( ('Alerta!'), ("Necesita seleccionar una cuenta de Desajuste."))

			monto = (self.importe_desajuste*self.tipo_cambio if self.caja.currency.id else self.importe_desajuste)
			debit = 0
			credit = 0
			if monto >0:
				if linea_f['debit'] != 0:
					credit = abs(monto)
				else:
					debit = abs(monto)
			else:
				if linea_f['debit'] != 0:
					debit = abs(monto)
				else:
					credit = abs(monto)

			linea_desajuste = {
				'name':'PAGO DE DIVERSAS FACTURAS',
				'partner_id':False,
				'nro_comprobante':self.ref_pago,
				'account_id':self.cuenta_desajuste.id,
				'type_document_id':False,
				'debit': float("%.2f"%( debit  )),
				'credit':float("%.2f"%( credit )),
				'analytic_account_id':self.cuenta_analitica.id,
				'amount_currency': ( float("%.2f"%( abs(self.importe_desajuste) * ( 1 if debit != 0 else -1 )  )) ) if self.caja.currency.id else 0,
				'currency_id':self.caja.currency.id,
				'currency_rate_it':self.tipo_cambio if self.caja.currency.id else 0,
				'flujo_caja_id':self.flujo_caja.id,
				'move_id':move_t.id,
			}
			self.env['account.move.line'].create(linea_desajuste)
		
		self.move_id.refresh()

		total_debit = 0
		total_credit = 0

		for i in self.move_id.line_id:
			total_debit += i.debit
			total_credit += i.credit


		if "%.2f"%total_debit != "%.2f"%total_credit:
			if not self.caja.profit_account_id.id or not self.caja.loss_account_id.id:
				raise osv.except_osv(('Alerta!'), ("El diario caja no tiene configurado cuenta de ganancia o perdida."))

			debit = 0 if total_debit - total_credit > 0 else abs(total_debit - total_credit)
			credit = 0 if total_debit - total_credit < 0 else abs(total_debit - total_credit)

			linea_desajuste_total = {
				'name':'PAGO DE DIVERSAS FACTURAS',
				'partner_id':False,
				'nro_comprobante':self.ref_pago,
				'account_id':self.caja.loss_account_id.id if debit != 0 else self.caja.profit_account_id.id,
				'type_document_id':False,
				'debit': float("%.2f"%( debit  )),
				'credit':float("%.2f"%( credit )),
				'analytic_account_id':False,
				'amount_currency':float("%.2f"%( abs( ((debit-credit)/self.tipo_cambio) if self.tipo_cambio!=0 else 0 ) * ( 1 if debit != 0 else -1 )  )),
				'currency_id':self.caja.currency.id,
				'currency_rate_it':self.tipo_cambio if self.caja.currency.id else 0,
				'flujo_caja_id':False,
				'move_id':move_t.id,
			}
			self.env['account.move.line'].create(linea_desajuste_total)

		if self.move_id.state == 'draft':
			self.move_id.button_validate()

		self.state = 'done'

	@api.onchange('period_id','caja')
	def onchange_period_id(self):
		if self.caja.id and self.caja.allow_date and (self.fecha < self.period_id.date_start or self.fecha > self.period_id.date_stop ):
			self.period_id = False
			raise osv.except_osv(('Alerta!'), ("La fecha esta fuera del periodo seleccionado y la caja no lo permite."))

		if self.caja.id and self.caja.currency.id:
			self.moneda = self.caja.currency.id
		elif self.caja.id:
			self.moneda = self.env['res.currency'].search([('name','=','PEN')])[0].id
		else:
			self.moneda = False

	@api.one
	def write(self,vals):
		t = super(account_voucher_advance,self).write(vals)
		self.refresh()
		if 'nada' in vals:
			pass
		else:
			if self.caja.id and self.caja.currency.id:
				self.write({'moneda' : self.caja.currency.id,'nada':'1'})
			elif self.caja.id:
				self.write({'moneda' : self.env['res.currency'].search([('name','=','PEN')])[0].id,'nada':'1'})
			else:
				self.write({'moneda' : False,'nada':'1'})
		return t

	@api.onchange('fecha')
	def onchange_fecha(self):
		if self.fecha:
			ss = self.fecha.split('-')[1] + '/' + self.fecha.split('-')[0]
			periodo = self.env['account.period'].search([('code','=',ss)])
			if len(periodo) >0:
				self.period_id = periodo[0].id
			else:
				self.period_id = False

			tc = self.env['res.currency.rate'].search([('currency_id.name','=','USD'),('name','=',self.fecha)])
			if len(tc):
				self.tipo_cambio = tc[0].type_sale
			else:
				self.tipo_cambio = 1
		else:
			self.period_id = False



class account_voucher_advance_line(models.Model):
	_name = 'account.voucher.advance.line'

	periodo = fields.Many2one('account.period','Periodo')
	fecha_emision = fields.Date(u'Fecha Emisión')
	empresa = fields.Many2one('res.partner','Empresa')
	ruc = fields.Char('RUC')
	cuenta = fields.Many2one('account.account','Cuenta Contable')
	divisa = fields.Many2one('res.currency','Divisa')
	tipo = fields.Char('Tipo')
	type_document_id = fields.Many2one('it.type.document','Tipo de Documento')
	nro_comprobante = fields.Char('Nro. Comprobante')
	saldo_mn = fields.Float('Saldo MN.')
	saldo_me = fields.Float('Saldo ME.')
	monto = fields.Float('Monto')
	padre = fields.Many2one('account.voucher.advance','Padre')
