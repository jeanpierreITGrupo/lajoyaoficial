# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from openerp import exceptions


class production_parameter(models.Model):
	_inherit = 'production.parameter'

	account_anal_padre = fields.Many2one('account.analytic.account','Cuenta Analítica Padre para Expediente')
	

class purchase_costing_detalles(models.Model):
	_name = 'purchase.costing.detalles'
	
	@api.one
	def get_expectativa_oro(self):

		if self.nro_lote.id:
			self.env.cr.execute(""" 
				select  sum(coalesce(sm.gold_expected,0))  from  purchase_costing pc
				inner join purchase_costing_detalles pcd on pcd.padre = pc.id
				inner join purchase_liquidation pl on pl.id = pcd.nro_lote
				left join stock_move sm on sm.lot_num = pl.id and sm.location_dest_id = """ + str(self.padre.location_id.id) + """
				left join stock_picking sp on sp.id = sm.picking_id and sp.state != 'draft'
				where pl.id = """ +str(self.nro_lote.id)+ """ 
				group by pl.id
				""")
			cont = 0
			for i in self.env.cr.fetchall():
				cont+= i[0]
			self.expectativa_oro = cont

	nro_lote = fields.Many2one('purchase.liquidation','Nro de Lote')
	expectativa_oro = fields.Float('Expectativa de Oro',digits=(12,2),compute="get_expectativa_oro")
	padre = fields.Many2one('purchase.costing','Padre')

class purchase_costing(models.Model):
	_name = 'purchase.costing'
	_rec_name = 'name'

	name = fields.Char("Nombre", default="/")
	periodo = fields.Many2one("account.period",'Periodo')
	date = fields.Date('Fecha de Apertura')
	acopiador = fields.Many2one('table.acopiador','Acopiador')
	zona = fields.Many2one('table.zone','Zona')
	lineas = fields.One2many('purchase.costing.detalles','padre','Lineas')
	location_id = fields.Many2one('stock.location',"Almacén de Lotes", required=1)
	cuenta_analytica = fields.Many2one('account.analytic.account','Cuenta Analitica')
	
	@api.model
	def create(self, vals):
		sequence_id = self.env['ir.sequence'].search([('name','=','Costing')])
		vals['name'] = self.env['ir.sequence'].get_id(sequence_id.id, 'id')
		t = super(purchase_costing, self).create(vals)

		param = self.env['production.parameter'].search([])[0]
		if  param.account_anal_padre.id:
			analitic_account = self.env['account.analytic.account']
			account_vals = {
				'name'		: t.name,
				'type'		: 'normal',
				'parent_id'	: param.account_anal_padre.id,
			}
			oml = analitic_account.create(account_vals)
			t.cuenta_analytica = oml.id
		else:
			raise osv.except_osv('Alerta!',"No se ha ingresado una Cuenta Analítica padre.")
		return t

	@api.one
	@api.constrains('name')
	def constrains_name(self):
		if self.name!= '/' and self.name:
			t = self.env['purchase.costing'].search([('name','=',self.name),('id','!=',self.id)])
			if len(t) >0:
				raise exceptions.Warning("No pueden existir dos expedientes con el mismo nombre " + self.name+".")


	@api.one
	def unlink(self):
		#Eliminación de la cuenta analítica asociada
		analytic_account = self.env['account.analytic.account'].search([('name','=',self.name)])
		account_lines = self.env['account.move.line'].search([])
		for line in account_lines:
			if line.analytic_account_id == analytic_account.id:
				raise osv.except_osv('Alerta!',"No se puede eliminar un expediente con una cuenta Analítica asociada a un gasto.")
		analytic_account.unlink()
		return super(purchase_costing,self).unlink()



class purchase_costing_detalle(models.Model):
	_name = 'purchase.costing.detalle'
	_rec_name = 'name'

	name = fields.Many2one('purchase.costing','Expediente')
	state = fields.Selection([('draft','Monitoreando'),('calculated','Calculado'),('updated','Kardex Act'),('done','Asentado')], default='draft')
	expedient_expenses = fields.Float("Gastos de Expediente")
	no_expedient_expenses_part = fields.Float("Parte proporcional de los gastos sin expediente")
	expedient_total_expected = fields.Float("Total de expectativa de oro para el expediente")
	period_id = fields.Many2one('account.period',"Periodo", required=1)
	journal_id = fields.Many2one('account.journal',"Diario para Asientos")
	location_id = fields.Many2one('stock.location',"Almacén a Consultar", required=1)
	lines = fields.One2many('purchase.costing.detalle.line','parent',"Líneas")


	@api.one
	def find_data(self):

		for line in self.lines:
			line.unlink()

		self.env.cr.execute(""" 
			select  pc.id,pl.id, sum(coalesce(sm.gold_expected,0)), min(sm.product_id),sum(coalesce(sm.product_uom_qty,0)),sum(coalesce(T.pricest,0)), min(sm.id) as sm_id  from  purchase_costing pc
			inner join purchase_costing_detalles pcd on pcd.padre = pc.id
			inner join purchase_liquidation pl on pl.id = pcd.nro_lote
			left join stock_move sm on sm.lot_num = pl.id and sm.location_dest_id = """ + str(self.location_id.id) + """
			left join stock_picking sp on sp.id = sm.picking_id and sp.state != 'draft'
			left join (
			   select ail.nro_lote as ailote, sum(ail.price_subtotal) as pricest from account_invoice ai
			   inner join account_invoice_line ail on ail.invoice_id = ai.id
			   inner join account_journal aj on aj.id = ai.journal_id
			   where aj.type in ('purchase','purchase_refund') and ai.state != 'draft'
			   group by ail.nro_lote
			) as T on T.ailote = pl.id
			where pc.id = """ + str(self.name.id) + """
			group by pc.id, pl.id
			""")


		line_obj = self.env['purchase.costing.detalle.line']
		for line in self.env.cr.fetchall():
			vals = {
				'parent'			: self.id,
				'expedient_number'	: self.name.id,
				'move_id'			: line[6],
				'lot_number'		: line[1],
				'gold_expected'		: line[2],
				'product'			: line[3],
				'tn_amount'			: line[4],
				'invoice_value'		: line[5],
			}


			line_obj.create(vals)


		params = self.env['production.parameter'].search([])
		analytic_account = self.env['account.analytic.account'].search([('name','=',self.name.name)])
		account_lines = self.env['account.move.line'].search([('analytic_account_id','=',analytic_account.id),('move_id.period_id','=',self.period_id.id)])
		self.expedient_expenses = 0
		self.expedient_total_expected = 0
		for line in account_lines:
			self.expedient_expenses += (line.debit - line.credit)
		for line in self.lines:
			self.expedient_total_expected += line.gold_expected
		expenses_no_expedient = self.env['expenses.without.record'].search([('period_id','=',self.period_id.id)])
		for line_ene in expenses_no_expedient.lines:
			if line_ene.expedient_id.id == self.name.id:
				self.no_expedient_expenses_part = line_ene.monto_proporcional



	@api.one
	def calculate(self):
		if self.lines:
			cont = 0
			sum_1 = 0
			sum_2 = 0
			for line in self.lines:
				cont += 1
				line.percentage_expenses = line.gold_expected/self.expedient_total_expected if self.expedient_total_expected!= 0 else 0

				if len(self.lines) == cont:
					line.expedient_value = line.parent.expedient_expenses - sum_1
					line.no_expedient_expenses = self.no_expedient_expenses_part - sum_2
				else:
					line.expedient_value = line.percentage_expenses*line.parent.expedient_expenses
					line.refresh()

					sum_1 += line.expedient_value
					line.no_expedient_expenses = line.percentage_expenses*self.no_expedient_expenses_part

					line.refresh()
					sum_2 += line.no_expedient_expenses

				line.total_value = line.invoice_value + line.expedient_value + line.no_expedient_expenses
				line.new_cu = round(line.total_value / line.tn_amount,2) if line.tn_amount != 0 else 0
			self.state = 'calculated'

	@api.one
	def update_kardex(self):
		for line in self.lines:
			if line.move_id.id:
				line.move_id.p_et2 = line.new_cu
		self.state = 'updated'

	@api.one
	def cancel_last(self):
		if self.state == 'calculated':
			for line in self.lines:
				line.percentage_expenses = 0
				line.expedient_value = 0
				line.no_expedient_expenses = 0
				line.total_value = 0
				line.new_cu = 0
			self.expedient_expenses = 0
			self.no_expedient_expenses_part = 0
			self.expedient_total_expected = 0
			for line in self.lines:
				line.unlink()
			self.state = 'draft'
		elif self.state == 'updated':
			for line in self.lines:
				if line.move_id.id:
					line.move_id.p_et2 = 0
			self.state = 'calculated'
		else:
			self.state = 'updated'


	@api.model
	def default_get(self, fields):
		res = super(purchase_costing_detalle,self).default_get(fields)
		parameters = self.env['production.parameter'].search([])
		res.update({'journal_id':parameters.journal_id.id})
		return res


class purchase_costing_detalle_line(models.Model):
	_name = 'purchase.costing.detalle.line'

	parent = fields.Many2one('purchase.costing.detalle', "Costo de Compra")
	move_id = fields.Many2one('stock.move', "Movimiento")
	expedient_number = fields.Char("Nro de Expediente")
	lot_number = fields.Many2one('purchase.liquidation',"Nro Lote")
	gold_expected = fields.Float("Cant. Oro Esperado")
	product = fields.Char("Producto")
	tn_amount = fields.Float("Tn")
	percentage_expenses = fields.Float("Porcentaje Gastos",digits=(10,7))
	invoice_value = fields.Float("Valor Factura", digits=(10,2))
	expedient_value = fields.Float("Valor Expediente", digits=(10,2))
	no_expedient_expenses = fields.Float("Gastos sin Expediente", digits=(10,2))
	total_value = fields.Float("Valor Total", digits=(10,2))
	new_cu = fields.Float("Nuevo C.U", digits=(10,6))

	_order = 'lot_number'