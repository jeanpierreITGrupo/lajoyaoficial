# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
import datetime

class stock_picking(models.Model):
	_inherit = "stock.picking"

	aprob_uid = fields.Many2one('res.users', "Usuario que transfirió", )
	aprob_date = fields.Datetime("Fecha en que se transfirió")

	@api.cr_uid_ids_context
	def do_enter_transfer_details(self, cr, uid, picking, context=None):
		self.pool.get('stock.picking').write(cr,uid,picking,{'aprob_uid' : uid, 'aprob_date' : datetime.datetime.now()})
		return super(stock_picking, self).do_enter_transfer_details(cr, uid, picking, context=None)