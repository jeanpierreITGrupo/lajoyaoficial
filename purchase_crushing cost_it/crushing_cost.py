# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import datetime

class crushing_cost(models.Model):
	_name = 'crushing.cost'
	_rec_name = 'name'

	name = fields.Char("Nombre", default="/")
	state = fields.Selection([('draft','Borrador'),('updated','Actualizado'),('transfered','Transferido'),('done','Asentado')], default='draft')
	period_id = fields.Many2one('account.period', "Periodo", required=1)
	account_id = fields.Many2one('account.analytic.account', "Cuenta Analítica", required=1)
	total_cost = fields.Float("Total Gasto", digits=(10,3))
	lines = fields.One2many('crushing.cost.line', 'parent', "Líneas")
	total_distribution = fields.Float("Total Distribución", digits=(10,6))


	picking_1 = fields.Many2one('stock.picking','Albarán Origen')
	picking_2 = fields.Many2one('stock.picking','Albarán Destino')

	@api.model
	def create(self, vals):
		sequence_id = self.env['ir.sequence'].search([('name','=','Crushing')])
		vals['name'] = self.env['ir.sequence'].get_id(sequence_id.id, 'id')
		return super(crushing_cost, self).create(vals)

	@api.one
	def update(self):

		if len(self.lines)==0:
			raise osv.except_osv('Alerta!',"No existe lotes seleccionados.")
			
		account_lines = self.env['account.move.line'].search([('analytic_account_id','=',self.account_id.id),('move_id.period_id','=',self.period_id.id)])
		self.total_cost = 0
		self.total_distribution = 0
		for line in self.lines:
			line.refresh()
			line.total_value = line.tn_amount*line.unit_cost
			line.tn_distribution = line.tn_amount*line.ponderation
		
		for line in account_lines:
			self.total_cost += (line.debit - line.credit)
		for line in self.lines:
			self.total_distribution += line.tn_distribution
		self.refresh()
		if not self.total_distribution > 0:
			raise osv.except_osv('Alerta!',"La ponderación de cada lote debe ser mayor a 0.")
		for line in self.lines:
			line.refresh()
			line.crushing_cost = (line.tn_distribution/self.total_distribution)*self.total_cost
			line.new_total = line.crushing_cost + line.total_value
			line.new_cu = line.new_total/line.tn_amount
		self.state = 'updated'

	@api.one
	def transfer(self):
		params = self.env['production.parameter'].search([])
		picking = self.env['stock.picking']
		move = self.env['stock.move']
		picking_type = params.top_origen_chancado
		
		#Traslado de productos a ubicación de producción.
		picking_vals = {
			'motivo_guia'		: '7',
			'move_type'			: 'direct',
			'picking_type_id'	: picking_type.id,
			'priority'			: '1',
			'date'				:  datetime.now(),
		}
		picking_obj = picking.create(picking_vals)


		self.write({'picking_1':picking_obj.id})

		for line in self.lines:
			move_vals = {
				'expedient_id'		: line.move_id.expedient_id.id,
				'picking_id'		: picking_obj.id,
				'lot_num'			: line.move_id.lot_num.id,
				'product_id'		: line.move_id.product_id.id,
				'gold_expected'		: line.move_id.gold_expected,
				'ponderation'		: line.move_id.ponderation,
				'product_uom_qty'	: line.move_id.product_uom_qty,
				'product_uom'		: line.move_id.product_uom.id,
				'p_et2'				: line.new_cu,
				'location_id'		: picking_type.default_location_src_id.id,
				'location_dest_id'	: picking_type.default_location_dest_id.id,
				'name'				: line.move_id.name,
				'invoice_state'		: line.move_id.invoice_state,
				'date'				: datetime.now(),
				'date_expected'		: datetime.now(),
				'state'				: 'done',
			}
			move_obj = move.create(move_vals)
		#Traslado de productos a almacén destino.

		picking_type = params.top_destino_chancado
		picking_vals = {
			'motivo_guia'		: '8',
			'move_type'			: 'direct',
			'picking_type_id'	: picking_type.id,
			'priority'			: '1',
			'date'				:  datetime.now(),
		}
		picking_obj_dest = picking.create(picking_vals)
		self.write({'picking_2':picking_obj_dest.id})

		for line in picking_obj.move_lines:
			move_vals = {
				'expedient_id'		: line.expedient_id.id,
				'picking_id'		: picking_obj_dest.id,
				'lot_num'			: line.lot_num.id,
				'product_id'		: line.product_id.id,
				'gold_expected'		: line.gold_expected,
				'ponderation'		: line.ponderation,
				'product_uom_qty'	: line.product_uom_qty,
				'product_uom'		: line.product_uom.id,
				'p_et2'				: line.p_et2,
				'location_id'		: picking_type.default_location_src_id.id,
				'location_dest_id'	: picking_type.default_location_dest_id.id,
				'name'				: line.name,
				'invoice_state'		: line.invoice_state,
				'date'				: datetime.now(),
				'date_expected'		: datetime.now(),
				'state'				: 'done',
			}
			move_obj_dest = move.create(move_vals)
		self.state = 'transfered'

	@api.one
	def cancel_last(self):
		if self.state == 'updated':
			for line in self.lines:
				line.unlink()
			self.total_cost = 0
			self.state = 'draft'
		elif self.state == 'transfered':
			if self.picking_1.id:
				if self.picking_1.state != 'draft':
					self.picking_1.action_revert_done()
					self.picking_1.unlink()
				else:
					self.picking_1.unlink()
				if self.picking_2.state != 'draft':
					self.picking_2.action_revert_done()
					self.picking_2.unlink()
				else:
					self.picking_2.unlink()
			self.state = 'updated'
		else:
			print "Nada"


class crushing_cost_line(models.Model):
	_name = 'crushing.cost.line'

	parent = fields.Many2one('crushing.cost', "Costo de Chancado")
	move_id = fields.Many2one('stock.move', "Movimiento")
	lot_num = fields.Many2one("purchase.liquidation","Nro de Lote")
	expedient_number = fields.Char("Nro de Expediente")
	gold_expected = fields.Float("Oro esperado", digits=(10,3))
	product = fields.Char("Producto")
	tn_amount = fields.Float("Tn", digits=(10,2))
	ponderation = fields.Float("Ponderación", digits=(10,2))
	total_value = fields.Float("Total Valor", digits=(10,2))
	unit_cost = fields.Float("C.U", digits=(10,2))
	tn_distribution = fields.Float("Tn Distribución", digits=(10,2))
	crushing_cost = fields.Float("Valor Costo Chancado", digits=(10,2))
	new_total = fields.Float("Nuevo Total", digits=(10,2))
	new_cu = fields.Float("Nuevo C.U", digits=(10,6))

	@api.one
	def write(self,vals):
		params = self.env['production.parameter'].search([])
		picking_type = params.top_origen_chancado

		if 'lot_num' in vals.keys():
			move_id = self.env['stock.move'].search([('lot_num','=',vals['lot_num']),('location_dest_id','=',picking_type.default_location_src_id.id)])
			if move_id:
				vals['move_id']	= move_id.id

				exp =  self.env['purchase.costing'].search([('lineas','=',vals['lot_num'])])
				if len(exp)>0:				
					vals['expedient_number'] = exp[0].name
				vals['gold_expected'] = move_id.gold_expected
				vals['product'] = move_id.product_id.name_template
				vals['tn_amount'] = move_id.product_uom_qty

				if 'ponderation' in vals:
					move_id.ponderation= vals['ponderation']
				else:
					vals['ponderation'] =  move_id.ponderation
									
				vals['ponderation'] = move_id.ponderation
				vals['unit_cost'] = move_id.p_et2
		return super(crushing_cost_line, self).write(vals)

	@api.model
	def create(self,vals):		
		params = self.env['production.parameter'].search([])
		picking_type = params.top_origen_chancado

		parent = self.env['crushing.cost'].search([('id','=',vals['parent'])])
		move_id = self.env['stock.move'].search([('lot_num','=',vals['lot_num']),('location_dest_id','=',picking_type.default_location_src_id.id)])
		if move_id:
			vals['move_id']	= move_id.id

			exp =  self.env['purchase.costing'].search([('lineas','=',vals['lot_num'])])
			if len(exp)>0:				
				vals['expedient_number'] = exp[0].name
			vals['gold_expected'] = move_id.gold_expected
			vals['product'] = move_id.product_id.name_template
			vals['tn_amount'] = move_id.product_uom_qty
			if 'ponderation' in vals:
				move_id.ponderation= vals['ponderation']
			else:
				vals['ponderation'] =  move_id.ponderation
			vals['unit_cost'] = move_id.p_et2
		return super(crushing_cost_line, self).create(vals)

	@api.onchange('lot_num')
	def onchange_lot_num(self):
		params = self.env['production.parameter'].search([])
		picking_type = params.top_origen_chancado

		if self.lot_num:
			move_id = self.env['stock.move'].search([('lot_num','=',self.lot_num.id),('location_dest_id','=',picking_type.default_location_src_id.id)])
			if move_id:
				exp =  self.env['purchase.costing'].search([('lineas','=',self.lot_num.id)])
				if len(exp)>0:
					self.expedient_number = exp[0].name
				self.gold_expected = move_id.gold_expected
				self.product = move_id.product_id.name_template
				self.tn_amount = move_id.product_uom_qty
				self.ponderation = move_id.ponderation
				self.unit_cost = move_id.p_et2
