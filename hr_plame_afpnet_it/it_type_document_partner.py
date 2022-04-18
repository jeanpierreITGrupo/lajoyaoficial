# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class it_type_document_partner(models.Model):
	_inherit = 'it.type.document.partner'

	afpnet_code = fields.Char("Código AFPNET", size=4)
