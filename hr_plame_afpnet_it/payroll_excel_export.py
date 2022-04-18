# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint
import io
from xlsxwriter.workbook import Workbook
import sys
from datetime import datetime
import os

class hr_planilla1(models.Model):
	_inherit = 'hr.planilla1'

	@api.multi
	def export_plame(self):
		#-------------------------------------------Datos---------------------------------------------------
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion + 'Planilla.xlsx')
		worksheet = workbook.add_worksheet("Reporte Planilla")

		#----------------Formatos------------------
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

		basic_format = workbook.add_format(basic)
		numeric_format = workbook.add_format(numeric)
		bold_format = workbook.add_format(bold)
		numeric_bold_format = workbook.add_format(numeric_bold_format)
		header_format = workbook.add_format(header)
		title_format = workbook.add_format(title)

		nro_columnas = 8
			
		tam_col = [0]*nro_columnas
		
		#----------------------------------------------Título--------------------------------------------------
		rc = self.env['res.company'].search([])[0]
		cabecera = rc.name
		worksheet.merge_range('A1:B1', cabecera, title_format)
		
		#---------------------------------------------Cabecera-----------------------------------------------
		worksheet.merge_range('A2:D2', "Planilla Mensual", bold_format)
		#worksheet.write('A3', "Periodo :", bold_format)
		fil = 5
		col = 0
		worksheet.write(fil, col, "Periodo", header_format)
		col += 1
		worksheet.write(fil, col, "Tipo Documento", header_format)
		col += 1
		worksheet.write(fil, col, "Nro. Documento", header_format)
		col += 1
		worksheet.write(fil, col, u"Código", header_format)
		col += 1
		worksheet.write(fil, col, "Nombre", header_format)
		col += 1
		worksheet.write(fil, col, u"Area", header_format)
		col += 1
		worksheet.write(fil, col, u"Ubicación", header_format)
		col += 1
		worksheet.write(fil, col, u"Cargo", header_format)
		col += 1
		worksheet.write(fil, col, u"Afiliación", header_format)
		col += 1
		worksheet.write(fil, col, u"Tipo Comisión", header_format)
		col += 1

		im = self.env['ir.model'].search([('name','=',self._inherit)])
		hlc = self.env['hr.lista.conceptos'].search([]).sorted(key=lambda r: r.position)
		for concepto in hlc:
			imf = self.env['ir.model.fields'].search([('model_id','=',im[0].id),('state','=','manual'),('name','=','x_'+concepto.code)])
			if len(imf) > 0:
				worksheet.write(fil, col, imf[0].field_description, header_format)
				col += 1

		fil = 6
		totals = [0]*len(hlc)
		planilla = self.env['hr.planilla1'].search([])

		for line in planilla:
			col = 0
			worksheet.write(fil, col, line.periodo.code if line.periodo.code else '', basic_format)
			col += 1
			worksheet.write(fil, col, line.type_doc if line.type_doc else '', basic_format)
			col += 1
			worksheet.write(fil, col, line.dni if line.dni else '', basic_format)
			col += 1
			worksheet.write(fil, col, line.codigo_trabajador if line.codigo_trabajador else '', basic_format)
			col += 1
			nombre = line.first_name_complete if line.first_name_complete else ''
			nombre = nombre +' '+line.last_name_father if line.last_name_father else ''
			nombre = nombre +' '+line.last_name_mother if line.last_name_mother else ''
			worksheet.write(fil, col, nombre if nombre else '', basic_format)
			col += 1
			worksheet.write(fil, col, line.department_id.name if line.department_id.name else '', basic_format)
			col += 1
			worksheet.write(fil, col, line.ubicacion_id.name if line.ubicacion_id.name else '', basic_format)
			col += 1
			worksheet.write(fil, col, line.cargo.name if line.cargo.name else '', basic_format)
			col += 1
			worksheet.write(fil, col, line.afiliacion.name if line.afiliacion.name else '', basic_format)
			col += 1
			worksheet.write(fil, col, "SI COM. MIXTA" if line.tipo_comision else "NO COM. MIXTA", basic_format)
			col += 1
			for concepto in hlc:
				imf = self.env['ir.model.fields'].search([('model_id','=',im[0].id),('state','=','manual'),('name','=','x_'+concepto.code)])
				if len(imf) > 0:
					f = "line." + eval("imf[0].name")
					worksheet.write(fil, col, eval(f), numeric_format)
					totals[col-10] += eval(f)
					col += 1
			fil += 1

		col = 10
		for tot in totals:
			worksheet.write(fil, col, tot, numeric_bold_format)
			col += 1

		tam_col = [10, 20, 15, 11]
		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[0])
		worksheet.set_column('C:C', tam_col[0])
		worksheet.set_column('D:D', tam_col[1])
		worksheet.set_column('E:E', tam_col[2])
		worksheet.set_column('F:AX', tam_col[3])
		worksheet.set_column('AY:AY', tam_col[2])
		worksheet.set_column('AZ:CC', tam_col[3])

		workbook.close()

		f = open(direccion + 'Planilla.xlsx', 'rb')
		
		vals = {
			'output_name': 'Planilla.xlsx',
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


	@api.multi
	def export_afp_net(self):
		#-------------------------------------------Datos---------------------------------------------------
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion + 'AFP Net.xlsx')
		worksheet = workbook.add_worksheet("Reporte AFP")

		#----------Formatos---------------------
		basic = {
			'align'		: 'left',
			'valign'	: 'vcenter',
			'text_wrap'	: 1,
			'font_size'	: 9,
			'font_name'	: 'Calibri'
		}

		numeric = basic.copy()
		numeric['num_format'] = '0.00'
		numeric['align'] = 'right'

		bold = basic.copy()
		bold['bold'] = 1

		header = bold.copy()
		header['bg_color'] = '#2ECCFA'
		header['border'] = 1
		header['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 15

		basic_format = workbook.add_format(basic)
		numeric_format = workbook.add_format(numeric)
		bold_format = workbook.add_format(bold)
		header_format = workbook.add_format(header)
		title_format = workbook.add_format(title)

		nro_columnas = 17
			
		tam_col = [0]*nro_columnas
		
		#----------------------------------------------Título--------------------------------------------------
		
		#---------------------------------------------Cabecera------------------------------------------------

		#------------------------------------------Insertando Data----------------------------------------------
		fil = 0
		col = 0
		planilla = self.env['hr.planilla1'].search([])
		hlc = self.env['hr.lista.conceptos'].search([('code','=','047')])
		
		
		# esta consulta va a tarer los montos del tareo que tengan conceptos amrcados con elementos de afp
		cadsql = """select ingresos-descuentos as monto, a.employee_idd from (
			select * from (
			select sum(hr_concepto_line.monto) as ingresos,
			hr_tareo_line.employee_id as employee_idi
			from hr_tareo_line
			inner join hr_concepto_line on hr_tareo_line.id = hr_concepto_line.tareo_line_id
			inner join hr_lista_conceptos on hr_concepto_line.concepto_id = hr_lista_conceptos.id
			inner join hr_concepto_remunerativo_line on hr_concepto_remunerativo_line.concepto = hr_lista_conceptos.id
			where hr_lista_conceptos.payroll_group = '1' and
			(afp_fon_pen = true or 
			afp_pri_se = true or 
			afp_co_va = true or 
			afp_co_mix = true or  
			afp_2p = true)
			and hr_tareo_line.tareo_id = """+str(planilla[0].tareo_id.id)+"""
			group by hr_tareo_line.employee_id) ingresos
			inner join (select sum(hr_concepto_line.monto) as descuentos,
			hr_tareo_line.employee_id  as employee_idd
			from hr_tareo_line
			inner join hr_concepto_line on hr_tareo_line.id = hr_concepto_line.tareo_line_id
			inner join hr_lista_conceptos on hr_concepto_line.concepto_id = hr_lista_conceptos.id
			inner join hr_concepto_remunerativo_line on hr_concepto_remunerativo_line.concepto = hr_lista_conceptos.id
			where hr_lista_conceptos.payroll_group = '2' and
			(afp_fon_pen = true or 
			afp_pri_se = true or 
			afp_co_va = true or 
			afp_co_mix = true or  
			afp_2p = true)
			and hr_tareo_line.tareo_id = """+str(planilla[0].tareo_id.id)+"""
			group by hr_tareo_line.employee_id) descuentos on ingresos.employee_idi = descuentos.employee_idd) a
			order by employee_idd"""

		self.env.cr.execute(cadsql)
		data_monto = self.env.cr.dictfetchall()
		
		
		
		
		for line in planilla:
			col = 0
			employee = self.env['hr.employee'].search([('id','=', line.employee_id.id)])
			if len(employee) and employee.afiliacion.name not in ['ONP','SIN REGIMEN']:
				period = line.periodo.code.split("/")
				worksheet.write(fil, col, fil+1, basic_format)
				col += 1
				worksheet.write(fil, col, employee.cusspp if employee.cusspp else "", basic_format)
				col += 1
				worksheet.write(fil, col, employee.type_document_id.afpnet_code if employee.type_document_id.afpnet_code else '', basic_format)
				col += 1
				worksheet.write(fil, col, employee.identification_id if employee.identification_id else '', basic_format)
				col += 1
				worksheet.write(fil, col, employee.last_name_father if employee.last_name_father else '', basic_format)
				col += 1
				worksheet.write(fil, col, employee.last_name_mother if employee.last_name_mother else '', basic_format)
				col += 1
				worksheet.write(fil, col, employee.first_name_complete if employee.first_name_complete else '', basic_format)
				col += 1
				worksheet.write(fil, col, 'S', basic_format)
				col += 1
				if employee.fecha_ingreso:
					date_employee = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
					if date_employee.month == int(period[0]) and date_employee.year == int(period[1]):
						worksheet.write(fil, col, 'S', basic_format)
					else:
						worksheet.write(fil, col, 'N', basic_format)
				else:
					worksheet.write(fil, col, 'N', basic_format)
				col += 1
				if employee.fecha_cese:
					date_employee = datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d')
					if date_employee.month == int(period[0]) and date_employee.year == int(period[1]):
						worksheet.write(fil, col, 'S', basic_format)
					else:
						worksheet.write(fil, col, 'N', basic_format)
				else:
					worksheet.write(fil, col, 'N', basic_format)
				col += 1
				worksheet.write(fil, col, " ", numeric_format)
				
				monto = 0
				# esto se debe de optimizar con un filter al diccionario
				for a in data_monto:
					if employee.id == a['employee_idd']:
						monto = a['monto']
				
				col += 1
				worksheet.write(fil, col, monto, numeric_format)
				
				
				
				
				# col += 1
				# if len(hlc) > 0:
					# hlc = hlc[0]
					# f = "line.x_"+hlc.code
					# worksheet.write(fil, col, eval(f), numeric_format)
				# else:
					# worksheet.write(fil, col, 0, numeric_format)
				col += 1
				worksheet.write(fil, col, 0, basic_format)
				col += 1
				worksheet.write(fil, col, 0, basic_format)
				col += 1
				worksheet.write(fil, col, 0, basic_format)
				col += 1
				if employee.afp_2p:
					worksheet.write(fil, col, 'M', basic_format)
					col += 1
				else:
					worksheet.write(fil, col, 'N', basic_format)
					col += 1
				worksheet.write(fil, col, " ", basic_format)
				col += 1
				fil += 1

		col_size = [3, 12, 18]
		worksheet.set_column('A:A', col_size[0])
		worksheet.set_column('B:B', col_size[1])
		worksheet.set_column('C:C', col_size[0])
		worksheet.set_column('D:F', col_size[1])
		worksheet.set_column('G:G', col_size[2])
		worksheet.set_column('H:K', col_size[0])
		worksheet.set_column('M:Q', col_size[0])
		workbook.close()

		f = open(direccion + 'AFP Net.xlsx', 'rb')
		
		vals = {
			'output_name': 'AFP Net.xlsx',
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


