# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_account(models.Model):
	_inherit = 'account.account'
	cashbank_code = fields.Char('Code', size=100)
	cashbank_number = fields.Char('Número de Cuenta',size=100)
	cashbank_financy = fields.Char('Entidad Financiera', size=100)