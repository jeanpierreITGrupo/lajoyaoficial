# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class table_zone(models.Model):
	_name = 'table.zone'

	name = fields.Char("Nombre")
	param =	fields.Float("Gasto")
	analytic_id  = fields.Many2one('account.analytic.account','Cuenta Analítica')
	code = fields.Char("Código")
	ubigeo = fields.Char('Ubigeo')

	_rec_name = 'name'

	@api.one
	def unlink(self):
		liquidations = self.env['purchase.liquidation'].search([])
		for liquidation in liquidations:
			if liquidation.source_zone.id == self.id:
				raise osv.except_osv('Alerta!',u"No se puede eliminar una zona relacionada a una Liquidación de Compra.")
		return super(table_zone, self).unlink()