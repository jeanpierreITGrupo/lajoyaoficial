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
from datetime import timedelta
import os
from dateutil.relativedelta import *
import decimal
import calendar

from openerp import models, fields, api
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



def days360(start_date, end_date, method_eu=False):
	start_day = start_date.day
	start_month = start_date.month
	start_year = start_date.year
	end_day = end_date.day
	end_month = end_date.month
	end_year = end_date.year

	if (
		start_day == 31 or
		(
			method_eu is False and
			start_month == 2 and (
				start_day == 29 or (
					start_day == 28 and
					calendar.isleap(start_year) is False
				)
			)
		)
	):
		start_day = 30

	if end_day == 31:
		if method_eu is False and start_day != 30:
			end_day = 1

			if end_month == 12:
				end_year += 1
				end_month = 1
			else:
				end_month += 1
		else:
			end_day = 30

	return (
		end_day + end_month * 30 + end_year * 360 -
		start_day - start_month * 30 - start_year * 360
	)



class hr_employee(models.Model):
	_inherit = 'hr.employee'

	currency = fields.Many2one('res.currency', 'Moneda')


class hr_cts(models.Model):
	_name = 'hr.cts'
	_rec_name = 'year'

	year = fields.Many2one('account.fiscalyear', u"Año Fiscal", required=1)
	period = fields.Selection([("05", "Depósito Mayo"),("11","Depósito Noviembre")],"Mes", required=1)
	period_id = fields.Many2one('account.period','Periodo',required=True)
	reward_id = fields.Many2one('hr.reward', u"Gratificación", required=1)
	change = fields.Float("Tipo de Cambio", digits=(2,3), required=1)
	cts_lines1 = fields.One2many('hr.cts.line', 'cts')
	cts_lines2 = fields.One2many('hr.cts.line', 'cts')

	deposit_date = fields.Date(u'Fecha depósito')
	previous_period_id = fields.Many2one('account.period','Periodo anterior')

	@api.one
	def get_cts(self):
		if self.change <= 0.00:
			raise osv.except_osv("Alert!", "El tipo de cambio no es correcto")
		periods = []
		in_date = ''
		end_date = ''
		ref_date = ''
		
		tareos = self.env['hr.tareo'].search([])
		cts_line = self.env['hr.cts.line']
		count = 1
		if self.period == '05':
			periods = [
			'11/'+str(int(self.year.code)-1), 
			'12/'+str(int(self.year.code)-1), 
			'01/'+str(int(self.year.code)), 
			'02/'+str(int(self.year.code)), 
			'03/'+str(int(self.year.code)), 
			'04/'+str(int(self.year.code))]
			prev_periods = [
			'05/'+str(int(self.year.code)-1),
			'06/'+str(int(self.year.code)-1),
			'07/'+str(int(self.year.code)-1), 
			'08/'+str(int(self.year.code)-1), 
			'09/'+str(int(self.year.code)-1), 
			'10/'+str(int(self.year.code)-1)]
			prev_years = [str(int(self.year.code)-1)]
			years = [self.year.code, str(int(self.year.code)-1)]
			ref_date = datetime.strptime(self.year.code+'-05-01', '%Y-%m-%d')
		else:
			periods = [
			'05/'+str(int(self.year.code)),
			'06/'+str(int(self.year.code)),
			'07/'+str(int(self.year.code)), 
			'08/'+str(int(self.year.code)), 
			'09/'+str(int(self.year.code)), 
			'10/'+str(int(self.year.code))]
			prev_periods = [
			'11/'+str(int(self.year.code)-1), 
			'12/'+str(int(self.year.code)-1), 
			'01/'+str(int(self.year.code)), 
			'02/'+str(int(self.year.code)), 
			'03/'+str(int(self.year.code)), 
			'04/'+str(int(self.year.code))
			]
			years = [self.year.code]
			prev_years = [self.year.code, str(int(self.year.code)-1)]
			ref_date = datetime.strptime(self.year.code+'-11-01', '%Y-%m-%d')
		
		employees = self.env['hr.employee'].search([('is_practicant','=',False)])
		

		for line in self.env['hr.cts.line'].search([('cts','=',self.id)]):
			line.unlink()
		for employee in employees:
			if self.period == '05':
				if employee.fecha_cese and datetime.strptime(employee.fecha_cese,"%Y-%m-%d") < datetime.strptime(self.year.code+"-05-01","%Y-%m-%d"):
					continue
				if datetime.strptime(employee.fecha_ingreso,"%Y-%m-%d") >= datetime.strptime(self.year.code+"-05-01","%Y-%m-%d"):
					continue
				# solo se paga a personas que tengan un mes minimo en la empresa
				if datetime.strptime(employee.fecha_ingreso,"%Y-%m-%d") > datetime.strptime(self.year.code+"-04-01","%Y-%m-%d"):
					continue
			else:
				if employee.fecha_cese and datetime.strptime(employee.fecha_cese,"%Y-%m-%d") < datetime.strptime(self.year.code+"-11-01","%Y-%m-%d"):
					continue
				if datetime.strptime(employee.fecha_ingreso,"%Y-%m-%d") >= datetime.strptime(self.year.code+"-11-01","%Y-%m-%d"):
					continue
				# solo se paga a personas que tengan un mes minimo en la empresa
				if datetime.strptime(employee.fecha_ingreso,"%Y-%m-%d") > datetime.strptime(self.year.code+"-10-01","%Y-%m-%d"):
					continue

			he_night = {}
			absences = {}
			bonuses = {}
			comision = {}
			in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
			if employee.fecha_cese:
				end_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
			###################################
			# PARA NO COSIDERAR LOS QUE TIENEN
			# FECHA DE INGRESO MAYOR QUE
			# MAYO Y NOVIEMBRE
			###################################
			elif datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d') < ref_date:
				end_date = False
			else:
				end_date = ref_date
			#######################
			# FIN DE CONSIDERACION
			#######################
			# if (not end_date) or end_date > ref_date:
			absence_subsi_tot = 0
			tareos_sub = []
			for tareo in tareos:
				periodo = tareo.periodo.code.split("/")
				if tareo.periodo.code in periods:
					htl = self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)])
					hcl = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','in',['007','008','009'])])
					res = 0
					for concept in hcl:
						res += concept.monto
					if res > 0.00:
						he_night[periodo[0]] = res
					tareoline= self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)])
					absence = tareoline.dias_suspension_perfecta
					absence_lsg = tareoline.licencia_sin_goce
					absence_subsi = tareoline.num_days_subs
					absence_imperf =  tareoline.dias_suspension_imperfecta

					if absence or absence_lsg:
						absences[periodo[0]] = absence+absence_lsg
					
					if absence_imperf:
						if periodo[0] in absences.keys():
							absences[periodo[0]] = absences[periodo[0]]+absence_imperf
						else:
							absences[periodo[0]] = absence_imperf

					if absence_subsi:
						if tareoline.dias_mes == absence_subsi:
							absence_subsi_tot = absence_subsi_tot+30
						else:	
							absence_subsi_tot = absence_subsi_tot+absence_subsi
						tareos_sub.append(tareoline.id)
					hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','010')])
					if hclb.monto > 0.00:
						bonuses[periodo[0]] = hclb.monto
					hcl2 = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','011')])
					if hcl2.monto > 0.00:
						comision[periodo[0]] = hcl2.monto
				# vamos a obtener los subsidios que corresponden a la cts anterior
				# para ello nos apoyamos en el campo cts_is_payed de las lineas
				# del tareo que nos indican si ya se pagaron esos elementos
				if self.period != '05':
					if tareo.periodo.code in prev_periods:
						htl = self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)])
						tareoline= self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id),('cts_is_payed','=',False)])
						absence_subsi = tareoline.num_days_subs
						if absence_subsi:
							absence_subsi_tot = absence_subsi_tot+absence_subsi
							tareos_sub.append(tareoline.id)

			st_nocturna = 0
			bonuses_total = 0
			comision_total = 0
			if len(he_night) >= 3:
				st_nocturna = sum(he_night.values())
			if len(bonuses) >= 3:
				bonuses_total = sum(bonuses.values())/6.00
			if len(comision) >= 3:
				comision_total = sum(comision.values())/6.00
			absences_total = sum(absences.values())
			
			if absence_subsi_tot>60:
				absences_total=absences_total+(absence_subsi_tot-60)
				
				for linetar in self.env['hr.tareo.line'].search([('id','in',tareos_sub)]):
					linetar.cts_is_payed=True
			
			#CACULO DIAS
			days = 0
			if self.period == '11':
				fecha_ing = datetime.strptime(employee.fecha_ingreso, '%Y-%m-%d')
				if fecha_ing <= datetime.strptime(self.year.code+"-05-01","%Y-%m-%d"):
					days = 0
					months = 6
				else:
					fecha_limite = datetime.strptime(self.year.code+"-10-31","%Y-%m-%d")
					days = (fecha_limite - fecha_ing + timedelta(days=1)).days
					res = days360(fecha_ing,fecha_limite+timedelta(days=1))
					months = int(res/30)
					days = res-(months*30)

					# days -= absences_total
			else:
				fecha_ing = datetime.strptime(employee.fecha_ingreso, '%Y-%m-%d')
				if fecha_ing <= datetime.strptime(str(int(self.year.code)-1)+"-11-01","%Y-%m-%d"):
					days = 0
					months = 6
				else:
					fecha_limite = datetime.strptime(self.year.code+"-04-30","%Y-%m-%d")
					days = (fecha_limite - fecha_ing + timedelta(days=1)).days
					res = days360(fecha_ing,fecha_limite+timedelta(days=1))
					months = int(res/30)
					days = res-(months*30)
					# days -= absences_total
			# voy a desconar las faltas
			months_ab=0
			days_ab=0
			if absences_total>0:
				if absences_total>30:
					months_ab = int(absences_total/30)
				days_ab = absences_total-(months_ab*30)
			
			months -= months_ab
			if days<days_ab:
				months-=1
				days=30-days_ab
			else:
				days -= days_ab
				
			#DIAS ANTERIORES
			p_days = 0
			cts_anterior = self.env['hr.cts'].search([('period_id','=',self.previous_period_id.id)])
			if len(cts_anterior):
				cts_anterior = cts_anterior[0]
				cts_anterior_emp = self.env['hr.cts.line'].search([('cts','=',cts_anterior.id),('employee_id','=',employee.id)])
				if len(cts_anterior_emp):
					cts_anterior_emp = cts_anterior_emp[0]
					p_days = cts_anterior_emp.days
			reward = self.env['hr.reward.line'].search([('reward','=',self.reward_id.id),('employee_id','=',employee.id)])
			hr_param = self.env['hr.parameters'].search([])
			hr_param_fam = self.env['hr.parameters'].search([('num_tipo','=',10001)])

			a_familiar = 0
			if employee.children_number > 0:
				#A FAMILIAR
				a_familiar = hr_param_fam.monto
				tmp_f = datetime.strptime(self.period_id.date_start,"%Y-%m-%d")
				tmp_f = tmp_f + relativedelta(months=-1)
				periodo_anterior = self.env['account.period'].search([('date_start','=',datetime.strftime(tmp_f,"%Y-%m-%d"))])
				if len(periodo_anterior):
					periodo_anterior = periodo_anterior[0]
					anterior_cts = self.env['hr.tareo'].search([('periodo','=',periodo_anterior.id)])
					if len(anterior_cts):
						anterior_cts = anterior_cts[0]
						cts_emp = self.env['hr.tareo.line'].search([('tareo_id','=',anterior_cts.id),('employee_id','=',employee.id)])
						if len(cts_emp):
							cts_emp = cts_emp[0]
							# a_familiar = cts_emp.a_familiar_first

			#FERIADOS
			feriados = 0
			fer_a = datetime.strptime(self.period_id.date_start,"%Y-%m-%d")
			fer_a = fer_a + relativedelta(months=-1)
			fer_a = datetime.strftime(fer_a,"%Y-%m-%d")
			
			
			
			f_ap1 = self.env['account.period'].search([('name','in',periods)])
			
			n=0

			if len(f_ap1):
				for f_ap in f_ap1:
				# f_ap = f_ap[0]
					f_ht = self.env['hr.tareo'].search([('periodo','=',f_ap.id)])
					if len(f_ht):
						f_ht = f_ht[0]
						f_htl = self.env['hr.tareo.line'].search([('tareo_id','=',f_ht.id),('employee_id','=',employee.id)])
						if len(f_htl):
							f_htl = f_htl[0]
							f_hcl = self.env['hr.concepto.line'].search([('tareo_line_id','=',f_htl.id),('concepto_id.code','in',['063'])])
							if len(f_hcl):
								if f_hcl[0].monto>0:
									n=n+1
									feriados = feriados+(f_hcl[0].monto if len(f_hcl) else 0)

			if n<3:
				feriados = 0
			
			feriados = feriados/6
			
			
			# f_ap = self.env['account.period'].search([('date_start','<=',fer_a),('date_stop','>=',fer_a)])
			# if len(f_ap):
				# f_ap = f_ap[0]
				# f_ht = self.env['hr.tareo'].search([('periodo','=',f_ap.id)])
				# if len(f_ht):
					# f_ht = f_ht[0]
					# f_htl = self.env['hr.tareo.line'].search([('tareo_id','=',f_ht.id),('employee_id','=',employee.id)])
					# if len(f_htl):
						# f_htl = f_htl[0]
						# f_hcl = self.env['hr.concepto.line'].search([('tareo_line_id','=',f_htl.id),('concepto_id.code','in',['063'])])
						# feriados = f_hcl[0].monto if len(f_hcl) else 0

			#BASICO DE GRATIFICACION ANTERIOR
			emp_basica = 0
			tmp_f = datetime.strptime(self.period_id.date_start,"%Y-%m-%d")
			tmp_f = tmp_f + relativedelta(months=-1)

			periodo_anterior = self.env['account.period'].search([('date_start','=',datetime.strftime(tmp_f,"%Y-%m-%d"))])
			if len(periodo_anterior):
				periodo_anterior = periodo_anterior[0]
				anterior_cts = self.env['hr.tareo'].search([('periodo','=',periodo_anterior.id)])
				if len(anterior_cts):
					anterior_cts = anterior_cts[0]
					cts_emp = self.env['hr.tareo.line'].search([('tareo_id','=',anterior_cts.id),('employee_id','=',employee.id)])
					if len(cts_emp):
						cts_emp = cts_emp[0]
						emp_basica = cts_emp.basica_first

			base_amount = emp_basica + st_nocturna/6.00 + reward.total_reward/6.00 + a_familiar + bonuses_total + comision_total + feriados
			cts_soles = (round((float(days)+float(p_days))*(float(base_amount)/360.00),4))-(absences_total*base_amount/360.00)+(round((float(months))*(float(base_amount)/12.00),4))

			cts_soles = round(months*(base_amount/12.00),2)
			cts_soles = cts_soles+(round((days+p_days)*(base_amount/360.00),2))

			print employee.last_name_father,months,days,p_days

			# ((days+p_days)*base_amount/360.00) 
			# - (absences_total*base_amount/360.00)
			vals = {
					'cts'				: self.id,
					'employee_id'		: employee.id,
					'order'				: count,
					'nro_doc'			: employee.identification_id,
					'code'				: employee.codigo_trabajador,
					'last_name_father'	: employee.last_name_father,
					'last_name_mother'	: employee.last_name_mother,
					'names'				: employee.first_name_complete,
					'in_date'			: employee.fecha_ingreso,
					'basic_amount'		: emp_basica if not employee.is_practicant else emp_basica/2.00,
					'a_familiar'		: a_familiar,
					'feriados'			: feriados,
					'reward_amount'		: reward.total_reward/6.00,
					'overtime_night1'	: he_night['01'] if '01' in he_night.keys() else 0.00,
					'overtime_night2'	: he_night['02'] if '02' in he_night.keys() else 0.00,
					'overtime_night3'	: he_night['03'] if '03' in he_night.keys() else 0.00,
					'overtime_night4'	: he_night['04'] if '04' in he_night.keys() else 0.00,
					'overtime_night5'	: he_night['05'] if '05' in he_night.keys() else 0.00,
					'overtime_night6'	: he_night['06'] if '06' in he_night.keys() else 0.00,
					'overtime_night7'	: he_night['07'] if '07' in he_night.keys() else 0.00,
					'overtime_night8'	: he_night['08'] if '08' in he_night.keys() else 0.00,
					'overtime_night9'	: he_night['09'] if '09' in he_night.keys() else 0.00,
					'overtime_night10'	: he_night['10'] if '10' in he_night.keys() else 0.00,
					'overtime_night11'	: he_night['11'] if '11' in he_night.keys() else 0.00,
					'overtime_night12'	: he_night['12'] if '12' in he_night.keys() else 0.00,
					'overtime_total'	: st_nocturna,
					'overtime_6'		: st_nocturna/6.00,
					'comision'			: comision_total,
					'bonus'				: bonuses_total,
					'base_amount'		: base_amount,
					'monthly_amount'	: base_amount/12.00,
					'dayly_amount'		: base_amount/360.00,
					'absences1'			: absences['01'] if '01' in absences.keys() else 0.00,
					'absences2'			: absences['02'] if '02' in absences.keys() else 0.00,
					'absences3'			: absences['03'] if '03' in absences.keys() else 0.00,
					'absences4'			: absences['04'] if '04' in absences.keys() else 0.00,
					'absences5'			: absences['05'] if '05' in absences.keys() else 0.00,
					'absences6'			: absences['06'] if '06' in absences.keys() else 0.00,
					'absences7'			: absences['07'] if '07' in absences.keys() else 0.00,
					'absences8'			: absences['08'] if '08' in absences.keys() else 0.00,
					'absences9'			: absences['09'] if '09' in absences.keys() else 0.00,
					'absences10'		: absences['10'] if '10' in absences.keys() else 0.00,
					'absences11'		: absences['11'] if '11' in absences.keys() else 0.00,
					'absences12'		: absences['12'] if '12' in absences.keys() else 0.00,
					'absences_total'	: absences_total,
					'months'			: months,
					'days'				: days,
					'previous_days'		: p_days,
					'amount_x_month'	: months*(base_amount/12.00),
					'amount_x_day'		: (days+p_days)*(base_amount/360.00),
					'absences_discount' : absences_total*base_amount/360.00,
					'cts_soles'			: months*(base_amount/12.00)+(days+p_days)*(base_amount/360.00),
					'change'			: self.change,
					# 'cts_dolars'		: cts_soles/self.change,
					'account'			: employee.cta_cts,
					'bank'				: employee.banco_cts,
				}
			cts_line.create(vals)
			count += 1

	@api.multi
	def resumen_pago(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo	= u'Resumen_pago_'+self.period_id.code.replace("/","")
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

		basic_format			= workbook.add_format(basic)
		bold_format			 = workbook.add_format(bold)
		percentage_format		= workbook.add_format(percentage)
		percentage_y_format		= workbook.add_format(percentage_y)
		numeric_int_format	  = workbook.add_format(numeric_int)
		numeric_y_format	  = workbook.add_format(numeric_y)
		numeric_gr_format	  = workbook.add_format(numeric_gr)
		numeric_int_bold_format = workbook.add_format(numeric_int_bold_format)
		numeric_format		  = workbook.add_format(numeric)
		numeric_bold_format	 = workbook.add_format(numeric_bold_format)
		title_format			= workbook.add_format(title)
		header_format		   = workbook.add_format(header)
		header_g_format		 = workbook.add_format(header_g)
		header_y_format		 = workbook.add_format(header_y)
		header_w_format		 = workbook.add_format(header_w)

		dts = {0:"lunes", 1:"martes", 2:u"miércoles", 3:"jueves", 4:"viernes", 5:u"sábado", 6:"domingo"}
		mts = {1:"enero", 2:"febrero", 3:"marzo", 4:"abril", 5:"mayo", 6:"junio", 7:"julio", 8:"agosto", 9:"septiembre", 10:"octubre", 11:"noviembre", 12:"diciembre"}

		rc = self.env['res.company'].search([])[0]
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', ("RUC: "+rc.partner_id.type_number) if rc.partner_id.type_number else 'RUC: ', title_format)

		row = 5
		worksheet.merge_range(row,0,row,6, 'Pago CTS '+mts[datetime.strptime(self.period_id.date_start,"%Y-%m-%d").month]+' '+self.period_id.fiscalyear_id.code, header_format)

		row += 1
		col = 0
		pago_headers = [u'', u'Fecha depósito', u'Trabajador', u'DNI', u'BCO', u'Cuenta', u'Total a depositar']
		for ph in pago_headers:
			worksheet.write(row, col, ph, header_w_format)
			col += 1

		row += 1
		item = 1
		for i in self.cts_lines2:
			col = 0
			worksheet.write(row, col, item, numeric_int_format)
			col += 1
			worksheet.write(row, col, self.deposit_date if self.deposit_date else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.name_related if i.employee_id.name_related else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.identification_id if i.employee_id.identification_id else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.banco_rem if i.employee_id.banco_rem else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.cta_rem if i.employee_id.cta_rem else '', basic_format)
			col += 1
			worksheet.write(row, col, i.cts_a_pagar if i.cts_a_pagar else 0, numeric_format)
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
			"type"	 : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"	: [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
		}

	@api.multi
	def get_excel(self):
		#-------------------------------------------Datos---------------------------------------------------
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion + 'CTS.xlsx')
		worksheet = workbook.add_worksheet("CTS")

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

		numeric3 = basic.copy()
		numeric3['align'] = 'right'
		numeric3['num_format'] = '0.000'

		numeric_bold_format = numeric.copy()
		numeric_bold_format['bold'] = 1

		bold = basic.copy()
		bold['bold'] = 1

		header = bold.copy()
		header['bg_color'] = '#A9D0F5'
		header['border'] = 1
		header['align'] = 'center'

		title = bold.copy()
		title['font_size'] = 12

		basic_format = workbook.add_format(basic)
		basic_center_format = workbook.add_format(basic_center)
		numeric_format = workbook.add_format(numeric)
		numeric_format3 = workbook.add_format(numeric3)
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
		worksheet.merge_range('A2:D2', "CTS", bold_format)
		worksheet.write('A3', u"Año :", bold_format)

		worksheet.write('B3', self.period + '/' + self.year.code, bold_format)

		columnas1 = ["Orden","Nro Documento", u"Código", "Apellido\nPaterno","Apellido\nMaterno","Nombres","Fecha\nIngreso","Sueldo",u"A.\nFamiliar","Feriados","1/6\nGratif."]
		meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']
		if self.period == '05':
			columnas1.append('H.E.\n'+'Noviembre')
			columnas1.append('H.E.\n'+'Diciembre')
			columnas1.append('H.E.\n'+'Enero')
			columnas1.append('H.E.\n'+'Febrero')
			columnas1.append('H.E.\n'+'Marzo')
			columnas1.append('H.E.\n'+'Abril')
		else:
			columnas1.append('H.E.\n'+'Mayo')
			columnas1.append('H.E.\n'+'Junio')
			columnas1.append('H.E.\n'+'Julio')
			columnas1.append('H.E.\n'+'Agosto')
			columnas1.append('H.E.\n'+'Setiembre')
			columnas1.append('H.E.\n'+'Octubre')
		columnas2 = ['H.E.\nTotal','1/6\nSobret.\nNoc',u'Bonificación','Base','Monto\nMes',u'Monto\nDía']
		if self.period == '05':
			columnas2.append(u'Días\nInasist.\n'+'Noviembre')
			columnas2.append(u'Días\nInasist.\n'+'Diciembre')
			columnas2.append(u'Días\nInasist.\n'+'Enero')
			columnas2.append(u'Días\nInasist.\n'+'Febrero')
			columnas2.append(u'Días\nInasist.\n'+'Marzo')
			columnas2.append(u'Días\nInasist.\n'+'Abril')
		else:
			columnas2.append(u'Días\nInasist.\n'+'Mayo')
			columnas2.append(u'Días\nInasist.\n'+'Junio')
			columnas2.append(u'Días\nInasist.\n'+'Julio')
			columnas2.append(u'Días\nInasist.\n'+'Agosto')
			columnas2.append(u'Días\nInasist.\n'+'Setiembre')
			columnas2.append(u'Días\nInasist.\n'+'Octubre')
		columnas3 = ['Total\nFaltas','Meses',u'Días','Monto\nPor\nMes',u'Monto\nPor\nDía', 'CTS\nSoles','Interes CTS','Otros descuentos','CTS a pagar','Tipo de\nCambio\nVenta',u'CTS\nDólares','Cuenta CTS','Banco']
		columnas = columnas1+columnas2+columnas3

		fil = 4
		for col in range(len(columnas)):
			worksheet.write(fil, col, columnas[col], header_format)

		#------------------------------------------Insertando Data----------------------------------------------
		fil = 5
		lines = self.env['hr.cts.line'].search([('cts',"=",self.id)])
		totals = [0]*33

		for line in lines:
			col = 0
			worksheet.write(fil, col, line.order, basic_format)
			col += 1
			worksheet.write(fil, col, line.nro_doc, basic_format)
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
			worksheet.write(fil, col, line.basic_amount, numeric_format)
			totals[col-7] += line.basic_amount
			col += 1
			worksheet.write(fil, col, line.a_familiar, numeric_format)
			totals[col-7] += line.a_familiar
			col += 1
			worksheet.write(fil, col, line.feriados, numeric_format)
			totals[col-7] += line.feriados
			col += 1
			worksheet.write(fil, col, line.reward_amount, numeric_format)
			totals[col-7] += line.reward_amount
			col += 1
			if self.period == '05':
				worksheet.write(fil, col, line.overtime_night11, numeric_format)
				totals[col-7] += line.overtime_night11
				col += 1
				worksheet.write(fil, col, line.overtime_night12, numeric_format)
				totals[col-7] += line.overtime_night12
				col += 1
				worksheet.write(fil, col, line.overtime_night1, numeric_format)
				totals[col-7] += line.overtime_night1
				col += 1
				worksheet.write(fil, col, line.overtime_night2, numeric_format)
				totals[col-7] += line.overtime_night2
				col += 1
				worksheet.write(fil, col, line.overtime_night3, numeric_format)
				totals[col-7] += line.overtime_night3
				col += 1
				worksheet.write(fil, col, line.overtime_night4, numeric_format)
				totals[col-7] += line.overtime_night4
				col += 1
			else:
				worksheet.write(fil, col, line.overtime_night5, numeric_format)
				totals[col-7] += line.overtime_night5
				col += 1
				worksheet.write(fil, col, line.overtime_night6, numeric_format)
				totals[col-7] += line.overtime_night6
				col += 1
				worksheet.write(fil, col, line.overtime_night7, numeric_format)
				totals[col-7] += line.overtime_night7
				col += 1
				worksheet.write(fil, col, line.overtime_night8, numeric_format)
				totals[col-7] += line.overtime_night8
				col += 1
				worksheet.write(fil, col, line.overtime_night9, numeric_format)
				totals[col-7] += line.overtime_night9
				col += 1
				worksheet.write(fil, col, line.overtime_night10, numeric_format)
				totals[col-7] += line.overtime_night10
				col += 1
			worksheet.write(fil, col, line.overtime_total, numeric_format)
			totals[col-7] += line.overtime_total
			col += 1
			worksheet.write(fil, col, line.overtime_6, numeric_format)
			totals[col-7] += line.overtime_6
			col += 1
			worksheet.write(fil, col, line.bonus, numeric_format)
			totals[col-7] += line.bonus
			col += 1
			worksheet.write(fil, col, line.base_amount, numeric_format)
			totals[col-7] += line.base_amount
			col += 1
			worksheet.write(fil, col, line.monthly_amount, numeric_format)
			totals[col-7] += line.monthly_amount
			col += 1
			worksheet.write(fil, col, line.dayly_amount, numeric_format)
			totals[col-7] += line.dayly_amount
			col += 1
			if self.period == '05':
				worksheet.write(fil, col, line.absences11, basic_center_format)
				totals[col-7] += line.absences11
				col += 1
				worksheet.write(fil, col, line.absences12, basic_center_format)
				totals[col-7] += line.absences12
				col += 1
				worksheet.write(fil, col, line.absences1, basic_center_format)
				totals[col-7] += line.absences1
				col += 1
				worksheet.write(fil, col, line.absences2, basic_center_format)
				totals[col-7] += line.absences2
				col += 1
				worksheet.write(fil, col, line.absences3, basic_center_format)
				totals[col-7] += line.absences3
				col += 1
				worksheet.write(fil, col, line.absences4, basic_center_format)
				totals[col-7] += line.absences4
				col += 1
			else:
				worksheet.write(fil, col, line.absences5, basic_center_format)
				totals[col-7] += line.absences5
				col += 1
				worksheet.write(fil, col, line.absences6, basic_center_format)
				totals[col-7] += line.absences6
				col += 1
				worksheet.write(fil, col, line.absences7, basic_center_format)
				totals[col-7] += line.absences7
				col += 1
				worksheet.write(fil, col, line.absences8, basic_center_format)
				totals[col-7] += line.absences8
				col += 1
				worksheet.write(fil, col, line.absences9, basic_center_format)
				totals[col-7] += line.absences9
				col += 1
				worksheet.write(fil, col, line.absences10, basic_center_format)
				totals[col-7] += line.absences10
				col += 1
			worksheet.write(fil, col, line.absences_total, basic_center_format)
			totals[col-7] += line.absences_total
			col += 1
			worksheet.write(fil, col, line.months, numeric_format)
			totals[col-7] += line.months
			col += 1
			worksheet.write(fil, col, line.days, numeric_format)
			totals[col-7] += line.days
			col += 1
			worksheet.write(fil, col, line.amount_x_month, numeric_format)
			totals[col-7] += line.amount_x_month
			col += 1
			worksheet.write(fil, col, line.amount_x_day, numeric_format)
			totals[col-7] += line.amount_x_day
			col += 1
			worksheet.write(fil, col, line.cts_soles, numeric_format)
			totals[col-7] += line.cts_soles
			col += 1
			worksheet.write(fil, col, line.interes, numeric_format)
			totals[col-7] += line.interes
			col += 1
			worksheet.write(fil, col, line.otros_dsc, numeric_format)
			totals[col-7] += line.otros_dsc
			col += 1
			worksheet.write(fil, col, line.cts_a_pagar, numeric_format)
			totals[col-7] += line.cts_a_pagar
			col += 1
			worksheet.write(fil, col, line.change, numeric_format3)
			totals[col-7] += line.change
			col += 1
			worksheet.write(fil, col, line.cts_dolars, numeric_format)
			totals[col-7] += line.cts_dolars
			col += 1
			worksheet.write(fil, col, line.account if line.account else '', basic_format)
			col += 1
			worksheet.write(fil, col, line.bank if line.bank else '', basic_format)
			col += 1
			fil += 1

		col = 7
		for total in totals:
			if col < 23 or col > 29:
				worksheet.write(fil, col, total, numeric_bold_format)
			col += 1

		col_size = [5, 12, 20, 9]

		worksheet.set_column('A:A', col_size[0])
		worksheet.set_column('B:E', col_size[1])
		worksheet.set_column('F:F', col_size[2])
		worksheet.set_column('G:AI', col_size[3])
		worksheet.set_column('AK:AL', col_size[2])
		workbook.close()

		f = open(direccion + 'CTS.xlsx', 'rb')

		vals = {
			'output_name': 'CTS.xlsx',
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
		doc = SimpleDocTemplate(direccion+"Boletas_CTS.pdf", pagesize=(600,900))

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
				('SPAN',(0,3),(5,3)),
				('SPAN',(6,3),(7,3)),
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
				#('GRID',(0,0),(-1,17),0.5, colors.black),
			]

		#------------------------------------------------------Insertando Data-----------------------------------------
		lines = self.env['hr.cts.line'].search([('cts','=',self.id)], order='code asc')
		company = self.env['res.users'].browse(self.env.uid).company_id
		count = 0
		for line in lines:
			employee = self.env['hr.employee'].search([('id','=',line.employee_id.id)])
			name = line.names + ' ' + line.last_name_father + ' ' + line.last_name_mother
			#--------------------------------------------------Cabecera
			# a = Image(direccion+"calquipalleft.png")
			# a.drawHeight = 50
			# a.drawWidth = 95
			# b = Image(direccion+"calquipalright.png")
			# b.drawHeight = 60
			# b.drawWidth = 80
			cabecera = [['','','',''],]
			table_c = Table(cabecera, colWidths=[120]*2, rowHeights=50, style=estilo_c)
			elements.append(table_c)
			#----------------------------------------------------Datos
			data = [
				['RUC: '+company.partner_id.type_number,'','','','','','',''],
				['Empleador : '+company.partner_id.name,'','','','','','',''],
				[u'Dirección : '+company.partner_id.street,'','','','','','',''],
				[u'Periodo : '+self.period+'/'+self.year.code,'','','','','',u'Código de Trabajador: '+(employee.codigo_trabajador if employee.codigo_trabajador else ''),''],
				['Documento de identidad','','Nombre y Apellidos','','','',U'Situación',''],
				['Tipo',u'Número','','','','','',''],
				[(employee.type_document_id.code if employee.type_document_id.code else ''),line.nro_doc,name,'','','','ACTIVO O SUBSIDIADO',''],
				['Fecha de ingreso','','Tipo de Trabajador','','Régimen Pensionario','','CUSPP',''],
				[line.in_date,'',(employee.tipo_trabajador.name if employee.tipo_trabajador.name else ''),'',(employee.afiliacion.name if employee.afiliacion.name else ''),'',employee.cusspp if employee.cusspp else '',''],
				['Código','Conceptos','','','','Ingresos S/.','Descuentos S/.','Neto S/.'],
				['Ingresos','','','','','','',''],
				['0904','CONMPENSACION POR TIEMPO DE SERVICIOS','','','','{:10,.2f}'.format(line.cts_soles),'',''],
				['','','','','','','',''],
				['Descuentos','','','','','','',''],
				['','','','','','','',''],
				['Aportes del Trabajador','','','','','','',''],
				['','','','','','','',''],
				['Neto a Pagar','','','','','','','{:10,.2f}'.format(line.cts_soles)],
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

		f = open(direccion + 'Boletas_CTS.pdf', 'rb')

		vals = {
			'output_name': 'Boletas_CTS.pdf',
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



class hr_cts_line(models.Model):
	_name = 'hr.cts.line'

	cts			   = fields.Many2one('hr.cts')
	order			 = fields.Integer("Orden", readonly=1)
	employee_id	   = fields.Many2one('hr.employee')
	nro_doc		   = fields.Char("Nro Documento")
	code			  = fields.Char("Código")
	last_name_father  = fields.Char("Apellido\nPaterno")
	last_name_mother  = fields.Char("Apellido\nMaterno")
	names			 = fields.Char("Nombres")
	in_date		   = fields.Date("Fecha\nIngreso")
	basic_amount	  = fields.Float("Sueldo", digits=(10,2))
	a_familiar		= fields.Float("A. Familiar", digits=(10,2))
	feriados		  = fields.Float("Feriados", digits=(10,2))
	reward_amount	 = fields.Float("1/6\nGratif.", digits=(10,2))
	overtime_night1   = fields.Float("H.E.\nEnero", digits=(10,2))
	overtime_night2   = fields.Float("H.E.\nFebrero", digits=(10,2))
	overtime_night3   = fields.Float("H.E.\nMarzo", digits=(10,2))
	overtime_night4   = fields.Float("H.E.\nAbril", digits=(10,2))
	overtime_night5   = fields.Float("H.E.\nMayo", digits=(10,2))
	overtime_night6   = fields.Float("H.E.\nJunio", digits=(10,2))
	overtime_night7   = fields.Float("H.E.\nJulio", digits=(10,2))
	overtime_night8   = fields.Float("H.E.\nAgosto", digits=(10,2))
	overtime_night9   = fields.Float("H.E.\nSetiembre", digits=(10,2))
	overtime_night10  = fields.Float("H.E.\nOctubre", digits=(10,2))
	overtime_night11  = fields.Float("H.E.\nNoviembre", digits=(10,2))
	overtime_night12  = fields.Float("H.E.\nDiciembre", digits=(10,2))
	overtime_total	= fields.Float("H.E.\nTotal", digits=(10,2))
	overtime_6		= fields.Float("1/6\nSobret.\nNoc.", digits=(10,2))
	comision		  = fields.Float(u"Comisión", digits=(10,2))
	bonus			 = fields.Float("Bonificación", digits=(10,2))
	base_amount	   = fields.Float("Base", digits=(10,2))
	monthly_amount	= fields.Float("Monto\nMes", digits=(10,4))
	dayly_amount	  = fields.Float(u"Monto\nDía", digits=(10,4))
	absences1		 = fields.Integer(u"Días\nInasist.\nEnero")
	absences2		 = fields.Integer(u"Días\nInasist.\nFebrero")
	absences3		 = fields.Integer(u"Días\nInasist.\nMarzo")
	absences4		 = fields.Integer(u"Días\nInasist.\nAbril")
	absences5		 = fields.Integer(u"Días\nInasist.\nMayo")
	absences6		 = fields.Integer(u"Días\nInasist.\nJunio")
	absences7		 = fields.Integer(u"Días\nInasist.\nJulio")
	absences8		 = fields.Integer(u"Días\nInasist.\nAgosto")
	absences9		 = fields.Integer(u"Días\nInasist.\nSetiembre")
	absences10		= fields.Integer(u"Días\nInasist.\nOctubre")
	absences11		= fields.Integer(u"Días\nInasist.\nNoviembre")
	absences12		= fields.Integer(u"Días\nInasist.\nDiciembre")
	absences_total	= fields.Integer(u"Total\nFaltas")
	months			= fields.Integer("Meses")
	days			  = fields.Integer(u"Días")
	previous_days	 = fields.Integer(u"Días periodo anterior")
	amount_x_month	= fields.Float("Monto\nPor\nMeses", digits=(10,2))
	amount_x_day	  = fields.Float(u"Monto\nPor\nDías", digits=(10,2))
	absences_discount = fields.Float('Dscto. Inasistencias', digits=(10,2))
	cts_soles		 = fields.Float("CTS\nSoles", digits=(10,2))
	interes		   = fields.Float(u'Interes CTS')
	otros_dsc		  = fields.Float(u'Otros descuentos')
	cts_a_pagar	   = fields.Float(u'CTS a pagar', compute="get_cts_a_pagar")
	change			= fields.Float("Tipo de\nCambio\nVenta", digits=(10,3))
	cts_dolars		= fields.Float(u"CTS\nDólares", digits=(10,2), compute="get_cts_dolars")
	account		   = fields.Char("Cuenta CTS")
	bank			  = fields.Char("Banco")

	conceptos_lines   = fields.One2many('hr.cts.conceptos','line_cts_id','conceptos')

	@api.multi
	def open_concepts(self):
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.cts.line',
			'res_id': self.id,
			'target': 'new',
		}

	@api.one
	def get_cts_a_pagar(self):
		self.cts_a_pagar = self.cts_soles + self.interes - self.otros_dsc

	@api.one
	def get_cts_dolars(self):
		self.cts_dolars = self.cts_a_pagar * self.cts.change

	@api.multi
	def set_concepts(self):
		sum_con = 0
		for con in self.conceptos_lines:
			sum_con += con.monto
		self.base_amount	   = self.basic_amount + self.overtime_6 + self.reward_amount + self.a_familiar + self.bonus + self.comision + sum_con
		self.monthly_amount	= self.base_amount/12.00
		self.dayly_amount	  = self.base_amount/360.00
		self.amount_x_month	= round(self.months*round(self.base_amount/12.00,2),2)
		self.amount_x_day	  = round(self.days*round(self.base_amount/360.00,4),2)
		self.absences_discount = self.absences_total*self.base_amount/360.00
		self.cts_soles		 = (self.months*self.base_amount/12.00) + (self.days*self.base_amount/360.00) - (self.absences_total*self.base_amount/360.00)
		self.cts_dolars		= self.cts_soles/self.cts.change
		self.account		   = self.employee_id.cta_cts
		self.bank			  = self.employee_id.banco_cts

		return True

class hr_cts_conceptos(models.Model):
	_name = 'hr.cts.conceptos'

	line_cts_id = fields.Many2one('hr.cts.line', 'linea')

	concepto_id	= fields.Many2one('hr.lista.conceptos', 'Concepto', required=True)
	monto		  = fields.Float('Monto')
