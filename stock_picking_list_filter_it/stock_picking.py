# -*- coding: utf-8 -*-
from openerp     import models, fields, api
from openerp.osv import osv

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	es_control = fields.Boolean('Control Producto en Proceso')

	@api.model
	def default_get(self,fields):
		res = super(stock_picking,self).default_get(fields)
		if 'control_prod' in self.env.context:
			pp = self.env['production.parameter'].search([])[0]
			res['es_control']      = True
			res['picking_type_id'] = pp.control_prod_proceso.id
			res['motivo_guia']     = '6'
		return res