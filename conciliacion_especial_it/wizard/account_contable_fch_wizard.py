# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class account_move(models.Model):
	_inherit = 'account.move'


	@api.multi
	def conciliacion_especial_x(self):
		for i in self:
			r_id = self.env['account.move.reconcile'].create({'type': 'auto', 'opening_reconciliation': True})

			for elem_f in i.line_id:
				self.env.cr.execute('update account_move_line set reconcile_id = %s where id = %s',(r_id.id, elem_f.id,))


