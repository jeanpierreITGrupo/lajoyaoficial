# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api

class hr_employee(models.Model):
	_inherit = 'hr.employee'

	end_contract_date = fields.Date("Fin Contrato")