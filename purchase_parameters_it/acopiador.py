# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class table_acopiador(models.Model):
	_name = 'table.acopiador'

	name = fields.Char("Nombre")