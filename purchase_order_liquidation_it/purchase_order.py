# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class purchase_order(models.Model):
	_inherit = "purchase.order"

	#liquidation_id = fields.Many2one('purchase.liquidation',"Liquidación")
	#cost_to_pay = fields.Float("Costo a pagar", digits=(10,2))

	#@api.onchange('liquidation_id')
	#def onchange_liquidation(self):
	#	if self.liquidation_id.id:
	#		liquidation_line_id = self.env['purchase.liquidation.line'].search([('parent','=',self.liquidation_id.id),('line_type','=','Renegociado')])
	#		if not liquidation_line_id:
	#			liquidation_line_id = self.env['purchase.liquidation.line'].search([('parent','=',self.liquidation_id.id),('line_type','=','Negociado')])
	#		self.cost_to_pay = liquidation_line_id.cost_to_pay

	#@api.model
	#def create(self,vals):
	#	if 'liquidation_id' in vals:
	#		liquidation_line_id = self.env['purchase.liquidation.line'].search([('parent','=',vals['liquidation_id']),('line_type','=','Renegociado')])
	#		if not liquidation_line_id:
	#			liquidation_line_id = self.env['purchase.liquidation.line'].search([('parent','=',vals['liquidation_id']),('line_type','=','Negociado')])
	#		vals['cost_to_pay'] = liquidation_line_id.cost_to_pay		
	#	return super(purchase_order,self).create(vals)
