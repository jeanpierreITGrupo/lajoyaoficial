# -*- encoding: utf-8 -*-
from openerp     import models, fields, api
from openerp.osv import osv, expression
from datetime    import datetime, timedelta
from calendar    import monthrange
import pprint
import codecs
import base64
import decimal
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_RIGHT

import io
import sys
import os


from xlsxwriter.workbook       import Workbook
from reportlab.pdfgen          import canvas
from reportlab.lib.units       import inch
from reportlab.lib.colors      import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase         import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes   import letter, A4, landscape
from reportlab.platypus        import SimpleDocTemplate, Table, TableStyle,BaseDocTemplate, PageTemplate, Frame, Paragraph, Table, PageBreak, Spacer, FrameBreak,Image
from reportlab.lib             import colors
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units       import  cm,mm
from reportlab.lib.utils       import simpleSplit
from cgi                       import escape
from reportlab                 import platypus

class hr_reporte_cc_wizard(models.TransientModel):
	_name = 'hr.reporte.cc.wizard'

	@api.multi
	def make_excel(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

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

		numeric_int_bold = numeric.copy()
		numeric_int_bold['bold'] = 1

		numeric_bold = numeric.copy()
		numeric_bold['bold'] = 1
		numeric_bold['num_format'] = '#,##0.00'

		bold = basic.copy()
		bold['bold'] = 1

		header = bold.copy()
		header['bg_color'] = '#A9D0F5'
		header['border'] = 1
		header['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 15

		highlight_line = basic.copy()
		highlight_line['bold'] = 1
		highlight_line['bg_color'] = '#C1E1FF'

		highlight_numeric_line = highlight_line.copy()
		highlight_numeric_line['num_format'] = '#,##0.00'
		highlight_numeric_line['align'] = 'right'		

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo    = u'Reporte_CC'
		workbook  = Workbook(direccion + titulo + '.xlsx')

		worksheet = workbook.add_worksheet("Centro de Costo")
		worksheet_sin_cc = workbook.add_worksheet("Sin Distribucion C.C.")
		
		basic_format                  = workbook.add_format(basic)
		bold_format                   = workbook.add_format(bold)
		numeric_int_format            = workbook.add_format(numeric_int)
		numeric_int_bold_format       = workbook.add_format(numeric_int_bold)
		numeric_format                = workbook.add_format(numeric)
		numeric_bold_format           = workbook.add_format(numeric_bold)
		title_format                  = workbook.add_format(title)
		header_format                 = workbook.add_format(header)
		highlight_line_format         = workbook.add_format(highlight_line)
		highlight_numeric_line_format = workbook.add_format(highlight_numeric_line)


		str_cross = ""
		str_select = ""
		headers = ["Apellido Paterno","Apellido Materno","Nombres",u"Codigo Trabajador","Fecha de Ingreso","Fecha de Cese"]
		hca = self.env['hr.cuentas.analiticas'].search([]).sorted(key=lambda r: r.code)
		for item in hca:
			str_cross  += '"' + item.code + ' ' + item.name +'" text,'
			str_select += 'conceptos."' + item.code + ' ' + item.name +'",'
			headers.append(item.code + ' ' + item.name)

		if len(str_cross) > 0:
			str_cross  = str_cross[:-1]
			str_select  = str_select[:-1]

		sql = """SELECT
				 he.last_name_father AS "Apellido Paterno",
				 he.last_name_mother AS "Apellido Materno",
				 he.first_name_complete AS "Nombres",
				 he.codigo_trabajador AS "Codigo Trabajador",
				 he.fecha_ingreso AS "Fecha de Ingreso",
				 he.fecha_cese AS "Fecha de Cese",
				 """+str_select+"""
				 FROM
				 (SELECT *
				 FROM crosstab(
				 	'
				 	SELECT
					he.id AS "employee_id",
					hca.code || '' '' || hca.name AS "cuenta_analitica",
					hdgl.porcentaje || '' %'' AS "porcentaje"
					FROM hr_employee he
					LEFT JOIN hr_distribucion_gastos hdg ON he.dist_c = hdg.id
					LEFT JOIN hr_distribucion_gastos_linea hdgl ON hdgl.distribucion_gastos_id = hdg.id
					LEFT JOIN hr_cuentas_analiticas hca ON hdgl.analitica = hca.id
					WHERE he.dist_c IS NOT NULL
					ORDER BY 1,2
				 	',
				 	'
				 	SELECT
					code || '' '' || name AS "cuenta_analitica"
					FROM
					hr_cuentas_analiticas
					ORDER BY 1
				 	'
			 	 ) AS ct (employee_id integer, """+str_cross+""")) conceptos
				 LEFT JOIN hr_employee he ON conceptos.employee_id = he.id
				 ORDER BY he.last_name_father
			 	 """

		# file = open('C:/Users/caja16/Desktop/sqldistribuciondelavida.txt','w')
		# file.write(sql)
		# print sql
		# file.close()

		self.env.cr.execute(sql)
		res_sql = self.env.cr.dictfetchall()

		rc = self.env['res.company'].search([])[0]
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', "RUC: "+rc.partner_id.type_number if rc.partner_id.type_number else 'RUC: ', title_format)

		row = 2
		col = 0

		row += 1
		for pos in range(len(headers)):
			worksheet.write(row,pos, headers[pos], header_format)

		row += 1
		for data in res_sql:
			for k,v in data.items():
				worksheet.write(row,headers.index(k),v,basic_format)
			row += 1

		col_sizes = [16.00, 24.71, 41.43]
		worksheet.set_column('A:M', col_sizes[0])

		rc = self.env['res.company'].search([])[0]
		worksheet_sin_cc.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet_sin_cc.merge_range('A2:D2', "RUC: "+rc.partner_id.type_number if rc.partner_id.type_number else 'RUC: ', title_format)

		row = 2
		col = 0

		row += 1
		headers2 = ["Apellido Paterno","Apellido Materno","Nombres",u"Codigo Trabajador","Fecha de Ingreso","Fecha de Cese"]
		for pos in range(len(headers2)):
			worksheet_sin_cc.write(row,pos, headers[pos], header_format)
		row += 1

		hscc = self.env['hr.employee'].search([('dist_c','=',False)])
		for data in hscc:
			col = 0
			worksheet_sin_cc.write(row,col,data.last_name_father,basic_format)
			col += 1
			worksheet_sin_cc.write(row,col,data.last_name_mother,basic_format)
			col += 1
			worksheet_sin_cc.write(row,col,data.first_name_complete,basic_format)
			col += 1
			worksheet_sin_cc.write(row,col,data.codigo_trabajador,basic_format)
			col += 1
			worksheet_sin_cc.write(row,col,data.fecha_ingreso if data.fecha_ingreso else '',basic_format)
			col += 1
			worksheet_sin_cc.write(row,col,data.fecha_cese if data.fecha_cese else '',basic_format)
			col += 1
			row += 1

		worksheet_sin_cc.set_column('A:M', col_sizes[0])

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