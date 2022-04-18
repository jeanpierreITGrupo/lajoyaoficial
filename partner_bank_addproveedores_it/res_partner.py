# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv
from openerp import netsvc

class res_partner_bank(models.Model):
	_inherit = 'res.partner.bank'

	currency_id_p = fields.Many2one('res.currency','Moneda')
