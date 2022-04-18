# -*- coding: utf-8 -*-

from openerp import models, fields, api

class it_ht_sunat(models.Model):
	_name = 'it.ht.sunat'
	name = fields.Char(required=True, string="Cuenta",size=12)

	_order = 'name'
	