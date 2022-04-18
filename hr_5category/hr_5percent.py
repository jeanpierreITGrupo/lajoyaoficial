# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import datetime
from datetime import datetime
import decimal
import calendar

class hr_5percent(models.Model):
	_name = 'hr.5percent'

	uit_id         = fields.Many2one('hr.uit.historical','Valor de la UIT')
	type_element   = fields.Selection([('hasta','Hasta'),('exceso','Por el exceso')],'Motivo')
	uit_qty        = fields.Float('UITs',digits=(12,2))
	tasa           = fields.Float('tasa',digits=(12,2))
	nodomicialiado = fields.Boolean('No domicialiado')