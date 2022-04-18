# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api  , exceptions , _

class account_journal(models.Model):
	_inherit = 'account.journal'
	is_journal_unic = fields.Boolean('Es Asiento Unico?')
	register_sunat = fields.Selection((('1','Compras'),
									('2','Ventas'),
									('3','Honorarios'),
									('4','Retenciones'),
									('5','Percepciones')								
									),'Registro Sunat')

	@api.one
	@api.constrains('is_journal_unic')
	def _check_description(self):
		if self.is_journal_unic:
			lobj_aj = self.env['account.journal'].search([('is_journal_unic','=','True')])
			if len(lobj_aj) > 1:
				self.is_journal_unic = False
				raise exceptions.Warning(_("No se puede seleccionar dos o mas Diarios para Asiento Unicos."))