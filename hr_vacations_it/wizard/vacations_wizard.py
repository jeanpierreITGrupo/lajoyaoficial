# -*- coding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs


class vacation_wizard(models.TransientModel):
	_name = "vacation.wizard"

	period = fields.Many2one('account.period', u"Periodo")
	name = fields.Many2one('hr.employee',"Nombre")
	vacation_lines = fields.One2many('vacation.line.wizard', 'parent')

	@api.onchange('period', 'name')
	def on_change_period(self):
		roles = self.env['vacation.role'].search([])
		vacation_line = self.env['vacation.line.wizard']
		data = []
		if self.period:
			period = self.period.code.split("/")			
			for role in roles:
				if role.period_id.id == self.period.id:
					for line in role.vacation_lines:
						# if int(line.in_date.split("-")[1]) == int(period[0]):
						if self.name and (line.name.upper() + " " + line.last_name.upper() + " " + line.surname.upper()) == self.name.name_related.upper():
							vals = {
								'employee_code'	: line.employee_code,
								'last_name'		: line.last_name,
								'surname'		: line.surname,
								'period'		: line.in_date.split("-")[1],
								'year'			: role.period_id.code,
								'name'			: line.name,
								'in_date'		: line.in_date,
								'days'			: line.days,
							}
							lines = []
							for orig_line in line.lines:
								lines.append((0,0,{'days':orig_line.days}))
							vals['lines'] = lines
							data.append((0,0,vals))
						elif not self.name:
							vals = {
								'employee_code'	: line.employee_code,
								'last_name'		: line.last_name,
								'surname'		: line.surname,
								'period'		: line.in_date.split("-")[1],
								'year'			: role.period_id.code,
								'name'			: line.name,
								'in_date'		: line.in_date,
								'days'			: line.days,
							}
							lines = []
							for orig_line in line.lines:
								lines.append((0,0,{'days':orig_line.days}))
							vals['lines'] = lines
							data.append((0,0,vals))
					self.vacation_lines = data
					break
		elif self.name:
			for role in roles:
				for line in role.vacation_lines:
					if (line.name.upper() + " " + line.last_name.upper() + " " + line.surname.upper()) == self.name.name_related.upper():
						vals = {
							'employee_code'	: line.employee_code,
							'last_name'		: line.last_name,
							'surname'		: line.surname,
							'period'		: line.in_date.split("-")[1],
							'year'			: role.period_id.code,
							'name'			: line.name,
							'in_date'		: line.in_date,
							'days'			: line.days,
						}
						lines = []
						for orig_line in line.lines:
							lines.append((0,0,{'days':orig_line.days}))
						vals['lines'] = lines
						data.append((0,0,vals))
				self.vacation_lines = data


			

class vacation_line_wizard(models.TransientModel):
	_name = "vacation.line.wizard"

	employee_code = fields.Char("Código del Trabajador", size=4, readonly="1")
	last_name     = fields.Char("Apellido Paterno", readonly="1")
	surname       = fields.Char("Apellido Materno", readonly="1")
	name          = fields.Char("Nombres", readonly="1")
	in_date       = fields.Date("Fecha de Ingreso", readonly="1")
	period        = fields.Integer("Periodo", readonly="1")
	year          = fields.Char(u"Rol de Vacaciones", readonly="1")
	parent        = fields.Many2one('vacation.wizard', "Vacation")
	lines         = fields.One2many('partial.vacation.line', 'parent_wizard', "Vacaciones parciales")
	days		  = fields.Integer(u'Días', readonly=True)

	@api.multi
	def open_wizard(self):
		return {
			'type'     : 'ir.actions.act_window',
			'name'     : "Detalle Vacaciones",
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'vacation.line.wizard',
			'res_id'   : self.id,
			'target'   : 'new',
		}