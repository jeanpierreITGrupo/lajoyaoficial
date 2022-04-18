# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp     import models, fields, api
import base64
import codecs
import datetime

from xlsxwriter.workbook import Workbook
import io
import os
import sys

class hr_employee(models.Model):
	_inherit = 'hr.employee'
	
	familiar_id  = fields.One2many('hr.datos.familiares','employee_id','tipo adelanto')
	emergency_id = fields.One2many('hr.emergency.phones','employee_id','llamada de emergencia')

	@api.multi
	def excel_menores_edad(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo    = u'Hijos_menores_de_18'
		workbook  = Workbook(direccion + titulo + '.xlsx')
		worksheet = workbook.add_worksheet("Menores_de_Edad")

		basic = {
			'align'		: 'left',
			'valign'	: 'vcenter',
			'text_wrap'	: 1,
			'font_size'	: 9,
			'font_name'	: 'Calibri'
		}

		numeric = basic.copy()
		numeric['align'] = 'right'
		numeric['num_format'] = '#,##0.00'

		numeric_int = basic.copy()
		numeric_int['align'] = 'right'

		numeric_int_bold_format = numeric.copy()
		numeric_int_bold_format['bold'] = 1

		numeric_bold_format = numeric.copy()
		numeric_bold_format['bold'] = 1
		numeric_bold_format['num_format'] = '#,##0.00'

		bold = basic.copy()
		bold['bold'] = 1

		header = bold.copy()
		header['bg_color'] = '#A9D0F5'
		header['border'] = 1
		header['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 15

		basic_format            = workbook.add_format(basic)
		bold_format             = workbook.add_format(bold)
		numeric_int_format      = workbook.add_format(numeric_int)
		numeric_int_bold_format = workbook.add_format(numeric_int_bold_format)
		numeric_format          = workbook.add_format(numeric)
		numeric_bold_format     = workbook.add_format(numeric_bold_format)
		title_format            = workbook.add_format(title)
		header_format           = workbook.add_format(header)

		rc = self.env['res.company'].search([])[0]
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', "RUC: "+rc.partner_id.type_number if rc.partner_id.type_number else 'RUC: ', title_format)

		headers = [u'DNI', u'Nombre', u'Parentezco', u'F. Nacimiento', u'Edad', u'Estudiante', u'Nombre Trabajador']

		for pos in range(len(headers)):
			worksheet.write(3,pos, headers[pos], header_format)

		row = 4
		for employee in self:
			for fam in employee.familiar_id:
				flag = False
				if fam.relative.code in ['05','06']:
					if fam.estudiante:
						if fam.age < 24:
							flag = True
					else:
						if fam.age < 18:
							flag = True

				if flag:					
					worksheet.write(row, 0, fam.documento if fam.documento else '', basic_format)
					worksheet.write(row, 1, fam.name if fam.name else '', basic_format)
					worksheet.write(row, 2, fam.relative.description if fam.relative.description else '', basic_format)
					worksheet.write(row, 3, fam.birth_date if fam.birth_date else '', basic_format)
					worksheet.write(row, 4, fam.age if fam.age else '', numeric_int_format)
					worksheet.write(row, 5, 'SI' if fam.estudiante else 'NO', basic_format)
					worksheet.write(row, 6, fam.employee_id.name_related if fam.employee_id.name_related else '', basic_format)
					row += 1

		col_sizes = [9.86, 24.71, 41.43]
		worksheet.set_column('A:A', col_sizes[0])
		worksheet.set_column('B:B', col_sizes[2])
		worksheet.set_column('C:C', col_sizes[1])
		worksheet.set_column('D:F', col_sizes[0])
		worksheet.set_column('G:G', col_sizes[2])

		workbook.close()

		f = open(direccion + titulo + '.xlsx', 'rb')
		
		vals = {
			'output_name': titulo + '.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id  = self.env['export.file.save'].create(vals)

		return {
			"type"     : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"    : [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
		}


class hr_datos_familiares(models.Model):
	_name = 'hr.datos.familiares'

	employee_id = fields.Many2one('hr.employee','padre')

	name       = fields.Char('Nombre')
	relative   = fields.Many2one('hr.vinculo.familiar', u'Parentesco', required=True)
	birth_date = fields.Date('Fecha de Nacimiento', required=True)
	age        = fields.Integer('Edad', compute="compute_age")
	documento  = fields.Char(u'Nº Documento')
	estudiante = fields.Boolean(u'Estudiante')

	@api.one
	def compute_age(self):
		c_age = 0
		if self.birth_date:
			bd = datetime.datetime.strptime(self.birth_date, "%Y-%m-%d")
			td = datetime.datetime.today()
			c_age = td.year - bd.year - 1
			if (bd.month >= td.month) and (bd.day >= td.day):
				c_age += 1
		self.age = c_age

class hr_emergency_phones(models.Model):
	_name = 'hr.emergency.phones'

	employee_id = fields.Many2one('hr.employee','padre')
	
	name  = fields.Char('Nombre')
	phone = fields.Char(u'Teléfono')

class hr_vinculo_familiar(models.Model):
	_name     = 'hr.vinculo.familiar'
	_rec_name = 'name'

	name        = fields.Char(u'Nombre', required=True)
	description = fields.Char(u'Descripción')
	code        = fields.Char(u'Código', required=True)