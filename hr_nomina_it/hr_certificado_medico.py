# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp     import models, fields, api
import base64
import codecs

from xlsxwriter.workbook import Workbook
import io
import os
import sys

class hr_certificado_medico(models.Model):
	_name     = 'hr.certificado.medico'
	_rec_name = 'name'

	name              = fields.Many2one('hr.employee','Nombre', required=True)
	codigo_trabajador = fields.Char(u'Código Trabajador', readonly=True)
	cargo             = fields.Char(u'Cargo', readonly=True)
	birth_date        = fields.Date(u'Fecha de Nacimiento', readonly=True)
	start_date        = fields.Date(u'Fecha de Inicio', readonly=True)
	basico            = fields.Float(u'Básico', readonly=True)

	certificado_lines = fields.One2many('hr.certificado.medico.lines','certificado_id','Lineas')

	@api.model
	def create(self, vals):
		he = self.env['hr.employee'].search([('id','=',vals['name'])])[0]
		vals['codigo_trabajador'] = he.codigo_trabajador
		vals['cargo']             = he.job_id.name
		vals['birth_date']        = he.birthday
		vals['start_date']        = he.fecha_ingreso
		vals['basico']            = he.basica
		t = super(hr_certificado_medico, self).create(vals)
		return t

	@api.one
	def write(self, vals):
		if 'name' in vals:
			he = self.env['hr.employee'].search([('id','=',vals['name'])])[0]
			vals['codigo_trabajador'] = he.codigo_trabajador
			vals['cargo']             = he.job_id.name
			vals['birth_date']        = he.birthday
			vals['start_date']        = he.fecha_ingreso
			vals['basico']            = he.basica

			for line in self.certificado_lines:
				line.unlink()
		t = super(hr_certificado_medico, self).write(vals)
		return t

	@api.multi
	def excel_certificado_medico(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo    = u'Certificados_Medicos'
		workbook  = Workbook(direccion + titulo + '.xlsx')
		worksheet = workbook.add_worksheet("Certificados")

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
		worksheet.merge_range('A2:D2', ("RUC: "+rc.partner_id.type_number) if rc.partner_id.type_number else 'RUC: ', title_format)
		headers = [u'N°', 
				   u'Nombre', 
				   u'Cargo', 
				   u'Fecha de Nacimiento', 
				   u'Fecha de Ingreso', 
				   u'Seguro SCTR', 
				   u'Particular',
				   u'Fecha del Accidente o Enfermedad',
				   u'Motivo',
				   u'N° Certificado',
				   u'Fecha de Inicio',
				   u'Fecha de Fin',
				   u'Cubre Empresa (20 Días)',
				   u'N° Días',
				   u'Subsidio',
				   u'N° Días',
				   u'Cobro de Subsidio',]

		for pos in range(len(headers)):
			worksheet.write(3,pos, headers[pos], header_format)

		n_cert = 1
		
		row = 4
		for certificado in self.sorted(key=lambda r: r.name.name_related):
			sum_days = [0]*2
			for line in certificado.certificado_lines:
				worksheet.write(row, 0, n_cert, numeric_int_format)
				worksheet.write(row, 1, certificado.name.name_related if certificado.name.name_related else '', basic_format)
				worksheet.write(row, 2, certificado.name.job_id.name if certificado.name.job_id.name else '', basic_format)
				worksheet.write(row, 3, certificado.name.birthday if certificado.name.birthday else '', basic_format)
				worksheet.write(row, 4, certificado.name.fecha_ingreso if certificado.name.fecha_ingreso else '', basic_format)
				worksheet.write(row, 5, "SI" if line.sctr else 'NO', basic_format)
				worksheet.write(row, 6, "SI" if line.particular else 'NO', basic_format)
				worksheet.write(row, 7, line.accident_date if line.accident_date else '', basic_format)
				worksheet.write(row, 8, line.reason if line.reason else '', basic_format)
				worksheet.write(row, 9, line.nro_cert if line.nro_cert else '', numeric_int_format)
				worksheet.write(row, 10, line.start_date if line.start_date else '', basic_format)
				worksheet.write(row, 11, line.end_date if line.end_date else '', basic_format)
				worksheet.write(row, 12, line.cubre if line.cubre else '', basic_format)
				worksheet.write(row, 13, line.cubre_nro_dias if line.cubre_nro_dias else '', numeric_int_format)
				worksheet.write(row, 14, line.subsidio if line.subsidio else '', basic_format)
				worksheet.write(row, 15, line.subsidio_nro_days if line.subsidio_nro_days else '', numeric_int_format)
				worksheet.write(row, 16, line.cobro_subsidio if line.cobro_subsidio else '', basic_format)

				sum_days[0] += line.cubre_nro_dias
				sum_days[1] += line.subsidio_nro_days
				row += 1

			worksheet.write(row, 12, 'TOTAL', bold_format)
			worksheet.write(row, 13, sum_days[0], numeric_int_bold_format)
			worksheet.write(row, 14, 'TOTAL', bold_format)
			worksheet.write(row, 15, sum_days[1], numeric_int_bold_format)
			row += 2
			n_cert += 1

		col_sizes = [4.43, 13.43, 21.29, 46.86]
		worksheet.set_column('A:A', col_sizes[0])
		worksheet.set_column('B:B', col_sizes[3])
		worksheet.set_column('C:C', col_sizes[2])
		worksheet.set_column('D:D', col_sizes[1])
		worksheet.set_column('E:E', col_sizes[1])
		worksheet.set_column('F:F', col_sizes[0])
		worksheet.set_column('G:G', col_sizes[0])
		worksheet.set_column('H:H', col_sizes[1])
		worksheet.set_column('I:I', col_sizes[3])
		worksheet.set_column('J:J', col_sizes[0])
		worksheet.set_column('K:K', col_sizes[1])
		worksheet.set_column('L:L', col_sizes[1])
		worksheet.set_column('M:M', col_sizes[3])
		worksheet.set_column('N:N', col_sizes[0])
		worksheet.set_column('O:O', col_sizes[3])
		worksheet.set_column('P:P', col_sizes[0])
		worksheet.set_column('Q:Q', col_sizes[3])

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

class hr_certificado_medico_lines(models.Model):
	_name = 'hr.certificado.medico.lines'

	certificado_id = fields.Many2one('hr.certificado.medico','Padre')

	sctr              = fields.Boolean(u'Seguro SCTR')
	particular        = fields.Boolean(u'Particular')
	accident_date     = fields.Date(u'Fecha de Accidente o Enfermedad')
	reason            = fields.Text(u'Motivo')
	nro_cert          = fields.Integer(u'Número de Certificado')
	start_date        = fields.Date(u'Fecha de Inicio')
	end_date          = fields.Date(u'Fecha de Fin')
	cubre             = fields.Text(u'Cubre Empresa (20 Días)')
	cubre_nro_dias    = fields.Integer(u'Número de Días')
	subsidio          = fields.Text(u'Subisidio')
	subsidio_nro_days = fields.Integer(u'Número de Días')
	cobro_subsidio    = fields.Text(u'Cobro de Subsidio')