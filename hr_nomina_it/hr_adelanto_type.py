# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class hr_adelanto_type(models.Model):
	_name = 'hr.adelanto.type'

	name = fields.Char('Tipo de adelanto')
	code = fields.Char(u'Código')


class hr_adelanto_type_employee(models.Model):
	_name = 'hr.adelanto.type.employee'

	adelanto_type_id = fields.Many2one('hr.adelanto.type','Tipo de adelanto')
	account_id = fields.Many2one('account.account','Cuenta contable')
	employee_id = fields.Many2one('hr.employee','Trabajador')
