# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api, exceptions , _
from openerp.osv import osv

import decimal

class purchase_liquidation(models.Model):
	_inherit = 'purchase.liquidation'

	hora_entrada = fields.Char(u'Hora entrada')

class table_acopiador(models.Model):
	_inherit = 'table.acopiador'

	doc_number = fields.Char("Nro. de documento", required=True)