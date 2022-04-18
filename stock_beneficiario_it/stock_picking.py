# -*- encoding: utf-8 -*-
import base64
from openerp.osv import osv
from openerp import models, fields, api

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	is_employee   = fields.Boolean('Es Empleado')
	b_employee_id = fields.Many2one('hr.employee','Beneficiario')
	department_he = fields.Char('Departamento')
	b_partner_id  = fields.Many2one('res.partner','Beneficiario')
	department_rp = fields.Char('Departamento')

	@api.onchange('b_employee_id')
	def onchange_b_employee_id(self):
		if self.b_employee_id.id == False:
			self.department_he = False
		else:
			self.department_he = (self.b_employee_id.department_id.parent_id.name if self.b_employee_id.department_id.parent_id.name else "") + " / " + (self.b_employee_id.department_id.name if self.b_employee_id.department_id.name else "")