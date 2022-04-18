# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class purchase_liquidation(models.Model):
	_inherit = 'purchase.liquidation'

	anterior_nombre = fields.Char('Anterior Correlativo',readonly=True)
	padre_id = fields.Many2one('purchase.liquidation','Padre')

	@api.one
	def reasignar_name(self):
		self.write({'anterior_nombre':self.name})

		sequence_id = self.env['ir.sequence'].search([('name','=','Liquidation')])
		tmp_newname = self.env['ir.sequence'].get_id(sequence_id.id, 'id')
		self.write({'name':tmp_newname})