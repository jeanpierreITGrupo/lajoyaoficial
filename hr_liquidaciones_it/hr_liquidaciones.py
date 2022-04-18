# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

import datetime
import decimal
from dateutil import relativedelta as rdelta
from calendar import monthrange

import sys
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, white, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
import calendar

def count_month_planilla(start_date,end_date):
	restar_cant_meses = 0
	if start_date.day > 1:
		restar_cant_meses += 1

	if end_date.day < calendar.monthrange(end_date.year,end_date.month)[1]:
		restar_cant_meses += 1

	difference = start_date.year - end_date.year
	if difference == 0:
		count_month_star = end_date.month - start_date.month + 1
		count_month_end = 0
	else:
		count_month_star = 12 - start_date.month + 1
		count_month_end = end_date.month
		difference -= 1

	count_month_total = count_month_star + count_month_end + 12*difference - restar_cant_meses
	if count_month_total<0:
		count_month_total=0	

	return count_month_total

def last_day_of_month(any_day):
	next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
	return next_month - datetime.timedelta(days=next_month.day)



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
		end_day + (end_month * 30) + (end_year * 360) -
		start_day - (start_month * 30) - (start_year * 360)
	)



def number_to_letter(number, mi_moneda=None):
	UNIDADES = (
		'',
		'UN ',
		'DOS ',
		'TRES ',
		'CUATRO ',
		'CINCO ',
		'SEIS ',
		'SIETE ',
		'OCHO ',
		'NUEVE ',
		'DIEZ ',
		'ONCE ',
		'DOCE ',
		'TRECE ',
		'CATORCE ',
		'QUINCE ',
		'DIECISEIS ',
		'DIECISIETE ',
		'DIECIOCHO ',
		'DIECINUEVE ',
		'VEINTE '
	)

	DECENAS = (
		'VENTI',
		'TREINTA ',
		'CUARENTA ',
		'CINCUENTA ',
		'SESENTA ',
		'SETENTA ',
		'OCHENTA ',
		'NOVENTA ',
		'CIEN '
	)

	CENTENAS = (
		'CIENTO ',
		'DOSCIENTOS ',
		'TRESCIENTOS ',
		'CUATROCIENTOS ',
		'QUINIENTOS ',
		'SEISCIENTOS ',
		'SETECIENTOS ',
		'OCHOCIENTOS ',
		'NOVECIENTOS '
	)

	MONEDAS = (
		{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
		{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DOLARES', 'symbol': u'US$'},
		{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
		{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
		{'country': u'Perú', 'currency': 'PEN', 'singular': u'SOL', 'plural': u'SOLES', 'symbol': u'S/.'},
		{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
	)
	# Para definir la moneda me estoy basando en los código que establece el ISO 4217
	# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
	# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.

	def __convert_group(n):
		"""Turn each group of numbers into letters"""
		output = ''

		if(n == '100'):
			output = "CIEN"
		elif(n[0] != '0'):
			output = CENTENAS[int(n[0]) - 1]

		k = int(n[1:])
		if(k <= 20):
			output += UNIDADES[k]
		else:
			if((k > 30) & (n[2] != '0')):
				output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
			else:
				output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
		return output
	#raise osv.except_osv('Alerta', number)
	number=str(round(float(number),2))
	separate = number.split(".")
	number = int(separate[0])
	if mi_moneda != None:
		try:
			moneda = ""
			for moneda1 in MONEDAS:
				if moneda1['currency']==mi_moneda:
				# moneda = ifilter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
				# return "Tipo de moneda inválida"
					if number < 2:
						#raise osv.except_osv('Alerta', number)
						if float(number)==0:
							moneda = moneda1['plural']
						else:
							if int(separate[1]) > 0:
								moneda = moneda1['plural']
							else:
								moneda = moneda1['singular']
					else:
						moneda = moneda1['plural']
		except:
			return "Tipo de moneda inválida"
	else:
		moneda = ""

	if int(separate[1]) >= 0:
		moneda = "con " + str(separate[1]).ljust(2,'0') + "/" + "100 " + moneda

	"""Converts a number into string representation"""
	converted = ''
	
	if not (0 <= number < 999999999):
		raise osv.except_osv('Alerta', number)
		#return 'No es posible convertir el numero a letras'

	
	
	number_str = str(number).zfill(9)
	millones = number_str[:3]
	miles = number_str[3:6]
	cientos = number_str[6:]
	

	if(millones):
		if(millones == '001'):
			converted += 'UN MILLON '
		elif(int(millones) > 0):
			converted += '%sMILLONES ' % __convert_group(millones)

	if(miles):
		if(miles == '001'):
			converted += 'MIL '
		elif(int(miles) > 0):
			converted += '%sMIL ' % __convert_group(miles)

	if(cientos):
		if(cientos == '001'):
			converted += 'UN '
		elif(int(cientos) > 0):
			converted += '%s ' % __convert_group(cientos)
	if float(number_str)==0:
		converted += 'CERO '
	converted += moneda

	return converted.upper()

def date_to_month(m):
	meses = {
		1:	"Enero",
		2:	"Febrero",
		3:	"Marzo",
		4: "Abril",
		5: "Mayo",
		6: "Junio",
		7: "Julio",
		8: "Agosto",
		9: "Setiembre",
		10: "Octubre",
		11: "Noviembre",
		12: "Diciembre",
	}
	return meses[m]

class hr_liquidaciones(models.Model):
	_name = 'hr.liquidaciones'

	period_id = fields.Many2one('account.period','Periodo')
	check_bonus = fields.Boolean('Bonificación')
	change_type = fields.Float(u'Tipo de cambio', digits=(12,3))
	sixth_gratification = fields.Many2one('hr.reward', u'1/6 Gratificación', required=True)

	familiar_assignation = fields.Float('Asignacion Familiar', compute="get_familiar_assignation")

	lines_cts = fields.One2many('hr.liquidaciones.lines.cts','liquidacion_id', u'Línea CTS')
	lines_grat = fields.One2many('hr.liquidaciones.lines.grat','liquidacion_id', u'Línea Gratificación')
	lines_vac = fields.One2many('hr.liquidaciones.lines.vac','liquidacion_id', u'Línea Vacaciones')

	

	cts_concept      = fields.Many2one('hr.lista.conceptos',u'CTS')
	grati_concept    = fields.Many2one('hr.lista.conceptos',u'Gratificaciones')
	bono_concept     = fields.Many2one('hr.lista.conceptos',u'Bonificaciones')
	vacacion_concept = fields.Many2one('hr.lista.conceptos',u'Vacaciones')
	indem_concept    = fields.Many2one('hr.lista.conceptos',u'Indemnización')

	_rec_name = 'period_id'

	@api.model
	def create(self, vals):
		hl = self.env['hr.liquidaciones'].search([('period_id','=',vals['period_id'])])
		t = super(hr_liquidaciones,self).create(vals)
		if len(hl) > 0:
			raise osv.except_osv('Alerta!', u"Ya existe una liquidación con el mismo periodo.")
		return t

	@api.one
	def get_familiar_assignation(self):
		if len(self.env['hr.parameters'].search([])) > 0:
			self.familiar_assignation = self.env['hr.parameters'].search([('num_tipo','=',10001)])[0].monto
		else:
			self.familiar_assignation = 85

	@api.one
	def calculate(self):
		
		for i in self.env["hr.employee"].search([]):		
			if i.fecha_cese <= self.period_id.date_stop and i.fecha_cese >= self.period_id.date_start and i.is_practicant==False:
				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(i.fecha_ingreso, fmt)
				f2 = datetime.datetime.strptime(i.fecha_cese, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				tmp_d1 = False
				if d1.day > 1:
					tmp_d1 = d1 + rdelta.relativedelta(days=monthrange(d1.year,d1.month)[1]-d1.day+1)
					d1 = tmp_d1
				rd = rdelta.relativedelta(d2,d1)
				# obj.computable_months = rd.months + (rd.years*12)
				# obj.computable_days = 0#rd.days
				res = days360(f1,f2)
				meses = int(res/30)
				dias = res-(meses*30)
				d2 = f2 + datetime.timedelta(days=1)
				rd = rdelta.relativedelta(d2,d1)
				if meses<=0 and dias<30:
					continue
			
				if len(self.env['hr.liquidaciones.lines.cts'].search([('liquidacion_id','=',self.id), ('employee_id','=',i.id)])) > 0:
					pass
				else:
					temp_faltas = 0

					obj = self.env["hr.tareo.line"].search([('dni','=',i.identification_id)])
					for f in obj:
						temp_faltas += f.dias_suspension_perfecta+f.licencia_sin_goce
					basic_rem = i.basica
					if i.children_number:
						basic_rem += self.familiar_assignation
					if i.is_practicant:
						basic_rem /= 2
					data = {
						'employee_id': i.id,
						'start_date': i.fecha_ingreso,
						'cese_date': i.fecha_cese,
						'basic_remuneration': basic_rem,
						'absences': temp_faltas,
						'sixth_gratification': 0,
						'issue_date': datetime.datetime.today(),
						'liquidacion_id': self.id,
					}
					self.env['hr.liquidaciones.lines.cts'].create(data)

					data_grat = {
						'employee_id': i.id,
						'start_date': i.fecha_ingreso,
						'cese_date': i.fecha_cese,
						'basic_remuneration': basic_rem,
						'absences': temp_faltas,
						'issue_date': datetime.datetime.today(),
						'liquidacion_id': self.id,
					}
					self.env['hr.liquidaciones.lines.grat'].create(data_grat)

					data_vac = {
						'employee_id': i.id,
						'start_date': i.fecha_ingreso,
						'cese_date': i.fecha_cese,
						'basic_remuneration': basic_rem,
						'absences': temp_faltas,
						'fall_due_holidays': 0,
						'issue_date': datetime.datetime.today(),
						'liquidacion_id': self.id,
					}
					self.env['hr.liquidaciones.lines.vac'].create(data_vac)



		for i in self.env['hr.liquidaciones.lines.cts'].search([('liquidacion_id','=',self.id)]):
			if i.employee_id.fecha_cese >= self.period_id.date_start:
				obj = self.env['hr.employee'].search([('id','=',i.employee_id.id)])
				if len(obj):
					rem_base = obj[0].basica
					if obj.children_number:
						rem_base += self.familiar_assignation
					if obj.is_practicant:
						rem_base /= 2
					i.basic_remuneration = rem_base
					i.start_date = obj[0].fecha_ingreso
					i.employee_id.children_number = obj[0].children_number
				else:
					i.unlink()
			else:
				i.unlink()
		for i in self.env['hr.liquidaciones.lines.grat'].search([('liquidacion_id','=',self.id)]):
			if i.employee_id.fecha_cese >= self.period_id.date_start:
				obj = self.env['hr.employee'].search([('id','=',i.employee_id.id)])
				if len(obj):
					rem_base = obj[0].basica
					if obj.children_number:
						rem_base += self.familiar_assignation
					if obj.is_practicant:
						rem_base /= 2
					i.basic_remuneration = rem_base
					i.start_date = obj[0].fecha_ingreso
					i.employee_id.children_number = obj[0].children_number
				else:
					i.unlink()
			else:
				i.unlink()
		for i in self.env['hr.liquidaciones.lines.vac'].search([('liquidacion_id','=',self.id)]):
			if i.employee_id.fecha_cese >= self.period_id.date_start:
				obj = self.env['hr.employee'].search([('id','=',i.employee_id.id)])
				rem_base = obj[0].basica
				if len(obj):
					if obj.children_number:
						rem_base += self.familiar_assignation
					if obj.is_practicant:
						rem_base /= 2
					i.basic_remuneration = rem_base
					i.start_date = obj[0].fecha_ingreso
					i.employee_id.children_number = obj[0].children_number

					on = self.env['hr.membership.line'].search([('membership','=',i.employee_id.afiliacion.id),('periodo','=',i.liquidacion_id.period_id.id)])
					if len(on)>0:
						tmpon = on[0]
						if tmpon.membership.name != 'ONP':
							incomes = 0
							for item in i.ingresos_lines:
								hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',item.concepto_id.id),('afp_pri_se','=',True)])
								for con in hcrl:
									incomes += item.monto
							i.AFP_SI = float(decimal.Decimal(str( (i.total_holidays+incomes) * (tmpon.prima/100.00) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP)) 
						else:
							i.AFP_SI = 0
				else:
					i.unlink()
			else:
				i.unlink()

	@api.multi
	def export(self):

		import io
		from xlsxwriter.workbook import Workbook

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")
		workbook = Workbook( direccion + u'Liquidaciones.xlsx')
		worksheet_cts = workbook.add_worksheet(u"Liquidación CTS")
		worksheet_grat = workbook.add_worksheet(u"Liquidación Gratificación")
		worksheet_vac = workbook.add_worksheet(u"Liquidación Vacación")
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)	

		x= 6				
		worksheet_cts.write(0,0, u"Liquidación CTS:", bold)

		worksheet_cts.write(5,0, u"Nombre",boldbord)
		worksheet_cts.write(5,1, u"Fecha Ingreso",boldbord)
		worksheet_cts.write(5,2, u"Fecha Inicio Comp.",boldbord)
		worksheet_cts.write(5,3, u"Fecha Cese",boldbord)
		worksheet_cts.write(5,4, u"Faltas",boldbord)
		worksheet_cts.write(5,5, u"Remuneración Básica",boldbord)
		worksheet_cts.write(5,6, u"Promedio Sobret Noc.",boldbord)
		worksheet_cts.write(5,7, u"6ta Gratificación",boldbord)
		worksheet_cts.write(5,8, u"Remuneración Computable",boldbord)
		worksheet_cts.write(5,9, u"Meses Comp.",boldbord)
		worksheet_cts.write(5,10, u"Días Comp.",boldbord)
		worksheet_cts.write(5,11, u"Por los Meses",boldbord)
		worksheet_cts.write(5,12, u"Por los Días",boldbord)
		worksheet_cts.write(5,13, u"Total a Pagar",boldbord)
		worksheet_cts.write(5,14, u"Interes CTS",boldbord)
		worksheet_cts.write(5,15, u"Total a pagar actualizado",boldbord)
		for line in self.lines_cts:
			worksheet_cts.write(x,0, "{0} {1} {2}".format(line.employee_id.last_name_father, line.employee_id.last_name_mother, line.employee_id.first_name_complete) if line.employee_id else '' ,bord )
			worksheet_cts.write(x,1,line.start_date if line.start_date else '', bord)
			worksheet_cts.write(x,2,line.comp_date if line.comp_date else '', bord)
			worksheet_cts.write(x,3,line.cese_date if line.cese_date else '', bord)
			worksheet_cts.write(x,4,line.absences if line.absences else '0', bord)
			worksheet_cts.write(x,5,line.basic_remuneration if line.basic_remuneration else '0', numberdos)
			worksheet_cts.write(x,6,line.nocturnal_surcharge_mean if line.nocturnal_surcharge_mean else '0', numberdos)
			worksheet_cts.write(x,7,line.sixth_gratification if line.sixth_gratification else '0', numberdos)
			worksheet_cts.write(x,8,line.computable_remuneration if line.computable_remuneration else '0', numberdos)
			worksheet_cts.write(x,9,line.computable_months if line.computable_months else '0', numberdos)
			worksheet_cts.write(x,10,line.computable_days if line.computable_days else '0', numberdos)
			worksheet_cts.write(x,11,line.for_months if line.for_months else '0', numberdos)
			worksheet_cts.write(x,12,line.for_days if line.for_days else '0', numberdos)
			worksheet_cts.write(x,13,line.total_payment if line.total_payment else '0', numberdos)
			worksheet_cts.write(x,14,line.interes if line.interes else '0', numberdos)
			worksheet_cts.write(x,15,line.total_actualizado if line.total_actualizado else '0', numberdos)
			x = x + 1
		worksheet_cts.set_column('A:A', 31.43)
		worksheet_cts.set_column('B:Z', 20)

		x=6
		worksheet_grat.write(0,0, u"Liquidación Gratificaciones:", bold)

		worksheet_grat.write(5,0, u"Nombre",boldbord)
		worksheet_grat.write(5,1, u"Fecha Ingreso",boldbord)
		worksheet_grat.write(5,2, u"Fecha Inicio Comp.",boldbord)
		worksheet_grat.write(5,3, u"Fecha Cese",boldbord)
		worksheet_grat.write(5,4, u"Faltas",boldbord)
		worksheet_grat.write(5,5, u"Remuneración Básica",boldbord)
		worksheet_grat.write(5,6, u"Promedio Sobret Noc.",boldbord)
		worksheet_grat.write(5,7, u"Remuneración Computable",boldbord)
		worksheet_grat.write(5,8, u"Meses Comp.",boldbord)
		worksheet_grat.write(5,9, u"Días Comp.",boldbord)
		worksheet_grat.write(5,10, u"Por los Meses",boldbord)
		worksheet_grat.write(5,11, u"Por los Días",boldbord)
		worksheet_grat.write(5,12, u"Total Meses",boldbord)
		worksheet_grat.write(5,13, u"Bonificación",boldbord)
		worksheet_grat.write(5,14, u"Total Grat. Bon.",boldbord)
		worksheet_grat.write(5,15, u"ONP",boldbord)
		worksheet_grat.write(5,16, u"AFP JUB",boldbord)
		worksheet_grat.write(5,17, u"AFP SI",boldbord)
		worksheet_grat.write(5,18, u"AFP COM",boldbord)
		worksheet_grat.write(5,19, u"Neto Total",boldbord)
		worksheet_grat.write(5,20, u"Adelanto", boldbord)
		worksheet_grat.write(5,21, u"Saldo", boldbord)
		worksheet_grat.write(5,22, u"Interes gratificación", boldbord)
		worksheet_grat.write(5,23, u"Total a pagar actualizado", boldbord)
		for line in self.lines_grat:
			worksheet_grat.write(x,0, "{0} {1} {2}".format(line.employee_id.last_name_father, line.employee_id.last_name_mother, line.employee_id.first_name_complete) if line.employee_id else '' ,bord )
			worksheet_grat.write(x,1,line.start_date if line.start_date else '', bord)
			worksheet_grat.write(x,2,line.comp_date if line.comp_date else '', bord)
			worksheet_grat.write(x,3,line.cese_date if line.cese_date else '', bord)
			worksheet_grat.write(x,4,line.absences if line.absences else '0', bord)
			worksheet_grat.write(x,5,line.basic_remuneration if line.basic_remuneration else '0', numberdos)
			worksheet_grat.write(x,6,line.nocturnal_surcharge_mean if line.nocturnal_surcharge_mean else '0', numberdos)
			worksheet_grat.write(x,7,line.computable_remuneration if line.computable_remuneration else '0' ,numberdos )
			worksheet_grat.write(x,8,line.computable_months if line.computable_months else '0' ,bord )
			worksheet_grat.write(x,9,line.computable_days if line.computable_days else '0' ,bord )
			worksheet_grat.write(x,10,line.for_months if line.for_months else '0' ,numberdos )
			worksheet_grat.write(x,11,line.for_days if line.for_days else '0' ,numberdos )
			worksheet_grat.write(x,12,line.total_months if line.total_months else '0' ,numberdos )
			worksheet_grat.write(x,13,line.bonus if line.bonus else '0' ,numberdos )
			worksheet_grat.write(x,14,line.total_gratification_bonus if line.total_gratification_bonus else '0' ,numberdos )
			worksheet_grat.write(x,15,line.ONP if line.ONP else '0' ,numberdos )
			worksheet_grat.write(x,16,line.AFP_JUB if line.AFP_JUB else '0' ,numberdos )
			worksheet_grat.write(x,17,line.AFP_SI if line.AFP_SI else '0' ,numberdos )
			worksheet_grat.write(x,18,line.AFP_COM if line.AFP_COM else '0' ,numberdos )
			worksheet_grat.write(x,19,line.total_net if line.total_net else '0' ,numberdos )
			worksheet_grat.write(x,20,line.adelanto if line.adelanto else '0' ,numberdos )
			worksheet_grat.write(x,21,line.saldo if line.saldo else '0' ,numberdos )
			worksheet_grat.write(x,22,line.interes if line.interes else '0' ,numberdos )
			worksheet_grat.write(x,23,line.total_actualizado if line.total_actualizado else '0' ,numberdos )
			x = x + 1
		worksheet_grat.set_column('A:A', 31.43)
		worksheet_grat.set_column('B:Z', 20)

		x=6
		worksheet_vac.write(0,0, u"Liquidación Vacación:", bold)

		worksheet_vac.write(5,0, u"Nombre", boldbord)
		worksheet_vac.write(5,1, u"Fecha Ingreso", boldbord)
		worksheet_vac.write(5,2, u"Fecha Inicio Comp.", boldbord)
		worksheet_vac.write(5,3, u"Fecha Cese", boldbord)
		worksheet_vac.write(5,4, u"Faltas", boldbord)
		worksheet_vac.write(5,5, u"Remuneración Básica", boldbord)
		worksheet_vac.write(5,6, u"Promedio Sobret. Noc.", boldbord)
		worksheet_vac.write(5,7, u"Remuneración Computable", boldbord)
		worksheet_vac.write(5,8, u"Meses Comp.", boldbord)
		worksheet_vac.write(5,9, u"Días Comp.", boldbord)
		worksheet_vac.write(5,10, u"Por los Meses", boldbord)
		worksheet_vac.write(5,11, u"Por los Días", boldbord)
		worksheet_vac.write(5,12, u"Vacaciones", boldbord)
		worksheet_vac.write(5,13, u"Vacaciones no Gozadas", boldbord)
		worksheet_vac.write(5,14, u"Total Vacaciones", boldbord)
		worksheet_vac.write(5,15, u"ONP", boldbord)
		worksheet_vac.write(5,16, u"AFP JUB", boldbord)
		worksheet_vac.write(5,17, u"AFP SI", boldbord)
		worksheet_vac.write(5,18, u"AFP COM", boldbord)
		worksheet_vac.write(5,19, u"Neto Total", boldbord)
		worksheet_vac.write(5,20, u"Interes vacación", boldbord)
		worksheet_vac.write(5,21, u"Total a pagar actualizado", boldbord)
		for line in self.lines_vac:
			worksheet_vac.write(x,0,"{0} {1} {2}".format(line.employee_id.last_name_father, line.employee_id.last_name_mother, line.employee_id.first_name_complete) if line.employee_id else '' ,bord )
			worksheet_vac.write(x,1,line.start_date if line.start_date else '' ,bord )
			worksheet_vac.write(x,2,line.comp_date if line.comp_date else '' ,bord )
			worksheet_vac.write(x,3,line.cese_date if line.cese_date else '' ,bord )
			worksheet_vac.write(x,4,line.absences if line.absences else '0' ,bord )
			worksheet_vac.write(x,5,line.basic_remuneration if line.basic_remuneration else '0' ,numberdos )
			worksheet_vac.write(x,6,line.nocturnal_surcharge_mean if line.nocturnal_surcharge_mean else '0' ,numberdos )
			worksheet_vac.write(x,7,line.computable_remuneration if line.computable_remuneration else '0' ,numberdos )
			worksheet_vac.write(x,8,line.computable_months if line.computable_months else '0' ,bord )
			worksheet_vac.write(x,9,line.computable_days if line.computable_days else '0' ,bord )
			worksheet_vac.write(x,10,line.for_months if line.for_months else '0' ,numberdos )
			worksheet_vac.write(x,11,line.for_days if line.for_days else '0' ,numberdos )
			worksheet_vac.write(x,12,line.total_holidays_sinva if line.total_holidays_sinva else '0' ,numberdos )
			worksheet_vac.write(x,13,line.fall_due_holidays if line.fall_due_holidays else '0' ,numberdos )
			worksheet_vac.write(x,14,line.total_holidays if line.total_holidays else '0' ,numberdos )
			worksheet_vac.write(x,15,line.ONP if line.ONP else '' ,numberdos )
			worksheet_vac.write(x,16,line.AFP_JUB if line.AFP_JUB else '0' ,numberdos )
			worksheet_vac.write(x,17,line.AFP_SI if line.AFP_SI else '0' ,numberdos )
			worksheet_vac.write(x,18,line.AFP_COM if line.AFP_COM else '0' ,numberdos )
			worksheet_vac.write(x,19,line.total_net if line.total_net else '0' ,numberdos )
			worksheet_vac.write(x,20,line.interes if line.interes else '0' ,numberdos )
			worksheet_vac.write(x,21,line.total_actualizado if line.total_actualizado else '0' ,numberdos )
			x = x + 1
		worksheet_vac.set_column('A:A', 31.43)
		worksheet_vac.set_column('B:Z', 20)

		workbook.close()
		
		f = open( direccion + u'Liquidaciones.xlsx', 'rb')
		
		
		vals = {
			'output_name': u'Liquidaciones.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}

	@api.multi
	def export_pdf(self,employee_ids):

		if not hasattr(employee_ids, '__iter__'):
			employee_ids = [employee_ids]

		self.reporteador(employee_ids)
		
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		import os
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		vals = {
			'output_name': 'Liquidaciones Reporte.pdf',
			'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
		}
		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def open_reporte_empleado_wizard(self):
		view_id = self.env.ref('hr_liquidaciones_it.view_reporte_empleado_wizard_form',False)
		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'reporte.empleado.wizard',
			# 'res_id'   : self.id,
			'view_id'  : view_id.id,
			'view_type': 'form',
			'view_mode': 'form',
			'views'    : [(view_id.id, 'form')],
			'target'   : 'new',
			#'flags'    : {'form': {'action_buttons': True}},
			'context'  : {'employees' : [line.employee_id.id for line in self.lines_cts],},
		}

	@api.multi
	def cabezera(self,c,wReal,hReal):

		import os
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		c.setFont("Arimo-Bold", 6)
		c.setFillColor(black)
		endl = 12
		pos_inicial = hReal-10
		pagina = 1

		c.drawCentredString((wReal/2.00),pos_inicial, "LIQUIDACIÓN DE BENEFICIOS SOCIALES")
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
		c.drawCentredString((wReal/2.00),pos_inicial, "LIQUIDACIÓN DE BENEFICIOS SOCIALES QUE OTORGA")
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
		c.drawCentredString((wReal/2.00),pos_inicial, "LA JOYA MINING SAC")
		# c.drawImage(direccion + 'calquipalright.png',20, hReal-20, width=120, height=50)

	@api.multi
	def reporteador(self, employee_ids):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize=A4)
		inicio = 0
		pos_inicial = hReal-60
		endl = 9
		font_size = 6

		pagina = 1
		textPos = 0

		pdfmetrics.registerFont(TTFont('Arimo-Bold', 'Arimo-Bold.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-BoldItalic', 'Arimo-BoldItalic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Italic', 'Arimo-Italic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Regular', 'Arimo-Regular.ttf'))

		hllc = self.env['hr.liquidaciones.lines.cts'].search([('employee_id','in',employee_ids),('liquidacion_id','=',self.id)])
		for i in hllc:
			self.cabezera(c,wReal,hReal)
			hllg = self.env['hr.liquidaciones.lines.grat'].search([('employee_id','=',i.employee_id.id),('liquidacion_id','=',self.id)])[0]
			hllv = self.env['hr.liquidaciones.lines.vac'].search([('employee_id','=',i.employee_id.id),('liquidacion_id','=',self.id)])[0]
			

			total_sum = 0

			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"DATOS PERSONALES")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.drawString( 40 , pos_inicial, u"Nombres y Apellidos")
			c.drawString( 140 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 150 , pos_inicial, i.employee_id.name_related if i.employee_id.name_related else '')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"DNI Nº")
			c.drawString( 140 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 150 , pos_inicial, i.employee_id.identification_id if i.employee_id.identification_id else '')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Cargo")
			c.drawString( 140 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 150 , pos_inicial, i.employee_id.job_id.name if i.employee_id.job_id.name else '')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Fecha de Ingreso")
			c.drawString( 140 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 150 , pos_inicial, i.employee_id.fecha_ingreso if i.employee_id.fecha_ingreso else '')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Fecha de Cese")
			c.drawString( 140 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 150 , pos_inicial, i.employee_id.fecha_cese if i.employee_id.fecha_cese else '')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)			
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Motivo")
			c.drawString( 140 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 150 , pos_inicial, i.cese_reason if i.cese_reason else '')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Afiliación")
			c.drawString( 140 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 150 , pos_inicial, i.employee_id.afiliacion.name if i.employee_id.afiliacion.name else '')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Último Sueldo Básico")
			c.drawString( 140 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 150 , pos_inicial, ('{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.employee_id.basica )) if i.basic_remuneration else "0.00") + " "*4 + u"NUEVOS SOLES")
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 240 , pos_inicial, u"Tipo de Cambio")
			c.drawString( 280 , pos_inicial, u":")
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 290 , pos_inicial, str(self.change_type) if self.change_type else '0.00')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

			# if self.change_type:
			# 	c.setFont("Arimo-Bold", font_size)
			# 	c.drawString( 40 , pos_inicial, u"T. Cambio")
			# 	c.drawString( 140 , pos_inicial, u":")
			# 	c.setFont("Arimo-Regular", font_size)
			# 	c.drawString( 150 , pos_inicial, str(self.change_type) if self.change_type else '')
			# 	pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Tiempo de Servicio")
			c.drawString( 140 , pos_inicial, u":")
			if i.employee_id.fecha_ingreso and i.employee_id.fecha_cese:
				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(i.start_date, fmt)
				f2 = datetime.datetime.strptime(i.cese_date, fmt)
				fr = rdelta.relativedelta(f2,f1) + rdelta.relativedelta(days=1)
				txt = ""

				res = days360(f1,f2+rdelta.relativedelta(days=1))
				meses = int(res/30)
				anios = int(meses/12)
				# meses1 = meses - int(meses/12)
				meses1 = meses - (anios*12)
				dias = res-(meses*30)
				
				if dias>=i.absences:
					dias = dias-i.absences
				else:
					meses1 = meses1 - 1
					dias = 30 +(dias- i.absences)


				if fr.years:
					txt += str(anios) + u" AÑO(S) "
				if fr.months:
					txt += str(meses1) + u" MES(ES)"
				if fr.days:
					txt += str(dias) + u" DÍA(S)"
				c.setFont("Arimo-Regular", font_size)
				c.drawString( 150 , pos_inicial, txt)




			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*2,pagina)

			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"BASES DE CÁLCULO")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			basraw = i.basic_remuneration
			afraw  = self.env['hr.parameters'].search([('num_tipo','=',10001)])[0].monto if i.employee_id.children_number else 0
			if i.employee_id.is_practicant:
				afraw /= 2
			basraw -= afraw
			if i.employee_id.basica:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"BÁSICO")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % basraw )) if basraw else '')
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if i.employee_id.children_number:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"ASIG. FAMILIAR")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				hp = self.env['hr.parameters'].search([('num_tipo','=',10001)])
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % afraw )) if afraw else '')
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if i.nocturnal_surcharge_mean:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"PROM. SOBRETAZA NOCTURNA")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.nocturnal_surcharge_mean )) if i.nocturnal_surcharge_mean else '')
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if i.sixth_gratification:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"1/6 ULTIMA GRATIF.")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.sixth_gratification )) if i.sixth_gratification else '')
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"1. COMPENSACIÓN POR TIEMPO DE SERVICIOS")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			fi = i.comp_date.split('-') if i.comp_date else ''
			fc = i.cese_date.split('-') if i.cese_date else ''
			str_fi = (date_to_month(int(fi[1]))+" "+fi[0]) if i.comp_date else '_'*8
			str_fc = (date_to_month(int(fc[1]))+" "+fc[0]) if i.cese_date else '_'*8
			c.drawString( 30 , pos_inicial, u"(Periodo "+str_fi+" A "+str_fc+")")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if i.total_payment:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"CTS")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.total_payment )) if i.total_payment else "0.00")
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if i.for_days or i.for_months:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Tiempo")
				c.drawString( 170 , pos_inicial, u":")
				tiempo_cts = ""
				if i.computable_months:
					tiempo_cts += str(int(i.computable_months)) + u" Mes(es) "
				if i.computable_days:
					tiempo_cts += str(int(i.computable_days)) + u" Día(s) "
				c.setFont("Arimo-Regular", font_size)
				c.drawString( 200 , pos_inicial, tiempo_cts)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if False:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Inters. CTS")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % 0 )) )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"2. VACACIONES")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			fi = hllv.comp_date.split('-') if hllv.comp_date else ''
			fc = hllv.cese_date.split('-') if hllv.cese_date else ''
			str_fi = (date_to_month(int(fi[1]))+" "+fi[0]) if hllv.comp_date else '_'*8
			str_fc = (date_to_month(int(fc[1]))+" "+fc[0]) if hllv.cese_date else '_'*8
			c.drawString( 30 , pos_inicial, u"(Periodo "+str_fi+" A "+str_fc+")")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.total_holidays_sinva:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Vacaciones Truncas")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.total_holidays_sinva )) if hllv.total_holidays_sinva else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.fall_due_holidays:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Remuneración Vacacional")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.fall_due_holidays )) if hllv.fall_due_holidays else "0.00")
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.compensation:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Vacaciones Indem.")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.compensation )) if hllv.compensation else "0.00")
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.for_days or hllv.for_months:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Tiempo")
				c.drawString( 170 , pos_inicial, u":")
				tiempo_vac = ""
				if hllv.computable_months:
					tiempo_vac += str(int(hllv.computable_months)) + u" Mes(es) "
				if hllv.computable_days:
					tiempo_vac += str(int(hllv.computable_days)) + u" Día(s) "
				c.setFont("Arimo-Regular", font_size)
				c.drawString( 200 , pos_inicial, tiempo_vac)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"3. GRATIFICACIONES")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			fi = hllg.comp_date.split('-') if hllg.comp_date else ''
			fc = hllg.cese_date.split('-') if hllg.cese_date else ''
			str_fi = (date_to_month(int(fi[1]))+" "+fi[0]) if hllg.comp_date else '_'*8
			str_fc = (date_to_month(int(fc[1]))+" "+fc[0]) if hllg.cese_date else '_'*8
			c.drawString( 30 , pos_inicial, u"(Periodo "+str_fi+" A "+str_fc+")")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllg.total_months:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Gratificación Trunca")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllg.total_months )) if hllg.total_months else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllg.bonus:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"BONIF EX.L. 30334")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllg.bonus )) if hllg.bonus else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllg.for_days or hllg.for_months:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Tiempo")
				c.drawString( 170 , pos_inicial, u":")
				tiempo_grat = ""
				if hllg.computable_months:
					tiempo_grat += str(int(hllg.computable_months)) + u" Mes(es) "
				if hllg.computable_days:
					tiempo_grat += str(int(hllg.computable_days)) + u" Día(s) "
				c.setFont("Arimo-Regular", font_size)
				c.drawString( 200 , pos_inicial,tiempo_grat)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"4. LIQUIDACIÓN")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if i.total_payment:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"CTS")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.total_payment )) if i.total_payment else "0.00")
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.total_holidays_sinva:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Vacaciones Truncas")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.total_holidays_sinva )) if hllv.total_holidays_sinva else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllg.total_months:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Gratificación Trunca")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllg.total_months )) if hllg.total_months else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			hfcdl = self.env['hr.five.category.devolucion.lines'].search([('devolucion_id.period_id','=',self.period_id.id),('employee_id','=',hllg.employee_id.id)])
			

			if len(hfcdl):
				hfcdl = hfcdl[0]
				if hfcdl.monto_devolver < 0:
					c.setFont("Arimo-Bold", font_size)
					c.drawString( 40 , pos_inicial, u"Devolucion Imp. Renta 5ta Categ.")
					c.drawString( 170 , pos_inicial, u":")
					c.setFont("Arimo-Regular", font_size)
					c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (hfcdl.monto_devolver*-1) )))
					pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
				else:
					c.setFont("Arimo-Bold", font_size)
					c.drawString( 40 , pos_inicial, u"Retención Imp. Renta 5ta Categ.")
					c.drawString( 170 , pos_inicial, u":")
					c.setFont("Arimo-Regular", font_size)
					c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (hfcdl.monto_devolver) )))
					pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)

			if (i.interes+hllg.interes+hllv.interes) > 0:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Intereses Liquidación")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (i.interes+hllg.interes+hllv.interes) )))
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllg.bonus:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"BONIF EX.L. 30334")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllg.bonus )) if hllg.bonus else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.fall_due_holidays:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Remuneración Vacacional")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.fall_due_holidays )) if hllv.fall_due_holidays else "0.00")
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.compensation:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"Vacaciones Indem")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.compensation )) if hllv.compensation else "0.00")
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)			
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"OTROS INGRESOS")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			tot_ingresos = i.total_payment + hllv.total_holidays_sinva + hllg.total_months + hllg.bonus + hllv.fall_due_holidays + hllv.compensation + ((hfcdl[0].monto_devolver*-1) if len(hfcdl) else 0) + (i.interes+hllg.interes+hllv.interes)
			for item in hllv.ingresos_lines:
				if item.monto:
					c.setFont("Arimo-Bold", font_size)
					c.drawString( 40 , pos_inicial, item.concepto_id.name)
					c.drawString( 170 , pos_inicial, u":")
					c.setFont("Arimo-Regular", font_size)
					c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % item.monto )) )
					tot_ingresos += item.monto
					pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Total Ingresos")
			c.setFont("Arimo-Bold", font_size)
			c.drawRightString( 330 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % tot_ingresos )) if tot_ingresos else "0.00" )
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*2,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Aportes Trabajador")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.ONP:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"SNP")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.ONP )) if hllv.ONP else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.AFP_JUB or hllv.AFP_SI or hllv.AFP_COM:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"AFP. PENSIONES")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.AFP_JUB )) if hllv.AFP_JUB else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"AFP. COM. PORC.")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.AFP_COM )) if hllv.AFP_COM else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"AFP. SEGUROS")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.AFP_SI )) if hllv.AFP_SI else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.afp_2p:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"AFP. 2%")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.afp_2p )) if hllv.afp_2p else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			if hllv.fondo_jub:
				c.setFont("Arimo-Bold", font_size)
				c.drawString( 40 , pos_inicial, u"FONDO DE JUBILACION")
				c.drawString( 170 , pos_inicial, u":")
				c.setFont("Arimo-Regular", font_size)
				c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % hllv.fondo_jub )) if hllv.fondo_jub else "0.00" )
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			tot_descuentos = hllv.ONP + hllv.AFP_JUB + hllv.AFP_SI + hllv.AFP_COM + hllv.afp_2p + hllv.fondo_jub
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"OTROS DESCUENTOS")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			for item in hllv.descuentos_lines:
				if item.concepto_id.payroll_group != '4':
					if item.monto:
						c.setFont("Arimo-Bold", font_size)
						c.drawString( 40 , pos_inicial, item.concepto_id.name)
						c.drawString( 170 , pos_inicial, u":")
						c.setFont("Arimo-Regular", font_size)
						c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % item.monto )) )
						tot_descuentos += item.monto
						pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)			
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Total Descuentos")
			c.setFont("Arimo-Bold", font_size)
			c.drawRightString( 330 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % tot_descuentos )) if tot_descuentos else "0.00")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			# pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			# c.setFont("Arimo-Bold", font_size)
			# c.drawString( 40 , pos_inicial, u"Aportes Empleador")
			# pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			# for item in hllv.descuentos_lines:
			# 	if item.concepto_id.payroll_group == '4':
			# 		if item.monto:
			# 			c.setFont("Arimo-Bold", font_size)
			# 			c.drawString( 40 , pos_inicial, item.concepto_id.name)
			# 			c.drawString( 170 , pos_inicial, u":")
			# 			c.setFont("Arimo-Regular", font_size)
			# 			c.drawRightString( 250 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % item.monto )) )
			# 			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			# pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Bold", font_size)
			c.drawString( 40 , pos_inicial, u"Total a Pagar")
			c.setFont("Arimo-Bold", font_size)
			c.drawRightString( 330 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (tot_ingresos - tot_descuentos) )) if (tot_ingresos - tot_descuentos) else "0.00")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*2,pagina)

			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"Neto a Pagar al Trabajador")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.setFont("Arimo-Regular", font_size)
			c.drawString( 40 , pos_inicial, u"SON")
			c.setFont("Arimo-Bold", font_size)
			tot_tot = '{:,.2f}'.format(decimal.Decimal ("%0.2f" % (tot_ingresos - tot_descuentos) ))
			c.drawString( 55 , pos_inicial, number_to_letter(float(tot_tot.replace(',',''))).capitalize() + " soles")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*3,pagina)

			c.setFont("Arimo-Regular", font_size)
			# isd = i.issue_date.split('-' ) if i.issue_date else ''
			isd = i.employee_id.fecha_cese.split('-') if i.employee_id.fecha_cese else ''
			c.drawString( 300 , pos_inicial, ("Arequipa " + isd[2] + " de "+date_to_month(int(isd[1]))+" del "+isd[0]) if i.issue_date else '_'*28)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)			
			txt = u"Dpto. de personal"
			c.drawCentredString( 100 , pos_inicial, u"_"*len(txt)*2)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.drawCentredString( 100 , pos_inicial, txt)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.drawCentredString( 100 , pos_inicial, u'LA JOYA MINING SAC')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*2,pagina)

			c.setFont("Arimo-Bold", font_size)
			c.drawString( 30 , pos_inicial, u"CONSTANCIA DE RECEPCIÓN")
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*4,pagina)

			style = getSampleStyleSheet()["Normal"]
			style.leading = 12
			style.alignment = 4

			paragraph1 = Paragraph(
				"<font size=6>" + u"Declaro estar conforme con la presente liquidación, haber recibido el importe de la misma así como el importe correspondiente a todas y cada una de  mis remuneraciones y beneficios no teniendo que reclamar en el futuro, quedando asi concluida la relación laboral. </font>",
				style
			)

			data= [[ paragraph1 ]]
			t=Table(data,colWidths=(515), rowHeights=(40))
			t.setStyle(TableStyle([
			('TEXTFONT', (0, 0), (-1, -1), 'Arimo-Regular'),
			('FONTSIZE',(0,0),(-1,-1),font_size)
			]))
			t.wrapOn(c,40,pos_inicial)
			t.drawOn(c,40,pos_inicial)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*3,pagina)

			c.setFont("Arimo-Regular", font_size)		
			txt = i.employee_id.name_related
			c.drawCentredString( 250 , pos_inicial, u"_"*len(txt)*2)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.drawCentredString( 250 , pos_inicial, txt)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
			c.drawCentredString( 250 , pos_inicial, i.employee_id.identification_id if i.employee_id.identification_id else '')

			pagina += 1
			c.showPage()
			inicio = 0
			pos_inicial = hReal-100
			pagina = 1
			textPos = 0
		c.save()

	@api.multi
	def particionar_text(self,c,d):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Arimo-Regular',8,d)
			if len(tet)>d:
				return tet[:-1]
		return tet


	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <10:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Arimo-Bold", 6)
			#c.drawCentredString(300,25,'Pag. ' + str(pagina+1))
			return pagina+1,hReal-60
		else:
			return pagina,posactual-valor

	@api.multi
	def open_cert_wizard(self):
		view_id = self.env.ref('hr_liquidaciones_it.view_hr_certificado_trabajo_wizard_form',False)
		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'hr.certificado.trabajo.wizard',
			# 'res_id'   : self.id,
			'view_id'  : view_id.id,
			'view_type': 'form',
			'view_mode': 'form',
			'views'    : [(view_id.id, 'form')],
			'target'   : 'new',
			#'flags'    : {'form': {'action_buttons': True}},
			'context'  : {'employees': [line.employee_id.id for line in self.lines_cts]},
		}

class hr_liquidaciones_lines_cts(models.Model):
	_name = 'hr.liquidaciones.lines.cts'

	liquidacion_id = fields.Many2one('hr.liquidaciones', 'liquidacion padre')

	code                     = fields.Char('Código', compute="get_code")
	employee_id              = fields.Many2one('hr.employee', 'Empleado')
	start_date               = fields.Date('Fecha Ingreso')
	comp_date                = fields.Date('Fecha Inicio Comp.')
	cese_date                = fields.Date('Fecha Cese')
	absences                 = fields.Integer('Faltas')
	basic_remuneration       = fields.Float('Remuneración Básica')
	nocturnal_surcharge_mean = fields.Float('Promedio Horas Extras')
	sixth_gratification      = fields.Float('1/6 Gratificación', compute="get_sixth_gratification")
	computable_remuneration  = fields.Float('Remuneración Computable', compute="get_computable_remuneration")
	computable_months        = fields.Float('Meses Comp.')
	computable_days          = fields.Float('Días Comp.')
	for_months               = fields.Float('Por los Meses', digits=(12,2), compute="get_for_months")
	for_days                 = fields.Float('Por los Días', digits=(12,2), compute="get_for_days")
	absences_discount	     = fields.Float('Descuento Faltas', digits=(12,2), compute="get_absences_discount")
	total_payment            = fields.Float('Total a Pagar', digits=(12,2), compute="get_total_payment")
	interes					 = fields.Float(u'Interes CTS')
	total_actualizado 		 = fields.Float(u'Total a pagar actualizado', compute="get_total_actualizado")
	issue_date               = fields.Date('Fecha Depósito')
	cese_reason              = fields.Text('Motivo de Cese')

	@api.one
	def get_code(self):
		self.code = self.employee_id.codigo_trabajador

	@api.one
	def get_sixth_gratification(self):
		if self.liquidacion_id.sixth_gratification:
			# employee_id
			fecha_mes       = self.liquidacion_id.period_id.date_stop
			fecha_mes = datetime.datetime.strptime(fecha_mes, '%Y-%m-%d')

			fechaingreso = datetime.datetime.strptime(self.start_date, '%Y-%m-%d')

			# datetime.datetime.strptime(self.cese_date, '%Y-%m-%d')
			lastdaymomnt    = monthrange(fecha_mes.year,fecha_mes.month)
			fechacese       = datetime.datetime.strptime(self.cese_date, '%Y-%m-%d')
			fechainicomputo = datetime.datetime.strptime(str(fecha_mes.year)+'-01-01', '%Y-%m-%d')
			if(self.comp_date):
				fechainicomputo = datetime.datetime.strptime(self.comp_date, '%Y-%m-%d')
			yearact		 = datetime.datetime.strptime(self.liquidacion_id.period_id.date_start, '%Y-%m-%d').year
			hr			  = False
			fechacese_month = False
			if fechacese.month<=6:	
				# fiscalyear
				if fechaingreso.year<=yearact-1:
					fiscalyear= self.env['account.fiscalyear'].search([('name','=',str(fecha_mes.year-1))])
					d = self.env['hr.reward'].search([('period','=','12'),('year','=',fiscalyear.id)])
					if len(d)>0:
						hr = d[0]
				
			if fechacese.month>=7:	
				if fechaingreso.year<=yearact:
					if fechaingreso.month<=7 or fechaingreso.year<yearact:
						fiscalyear= self.env['account.fiscalyear'].search([('name','=',str(fecha_mes.year))])
						d = self.env['hr.reward'].search([('period','=','07'),('year','=',fiscalyear.id)])
						if len(d)>0:
							hr  = d[0]
							if fechacese.month==12:
								d   = self.env['hr.reward'].search([('period','=','12'),('year','=',fiscalyear.id)])
								if len(d)>0:
									hr  = d[0]
									if fechacese.day != lastdaymomnt[1]:
										d   = self.env['hr.reward'].search([('period','=','07'),('year','=',fiscalyear.id)])
										if len(d)>0:
											hr  = d[0]
										else:
											hr=False
								else:
									hr = False

			
			
			
			
			
			# hr              = False
			# fechacese_month = False
			# if fechacese.month<=6:	
				# fiscalyear
				# fiscalyear= self.env['account.fiscalyear'].search([('name','=',str(fecha_mes.year-1))])
				# d = self.env['hr.reward'].search([('period','=','12'),('year','=',fiscalyear.id)])
				# if len(d)>0:
					
					# hr = d[0]
				
			# if fechacese.month>=7:	
				# fiscalyear= self.env['account.fiscalyear'].search([('name','=',str(fecha_mes.year))])
				# d = self.env['hr.reward'].search([('period','=','07'),('year','=',fiscalyear.id)])
				# if len(d)>0:
					# hr  = d[0]
					# if fechacese.month==12:
						# d   = self.env['hr.reward'].search([('period','=','12'),('year','=',fiscalyear.id)])
						# if len(d)>0:
							# hr  = d[0]
							# if fechacese.day != lastdaymomnt[1]:
								# d   = self.env['hr.reward'].search([('period','=','07'),('year','=',fiscalyear.id)])
								# if len(d)>0:
									# hr  = d[0]
								# else:
									# hr=False
						# else:
							# hr = False
			hr=self.liquidacion_id.sixth_gratification
			if hr:
				res_sitxh = 0
				hrl = self.env['hr.reward.line'].search([('reward','=',hr.id),('employee_id','=',self.employee_id.id)])
				for line in hrl:
					res_sitxh += line.total_reward
				self.sixth_gratification = res_sitxh/6.00
				if self.employee_id.id==151:
					self.sixth_gratification = 500
			else:
				self.sixth_gratification = 0	
		else:
			self.sixth_gratification = 0

	@api.one
	def get_computable_remuneration(self):
		self.computable_remuneration = self.basic_remuneration + self.nocturnal_surcharge_mean + self.sixth_gratification 

	@api.one
	def get_for_months(self):
		self.for_months = float(decimal.Decimal(str( (self.computable_remuneration / 12) * self.computable_months )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def get_for_days(self):
		self.for_days = float(decimal.Decimal(str( ((self.computable_remuneration / 360) * self.computable_days) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
		"""if self.computable_months == 0:
			self.for_days = 0
		else:
			#self.for_days = float(decimal.Decimal(str( (((self.computable_remuneration / 12) / 30) * self.computable_days) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
			self.for_days = float(decimal.Decimal(str( ((self.computable_remuneration / 360) * self.computable_days) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))"""

	@api.one
	def get_absences_discount(self):
		self.absences_discount = self.computable_remuneration/360.00*self.absences

	@api.one
	def get_total_payment(self):
		self.total_payment = float(decimal.Decimal(str( self.for_months + self.for_days)).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def get_total_actualizado(self):
		self.total_actualizado = float(decimal.Decimal(str( self.total_payment + self.interes)).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def write(self, vals):
		t = super(hr_liquidaciones_lines_cts, self).write(vals)
		self.refresh()
		cont_noct = self.nocturnal_surcharge_mean
		falt = self.absences
		fd = self.issue_date
		obj = self.env['hr.liquidaciones.lines.grat'].search([('employee_id','=',self.employee_id.id),
																  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if obj.comp_date:
				start_period = datetime.datetime.strptime(obj.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(obj.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',obj.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',obj.employee_id.id)])
				for falta in hlf:
					res_absences += falta.gratificaciones


				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(obj.comp_date, fmt)
				f2 = datetime.datetime.strptime(obj.cese_date, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				tmp_d1 = False
				if d1.day > 1:
					tmp_d1 = d1 + rdelta.relativedelta(days=monthrange(d1.year,d1.month)[1]-d1.day+1)
					d1 = tmp_d1
				rd = rdelta.relativedelta(d2,d1)
				# obj.computable_months = rd.months + (rd.years*12)
				# obj.computable_days = 0#rd.days
				res = days360(f1,f2)+1
				meses = int(res/30)
				dias = res-(meses*30)
				d2 = f2 + datetime.timedelta(days=1)
				rd = rdelta.relativedelta(d2,d1)

				hlp = self.env['hr.liquidaciones.parametros'].search([])[0]
				if dias > 0 and hlp.faltas_gratificaciones:
					res_absences = 0
					
				fechacese	   = datetime.datetime.strptime(obj.cese_date, '%Y-%m-%d')
				lastdaymomnt = str(last_day_of_month(datetime.date(fechacese.year, fechacese.month, 1)))[8:]
				# if str(obj.cese_date)[8:]!=lastdaymomnt:
				# 	if int(str(obj.comp_date)[8:])!=1:
				# 		meses = meses - 1
				month_planilla = count_month_planilla(f1, f2)
				
				to_write["computable_months"] = month_planilla
				to_write["computable_days"]   = 0

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			obj.write(to_write)

		obj2 = self.env['hr.liquidaciones.lines.vac'].search([('employee_id','=',self.employee_id.id),
																  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if obj2.comp_date:
				start_period = datetime.datetime.strptime(obj2.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(obj2.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',obj2.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',obj2.employee_id.id)])
				for falta in hlf:
					res_absences += falta.vacaciones

				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(obj2.comp_date, fmt)
				f2 = datetime.datetime.strptime(obj2.cese_date, fmt)
				d1 = f1
				d2 = f2
				res = days360(f1,d2)
				meses = int(res/30)
				dias = res-(meses*30)
				d2 = f2 + datetime.timedelta(days=1)
				rd = rdelta.relativedelta(d2,d1)
				if dias>=res_absences:
					dias = dias-res_absences
				else:
					meses = meses - 1
					dias = 30 +(dias- res_absences)
				to_write["computable_months"] = meses
				to_write["computable_days"]   = dias

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			obj2.write(to_write)

		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if self.comp_date:
				start_period = datetime.datetime.strptime(self.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(self.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',self.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',self.employee_id.id)])
				for falta in hlf:
					res_absences += falta.cts

				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(self.comp_date, fmt)
				f2 = datetime.datetime.strptime(self.cese_date, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				rd = rdelta.relativedelta(d2,d1)

				res = days360(f1,d2)
				meses = int(res/30)
				dias = res-(meses*30)

				# self.computable_months = rd.months + (rd.years*12)
				# self.computable_days = rd.days
				if dias>=res_absences:
					dias = dias-res_absences
				else:
					meses = meses - 1
					dias = 30 +(dias- res_absences)
				to_write["computable_months"] = meses
				to_write["computable_days"]   = dias

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			self.write(to_write)

			keywords = ['cts_concept']
			for keyword in keywords:
				for i in self.env['hr.concepto.empleado.relacion'].search([('period_id','=',self.liquidacion_id.period_id.id),('campo','=',keyword),('employee_id','=',self.employee_id.id)]):
					i.unlink()

				hcer_vals = {
					'campo'      : keyword,
					'concepto_id': self.liquidacion_id.cts_concept.id,
					'monto'      : self.total_payment,
					'period_id'  : self.liquidacion_id.period_id.id,
					'employee_id': self.employee_id.id,
				}
				self.env['hr.concepto.empleado.relacion'].create(hcer_vals)


		return t

	@api.one
	def unlink(self):
		if 'cont' in self.env.context:
			pass
		else:
			obj = self.env['hr.liquidaciones.lines.grat'].search([('employee_id','=',self.employee_id.id),
																	  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
			obj2 = self.env['hr.liquidaciones.lines.vac'].search([('employee_id','=',self.employee_id.id),
																	  ('liquidacion_id','=',self.liquidacion_id.id)])[0]

			obj.with_context({'cont':True}).unlink()
			obj2.with_context({'cont':True}).unlink()
		return super(hr_liquidaciones_lines_cts, self).unlink()

class hr_liquidaciones_lines_grat(models.Model):
	_name = 'hr.liquidaciones.lines.grat'

	liquidacion_id = fields.Many2one('hr.liquidaciones', 'liquidacion padre')

	code                      = fields.Char('Código', compute="get_code")
	employee_id               = fields.Many2one('hr.employee', 'Empleado')
	start_date                = fields.Date('Fecha Ingreso')
	comp_date                 = fields.Date('Fecha Inicio Comp.')
	cese_date                 = fields.Date('Fecha Cese')
	absences                  = fields.Integer('Faltas')
	basic_remuneration        = fields.Float('Remuneración Básica')
	nocturnal_surcharge_mean  = fields.Float('Promedio Sobret Noc.')
	computable_remuneration   = fields.Float('Remuneración Computable', compute="get_computable_remuneration")
	computable_months         = fields.Float('Meses Comp.')
	computable_days           = fields.Float('Días Comp.')
	for_months                = fields.Float('Por los Meses', digits=(12,2), compute="get_for_months")
	for_days                  = fields.Float('Por los Días', digits=(12,2), compute="get_for_days")
	absences_discount         = fields.Float('Descuento Faltas', digits=(12,2), compute="get_absences_discount")
	total_months              = fields.Float('Total Meses', digits=(12,2), compute="get_total_months")
	bonus                     = fields.Float('Bonificación 9%', digits=(12,2), compute="get_bonus")
	total_gratification_bonus = fields.Float('Total Gratificaciíón y Bono', digits=(12,2), compute="get_total_gratification_bonus")
	ONP                       = fields.Float('ONP')
	AFP_JUB                   = fields.Float('AFP JUB')
	AFP_SI                    = fields.Float('AFP SI')
	AFP_COM                   = fields.Float('AFP COM')
	total_net                 = fields.Float('Neto a Pagar', digits=(12,2), compute="get_total_net")
	adelanto                  = fields.Float(u'Adelanto', digits=(12,2))
	saldo                     = fields.Float(u'Saldo', compute="get_saldo")
	interes                   = fields.Float(u'Interes gratificación')
	total_actualizado         = fields.Float(u'Total a pagar actualizado', compute="get_total_actualizado")
	issue_date                = fields.Date('Fecha Depósito')
	cese_reason               = fields.Text('Motivo de Cese')

	@api.one
	def get_code(self):
		self.code = self.employee_id.codigo_trabajador

	@api.one
	def get_computable_remuneration(self):
		self.computable_remuneration = self.basic_remuneration + self.nocturnal_surcharge_mean

	@api.one
	def get_for_months(self): 
		self.for_months = float(decimal.Decimal(str( (self.computable_remuneration / 6) * self.computable_months )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def get_for_days(self):
		if self.computable_months == 0:
			self.for_days = 0
		else:
			self.for_days = float(decimal.Decimal(str( (self.computable_remuneration / 180) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP)) * self.computable_days

	@api.one
	def get_absences_discount(self):
		if self.computable_months == 0:
			self.absences_discount = 0
		else:
			self.absences_discount = self.computable_remuneration/180.00*self.absences

	@api.one
	def get_total_months(self):
		self.total_months = self.for_months + self.for_days

	@api.one
	def get_bonus(self):
		if self.liquidacion_id.check_bonus == True:
			pct = 0.09
			if self.employee_id.use_eps:
				hp = self.env['hr.parameters'].search([('num_tipo','=',5)])[0]
				pct -= (hp.monto/100.00)
			self.bonus = float(decimal.Decimal(str( self.total_months * pct )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
		else:
			self.bonus = 0

	@api.one
	def get_total_gratification_bonus(self):
		if self.liquidacion_id.check_bonus == True:
			self.total_gratification_bonus = self.total_months + self.bonus
		else:
			self.total_gratification_bonus = self.total_months

	@api.one
	def get_total_net(self):
		self.total_net = float(decimal.Decimal(str( self.total_gratification_bonus )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def get_saldo(self):
		self.saldo = float(decimal.Decimal(str( (self.total_net - self.adelanto) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def get_total_actualizado(self):
		self.total_actualizado = float(decimal.Decimal(str( (self.saldo + self.interes) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def write(self, vals):
		t = super(hr_liquidaciones_lines_grat, self).write(vals)
		cont_noct = self.nocturnal_surcharge_mean
		falt = self.absences
		fd = self.issue_date
		obj = self.env['hr.liquidaciones.lines.cts'].search([('employee_id','=',self.employee_id.id),
																  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if obj.comp_date:

				start_period = datetime.datetime.strptime(obj.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(obj.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',obj.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',obj.employee_id.id)])
				for falta in hlf:
					res_absences += falta.cts

				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(obj.comp_date, fmt)
				f2 = datetime.datetime.strptime(obj.cese_date, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				rd = rdelta.relativedelta(d2,d1)
				# obj.computable_months = rd.months + (rd.years*12)
				# obj.computable_days = rd.days

				res = days360(f1,d2)+1
				meses = int(res/30)
				dias = res-(meses*30)
				if dias>=res_absences:
					dias = dias-res_absences
				else:
					meses = meses - 1
					dias = 30 +(dias- res_absences)
				to_write["computable_months"] = meses
				to_write["computable_days"]   = dias

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			obj.write(to_write)
			

		obj2 = self.env['hr.liquidaciones.lines.vac'].search([('employee_id','=',self.employee_id.id),
																  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if obj2.comp_date:
				start_period = datetime.datetime.strptime(obj2.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(obj2.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',obj2.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',obj2.employee_id.id)])
				for falta in hlf:
					res_absences += falta.vacaciones

				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(obj2.comp_date, fmt)
				f2 = datetime.datetime.strptime(obj2.cese_date, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				rd = rdelta.relativedelta(d2,d1)
				# obj2.computable_months = rd.months + (rd.years*12)
				# obj2.computable_days = rd.days
				res = days360(f1,d2)
				meses = int(res/30)
				dias = res-(meses*30)
				if dias>=res_absences:
					dias = dias-res_absences
				else:
					meses = meses - 1
					dias = 30 +(dias- res_absences)
				to_write["computable_months"] = meses
				to_write["computable_days"]   = dias

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			obj2.write(to_write)

		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if self.comp_date:
				start_period = datetime.datetime.strptime(self.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(self.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',self.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',self.employee_id.id)])
				for falta in hlf:
					res_absences += falta.gratificaciones

				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(self.comp_date, fmt)
				f2 = datetime.datetime.strptime(self.cese_date, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				tmp_d1 = False
				if d1.day > 1:
					tmp_d1 = d1 + rdelta.relativedelta(days=monthrange(d1.year,d1.month)[1]-d1.day+1)
					d1 = tmp_d1
				rd = rdelta.relativedelta(d2,d1)
				res = days360(f1,d2)+1
				meses = int(res/30)
				dias = res-(meses*30)
				print self.employee_id.first_name_complete,res, meses,dias,int(str(self.comp_date)[8:])


				hlp = self.env['hr.liquidaciones.parametros'].search([])[0]
				if dias > 0 and hlp.faltas_gratificaciones:
					res_absences = 0
				fechacese	   = datetime.datetime.strptime(self.cese_date, '%Y-%m-%d')
				lastdaymomnt = str(last_day_of_month(datetime.date(fechacese.year, fechacese.month, 1)))[8:]

				# if str(self.cese_date)[8:]!=lastdaymomnt:
				# 	if int(str(self.comp_date)[8:])!=1:
				# 		meses = meses - 1

				month_planilla = count_month_planilla(f1, f2)
				if dias>=res_absences:
					dias = dias-res_absences
				else:
					meses = meses - 1
					dias = 30 +(dias- res_absences)				
				to_write["computable_months"] = float(month_planilla)
				to_write["computable_days"]   = 0

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			self.write(to_write)

			keywords = ['grati_concept','bono_concept']
			for keyword in keywords:
				for i in self.env['hr.concepto.empleado.relacion'].search([('period_id','=',self.liquidacion_id.period_id.id),('campo','=',keyword),('employee_id','=',self.employee_id.id)]):
					i.unlink()

				crt_monto = 0
				crt_concepto = False
				if keyword == 'grati_concept':
					crt_monto = self.total_months
					crt_concepto = self.liquidacion_id.grati_concept.id
				if keyword == 'bono_concept':
					crt_monto = self.bonus
					crt_concepto = self.liquidacion_id.bono_concept.id
				hcer_vals = {
					'campo'      : keyword,
					'concepto_id': crt_concepto,
					'monto'      : crt_monto,
					'period_id'  : self.liquidacion_id.period_id.id,
					'employee_id': self.employee_id.id,
				}
				self.env['hr.concepto.empleado.relacion'].create(hcer_vals)



		return t

	@api.one
	def unlink(self):
		if 'cont' in self.env.context:
			pass
		else:
			obj = self.env['hr.liquidaciones.lines.cts'].search([('employee_id','=',self.employee_id.id),
																	  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
			obj2 = self.env['hr.liquidaciones.lines.vac'].search([('employee_id','=',self.employee_id.id),
																	  ('liquidacion_id','=',self.liquidacion_id.id)])[0]

			obj.with_context({'cont':True}).unlink()
			obj2.with_context({'cont':True}).unlink()
		return super(hr_liquidaciones_lines_grat, self).unlink()

class hr_liquidaciones_lines_vac(models.Model):
	_name = 'hr.liquidaciones.lines.vac'

	liquidacion_id = fields.Many2one('hr.liquidaciones', 'liquidacion padre')

	code                     = fields.Char('Código', compute="get_code")
	employee_id              = fields.Many2one('hr.employee', 'Empleado')
	start_date               = fields.Date('Fecha Ingreso')
	comp_date                = fields.Date('Fecha Inicio Comp.')
	cese_date                = fields.Date('Fecha Cese')
	absences                 = fields.Integer('Faltas')
	fall_due_holidays        = fields.Float('Remuneración vacacional')
	basic_remuneration       = fields.Float('Remuneración Básica')
	nocturnal_surcharge_mean = fields.Float('Promedio Sobret Noc.')
	computable_remuneration  = fields.Float('Remuneración Computable', compute="get_computable_remuneration")
	computable_months        = fields.Float('Meses Comp.')
	computable_days          = fields.Float('Días Comp.')
	for_months               = fields.Float('Por los Meses', digits=(12,2), compute="get_for_months")
	for_days                 = fields.Float('Por los Días', digits=(12,2), compute="get_for_days")
	absences_discount        = fields.Float('Descuento Faltas', digits=(12,2), compute="get_absences_discount")
	total_holidays           = fields.Float('Total Vacaciones', digits=(12,2), compute="get_total_holidays")
	total_holidays_sinva     = fields.Float('Vacaciones', digits=(12,2), compute="get_total_holidays_sinva")
	ONP                      = fields.Float('ONP', digits=(12,2), compute="get_onp")
	AFP_JUB                  = fields.Float('AFP JUB', digits=(12,2), compute="get_afp_jub")
	AFP_SI                   = fields.Float('AFP SI', digits=(12,2))#, compute="get_afp_si")
	AFP_COM                  = fields.Float('AFP COM', digits=(12,2), compute="get_afp_com")
	afp_2p                   = fields.Float(u'AFP 2%', compute="get_afp_2p")
	fondo_jub                = fields.Float(u'Fondo Jubilación', compute="get_fondo_jub")
	compensation             = fields.Float('Indemnización')
	total_net                = fields.Float('Neto a Pagar', digits=(12,2), compute="get_total_net")
	interes                  = fields.Float(u'Interes vacación')
	total_actualizado        = fields.Float(u'Total a pagar actualizado', compute="get_total_actualizado")
	issue_date               = fields.Date('Fecha Emisión')
	cese_reason              = fields.Text('Motivo de Cese')

	ingresos_lines			 = fields.One2many('hr.liquidaciones.ingresos.vac','line_vac_id','Ingresos')
	descuentos_lines		 = fields.One2many('hr.liquidaciones.descuentos.vac','line_vac_id','Descuentos')

	@api.multi
	def open_incomes(self):
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.liquidaciones.lines.vac',
			'res_id': self.id,
			'target': 'new',
		}

	@api.multi
	def set_incomes(self):
		return True

	@api.one
	def get_code(self):
		self.code = self.employee_id.codigo_trabajador

	@api.one
	def get_computable_remuneration(self):
		self.computable_remuneration = self.basic_remuneration + self.nocturnal_surcharge_mean

	@api.one
	def get_for_months(self): 
		self.for_months = float(decimal.Decimal(str( (self.computable_remuneration / 12) * self.computable_months )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def get_for_days(self):
		self.for_days = float(decimal.Decimal(str( ((self.computable_remuneration / 360) * self.computable_days) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

		# if self.computable_months == 0:
		# 	self.for_days = 0
		# else:
		# 	#self.for_days = float(decimal.Decimal(str( (((self.computable_remuneration / 12) / 30) * self.computable_days) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
		# 	self.for_days = float(decimal.Decimal(str( ((self.computable_remuneration / 360) * self.computable_days) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def get_absences_discount(self):
		self.absences_discount = self.computable_remuneration/360.00*self.absences

	@api.one
	def get_total_holidays_sinva(self):
		self.total_holidays_sinva = self.for_months + self.for_days

	@api.one
	def get_total_holidays(self):
		self.total_holidays = self.fall_due_holidays + self.total_holidays_sinva 

	@api.one
	def get_onp(self):
		on = self.env['hr.membership.line'].search([('membership','=',self.employee_id.afiliacion.id),('periodo','=',self.liquidacion_id.period_id.id)])
		if len(on)>0:
			tmpon = on[0]
			if tmpon.membership.name == 'ONP':
				incomes = 0
				for item in self.ingresos_lines:
					hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',item.concepto_id.id),('onp','=',True)])
					for con in hcrl:
						incomes += item.monto
				self.ONP = float(decimal.Decimal(str( (self.total_holidays+incomes) * (tmpon.tasa_pensiones/100.00) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
			else:
				self.ONP = 0

	@api.one
	def get_afp_jub(self):
		on = self.env['hr.membership.line'].search([('membership','=',self.employee_id.afiliacion.id),('periodo','=',self.liquidacion_id.period_id.id)])
		if len(on)>0:
			tmpon = on[0]
			if tmpon.membership.name != 'ONP':
				incomes = 0
				for item in self.ingresos_lines:
					hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',item.concepto_id.id),('afp_fon_pen','=',True)])
					for con in hcrl:
						incomes += item.monto
				self.AFP_JUB = float(decimal.Decimal(str( (self.total_holidays+incomes) * (tmpon.tasa_pensiones/100.00) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
			else:
				self.AFP_JUB = 0

	@api.one
	def get_afp_si(self):
		on = self.env['hr.membership.line'].search([('membership','=',self.employee_id.afiliacion.id),('periodo','=',self.liquidacion_id.period_id.id)])
		if len(on)>0:
			tmpon = on[0]
			if tmpon.membership.name != 'ONP':
				incomes = 0
				for item in self.ingresos_lines:
					hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',item.concepto_id.id),('afp_pri_se','=',True)])
					for con in hcrl:
						incomes += item.monto
				self.AFP_SI = float(decimal.Decimal(str( (self.total_holidays+incomes) * (tmpon.prima/100.00) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP)) 
			else:
				self.AFP_SI = 0

	@api.one
	def get_afp_com(self):
		on = self.env['hr.membership.line'].search([('membership','=',self.employee_id.afiliacion.id),('periodo','=',self.liquidacion_id.period_id.id)])
		if len(on)>0:
			tmpon = on[0]
			if tmpon.membership.name != 'ONP':
				incomes = 0
				for item in self.ingresos_lines:
					hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',item.concepto_id.id),('afp_co_va','=',True)])
					if self.employee_id.c_mixta:
						hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',item.concepto_id.id),('afp_co_mix','=',True)])
					for con in hcrl:
						incomes += item.monto
				if self.employee_id.c_mixta:
					self.AFP_COM = float(decimal.Decimal(str( (self.total_holidays+incomes) * (tmpon.c_mixta/100) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
				else:
					self.AFP_COM = float(decimal.Decimal(str( (self.total_holidays+incomes) * (tmpon.c_variable/100) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
			else:
				self.AFP_COM = 0

	@api.one
	def get_afp_2p(self):		
		res_icon = 0
		if self.employee_id.afp_2p:
			res_icon = self.total_holidays
			for i in self.ingresos_lines:
				hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',i.concepto_id.id)])
				if len(hcrl):
					hcrl = hcrl[0]
					if hcrl.afp_2p:
						res_icon += i.monto
			for i in self.descuentos_lines:
				hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',i.concepto_id.id)])
				if len(hcrl):
					hcrl = hcrl[0]
					if hcrl.afp_2p:
						res_icon -= i.monto

			hp = self.env['hr.parameters'].search([('num_tipo','=',8)])[0]
			res_icon = res_icon * hp.monto/100.00
		self.afp_2p = res_icon

	@api.one
	def get_fondo_jub(self):
		res_icon = 0
		if self.employee_id.fondo_jub:
			res_icon = self.total_holidays
			for i in self.ingresos_lines:
				hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',i.concepto_id.id)])
				if len(hcrl):
					hcrl = hcrl[0]
					if hcrl.jubilacion:
						res_icon += i.monto
			for i in self.descuentos_lines:
				hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto','=',i.concepto_id.id)])
				if len(hcrl):
					hcrl = hcrl[0]
					if hcrl.jubilacion:
						res_icon -= i.monto

			hp = self.env['hr.parameters'].search([('num_tipo','=',3)])[0]
			res_icon = res_icon * hp.monto/100.00
		self.fondo_jub = res_icon

	@api.one
	def get_total_net(self):
		va = self.total_holidays - self.ONP - self.AFP_JUB - self.AFP_SI - self.AFP_COM + self.compensation
		self.total_net = float(decimal.Decimal(str( va )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

	@api.one
	def get_total_actualizado(self):
		self.total_actualizado = float(decimal.Decimal(str( (self.total_net + self.interes) )).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))	

	@api.one
	def write(self, vals):
		t = super(hr_liquidaciones_lines_vac, self).write(vals)
		cont_noct = self.nocturnal_surcharge_mean
		falt = self.absences
		fd = self.issue_date
		obj = self.env['hr.liquidaciones.lines.cts'].search([('employee_id','=',self.employee_id.id),
																  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if obj.comp_date:
				start_period = datetime.datetime.strptime(obj.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(obj.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',obj.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',obj.employee_id.id)])
				for falta in hlf:
					res_absences += falta.cts

				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(obj.comp_date, fmt)
				f2 = datetime.datetime.strptime(obj.cese_date, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				rd = rdelta.relativedelta(d2,d1)
				# obj.computable_months = rd.months + (rd.years*12)
				# obj.computable_days = rd.days


				res = days360(f1,d2)
				meses = int(res/30)
				dias = res-(meses*30)
				if dias>=res_absences:
					dias = dias-res_absences
				else:
					meses = meses - 1
					dias = 30 +(dias- res_absences)				

				to_write["computable_months"] = meses
				to_write["computable_days"]   = dias

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			obj.write(to_write)			

		obj2 = self.env['hr.liquidaciones.lines.grat'].search([('employee_id','=',self.employee_id.id),
																  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if obj2.comp_date:
				start_period = datetime.datetime.strptime(obj2.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(obj2.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',obj2.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',obj2.employee_id.id)])
				for falta in hlf:
					res_absences += falta.gratificaciones

				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(obj2.comp_date, fmt)
				f2 = datetime.datetime.strptime(obj2.cese_date, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				tmp_d1 = False
				if d1.day > 1:
					tmp_d1 = d1 + rdelta.relativedelta(days=monthrange(d1.year,d1.month)[1]-d1.day+1)
					d1 = tmp_d1
				rd = rdelta.relativedelta(d2,d1)
				# obj2.computable_months = rd.months + (rd.years*12)
				# obj2.computable_days = 0#rd.days
				
				res = days360(f1,d2)+1
				meses = int(res/30)
				dias = res-(meses*30)
				fechacese	   = datetime.datetime.strptime(obj2.cese_date, '%Y-%m-%d')
				lastdaymomnt = str(last_day_of_month(datetime.date(fechacese.year, fechacese.month, 1)))[8:]
				# if str(obj2.cese_date)[8:]!=lastdaymomnt:
				# 	if int(str(obj2.comp_date)[8:])!=1:
				# 		meses = meses - 1


				hlp = self.env['hr.liquidaciones.parametros'].search([])[0]
				if dias > 0 and hlp.faltas_gratificaciones:
					res_absences = 0

				month_planilla = count_month_planilla(f1, f2)
				to_write["computable_months"] = month_planilla
				to_write["computable_days"]   = 0

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			obj2.write(to_write)

		if "flag_dont_write" in vals:
			pass
		else:
			res_absences = 0
			to_write = {}
			if self.comp_date:
				start_period = datetime.datetime.strptime(self.comp_date,"%Y-%m-%d")
				start_period -= rdelta.relativedelta(days=start_period.day-1)
				stop_period  = datetime.datetime.strptime(self.cese_date,"%Y-%m-%d")
				stop_period += rdelta.relativedelta(days=(monthrange(stop_period.year,stop_period.month)[1]-stop_period.day))
				ap = self.env['account.period'].search([('date_start','>=',start_period),('date_stop','<=',stop_period)])
				ht = self.env['hr.tareo'].search([('periodo','in',ap.ids)])
				for tareo in ht:
					htl = self.env['hr.tareo.line'].search([('employee_id','=',self.employee_id.id),('tareo_id','=',tareo.id)])
					if len(htl):
						htl = htl[0]
						res_absences += htl.dias_suspension_perfecta+htl.licencia_sin_goce
				hlf = self.env['hr.liquidaciones.faltas'].search([('period_id','in',ap.ids),('employee_id','=',self.employee_id.id)])
				for falta in hlf:
					res_absences += falta.vacaciones

				fmt = '%Y-%m-%d'
				f1 = datetime.datetime.strptime(self.comp_date, fmt)
				f2 = datetime.datetime.strptime(self.cese_date, fmt)
				d1 = f1
				# d2 = f2 - datetime.timedelta(days=res_absences) + datetime.timedelta(days=1)
				d2 = f2 + datetime.timedelta(days=1)
				rd = rdelta.relativedelta(d2,d1)
				# self.computable_months = rd.months + (rd.years*12)
				# self.computable_days = rd.days
				res = days360(f1,d2,False)
				meses = int(res/30)
				dias = res-(meses*30)
				
				if dias>=res_absences:
					dias = dias-res_absences
				else:
					meses = meses - 1
					dias = 30 +(dias- res_absences)
				to_write["computable_months"] = meses
				to_write["computable_days"]   = dias

			to_write["absences"]        = res_absences
			to_write["flag_dont_write"] = True
			to_write["flag_absences"]   = True
			to_write["issue_date"]      = fd
			to_write["cese_reason"]     = self.cese_reason

			self.write(to_write)

			keywords = ['vacacion_concept','indem_concept']
			for keyword in keywords:
				for i in self.env['hr.concepto.empleado.relacion'].search([('period_id','=',self.liquidacion_id.period_id.id),('campo','=',keyword),('employee_id','=',self.employee_id.id)]):
					i.unlink()

				crt_monto = 0
				crt_concepto = False
				if keyword == 'vacacion_concept':
					crt_monto = self.total_holidays_sinva
					crt_concepto = self.liquidacion_id.vacacion_concept.id
				if keyword == 'indem_concept':
					crt_monto = self.compensation
					crt_concepto = self.liquidacion_id.indem_concept.id

				hcer_vals = {
					'campo'      : keyword,
					'concepto_id': crt_concepto,
					'monto'      : crt_monto,
					'period_id'  : self.liquidacion_id.period_id.id,
					'employee_id': self.employee_id.id,
				}
				self.env['hr.concepto.empleado.relacion'].create(hcer_vals)


		return t

	@api.one
	def unlink(self):
		if 'cont' in self.env.context:
			pass
		else:
			obj = self.env['hr.liquidaciones.lines.cts'].search([('employee_id','=',self.employee_id.id),
																	  ('liquidacion_id','=',self.liquidacion_id.id)])[0]
			obj2 = self.env['hr.liquidaciones.lines.grat'].search([('employee_id','=',self.employee_id.id),
																	  ('liquidacion_id','=',self.liquidacion_id.id)])[0]

			obj.with_context({'cont':True}).unlink()
			obj2.with_context({'cont':True}).unlink()
		return super(hr_liquidaciones_lines_vac, self).unlink()



class hr_liquidaciones_ingresos_vac(models.Model):
	_name = 'hr.liquidaciones.ingresos.vac'

	line_vac_id = fields.Many2one('hr.liquidaciones.lines.vac', 'linea')

	concepto_id = fields.Many2one('hr.lista.conceptos', 'Concepto', required=True)
	monto		= fields.Float('Monto')

class hr_liquidaciones_descuentos_vac(models.Model):
	_name = 'hr.liquidaciones.descuentos.vac'

	line_vac_id = fields.Many2one('hr.liquidaciones.lines.vac', 'linea')

	concepto_id = fields.Many2one('hr.lista.conceptos', 'Concepto', required=True)
	monto		= fields.Float('Monto')

class hr_concepto_empleado_relacion(models.Model):
	_name = 'hr.concepto.empleado.relacion'

	campo       = fields.Char('campo')
	concepto_id = fields.Many2one('hr.lista.conceptos','concepto')
	monto       = fields.Float('monto')
	period_id   = fields.Many2one('account.period','periodo')
	employee_id = fields.Many2one('hr.employee','empleado')

class hr_liquidaciones_view(models.Model):
	_name = 'hr.liquidaciones.view'
	_auto = False

	padre = fields.Many2one('hr.liquidaciones','Padre')
	cel = fields.Selection([('1','CTS'),('2','Gratificacion'),('3','Vacacion')],'Tipo')
	id_linea = fields.Integer('Linea')

	cts_id = fields.Many2one('hr.liquidaciones.lines.cts','Linea')
	grat_id = fields.Many2one('hr.liquidaciones.lines.grat','Linea')
	vac_id = fields.Many2one('hr.liquidaciones.lines.vac','Linea')

	code = fields.Char('Código', compute="get_code")
	start_date = fields.Date('Fecha Ingreso',compute='get_start_date')
	comp_date = fields.Date('Fecha Inicio Comp.',compute='get_comp_date')
	cese_date = fields.Date('Fecha Cese',compute='get_cese_date')
	absences = fields.Integer('Faltas',compute='get_absences')
	fall_due_holidays = fields.Float('Vacaciones Adeudadas', compute="get_fall_due_holidays")
	basic_remuneration = fields.Float('Remuneración Básica',compute='get_basic_remuneration')
	nocturnal_surcharge_mean = fields.Float('Promedio Sobret. Noc.',compute='get_nocturnal_surcharge_mean')
	sixth_gratification = fields.Float('1/6 Gratificación',compute='get_sixth_gratification')
	computable_remuneration = fields.Float('Remuneración Computable',compute='get_computable_remuneration')
	computable_months = fields.Integer('Meses Comp',compute='get_computable_months')
	computable_days = fields.Integer('Días Comp',compute='get_computable_days')
	for_months = fields.Float('Por los Meses',compute='get_for_months')
	for_days = fields.Float('Por los Días',compute='get_for_days')
	total_months = fields.Float('Total Meses', compute="get_total_months")
	bonus = fields.Float('Bonificación 9%', compute="get_bonus")
	total_gratification_bonus = fields.Float('Total Gratificación y Bono', compute="get_total_gratification_bonus")
	total_holidays = fields.Float('Total Vacaciones', compute="get_total_holidays")
	ONP = fields.Float('ONP',compute='get_onp')
	AFP_JUB = fields.Float('AFP JUB',compute='get_afp_jub')
	AFP_SI = fields.Float('AFP SI',compute='get_afp_si')
	AFP_COM = fields.Float('AFP COM',compute='get_afp_com')
	total_payment = fields.Float('Total a Pagar',compute='get_total_payment')

	trabajador = fields.Many2one('hr.employee','Trabajador')
	_order = 'cel'

	@api.one
	def get_code(self):
		if self.cel == '1':
			self.code = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].code
		elif self.cel == '2':
			self.code = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].code
		elif self.cel == '3':
			self.code = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].code

	@api.one
	def get_start_date(self):
		if self.cel == '1':
			self.start_date = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].start_date
		elif self.cel == '2':
			self.start_date = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].start_date
		elif self.cel == '3':
			self.start_date = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].start_date

	@api.one
	def get_comp_date(self):
		if self.cel == '1':
			self.comp_date = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].comp_date
		elif self.cel == '2':
			self.comp_date = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].comp_date
		elif self.cel == '3':
			self.comp_date = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].comp_date

	@api.one
	def get_cese_date(self):
		if self.cel == '1':
			self.cese_date = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].cese_date
		elif self.cel == '2':
			self.cese_date = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].cese_date
		elif self.cel == '3':
			self.cese_date = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].cese_date

	@api.one
	def get_absences(self):
		if self.cel == '1':
			self.absences = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].absences
		elif self.cel == '2':
			self.absences = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].absences
		elif self.cel == '3':
			self.absences = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].absences

	@api.one
	def get_fall_due_holidays(self):
		if self.cel == '3':
			self.fall_due_holidays = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].fall_due_holidays

	@api.one
	def get_basic_remuneration(self):
		if self.cel == '1':
			self.basic_remuneration = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].basic_remuneration
		elif self.cel == '2':
			self.basic_remuneration = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].basic_remuneration
		elif self.cel == '3':
			self.basic_remuneration = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].basic_remuneration

	@api.one
	def get_nocturnal_surcharge_mean(self):
		if self.cel == '1':
			self.nocturnal_surcharge_mean = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].nocturnal_surcharge_mean
		elif self.cel == '2':
			self.nocturnal_surcharge_mean = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].nocturnal_surcharge_mean
		elif self.cel == '3':
			self.nocturnal_surcharge_mean = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].nocturnal_surcharge_mean

	@api.one
	def get_sixth_gratification(self):
		if self.cel == '1':
			self.sixth_gratification = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].sixth_gratification
		else:
			self.sixth_gratification = False

	@api.one
	def get_computable_remuneration(self):
		if self.cel == '1':
			self.computable_remuneration = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].computable_remuneration
		elif self.cel == '2':
			self.computable_remuneration = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].computable_remuneration
		elif self.cel == '3':
			self.computable_remuneration = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].computable_remuneration

	@api.one
	def get_computable_months(self):
		if self.cel == '1':
			self.computable_months = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].computable_months
		elif self.cel == '2':
			self.computable_months = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].computable_months
		elif self.cel == '3':
			self.computable_months = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].computable_months

	@api.one
	def get_computable_days(self):
		if self.cel == '1':
			self.computable_days = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].computable_days
		elif self.cel == '2':
			self.computable_days = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].computable_days
		elif self.cel == '3':
			self.computable_days = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].computable_days

	@api.one
	def get_for_months(self):
		if self.cel == '1':
			self.for_months = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].for_months
		elif self.cel == '2':
			self.for_months = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].for_months
		elif self.cel == '3':
			self.for_months = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].for_months

	@api.one
	def get_for_days(self):
		if self.cel == '1':
			self.for_days = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].for_days
		elif self.cel == '2':
			self.for_days = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].for_days
		elif self.cel == '3':
			self.for_days = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].for_days

	@api.one
	def get_total_months(self):
		if self.cel == '2':
			self.total_months = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].total_months
		else:
			self.total_months = False

	@api.one
	def get_bonus(self):
		if self.cel == '2':
			self.bonus = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].bonus
		else:
			self.bonus = False
	
	@api.one
	def get_total_gratification_bonus(self):
		if self.cel == '2':
			self.total_gratification_bonus = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].total_gratification_bonus
		else:
			self.total_gratification_bonus = False

	@api.one
	def get_total_holidays(self):
		if self.cel == '3':
			self.total_holidays = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].total_holidays
		else:
			self.total_holidays = False

	@api.one
	def get_onp(self):
		if self.cel == '2':
			self.ONP = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].ONP
		elif self.cel =='3':
			self.ONP = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].ONP
		else:
			self.ONP = False

	@api.one
	def get_afp_jub(self):
		if self.cel == '2':
			self.AFP_JUB = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].AFP_JUB
		elif self.cel =='3':
			self.AFP_JUB = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].AFP_JUB
		else:
			self.AFP_JUB = False

	@api.one
	def get_afp_si(self):
		if self.cel == '2':
			self.AFP_SI = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].AFP_SI
		elif self.cel =='3':
			self.AFP_SI = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].AFP_SI
		else:
			self.AFP_SI = False


	@api.one
	def get_afp_com(self):
		if self.cel == '2':
			self.AFP_COM = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].AFP_COM
		elif self.cel =='3':
			self.AFP_COM = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].AFP_COM
		else:
			self.AFP_COM = False

	@api.one
	def get_total_payment(self):
		if self.cel == '1':
			self.total_payment = self.env['hr.liquidaciones.lines.cts'].search([('id','=',self.id_linea)])[0].total_payment
		elif self.cel == '2':
			self.total_payment = self.env['hr.liquidaciones.lines.grat'].search([('id','=',self.id_linea)])[0].total_net
		elif self.cel == '3':
			self.total_payment = self.env['hr.liquidaciones.lines.vac'].search([('id','=',self.id_linea)])[0].total_net

	def init(self,cr):
		cr.execute("""
			CREATE OR REPLACE view hr_liquidaciones_view as (
				SELECT row_number() OVER () AS id,* 
				FROM (

					select id as id_linea,'1' as cel,liquidacion_id as padre, employee_id as trabajador  from hr_liquidaciones_lines_cts where liquidacion_id is not null
					union all
					select id as id_linea, '2' as cel, liquidacion_id as padre, employee_id as trabajador from hr_liquidaciones_lines_grat where liquidacion_id is not null
					union all
					select id as id_linea,'3' as cel, liquidacion_id as padre, employee_id as trabajador from hr_liquidaciones_lines_vac where liquidacion_id is not null

				)T)

			""")

class hr_liquidaciones_parametros(models.Model):
	_name = 'hr.liquidaciones.parametros'

	name = fields.Char(u'Parámetros Liquidaciones', default='Parametros Liquidaciones')

	faltas_gratificaciones = fields.Boolean('Descontar faltas en gratificaciones')

	def init(self, cr):
		cr.execute('select id from hr_liquidaciones_parametros')
		ids = cr.fetchall()

		if len(ids) == 0:
			cr.execute("""INSERT INTO hr_liquidaciones_parametros (name) VALUES ('Parametros Liquidaciones')""")

class hr_liquidaciones_faltas(models.Model):
	_name = 'hr.liquidaciones.faltas'

	period_id       = fields.Many2one('account.period', 'Periodo')
	employee_id     = fields.Many2one('hr.employee', 'Empleado')
	cts             = fields.Integer('CTS')
	gratificaciones = fields.Integer('Gratificaciones')
	vacaciones      = fields.Integer('Vacaciones')
