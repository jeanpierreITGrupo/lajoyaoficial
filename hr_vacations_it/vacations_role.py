# -*- coding: utf-8 -*-
from openerp                import models, fields, api
from openerp.osv            import osv
import base64

from dateutil.relativedelta import *
import codecs
import pprint
import io
import sys
import os
from xlsxwriter.workbook    import Workbook
from datetime               import datetime


class vacation_role(models.Model):
	_name = "vacation.role"
	_rec_name = 'period_id'

	period_id = fields.Many2one('account.period', u"Perido", required=1)
	total     = fields.Integer("Cantidad", readonly=1)
	state     = fields.Boolean('Guardado', default=False)

	vacation_lines = fields.One2many('vacation.role.line', 'parent')

	@api.model
	def create(self,vals):
		vals['state'] = True
		return super(vacation_role,self).create(vals)

	@api.one
	def unlink(self):
		for vacation in self.vacation_lines:
			for partial in vacation.lines:
				partial.unlink()
			vacation.unlink()
		return super(vacation_role,self).unlink()

	@api.multi
	def find_employees(self):
		if self.state:
			employees = self.env['hr.employee'].search([('fecha_cese','=',False)])
			vacation_line = self.env['vacation.role.line']
			data = []
			value = {}
			if self.vacation_lines:
				for line in self.vacation_lines:
					line.unlink()

			total = 0
			for employee in employees:
				vals = {
					'employee_id'	: employee.id,
					'employee_code'	: employee.codigo_trabajador,
					'last_name'		: employee.last_name_father,
					'surname'		: employee.last_name_mother,
					'name'			: employee.first_name_complete,
					'in_date'		: employee.fecha_ingreso,
					'parent'		: self.id
				}
				vacation_line.create(vals)
				total += 1
			self.total = total
			return True

	@api.multi
	def get_excel(self):
		#-------------------------------------------Datos---------------------------------------------------
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion + 'Vacaciones.xlsx')
		worksheet = workbook.add_worksheet("Deudores")

		#----------Formatos---------------------
		basic = {
			'align'		: 'left',
			'valign'	: 'vcenter',
			'text_wrap'	: 1,
			'font_size'	: 9,
			'font_name'	: 'Calibri'
		}

		bold = basic.copy()
		bold['bold'] = 1

		basic_number = basic.copy()
		basic_number['align'] = 'right'

		header = bold.copy()
		header['bg_color'] = '#2ECCFA'
		header['border'] = 1
		header['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 18

		basic_format = workbook.add_format(basic)
		basic_number_format = workbook.add_format(basic_number)
		bold_format = workbook.add_format(bold)
		header_format = workbook.add_format(header)
		title_format = workbook.add_format(title)

		nro_columnas = 8
			
		tam_col = [0]*nro_columnas
		
		#----------------------------------------------Título--------------------------------------------------
		cabecera = "Rol de Vacaciones"
		worksheet.merge_range('A1:D1', cabecera, title_format)
		
		#---------------------------------------------Cabecera-----------------------------------------------
		worksheet.write('A3', u"Periodo", bold_format)
		worksheet.write('A4', "Cantidad", bold_format)
		worksheet.write('B6', u"Código del Trabajador", header_format)
		worksheet.write('C6', "Apellido Paterno", header_format)
		worksheet.write('D6', "Apellido Materno", header_format)
		worksheet.write('E6', "Nombres", header_format)
		worksheet.write('F6', "Periodo", header_format)
		worksheet.write('G6', "Fecha Ingreso", header_format)
		worksheet.write('H6', u"Días", header_format)
				
		worksheet.write('B3', self.period_id.code, basic_format)
		worksheet.write('B4', self.total, basic_format)


		#............Escribe en archivo Excel
		top_shift = 7
		for line in self.vacation_lines:
			worksheet.write('B'+str(top_shift), line.employee_code, basic_format)
			worksheet.write('C'+str(top_shift), line.last_name, basic_format)
			worksheet.write('D'+str(top_shift), line.surname, basic_format)
			worksheet.write('E'+str(top_shift), line.name, basic_format)
			worksheet.write('F'+str(top_shift), line.period, basic_number_format)
			worksheet.write('G'+str(top_shift), line.in_date if line.in_date else "", basic_format)
			worksheet.write('H'+str(top_shift), line.days if line.days > 0 else 0, basic_number_format)
			top_shift += 1


		tam_col = [10, 15, 15, 15, 15, 15, 15, 15, 15, 15]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])

		workbook.close()

		f = open(direccion + 'Vacaciones.xlsx', 'rb')
		
		vals = {
			'output_name': 'Vacaciones.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}


class vacation_role_line(models.Model):
	_name = "vacation.role.line"

	parent = fields.Many2one('vacation.role', "Vacation Role")

	employee_id   = fields.Many2one('hr.employee','Empleado')
	employee_code = fields.Char("Código del Trabajador", size=4, readonly=1)
	last_name     = fields.Char("Apellido Paterno", readonly=1)
	surname       = fields.Char("Apellido Materno", readonly=1)
	name          = fields.Char("Nombres", readonly=1)
	in_date       = fields.Date("Fecha de Ingreso", readonly=1)
	period        = fields.Integer("Periodo", compute='compute_period', readonly=1, store=1)
	days          = fields.Integer(u'Días', compute="compute_days")

	lines = fields.One2many('partial.vacation.line', 'parent', "Vacaciones parciales")

	@api.depends('in_date')
	def compute_period(self):
	    self.period = self.in_date.split("-", 2)[1]

	@api.one
	def compute_days(self):
		res = 0
		for partial in self.lines:
			res += partial.days
		self.days = res

	@api.one
	def save_data(self):
		htl = self.env['hr.tareo.line'].search([('tareo_id.periodo','=',self.parent.period_id.id),('employee_id','=',self.employee_id.id)])
		for line in htl:
			line.dias_vacaciones = self.days
			line.with_context({'active_id':line.id}).onchange_all()
		return True

	@api.multi
	def open_wizard(self):
		return {
			'type'     : 'ir.actions.act_window',
			'name'     : "Detalle Vacaciones",
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'vacation.role.line',
			'res_id'   : self.id,
			'target'   : 'new',
		}


class partial_vacation_line(models.Model):
	_name = 'partial.vacation.line'

	parent        = fields.Many2one('vacation.role.line',"Vacaciones")
	
	init_date     = fields.Date("Fecha inicio")
	end_date      = fields.Date("Fecha fin")
	days          = fields.Integer(u"Cantidad días")
	parent_wizard = fields.Many2one('vacation.role.line',"Vacaciones")

	@api.onchange('init_date', 'end_date')
	def onchange_dates(self):
		if self.init_date and self.end_date:
			self.days = relativedelta(datetime.strptime(str(self.end_date), '%Y-%m-%d'),datetime.strptime(str(self.init_date), '%Y-%m-%d')).days+1