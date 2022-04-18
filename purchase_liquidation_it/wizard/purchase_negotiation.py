# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

import datetime

class purchase_negotiation(models.TransientModel):
	_name = 'purchase.negotiation'
	
	line_id = fields.Many2one('purchase.liquidation.line', "Linea")
	in_date = fields.Date("Fecha Recepción")
	source_zone = fields.Many2one('table.zone',"Origen")
	lot = fields.Char("Lote")
	material = fields.Char("Material")
	presentation = fields.Char("Presentación")
	tmh = fields.Float("TMH", digits=(10,3))
	h2o = fields.Float("%_H2O", digits=(10,3))
	tms = fields.Float("TMS", digits=(10,3))
	ley_oz = fields.Float("Ley Oz", digits=(10,3))
	percentage_param_ley = fields.Float("Porcentaje Ley", digits=(10,2))
	percentage_recovery = fields.Float("%_Recup.",digits=(10,2)) 
	points_param = fields.Float("Puntos Param", digits=(10,2), invisible=1) 
	percentage_param = fields.Float("Porcentaje Param", digits=(10,2)) 
	int_price = fields.Float("Precio Intern.", digits=(10,2))
	real_int_price = fields.Float("Precio Intern.", digits=(10,2))
	int_price_margin = fields.Float("Margen de P. Inter.", digits=(10,2))
	maquila = fields.Float("Maquila", digits=(10,2))
	soda = fields.Float("NaOH kg/TN", digits=(10,2))
	cianuro = fields.Float("NaCN kg/TN", digits=(10,2))
	value_consumed = fields.Float("Consumo Q Valorado", digits=(10,2))
	g_adm = fields.Float("G Adm", digits=(10,2))
	total_maquila = fields.Float("Total Maquila", digits=(10,2))
	adjust_factor = fields.Float("Factor Ajuste", digits=(10,4), default=1.1023)
	cost = fields.Float("Costo/TM", digits=(10,2))
	old_cost_to_pay = fields.Float("Costo Original", digits=(10,2))
	new_cost_to_pay = fields.Float("Nuevo Costo", digits=(10,2))
	difference = fields.Float("Diferencia", digits=(10,2))
	dif_igv = fields.Float("Igv", digits=(10,2))
	sum_to_pay = fields.Float("Por Pagar", digits=(10,2))
	observations = fields.Text("Observaciones")
	is_especial = fields.Boolean("Cálculo especial")
	porcentaje_diferencia = fields.Char("Margen")

	h2o_ref = fields.Float("%_H2O", digits=(10,3))
	ley_oz_ref = fields.Float("Ley Oz", digits=(10,3))
	percentage_recovery_ref = fields.Float("%_Recup.",digits=(10,2))
	int_price_margin_ref = fields.Float("Margen de P. Inter.", digits=(10,2))

	@api.model
	def default_get(self, fields):
		res = super(purchase_negotiation,self).default_get(fields)
		base_line = self.env['purchase.liquidation.line'].search([('parent','=',self.env.context.get('active_id', [])),('line_type','=','Negociado'),('mineral','=','oro')])
		if not base_line:
			base_line = self.env['purchase.liquidation.line'].search([('parent','=',self.env.context.get('active_id', [])),('line_type','=','Propuesta'),('mineral','=','oro')])
		vals = {
			'line_id'                : base_line.id,
			'in_date'                : base_line.in_date,
			'source_zone'            : base_line.source_zone.id,
			'lot'                    : base_line.lot,
			'material'               : base_line.material,
			'presentation'           : base_line.presentation,
			'tmh'                    : base_line.tmh,
			'h2o'                    : base_line.h2o,
			'h2o_ref'                : base_line.h2o,
			'tms'                    : base_line.tms,
			'ley_oz'                 : base_line.ley_oz,
			'ley_oz_ref'             : base_line.ley_oz,
			'percentage_param_ley'   : base_line.percentage_param_ley,
			'percentage_recovery'    : base_line.percentage_recovery,
			'percentage_recovery_ref': base_line.percentage_recovery,
			'points_param'           : base_line.points_param,
			'percentage_param'       : base_line.percentage_param,
			'int_price'              : base_line.int_price,
			'real_int_price'         : base_line.real_int_price,
			'int_price_margin'       : base_line.int_price_margin,
			'int_price_margin_ref'   : base_line.int_price_margin,
			'maquila'                : base_line.maquila,
			'soda'                   : base_line.soda,
			'cianuro'                : base_line.cianuro,
			'value_consumed'         : base_line.value_consumed,
			'g_adm'                  : base_line.g_adm,
			'total_maquila'          : base_line.total_maquila,
			'adjust_factor'          : base_line.adjust_factor,
			'cost'                   : base_line.cost,
			'old_cost_to_pay'        : base_line.cost_to_pay,
			'is_especial'            : base_line.parent.is_especial,
		}
		res.update(vals)
		return res

	@api.onchange('h2o')
	def onchange_tms(self):
		self.tms = self.tmh - (self.tmh*self.h2o/100)

	@api.onchange('int_price_margin')
	def onchange_int_price(self):
		self.int_price = self.real_int_price - self.int_price_margin

	@api.onchange('value_consumed','g_adm')
	def onchange_total_maquila(self):
		self.total_maquila = self.value_consumed + self.g_adm

	@api.onchange('ley_oz','percentage_recovery','int_price','maquila','total_maquila','adjust_factor')
	def onchange_cost(self):
		if self.is_especial:
			self.cost = ((self.ley_oz*(self.percentage_recovery/100)*self.int_price)*self.adjust_factor-self.maquila-self.total_maquila)
		else:
			self.cost = ((self.ley_oz*(self.percentage_recovery/100)*self.int_price)-self.maquila-self.total_maquila)*self.adjust_factor

	@api.onchange('cost','tms')
	def onchange_cost_pay(self):
		self.new_cost_to_pay = self.cost*self.tms
		self.difference = self.old_cost_to_pay - self.new_cost_to_pay
		self.dif_igv = self.new_cost_to_pay*0.18
		self.sum_to_pay = self.new_cost_to_pay + self.dif_igv
		self.porcentaje_diferencia = "%.2f"%(( ( self.sum_to_pay / (self.old_cost_to_pay*1.18) )  if self.old_cost_to_pay != 0 else 0 )*100) + ' %'


	@api.one
	def save_negotiation(self):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		if not len(employee):
			ru = self.env['res.users'].search([('id','=',self.env.uid)])[0]
			raise osv.except_osv('Alerta!',"El usuario "+ru.name+" no puede generar "+(u"negociación" if self.line_id.line_type == 'Propuesta' else u"renegociación")+". Falta configurar empleado.")

		#if not employee:
		#	raise osv.except_osv('Alerta!',"El usuario actual no tiene asignado un Recurso Humano.")
		vals = {
			'parent'				: self.line_id.parent.id,
			'line_type'				: 'Negociado' if self.line_id.line_type == 'Propuesta' else 'Renegociado',
			'in_date'				: self.line_id.in_date,
			'mineral'				: 'oro',
			'employee'				: employee.id,
			'num_liquidation'		: self.line_id.lot.split('-')[1],
			'print_date'			: fields.Date.today(),
			'source_zone'			: self.line_id.source_zone.id,
			'lot'					: self.line_id.lot,
			'material'				: self.line_id.material,
			'presentation'			: self.line_id.presentation,
			'tmh'					: self.line_id.tmh,
			'h2o'					: self.h2o,
			'ley_oz'				: self.ley_oz,
			'percentage_param_ley'	: self.line_id.percentage_param_ley,
			'percentage_recovery'	: self.percentage_recovery,
			'points_param'			: self.line_id.points_param,
			'percentage_param'		: self.line_id.percentage_param,
			'real_int_price'		: self.line_id.real_int_price,
			'int_price_margin'		: self.int_price_margin,
			'maquila'				: self.maquila,
			'soda'					: self.line_id.soda,
			'cianuro'				: self.line_id.cianuro,
			'value_consumed'		: self.value_consumed,
			'g_adm'					: self.g_adm,
			'adjust_factor'			: self.line_id.adjust_factor,
			'observations'			: self.observations,
		}	
		vals['tms'] = vals['tmh'] - (vals['tmh']*vals['h2o']/100)
		vals['int_price'] = vals['real_int_price'] - vals['int_price_margin']
		vals['total_maquila'] = vals['value_consumed'] + vals['g_adm']
		if self.is_especial:
			vals['cost'] = ((vals['ley_oz']*(vals['percentage_recovery']/100)*vals['int_price'])*vals['adjust_factor']-vals['maquila']-vals['total_maquila'])
		else:
			vals['cost'] = ((vals['ley_oz']*(vals['percentage_recovery']/100)*vals['int_price'])-vals['maquila']-vals['total_maquila'])*vals['adjust_factor']
		vals['cost_to_pay'] = vals['cost']*vals['tms']
		data_line = self.env['purchase.liquidation.line'].search([('parent','=',self.line_id.parent.id),('line_type','=','Datos'),('mineral','=','oro')]) 
		vals['comparative_index'] = vals['cost_to_pay']/data_line.cost_to_pay*100
		liquidation_line = self.env['purchase.liquidation.line']
		liquidation_line.create(vals)
		pl = self.env['purchase.liquidation'].search([('id','=',self.line_id.parent.id)])[0]

		if self.line_id.parent.state == 'negotiated':
			self.line_id.parent.state = 'done'
			pl.message_post(body=u"<p>Renegociación generada.</p>")
		else:
			self.line_id.parent.state = 'negotiated'
			pl.message_post(body=u"<p>Negociación generada.</p>")

		pl.fecha_botonaso = datetime.datetime.today()