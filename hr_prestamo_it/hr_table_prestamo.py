# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class hr_table_prestamo(models.Model):
	_name = 'hr.table.prestamo'
	_rec_name = 'name'

	name       = fields.Char('Nombre')
	account_id = fields.Many2one('account.account','Cuenta')