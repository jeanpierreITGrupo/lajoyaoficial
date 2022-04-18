# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class hr_employee(models.Model):
	_inherit = 'hr.employee'

	@api.one
	def compute_last_name_full(self):
		self.last_name_full = " ".join([self.last_name_father.upper() if self.last_name_father else '', self.last_name_mother.upper() if self.last_name_mother else ''])

	@api.one
	def compute_name_upper(self):
		self.name_upper = self.first_name_complete.upper() if self.first_name_complete else ''

	last_name_full = fields.Char('Apellidos', compute="compute_last_name_full")
	name_upper     = fields.Char('Nombres', compute="compute_name_upper")