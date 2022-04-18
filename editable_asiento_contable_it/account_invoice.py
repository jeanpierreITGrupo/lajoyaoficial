# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
import datetime

class account_journal(models.Model):
	_inherit = 'account.journal'

	editar_nombre_asiento = fields.Boolean('Editar Asiento')

class account_move(models.Model):
	_inherit = 'account.move'

	es_editable = fields.Boolean('Es editable',related='journal_id.editar_nombre_asiento')


	@api.one
	def write(self,vals):
		t = super(account_move,self).write(vals)
		fact = self.env['account.invoice'].search([('move_id','=',self.id)])
		for i in fact:
			self.env.cr.execute(""" update account_invoice set internal_number = '""" + self.name + """' where id = """ + str(i.id))
			self.env.cr.execute(""" update account_invoice set number = supplier_invoice_number where id = """ + str(i.id))
		return t