# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv
from openerp import netsvc


class actualizar_plata_wizard(models.Model):
	_name = 'actualizar.plata.wizard'


	period_id = fields.Many2one('account.period','Periodo',required=True)
	account_id = fields.Many2one('account.account','Cuenta',required=True)
	

	@api.multi
	def do_rebuild(self):
		self.env.cr.execute("""

update account_move_line  set check_plata = true where id in (
select aml.id from account_move am
inner join account_move_line aml on aml.move_id = am.id
inner join account_account aa on aa.id = aml.account_id
inner join purchase_liquidation pl on pl.id = aml.nro_lote
where  aa.id = """+ str(self.account_id.id) +""" and am.period_id = """+ str(self.period_id.id) +"""  )

			""")