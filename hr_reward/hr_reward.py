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
from dateutil.relativedelta import *
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, PageBreak, Spacer
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
from reportlab import platypus

class hr_reward(models.Model):
	_name = "hr.reward"
	_rec_name = 'year'

	year         = fields.Many2one('account.fiscalyear', u"Año", required=1)
	period_id    = fields.Many2one('account.period','Periodo',required=True)
	period       = fields.Selection([('07',"Gratificación Fiestas Patrias"),('12',"Gratificación Navidad")], "Mes", required=1)
	plus_9       = fields.Boolean("Considerar Bono 9%")
	reward_lines = fields.One2many('hr.reward.line', 'reward', "Lineas")
	adelanto_lines = fields.One2many('hr.reward.adelanto.lines','reward_id','Lineas')
	deposit_date = fields.Date(u'Fecha depósito')

	def name_get(self, cr, uid, ids, context=None):
		res = []
		for record in self.browse(cr, uid, ids, context=context):
			if record.period == '07':
				res.append((record.id, record.year.code+' - '+'Fiestas Patrias'))
			else:
				res.append((record.id, record.year.code+' - '+'Navidad'))
		return res

	@api.multi
	def open_wizard(self):
		return {
            'name'		: ('Agregar/Reemplazar Empleado'),
            'view_type'	: 'form',
            'view_mode'	: 'form',
            'res_model'	: 'reward.employee.wizard',
            'view_id'	: False,
            'type'		: 'ir.actions.act_window',
            'target'	: 'new',
        }

	@api.one
	def get_rewards(self):
		employees = self.env['hr.employee'].search([('is_practicant','=',False)])
		tareos    = self.env['hr.tareo'].search([])
		reward_line = self.env['hr.reward.line']
		for line in self.env['hr.reward.line'].search([('reward','=',self.id)]):
			line.unlink()
		if self.period == '07':
			final_date = datetime.strptime(self.year.code+'-07-01', '%Y-%m-%d')
			for employee in employees:
				if not employee.fecha_ingreso:
					raise osv.except_osv('Alerta!',"No existe fecha de ingreso para el empleado "+employee.name)
				in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
				if in_date.day != 1:
					in_date = in_date + relativedelta(months=1)
					in_date = in_date.replace(day=1)
				#Verifica que el empleado no haya sido despedido antes de la fecha de gratificación
				if  (not employee.fecha_cese) or (datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').year == int(self.year.code) and datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').month > 6):
					total_days = (final_date - in_date).days
					days = 0
					if total_days > 180:
						months = 6
					else:
						months = total_days / 30.00
						months = int(months)
					if months >= 1:
						in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
						in_date = in_date.replace(day=1)
						hr_param = self.env['hr.parameters'].search([])
						a_familiar = 0
						if employee.children_number > 0:
							a_familiar = self.env['hr.parameters'].search([('num_tipo','=','10001')])[0].monto
						he_night = []
						ex_plus  = []
						absences = 0
						for tareo in tareos:
							periodo = tareo.periodo.code.split("/")
							if periodo[1] == self.year.code and periodo[0] in ['01', '02', '03', '04', '05', '06']:
								#Cálculo de faltas
								htl = self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)])
								absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
								#Cálculo bonificación
								hcl = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','010')])
								if hcl.monto > 0.00:
									ex_plus.append(hcl.monto)
								#Cálculo de sobre tasa nocturna
								hcl_st = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','in',['007','008','009'])])
								res = 0
								for concept in hcl_st:
									res += concept.monto
								if res > 0.00:
									he_night.append(res)
						st_nocturna = 0
						tot_ex_plus = sum(ex_plus)
						if len(he_night) >= 3:
							st_nocturna = sum(he_night)/6.00
						if len(ex_plus) >= 3:
							tot_ex_plus = sum(ex_plus)/6.00
						#BASICO DE GRATIFICACION ANTERIOR
						emp_basica = 0
						tmp_f = datetime.strptime(self.period_id.date_start,"%Y-%m-%d")
						tmp_f = tmp_f + relativedelta(months=-1)
						periodo_anterior = self.env['account.period'].search([('date_start','=',datetime.strftime(tmp_f,"%Y-%m-%d"))])
						if len(periodo_anterior):
							periodo_anterior = periodo_anterior[0]
							anterior_reward = self.env['hr.tareo'].search([('periodo','=',periodo_anterior.id)])
							if len(anterior_reward):
								anterior_reward = anterior_reward[0]
								reward_emp = self.env['hr.tareo.line'].search([('tareo_id','=',anterior_reward.id),('employee_id','=',employee.id)])
								if len(reward_emp):
									reward_emp = reward_emp[0]
									if len(reward_emp):
										reward_emp = reward_emp[0]
										emp_basica = reward_emp.basica_first
						complete_amount = emp_basica + a_familiar + st_nocturna + tot_ex_plus
						adelanto_grat = 0
						for i in self.adelanto_lines:
							if i.employee_id.id == employee.id:
								adelanto_grat += i.monto
						vals = {
							'reward'				: self.id,
							'employee_id'			: employee.id,
							'identification_number'	: employee.identification_id,
							'code'					: employee.codigo_trabajador,
							'last_name_father'		: employee.last_name_father,
							'last_name_mother'		: employee.last_name_mother,
							'names'					: employee.first_name_complete,
							'in_date'				: employee.fecha_ingreso,
							'months'				: months,
							'days'					: days,
							'absences'				: absences,
							'basic'					: emp_basica,
							'ex_plus'				: tot_ex_plus,
							'a_familiar'			: a_familiar,
							'he_night'				: st_nocturna,
							'complete_amount'		: complete_amount,
							'monthly_amount'		: complete_amount/6.00,
							'dayly_amount'			: complete_amount/180.00,
							'months_reward'			: months*complete_amount/6.00,
							'days_reward'			: days*complete_amount/180.00,
							'absences_amount'		: absences*complete_amount/180.00,
							'adelanto'				: adelanto_grat,
						}
						vals['total_reward'] = vals['months_reward'] + vals['days_reward'] - vals['absences_amount']
						vals['plus_9']       = 0
						if self.plus_9:
							hp = self.env['hr.parameters'].search([('num_tipo','=',4)])
							if employee.use_eps:
								hp2 = self.env['hr.parameters'].search([('num_tipo','=',5)])
								vals['plus_9'] = vals['total_reward']*(hp.monto-hp2.monto)/100.00
							else:
								vals['plus_9'] = vals['total_reward']*hp.monto/100.00
						vals['total_to_pay'] = vals['total_reward'] + vals['plus_9'] - vals['adelanto']
						vals['total'] = vals['total_reward'] + vals['plus_9'] - vals['adelanto']
						reward_line.create(vals)
		else:
			final_date = datetime.strptime(str(int(self.year.code)+1)+'-01-01', '%Y-%m-%d')
			for employee in employees:
				if not employee.fecha_ingreso:
					raise osv.except_osv('Alerta!',"No existe fecha de ingreso para el empleado "+employee.name)
				in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
				if in_date.day != 1:
					in_date = in_date + relativedelta(months=1)
					in_date = in_date.replace(day=1)
				#Verifica que el empleado no haya sido despedido antes de la fecha de gratificación
				if  (not employee.fecha_cese) or datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').year > int(self.year.code):
					total_days = (final_date - in_date).days
					days = 0
					if total_days > 180:
						months = 6
					else:
						months = total_days / 30.00
						months = int(months)
					if months >= 1:
						in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
						in_date = in_date.replace(day=1)
						hr_param = self.env['hr.parameters'].search([])
						a_familiar = 0
						if employee.children_number > 0:
							a_familiar = self.env['hr.parameters'].search([('num_tipo','=','10001')])[0].monto
						he_night = []
						ex_plus  = []
						absences = 0
						for tareo in tareos:
							periodo = self.env['account.period'].search([('id','=',tareo.periodo.id)]).code.split("/")
							if periodo[1] == self.year.code and periodo[0] in ['07', '08', '09', '10', '11', '12']:
								#Cálculo de faltas
								htl = self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)])
								absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
								#Cálculo bonificación
								hcl = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','010')])
								if hcl.monto > 0.00:
									ex_plus.append(hcl.monto)
								#Cálculo de sobre tasa nocturna
								hcl_st = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','008')])
								if hcl_st.monto > 0.00:
									he_night.append(hcl_st.monto)
						st_nocturna = 0
						tot_ex_plus = sum(ex_plus)
						if len(he_night) >= 3:
							st_nocturna = sum(he_night)/6.00
						if len(ex_plus) >= 3:
							tot_ex_plus = sum(ex_plus)/6.00
						#BASICO DE GRATIFICACION ANTERIOR
						emp_basica = 0
						tmp_f = datetime.strptime(self.period_id.date_start,"%Y-%m-%d")
						tmp_f = tmp_f + relativedelta(months=-1)
						periodo_anterior = self.env['account.period'].search([('date_start','=',datetime.strftime(tmp_f,"%Y-%m-%d"))])
						if len(periodo_anterior):
							periodo_anterior = periodo_anterior[0]
							anterior_reward = self.env['hr.tareo'].search([('periodo','=',periodo_anterior.id)])
							if len(anterior_reward):
								anterior_reward = anterior_reward[0]
								reward_emp = self.env['hr.tareo.line'].search([('tareo_id','=',anterior_reward.id),('employee_id','=',employee.id)])
								if len(reward_emp):
									reward_emp = reward_emp[0]
									if len(reward_emp):
										reward_emp = reward_emp[0]
										emp_basica = reward_emp.basica_first
						complete_amount = emp_basica + a_familiar + st_nocturna + tot_ex_plus
						adelanto_grat = 0
						for i in self.adelanto_lines:
							if i.employee_id.id == employee.id:
								adelanto_grat += i.monto

						vals = {
							'reward'				: self.id,
							'employee_id'			: employee.id,
							'identification_number'	: employee.identification_id,
							'code'					: employee.codigo_trabajador,
							'last_name_father'		: employee.last_name_father,
							'last_name_mother'		: employee.last_name_mother,
							'names'					: employee.first_name_complete,
							'in_date'				: employee.fecha_ingreso,
							'months'				: months,
							'days'					: days,
							'absences'				: absences,
							'basic'					: emp_basica if not employee.is_practicant else emp_basica/2.00,
							'ex_plus'				: tot_ex_plus,
							'a_familiar'			: a_familiar,
							'he_night'				: st_nocturna,
							'complete_amount'		: complete_amount,
							'monthly_amount'		: complete_amount/6.00,
							'dayly_amount'			: complete_amount/180.00,
							'months_reward'			: months*complete_amount/6.00,
							'days_reward'			: days*complete_amount/180.00,
							'absences_amount'		: absences*complete_amount/180.00,
							'adelanto'				: adelanto_grat,
						}
						vals['total_reward'] = vals['months_reward'] + vals['days_reward'] - vals['absences_amount']
						vals['plus_9']       = 0
						if self.plus_9:
							hp = self.env['hr.parameters'].search([('num_tipo','=',4)])
							if employee.use_eps:
								hp2 = self.env['hr.parameters'].search([('num_tipo','=',5)])
								vals['plus_9'] = vals['total_reward']*(hp.monto-hp2.monto)/100.00
							else:
								vals['plus_9'] = vals['total_reward']*hp.monto/100.00
						vals['total_to_pay'] = vals['total_reward'] + vals['plus_9'] - vals['adelanto']
						vals['total'] = vals['total_reward'] + vals['plus_9'] - vals['adelanto']
						reward_line.create(vals)

	@api.multi
	def get_excel(self):
		#-------------------------------------------Datos---------------------------------------------------
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion + 'Gratificaciones.xlsx')
		worksheet = workbook.add_worksheet("Gratificaciones")

		#----------------Formatos------------------
		basic = {
			'align'		: 'left',
			'valign'	: 'vcenter',
			'text_wrap'	: 1,
			'font_size'	: 9,
			'font_name'	: 'Calibri'
		}

		basic_center = basic.copy()
		basic_center['align'] = 'center'

		numeric = basic.copy()
		numeric['align'] = 'right'
		numeric['num_format'] = '0.00'

		numeric_bold_format = numeric.copy()
		numeric_bold_format['bold'] = 1

		bold = basic.copy()
		bold['bold'] = 1

		header = bold.copy()
		header['bg_color'] = '#A9D0F5'
		header['border'] = 1
		header['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 15

		basic_format = workbook.add_format(basic)
		basic_center_format = workbook.add_format(basic_center)
		numeric_format = workbook.add_format(numeric)
		bold_format = workbook.add_format(bold)
		numeric_bold_format = workbook.add_format(numeric_bold_format)
		header_format = workbook.add_format(header)
		title_format = workbook.add_format(title)

		nro_columnas = 17

		tam_col = [0]*nro_columnas

		#----------------------------------------------Título--------------------------------------------------
		rc = self.env['res.company'].search([])[0]
		cabecera = rc.name
		worksheet.merge_range('A1:B1', cabecera, title_format)
		#---------------------------------------------Cabecera------------------------------------------------
		worksheet.merge_range('A2:D2', "Gratificaciones", bold_format)
		worksheet.write('A3', u"Año :", bold_format)

		worksheet.write('B3', self.year.code, bold_format)

		columnas = ["Orden","Nro Documento", u"Código", "Apellido\nPaterno","Apellido\nMaterno","Nombres","Fecha\nIngreso","Meses",u"Días","Faltas",u"Básico",u"Bonificación","A.\nFamiliar","Pro.\nSt.\nNoc.","Rem.\nCom.","M. por\nMes",u"M. por\nDía","Grat. Por\nlos Meses",u"Grat. Por\nlos Días","Total\nFaltas",u"Total\nGratificación","Bonif.\n9%",u"Adelanto","Total\nPagar"]
		fil = 4

		for col in range(len(columnas)):
			worksheet.write(fil, col, columnas[col], header_format)

		#------------------------------------------Insertando Data----------------------------------------------
		fil = 5
		lines = self.env['hr.reward.line'].search([('reward',"=",self.id)])
		totals = [0]*14

		for line in lines:
			col = 0
			worksheet.write(fil, col, line.order, basic_format)
			col += 1
			worksheet.write(fil, col, line.identification_number, basic_format)
			col += 1
			worksheet.write(fil, col, line.code, basic_format)
			col += 1
			worksheet.write(fil, col, line.last_name_father, basic_format)
			col += 1
			worksheet.write(fil, col, line.last_name_mother, basic_format)
			col += 1
			worksheet.write(fil, col, line.names, basic_format)
			col += 1
			worksheet.write(fil, col, line.in_date, basic_center_format)
			col += 1
			worksheet.write(fil, col, line.months, basic_center_format)
			col += 1
			worksheet.write(fil, col, line.days, basic_center_format)
			col += 1
			worksheet.write(fil, col, line.absences, basic_center_format)
			col += 1
			worksheet.write(fil, col, line.basic, numeric_format)
			totals[col-10] += line.basic
			col += 1
			worksheet.write(fil, col, line.ex_plus, numeric_format)
			totals[col-10] += line.ex_plus
			col += 1
			worksheet.write(fil, col, line.a_familiar, numeric_format)
			totals[col-10] += line.a_familiar
			col += 1
			worksheet.write(fil, col, line.he_night, numeric_format)
			totals[col-10] += line.he_night
			col += 1
			worksheet.write(fil, col, line.complete_amount, numeric_format)
			totals[col-10] += line.complete_amount
			col += 1
			worksheet.write(fil, col, line.monthly_amount, numeric_format)
			totals[col-10] += line.monthly_amount
			col += 1
			worksheet.write(fil, col, line.dayly_amount, numeric_format)
			totals[col-10] += line.dayly_amount
			col += 1
			worksheet.write(fil, col, line.months_reward, numeric_format)
			totals[col-10] += line.months_reward
			col += 1
			worksheet.write(fil, col, line.days_reward, numeric_format)
			totals[col-10] += line.days_reward
			col += 1
			worksheet.write(fil, col, line.absences_amount, numeric_format)
			totals[col-10] += line.absences_amount
			col += 1
			worksheet.write(fil, col, line.total_reward, numeric_format)
			totals[col-10] += line.total_reward
			col += 1
			worksheet.write(fil, col, line.plus_9, numeric_format)
			totals[col-10] += line.plus_9
			col += 1
			worksheet.write(fil, col, line.adelanto, numeric_format)
			totals[col-10] += line.adelanto

			col += 1
			worksheet.write(fil, col, line.total, numeric_format)
			totals[col-10] += line.total
			col += 1
			fil += 1

		col = 10
		for i in range(len(totals)):
			worksheet.write(fil, col, totals[i], numeric_bold_format)
			col += 1

		col_size = [5, 12, 20]
		worksheet.set_column('A:A', col_size[0])
		worksheet.set_column('B:E', col_size[1])
		worksheet.set_column('F:F', col_size[2])
		worksheet.set_column('G:U', col_size[1])
		workbook.close()

		f = open(direccion + 'Gratificaciones.xlsx', 'rb')

		vals = {
			'output_name': 'Gratificaciones.xlsx',
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
	def get_pdf(self):
		pdfmetrics.registerFont(TTFont('ARIAL', 'Arial.ttf'))
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		doc = SimpleDocTemplate(direccion+"Boletas.pdf", pagesize=(600,900))

		colorfondo = colors.lightblue
		elements=[]
		#Definiendo los estilos de la cabecera.
		estilo_c = [
					('SPAN',(0,0),(1,0)),
					('SPAN',(2,0),(3,0)),
					('ALIGN',(2,0),(3,0),'RIGHT'),
				]

		#Definiendo los estilos que tendrán las filas.
		estilo=[
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('ALIGN',(0,4),(7,8),'CENTER'),
				('FONTSIZE', (0, 0), (-1, -1), 7),
				('FONT', (0, 0), (-1,-1),'ARIAL'),
				('BOX',(0,0),(7,3),0.5,colors.black),
				('SPAN',(0,0),(7,0)),
				('SPAN',(0,1),(7,1)),
				('SPAN',(0,2),(7,2)),
				('SPAN',(0,3),(7,3)),
				('BACKGROUND',(0,0),(7,3), colorfondo),
				('SPAN',(0,4),(1,4)),
				('GRID',(0,4),(7,8),0.5,colors.black),
				('SPAN',(2,4),(5,5)),
				('SPAN',(6,4),(7,5)),
				('BACKGROUND',(0,4),(7,5), colorfondo),
				('SPAN',(2,6),(5,6)),
				('SPAN',(6,6),(7,6)),
				('SPAN',(0,7),(1,7)),
				('SPAN',(2,7),(3,7)),
				('SPAN',(4,7),(5,7)),
				('SPAN',(6,7),(7,7)),
				('BACKGROUND',(0,7),(7,7), colorfondo),
				('SPAN',(0,8),(1,8)),
				('SPAN',(2,8),(3,8)),
				('SPAN',(4,8),(5,8)),
				('SPAN',(6,8),(7,8)),
				('SPAN',(1,9),(4,9)),
				('GRID',(0,9),(7,9),0.5,colors.black),
				('BACKGROUND',(0,9),(7,10), colorfondo),
				('SPAN',(1,11),(4,11)),
				('SPAN',(1,12),(4,12)),
				('ALIGN',(5,11),(5,12),'RIGHT'),
				('BACKGROUND',(0,13),(7,13), colorfondo),
				('SPAN',(0,15),(7,15)),
				('BACKGROUND',(0,15),(7,15), colorfondo),
				('SPAN',(0,17),(6,17)),
				('BACKGROUND',(0,17),(7,17), colorfondo),
				('ALIGN',(7,17),(7,17),'RIGHT'),
				('BOX',(0,10),(7,17),0.5,colors.black),
				('SPAN',(0,22),(2,22)),
				('SPAN',(5,22),(7,22)),
				('LINEABOVE',(0,22),(2,22),1.1,colors.black),
				('SPAN',(0,23),(2,23)),
				('SPAN',(5,23),(7,23)),
				('LINEABOVE',(5,22),(7,22),1.1,colors.black),
				('ALIGN',(0,22),(7,23),'CENTER'),
			]

		#------------------------------------------------------Insertando Data-----------------------------------------
		lines = self.env['hr.reward.line'].search([('reward','=',self.id)])
		company = self.env['res.users'].browse(self.env.uid).company_id
		count = 0
		for line in lines:
			employee = self.env['hr.employee'].search([('id','=',line.employee_id.id)])
			name = line.names + ' ' + line.last_name_father + ' ' + line.last_name_mother
			#--------------------------------------------------Cabecera
			a = Image(direccion+"calquipalleft.png")
			a.drawHeight = 50
			a.drawWidth = 95
			b = Image(direccion+"calquipalright.png")
			b.drawHeight = 60
			b.drawWidth = 80
			cabecera = [[a,'',b,''],]
			table_c = Table(cabecera, colWidths=[120]*2, rowHeights=50, style=estilo_c)
			elements.append(table_c)
			#----------------------------------------------------Datos
			data = [
				['RUC: '+company.partner_id.type_number,'','','','','','',''],
				['Empleador : '+company.partner_id.name,'','','','','','',''],
				[u'Dirección : '+company.partner_id.street,'','','','','','',''],
				[u'Periodo : '+self.period+'/'+self.year.code,'','','','','','',''],
				['Documento de identidad','','Nombre y Apellidos','','','',U'Situación',''],
				['Tipo',u'Número','','','','','',''],
				[employee.type_document_id.code,line.identification_number,name,'','','','ACTIVO O SUBSIDIADO',''],
				['Fecha de ingreso','',u'Título del Trabajo','','Régimen Pensionario','','CUSPP',''],
				[line.in_date,'',employee.job_id.name,'',employee.afiliacion.name,'',employee.cusspp if employee.cusspp else '',''],
				['Código','Conceptos','','','','Ingresos S/.','Descuentos S/.','Neto S/.'],
				['Ingresos','','','','','','',''],
				['0406','GRATIFICACIONES DE FIESTAS PATRIAS Y NAVIDAD - LEY 29351','','','','{:10,.2f}'.format(line.total_reward),'',''],
				['0313','BONIFICACION EXTRAORDINARIA PROPORCIONAL - LEY 29351','','','','{:10,.2f}'.format(line.plus_9),'',''],
				['Descuentos','','','','','','',''],
				['','','','','','','',''],
				['Aportes del Trabajador','','','','','','',''],
				['','','','','','','',''],
				['Neto a Pagar','','','','','','','{:10,.2f}'.format(line.total)],
				['','','','','','','',''],
				['','','','','','','',''],
				['','','','','','','',''],
				['','','','','','','',''],
				[company.partner_id.name.upper(),'','','','',name,'',''],
				['EMPLEADOR','','','','','TRABAJADOR','',''],
			]
			t=Table(data, colWidths=[60]*8,rowHeights=12,style=estilo)
			elements.append(t)
			count += 1
			if count == 2:
				elements.append(PageBreak())
				count = 0
			else:
				elements.append(Spacer(0,90))
		doc.bottomMargin = 0
		doc.topMargin = 50
		doc.build(elements)

		f = open(direccion + 'Boletas.pdf', 'rb')

		vals = {
			'output_name': 'Boletas.pdf',
			'output_file': f.read().encode("base64"),
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
	def resumen_pago(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo    = u'Resumen_pago_'+self.period_id.code.replace("/","")
		workbook  = Workbook(direccion + titulo + '.xlsx')
		worksheet = workbook.add_worksheet("Resumen")

		basic = {
			'align'		: 'left',
			'valign'	: 'vcenter',
			'text_wrap'	: 1,
			'font_size'	: 9,
			'font_name'	: 'Calibri'
		}

		percentage = basic.copy()
		percentage['align'] = 'right'
		percentage['num_format'] = '0.00%'

		percentage_y = percentage.copy()
		percentage_y['bg_color'] = '#F2E400'

		numeric = basic.copy()
		numeric['align'] = 'right'
		numeric['num_format'] = '#,##0.00'

		numeric_y = numeric.copy()
		numeric_y['bg_color'] = '#F2E400'

		numeric_gr = numeric.copy()
		numeric_gr['bg_color'] = '#CECECE'

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
		header['bg_color'] = '#CECECE'
		header['border'] = 1
		header['align'] = 'center'

		header_w = bold.copy()
		header_w['bg_color'] = '#FFFFFF'
		header_w['border'] = 1
		header_w['align'] = 'center'

		header_g = bold.copy()
		header_g['bg_color'] = '#4FA147'
		header_g['border'] = 1
		header_g['align'] = 'center'

		header_y = bold.copy()
		header_y['bg_color'] = '#F2E400'
		header_y['border'] = 1
		header_y['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 15

		basic_format            = workbook.add_format(basic)
		bold_format             = workbook.add_format(bold)
		percentage_format		= workbook.add_format(percentage)
		percentage_y_format		= workbook.add_format(percentage_y)
		numeric_int_format      = workbook.add_format(numeric_int)
		numeric_y_format      = workbook.add_format(numeric_y)
		numeric_gr_format      = workbook.add_format(numeric_gr)
		numeric_int_bold_format = workbook.add_format(numeric_int_bold_format)
		numeric_format          = workbook.add_format(numeric)
		numeric_bold_format     = workbook.add_format(numeric_bold_format)
		title_format            = workbook.add_format(title)
		header_format           = workbook.add_format(header)
		header_g_format         = workbook.add_format(header_g)
		header_y_format         = workbook.add_format(header_y)
		header_w_format         = workbook.add_format(header_w)

		dts = {0:"lunes", 1:"martes", 2:u"miércoles", 3:"jueves", 4:"viernes", 5:u"sábado", 6:"domingo"}
		mts = {1:"enero", 2:"febrero", 3:"marzo", 4:"abril", 5:"mayo", 6:"junio", 7:"julio", 8:"agosto", 9:"septiembre", 10:"octubre", 11:"noviembre", 12:"diciembre"}

		rc = self.env['res.company'].search([])[0]
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', ("RUC: "+rc.partner_id.type_number) if rc.partner_id.type_number else 'RUC: ', title_format)

		row = 5
		worksheet.merge_range(row,0,row,6, 'Pago Gratificaciones '+ ('Fiestas Patrias ' if self.period == '07' else 'Navidad ') + self.year.code, header_format)

		row += 1
		col = 0
		pago_headers = [u'', u'Fecha depósito', u'Trabajador', u'DNI', u'BCO', u'Cuenta', u'Total a depositar']
		for ph in pago_headers:
			worksheet.write(row, col, ph, header_w_format)
			col += 1

		row += 1
		item = 1
		for i in self.reward_lines:
			col = 0
			worksheet.write(row, col, item, numeric_int_format)
			col += 1
			worksheet.write(row, col, self.deposit_date if self.deposit_date else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.name_related if i.employee_id.name_related else '', basic_format)
			col += 1
			worksheet.write(row, col, i.identification_number if i.identification_number else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.banco_rem if i.employee_id.banco_rem else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.cta_rem if i.employee_id.cta_rem else '', basic_format)
			col += 1
			worksheet.write(row, col, i.total if i.total else 0, numeric_format)
			#worksheet.write(row, col, i.total_to_pay if i.total_to_pay else 0, numeric_format)
			col += 1
			item += 1
			row += 1

		col_sizes = [13.57, 27.86]
		worksheet.set_column('A:B', col_sizes[0])
		worksheet.set_column('C:C', col_sizes[1])
		worksheet.set_column('D:G', col_sizes[0])

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

	@api.one
	def get_adelantos(self): 
		for line in self.reward_lines:
			t_adel   = self.env['hr.table.adelanto'].search([('is_basket','=',False),('reward_dicount_type','=',self.period)])
			ids_adel = []
			anio = str(self.period_id.code)[3:]
			for ade in t_adel:
				ids_adel.append(ade.id)
			ha  = self.env['hr.adelanto'].search([('employee','=',line.employee_id.id),('adelanto_id','in',ids_adel)])
			res = 0
			for item in ha:
				if str(item.fecha)[:4]==anio:
					res += item.monto


			vals = {}

			vals['employee_id'] = line.employee_id.id
			vals['monto']		= res

			hral = self.env['hr.reward.adelanto.lines'].search([('employee_id','=',line.employee_id.id),('reward_id','=',self.id)])
			if len(hral):
				hral[0].write(vals)
			else:
				vals['reward_id'] = self.id
				self.env['hr.reward.adelanto.lines'].create(vals)
			line.delanto = res


class hr_reward_line(models.Model):
	_name = 'hr.reward.line'

	reward                = fields.Many2one('hr.reward', "Reward")
	employee_id           = fields.Many2one('hr.employee', "Empleado")
	order                 = fields.Integer("Orden", compute='get_order')
	identification_number = fields.Char("Nro Documento", size=9)
	code                  = fields.Char("Código", size=4)
	last_name_father      = fields.Char("Apellido Paterno")
	last_name_mother      = fields.Char("Apellido Materno")
	names                 = fields.Char("Nombres")
	in_date               = fields.Date("Fecha Ingreso")
	months                = fields.Integer("Meses")
	days                  = fields.Integer(u"Días")
	absences              = fields.Integer("Faltas")
	basic                 = fields.Float(u"Básico", digits=(10,2))
	ex_plus               = fields.Float(u"Bonificación", digits=(10,2))
	a_familiar            = fields.Float("A. Familiar", digits=(10,2))
	he_night              = fields.Float("Pro. St. Noc.", digits=(10,2))
	complete_amount       = fields.Float("Rem. Com.", digits=(10,2))
	monthly_amount        = fields.Float("M. por Mes", digits=(10,2))
	dayly_amount          = fields.Float(u"M. por Día", digits=(10,2))
	months_reward         = fields.Float("Grat. Por los\nMeses", digits=(10,2))
	days_reward           = fields.Float(u"Grat. Por los\nDías", digits=(10,2))
	absences_amount       = fields.Float(u"Total Faltas", digits=(10,2))
	total_reward          = fields.Float(u"Total\nGratificación", digits=(10,2))
	plus_9                = fields.Float(u"Bonif. 9%", digits=(10,2))
	adelanto			  = fields.Float(u'Adelanto', digits=(10,2))
	total_to_pay		  = fields.Float(u'Gratificación a pagar', digits=(10,2))
	total                 = fields.Float(u"Total Pagar", digits=(10,2))

	conceptos_lines       = fields.One2many('hr.reward.conceptos','line_reward_id','Ingresos')

	@api.multi
	def get_order(self):
		order = 1
		for line in self:
			line.order = order
			order      += 1

	@api.multi
	def open_concepts(self):
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.reward.line',
			'res_id': self.id,
			'target': 'new',
		}

	@api.multi
	def set_concepts(self):
		sum_con = 0
		for con in self.conceptos_lines:
			sum_con += con.monto
		self.complete_amount = self.employee_id.basica + self.a_familiar + self.he_night + self.ex_plus + sum_con
		self.monthly_amount  = self.complete_amount/6.00
		self.dayly_amount    = self.complete_amount/180.00
		self.months_reward   = self.months*round(self.complete_amount/6.00,2)
		self.days_reward     = self.days*round(self.complete_amount/180.00,2)
		self.absences_amount = self.absences*round(self.complete_amount/180.00,2)
		self.total_reward    = self.months_reward + self.days_reward - self.absences_amount

		if self.reward.plus_9:
			hp = self.env['hr.parameters'].search([('num_tipo','=',4)])
			self.plus_9 = 0
			if self.employee_id.use_eps:
				hp2 = self.env['hr.parameters'].search([('num_tipo','=',5)])
				self.plus_9 = self.total_reward*(hp.monto-hp2.monto)/100.00
			else:
				self.plus_9 = self.total_reward*hp.monto/100.00

		self.total_to_pay = self.total_reward+self.plus_9-self.adelanto
		self.total = self.total_reward + self.plus_9
		return True

class hr_reward_conceptos(models.Model):
	_name = 'hr.reward.conceptos'

	line_reward_id = fields.Many2one('hr.reward.line', 'linea')

	concepto_id    = fields.Many2one('hr.lista.conceptos', 'Concepto', required=True)
	monto          = fields.Float('Monto')

class hr_reward_adelanto_lines(models.Model):
	_name = 'hr.reward.adelanto.lines'

	reward_id = fields.Many2one('hr.reward','padre')

	employee_id = fields.Many2one('hr.employee', u'Empleado', required=True)
	monto 		= fields.Float(u'Monto')
