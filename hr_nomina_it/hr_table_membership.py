# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class hr_table_membership(models.Model):
	_name = 'hr.table.membership'
	_rec = 'name'

	name       = fields.Char('Nombre', required=True)
	code       = fields.Char('Código', required=True)
	account_id = fields.Many2one('account.account', 'Cuenta')
	mem_type   = fields.Selection([('private','Privada')],'Tipo')