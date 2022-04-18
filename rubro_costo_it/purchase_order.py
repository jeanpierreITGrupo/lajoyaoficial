# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class rubro_costo_it(models.Model):
	_name = 'rubro.costo.it'

	name = fields.Char('Rubro Costo')
	code = fields.Char('Codigo')
	_rec_name = 'code'


class account_account(models.Model):
	_inherit = 'account.account'

	rubro_costo_id = fields.Many2one('rubro.costo.it','Rubro Costo')
