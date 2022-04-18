# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import openerp.addons.decimal_precision as dp

class min_max_wizard(models.TransientModel):
	_name = 'min.max.wizard'

	rotation = fields.Integer(u'Día(s) de Rotación', required=True)
	warehouse_id = fields.Many2one('stock.warehouse', u'Almacén', required=True)
	evaluation = fields.Selection([('faltantes', 'Faltantes'),
								   ('sobrantes', 'Sobrantes')],'Evaluar', required=True)

	show_in = fields.Selection([('1','Pantalla'),('2','Excel')],'Mostrar en', required=True)

	@api.multi
	def do_rebuild(self):
		return self.env['min.max.view'].display_q(self.rotation, self.evaluation, [self.warehouse_id.lot_stock_id.id], self.show_in)


