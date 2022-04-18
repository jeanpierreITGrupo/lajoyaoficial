# -*- encoding: utf-8 -*-
import base64
from openerp.osv import osv
from openerp import models, fields, api
from datetime import date,timedelta


class res_company(models.Model):
	_inherit = 'res.company'

	sctr   = fields.Boolean('SCTR')
	senati = fields.Boolean('Senati')