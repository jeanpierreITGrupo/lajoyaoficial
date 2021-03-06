# -*- encoding: utf-8 -*-
from openerp     import models, fields, api
from openerp.osv import osv, expression
from datetime    import datetime, timedelta
from calendar    import monthrange
from dateutil    import relativedelta
import pprint
import codecs
import base64
import decimal
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_RIGHT

from reportlab.pdfgen          import canvas
from reportlab.lib.units       import inch
from reportlab.lib.colors      import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase         import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes   import letter, A4, landscape
from reportlab.platypus        import SimpleDocTemplate, Table, TableStyle,BaseDocTemplate, PageTemplate, Frame
from reportlab.lib             import colors
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus        import Paragraph, Table, PageBreak, Spacer, FrameBreak,Image
from reportlab.lib.units       import  cm,mm
from reportlab.lib.utils       import simpleSplit
from cgi                       import escape
from reportlab                 import platypus

from xlsxwriter.workbook import Workbook
import io
import os
import sys


def frac(n):
	i = int(n)
	f = round((n - int(n)), 4)
	return (i, f)


def frmt(hour): 
	hours, _min = frac(hour)
	minutes, _sec = frac(_min*60)
	seconds, _msec = frac(_sec*60)
	return "%s:%s:%s"%(hours, minutes, seconds)



class hr_resumen_provisiones(models.Model):
	_name = 'hr.resumen.provisiones'

	tareo_line_id = fields.Many2one('hr.tareo.line','Padre')
	
	tareo_id     = fields.Many2one('hr.tareo',u'Tareo')
	dni          = fields.Char(u'Dni')
	pagado       = fields.Float(u'Monto Pagado')
	acumulado    = fields.Float(u'Monto Acumulado')
	diferencia   = fields.Float(u'Diferencia')
	concept_type = fields.Char(u'Tipo')

	haber_provision_id   = fields.Many2one('account.account','cuenta haber de provision')
	
class hr_concepto_line(models.Model):
	_name = 'hr.concepto.line'

	tareo_line_id = fields.Many2one('hr.tareo.line','Padre')

	concepto_id   = fields.Many2one('hr.lista.conceptos','Concepto', required=True)
	payroll_group = fields.Selection([('1','Ingreso'),
									  ('2','Descuentos de la Base'),
									  ('3','Aportes Trabajador'),
									  ('4','Aportes Empleador'),
									  ('5','Descuentos del Neto'),
									  ('6','Neto'),], 'Grupo Planilla', related="concepto_id.payroll_group")
	monto         = fields.Float('Monto')


class hr_tareo_line(models.Model):
	_name = 'hr.tareo.line'

	state               = fields.Selection([('close','Cerrado'),('open','Abierto')],related='tareo_id.state')
	codigo_trabajador   = fields.Char(u'C??digo')
	basica              = fields.Float('B??sico', digits=(12,2))
	a_familiar          = fields.Float('A. Familiar', readonly=1, digits=(12,2))
	vacaciones          = fields.Float('Vacaciones', digits=(12,2))
	subsidiomaternidad  = fields.Float('Subsidio Maternidad', digits=(12,2))
	subsidioincapacidad = fields.Float('Subsidio Incapacidad', digits=(12,2))
	neto       			= fields.Float('Neto', digits=(12,2))
	tareo_id            = fields.Many2one('hr.tareo', 'Detalle')

	#PESTA??A EMPLEADO
	employee_id       = fields.Many2one('hr.employee', "Empleado")
	dni               = fields.Char('DNI', size=20) #aparece en vista form
	apellido_paterno  = fields.Char('Apellido Paterno', size=20, readonly=1) #aparece en vista form
	apellido_materno  = fields.Char('Apellido Materno', size=20, readonly=1) #aparece en vista form
	nombre            = fields.Char('Nombres', size=30, readonly=1) #aparece en vista form
	cargo             = fields.Many2one('hr.job','Cargo', size=50, readonly=1)
	afiliacion        = fields.Many2one('hr.table.membership','Afiliaci??n')
	zona              = fields.Char('Zona')
	tipo_comision     = fields.Boolean('Tipo Comisi??n')

	#PESTA??A INGRESOS
	basica_first                   = fields.Float('B??sico', digits=(12,2))
	a_familiar_first               = fields.Float('A. Familiar', readonly=1, digits=(12,2))
	dias_trabajador                = fields.Integer('Dias Trabajados')
	horas_ordinarias_trabajadas    = fields.Float('Horas Ordinarias Trabajadas', digits=(12,2))
	dias_vacaciones                = fields.Float(u'D??as Vacaciones', digits=(12,2))
	num_days_subs                  = fields.Integer(u'D??as subsidiados por Enfermedad')
	num_days_subs_mater            = fields.Integer(u'D??as subsidiados por Maternidad')
	num_days_not_subs              = fields.Integer(u'D??as no subsidiados o permisos')
	horas_extra_diurna             = fields.Float('Horas Extras Diurnas', digits=(12,2))
	horas_extra_nocturna           = fields.Float('Horas Extras Nocturna', digits=(12,2))
	horas_extra_descanso           = fields.Float('Horas Extras 100%', digits=(12,2))
	horas_extra_feriado_diur       = fields.Float('HE feriados diurnas', digits=(12,2))
	horas_extra_feriado_noct       = fields.Float('HE feriados nocturnas', digits=(12,2))
	horas_extra_feriado            = fields.Float('Horas Extras Feriado', digits=(12,2))
	horas_extra_descanso_diurnas   = fields.Float('HE Descanso diurnas', digits=(12,2))
	horas_extra_descanso_nocturnas = fields.Float('HE Descanso nocturnas', digits=(12,2))
	dias_feriados_trabajados	   = fields.Float(u'D??as feriados trabajados', digits=(12,2))
	total_ingresos 				   = fields.Float('Total', compute="compute_total_ingresos")
	vacaciones_inicio              = fields.Date(u'Vacaciones Inicio')
	vacaciones_retorno             = fields.Date(u'Vacaciones Retorno')
	dias_mes     				   = fields.Integer(u'D??as del mes')
	
	conceptos_ingresos_lines       = fields.One2many('hr.concepto.line', 'tareo_line_id','lineas', domain=[('payroll_group','=','1')])

	#PESTA??A DESCUENTOS DE LA BASE
	dias_suspension_perfecta        = fields.Integer('Faltas injustificadas o suspensiones')
	dias_suspension_imperfecta      = fields.Integer('Dias Suspensi??n Imperfecta')
	tardanza_horas                  = fields.Float('Tardanza Horas', digits=(12,4))
	total_descuentos_base 			= fields.Float('Total', compute="compute_total_descuentos_base")
	permisos 					    = fields.Integer(u'Permisos')
	descansos					    = fields.Integer(u'Descansos M??dicos')
	licencia_goce				    = fields.Integer(u'Licencia con goce de haberes')
	licencia_sin_goce			    = fields.Integer(u'Licencia sin goce de haberes')
	
	conceptos_descuentos_base_lines = fields.One2many('hr.concepto.line', 'tareo_line_id','lineas', domain=[('payroll_group','=','2')])
	
	#PESTA??A APORTES TRABAJADOR
	total_aportes_trabajador 		   = fields.Float('Total', compute="compute_total_aportes_trabajador")

	conceptos_aportes_trabajador_lines = fields.One2many('hr.concepto.line', 'tareo_line_id','lineas', domain=[('payroll_group','=','3')])

	#PESTA??A APORTES EMPLEADOR
	total_aportes_empleador 		  = fields.Float('Total', compute="compute_total_aportes_empleador")

	conceptos_aportes_empleador_lines = fields.One2many('hr.concepto.line', 'tareo_line_id','lineas', domain=[('payroll_group','=','4')])

	#PESTA??A DESCUENTOS NETO
	total_descuento_neto 		    = fields.Float('Total', compute="compute_total_descuento_neto")

	conceptos_descuentos_neto_lines = fields.One2many('hr.concepto.line', 'tareo_line_id','lineas', domain=[('payroll_group','=','5')])

	#PESTA??A NETO
	importe_vac			 = fields.Char(u'Importe de Vacaciones N?? OP')

	conceptos_neto_lines = fields.One2many('hr.concepto.line', 'tareo_line_id','lineas', domain=[('payroll_group','=','6')])

	#PESTA??A DETALLE DEL NETO
	conceptos_detalle_neto_lines = fields.One2many('hr.concepto.line', 'tareo_line_id','lineas', domain=[('payroll_group','=','7')])

	#PESTA??A PROVISIONES
	resumen_provisiones_lines = fields.One2many('hr.resumen.provisiones', 'tareo_line_id', 'lineas')









	total_remunerable              = fields.Float('Total Remun. Computable', digits=(12,2))
	tipo_suspension_perfecta       = fields.Char('Tipo Suspensi??n Perfecta')
	tipo_suspension_imperfecta     = fields.Char('Tipo Suspensi??n Imperfecta')

	# horas extras diurnas y nocturnas para feriados

	descuento_dominical = fields.Float('Descuento Dominical', digits=(12,2))

	total_horas_extras         = fields.Float('Total Horas Extras', digits=(12,2))
	total_horas_extras_horas   = fields.Float('Horas', digits=(12,2))
	total_horas_extras_minutos = fields.Float('Minutos', digits=(12,2))

	####
	vacaciones_trunca    = fields.Float('Vacaciones Trunca', digits=(12,2))
	monto_boni_grati_liq = fields.Float('bonificacion liq', digits=(12,2))	
	h_25                 = fields.Float('H_25%', digits=(12,2))
	h_35                 = fields.Float('H_35%', digits=(12,2))
	h_100                = fields.Float('H_100%', digits=(12,2))

	otros_ingreso   = fields.Float('Otros Ingreso', digits=(12,2))
	tardanzas       = fields.Float('Tardanzas', digits=(12,2))
	inasistencias   = fields.Float('Inasistencias', digits=(12,2))
	dscto_domi      = fields.Float('Dscto. Domi.', digits=(12,2))
	rmb             = fields.Float('RMB', digits=(12,2))
	onp             = fields.Float('ONP', digits=(12,2))
	afp_jub         = fields.Float('AFP_JUB', digits=(12,2))
	afp_psi         = fields.Float('AFP_PSI', digits=(12,2))
	afp_com         = fields.Float('AFP_COM', digits=(12,2))
	quinta_cat      = fields.Float('5TA CAT', digits=(12,2))
	total_descuento = fields.Float('Total Descuento', digits=(12,2))
	neto            = fields.Float('NETO', digits=(12,2))
	neto_sueldo     = fields.Float('NETO SUELDO', digits=(12,2))
	neto_vacaciones = fields.Float('NETO VACACIONES', digits=(12,2))
	adelantos       = fields.Float('Adelantos', digits=(12,2))
	prestamos       = fields.Float('Prestamos', digits=(12,2))
	otros_dct       = fields.Float('Otros Descuentos', digits=(12,2))
	saldo_sueldo    = fields.Float('Saldo a Pagar Sueldo', digits=(12,2))
	essalud         = fields.Float('ESSALUD', digits=(12,2))
	senaty          = fields.Float('SENATI', digits=(12,2))
	rma_pi          = fields.Float('RMA PI', digits=(12,2))
	dsc_afp         = fields.Float('DSC AFP', digits=(12,2))
	cts             = fields.Float('CTS', digits=(12,2))
	gratificacion   = fields.Float('Gratificaci??n', digits=(12,2))
	gratificacion_extraordinaria      = fields.Float('Gratificaci??n Trunca', digits=(12,2))
	gratificacion_extraordinaria_real = fields.Float('Gratificaci??n Extraordinaria', digits=(12,2))
	centro_costo                      = fields.Many2one('hr.distribucion.gastos','Centro C.')
	
	# aditional concepts from email
	sctr         = fields.Float('SCTR', digits=(12,2))
	eps          = fields.Float('EPS %', digits=(12,2))
	bonificacion = fields.Float('Bonificaci??n', digits=(12,2))
	
	comision     = fields.Float('Conmisi??n', digits=(12,2))
	boni_grati   = fields.Float('Bonificaci??n de Gratificaci??n', digits=(12,2))

	# main id
	
	cta_prestamo  = fields.Many2one('account.account','ctaprestamo')	
	total_boleta  = fields.Float('Total boleta', digits=(12,2))


	@api.one
	def compute_total_ingresos(self):
		res = 0
		for line in self.conceptos_ingresos_lines:
			res += line.monto
		self.total_ingresos = res

	@api.one
	def compute_total_descuentos_base(self):
		res = 0
		for line in self.conceptos_descuentos_base_lines:
			res += line.monto
		self.total_descuentos_base = res

	@api.one
	def compute_total_aportes_trabajador(self):
		res = 0
		for line in self.conceptos_aportes_trabajador_lines:
			res += line.monto
		self.total_aportes_trabajador = res

	@api.one
	def compute_total_aportes_empleador(self):
		res = 0
		for line in self.conceptos_aportes_empleador_lines:
			res += line.monto
		self.total_aportes_empleador = res

	@api.one
	def compute_total_descuento_neto(self):
		res = 0
		for line in self.conceptos_descuentos_neto_lines:
			res += line.monto
		self.total_descuento_neto = res

	@api.onchange('dni',
				  'nombre',
				  'apellido_paterno',
				  'apellido_materno',
				  'cargo',
				  'afiliacion',
				  'tipo_comision',
				  'zona',
				  'basica_first',
				  'a_familiar_first',
				  'dias_trabajador',
				  'horas_ordinarias_trabajadas',
				  'dias_vacaciones',
				  'num_days_subs',
				  'num_days_subs_mater',
				  'horas_extra_diurna',
				  'horas_extra_nocturna',
				  'horas_extra_descanso',
				  'horas_extra_feriado_diur',
				  'horas_extra_feriado_noct',
				  'horas_extra_feriado',
				  'horas_extra_descanso_diurnas',
				  'horas_extra_descanso_nocturnas',
				  'dias_suspension_perfecta',
				  'dias_suspension_imperfecta',
				  'tardanza_horas')
	def onchange_all(self):
		htl = self.env['hr.tareo.line'].search([('id','=',self.env.context['active_id'])])[0]
		hhe = self.env['hr.horas.extra'].search([])[0]
		for con_in in htl.conceptos_ingresos_lines:
			hpaf = self.env['hr.parameters'].search([('num_tipo','=','10001')])
			a_f = hpaf[0].monto if htl.employee_id.children_number>0 and len(hpaf) > 0 else 0
			if self.dias_vacaciones>0 or self.num_days_subs>0:
				afan_value = ((a_f/30.00) * htl.dias_trabajador)
			else:
				afan_value = a_f
			if con_in.concepto_id.code == '001': #basico
				con_in.monto = (htl.basica_first/30.00 * htl.dias_trabajador) if not htl.employee_id.is_practicant else 0
			if con_in.concepto_id.code == '002': #afamiliar
				con_in.monto = afan_value
				htl.a_familiar_first=afan_value

			if con_in.concepto_id.code == '004': #VACACIONES
				hp = self.env['hr.parameters'].search([('num_tipo','=',10001)])[0]
				res = (htl.basica_first/30.00*htl.dias_vacaciones)
				if htl.employee_id.children_number > 0:
					res += (hp.monto/30.00*htl.dias_vacaciones)
				if con_in.monto==0:
					con_in.monto = res
			if con_in.concepto_id.code == '012': #practicante
				con_in.monto = ((htl.basica_first+afan_value)/30.00 * htl.dias_trabajador) if htl.employee_id.is_practicant else 0
			if con_in.concepto_id.code == '013': #movilidad
				con_in.monto = htl.employee_id.movilidad
			if con_in.concepto_id.code == '014': #INDEMNIZACION
				hl = self.env['hr.liquidaciones.lines.vac'].search([('liquidacion_id.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
				res = 0
				for line in hl:
					res += line.compensation
				con_in.monto = res
			if con_in.concepto_id.code == '017': #CTS
				hctl = self.env['hr.cts.line'].search([('cts.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
				res = 0
				for line in hctl:
					res += line.cts_a_pagar
				con_in.monto = res
			if con_in.concepto_id.code == '018': #GRATIFICACIONES
				hrl = self.env['hr.reward.line'].search([('reward.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
				res = 0
				for line in hrl:
					res += line.total_reward
				con_in.monto = res
			
			if con_in.concepto_id.code == '020': #BONO DE GRATIFICACION
				# hl = self.env['hr.liquidaciones.lines.grat'].search([('liquidacion_id.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
				# res = 0
				# for line in hl:
				# 	res += line.bonus
				hrl = self.env['hr.reward.line'].search([('reward.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
				res = 0
				for line in hrl:
					res += line.plus_9
				con_in.monto = res

		for con_desc_b in htl.conceptos_descuentos_base_lines:
			if con_desc_b.concepto_id.code == '024': #tardanzas
				con_desc_b.monto = (((htl.basica_first+afan_value)/30.00)/8.00)*htl.tardanza_horas
			if con_desc_b.concepto_id.code == '025': #inasistencias
				con_desc_b.monto = (htl.basica_first/30.00)*htl.dias_suspension_perfecta
			if con_desc_b.concepto_id.code == '102': #Licencia sin gose de haber
				con_desc_b.monto = (htl.basica_first/30.00)*htl.licencia_sin_goce

		for con_ap_trab in htl.conceptos_aportes_trabajador_lines:
	 		if con_ap_trab.concepto_id.code == '028': #ONP
				if htl.afiliacion.code:
					raw_base = 0
					if htl.afiliacion.code == 'ONP':
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.onp:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.onp:
									raw_base -= item.monto
					
						hml = self.env['hr.membership.line'].search([('membership','=',htl.afiliacion.id),('periodo','=',htl.tareo_id.periodo.id)])
						if len(hml) > 0: #PORCENTAJE DE ONP
							raw_base *= hml[0].tasa_pensiones/100.00

						con_ap_trab.monto = raw_base
					else:
						con_ap_trab.monto = 0
				else:
					con_ap_trab.monto = 0

			if con_ap_trab.concepto_id.code in ['029','030','031','106','107','108','109','110','111','112','113','114']: #AFP (JUB, PSI, COM)
				if htl.afiliacion.code:
					raw_base_j = 0
					raw_base_p = 0
					raw_base_c = 0
					if htl.afiliacion.code != 'ONP':
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_fon_pen:
									raw_base_j += item.monto
								if hcrl.afp_pri_se:
									raw_base_p += item.monto
								if htl.employee_id.c_mixta:
									if hcrl.afp_co_mix:
										raw_base_c += item.monto
								else:
									if hcrl.afp_co_va:
										raw_base_c += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:

								hcrl = hcrl[0]
								if hcrl.afp_fon_pen:
									raw_base_j -= item.monto
								if hcrl.afp_pri_se:
									raw_base_p -= item.monto
								if htl.employee_id.c_mixta:
									if hcrl.afp_co_mix:
										raw_base_c -= item.monto
								else:
									if hcrl.afp_co_va:
										raw_base_c -= item.monto

						hml = self.env['hr.membership.line'].search([('membership','=',htl.afiliacion.id),('periodo','=',htl.tareo_id.periodo.id)])

						if len(hml) > 0: #PORCENTAJE DE AFP (JUB, PSI, COM)
							if htl.afiliacion.code=='AFP PRIMA':
								if con_ap_trab.concepto_id.code == '029':
									raw_base_j *= hml[0].tasa_pensiones/100.00
								if con_ap_trab.concepto_id.code == '030':
									if raw_base_p > hml.rma:
										raw_base_p = hml.rma * hml[0].prima/100.00
									else:
										raw_base_p *= hml[0].prima/100.00
								if con_ap_trab.concepto_id.code == '031':
									if htl.employee_id.c_mixta:
										raw_base_c *= hml[0].c_mixta/100.00
									else:
										raw_base_c *= hml[0].c_variable/100.00

							if htl.afiliacion.code=='AFP HABITAT':
								if con_ap_trab.concepto_id.code == '106':
									raw_base_j *= hml[0].tasa_pensiones/100.00
								if con_ap_trab.concepto_id.code == '107':
									if raw_base_p > hml.rma:
										raw_base_p = hml.rma * hml[0].prima/100.00
									else:
										raw_base_p *= hml[0].prima/100.00
								if con_ap_trab.concepto_id.code == '108':
									if htl.employee_id.c_mixta:
										raw_base_c *= hml[0].c_mixta/100.00
									else:
										raw_base_c *= hml[0].c_variable/100.00

							if htl.afiliacion.code=='AFP INTEGRA':
								if con_ap_trab.concepto_id.code == '109':
									raw_base_j *= hml[0].tasa_pensiones/100.00
								if con_ap_trab.concepto_id.code == '110':
									if raw_base_p > hml.rma:
										raw_base_p = hml.rma * hml[0].prima/100.00
									else:
										raw_base_p *= hml[0].prima/100.00
								if con_ap_trab.concepto_id.code == '111':
									if htl.employee_id.c_mixta:
										raw_base_c *= hml[0].c_mixta/100.00
									else:
										raw_base_c *= hml[0].c_variable/100.00

							if htl.afiliacion.code=='AFP PROFUTURO':
								if con_ap_trab.concepto_id.code == '112':
									raw_base_j *= hml[0].tasa_pensiones/100.00
								if con_ap_trab.concepto_id.code == '113':
									if raw_base_p > hml.rma:
										raw_base_p = hml.rma * hml[0].prima/100.00
									else:
										raw_base_p *= hml[0].prima/100.00
								if con_ap_trab.concepto_id.code == '114':
									if htl.employee_id.c_mixta:
										raw_base_c *= hml[0].c_mixta/100.00
									else:
										raw_base_c *= hml[0].c_variable/100.00



						if htl.afiliacion.code=='AFP PRIMA':				
							if con_ap_trab.concepto_id.code == '029':
								con_ap_trab.monto = raw_base_j
							if con_ap_trab.concepto_id.code == '030':
								con_ap_trab.monto = raw_base_p
							if con_ap_trab.concepto_id.code == '031':
								con_ap_trab.monto = raw_base_c
						if htl.afiliacion.code=='AFP HABITAT':				
							if con_ap_trab.concepto_id.code == '106':
								con_ap_trab.monto = raw_base_j
							if con_ap_trab.concepto_id.code == '107':
								con_ap_trab.monto = raw_base_p
							if con_ap_trab.concepto_id.code == '108':
								con_ap_trab.monto = raw_base_c

						if htl.afiliacion.code=='AFP INTEGRA':				
							if con_ap_trab.concepto_id.code == '109':
								con_ap_trab.monto = raw_base_j
							if con_ap_trab.concepto_id.code == '110':
								con_ap_trab.monto = raw_base_p
							if con_ap_trab.concepto_id.code == '111':
								con_ap_trab.monto = raw_base_c

						if htl.afiliacion.code=='AFP PROFUTURO':				
							if con_ap_trab.concepto_id.code == '112':
								con_ap_trab.monto = raw_base_j
							if con_ap_trab.concepto_id.code == '113':
								con_ap_trab.monto = raw_base_p
							if con_ap_trab.concepto_id.code == '114':
								con_ap_trab.monto = raw_base_c								
					else:
						if htl.afiliacion.code=='AFP PRIMA':
							if con_ap_trab.concepto_id.code == '029':
								con_ap_trab.monto = 0
							if con_ap_trab.concepto_id.code == '030':
								con_ap_trab.monto = 0
							if con_ap_trab.concepto_id.code == '031':
								con_ap_trab.monto = 0
						
						if htl.afiliacion.code=='AFP HABITAT':
							if con_ap_trab.concepto_id.code == '106':
								con_ap_trab.monto = 0
							if con_ap_trab.concepto_id.code == '107':
								con_ap_trab.monto = 0
							if con_ap_trab.concepto_id.code == '108':
								con_ap_trab.monto = 0

						if htl.afiliacion.code=='AFP INTEGRA':
							if con_ap_trab.concepto_id.code == '109':
								con_ap_trab.monto = 0
							if con_ap_trab.concepto_id.code == '110':
								con_ap_trab.monto = 0
							if con_ap_trab.concepto_id.code == '111':
								con_ap_trab.monto = 0

						if htl.afiliacion.code=='AFP PROFUTURO':
							if con_ap_trab.concepto_id.code == '112':
								con_ap_trab.monto = 0
							if con_ap_trab.concepto_id.code == '113':
								con_ap_trab.monto = 0
							if con_ap_trab.concepto_id.code == '114':
								con_ap_trab.monto = 0


				else:
					# PRIMA
					if con_ap_trab.concepto_id.code == '029':
						con_ap_trab.monto = 0
					if con_ap_trab.concepto_id.code == '030':
						con_ap_trab.monto = 0
					if con_ap_trab.concepto_id.code == '031':
						con_ap_trab.monto = 0

					#HBITAT
					if con_ap_trab.concepto_id.code == '106':
						con_ap_trab.monto = 0
					if con_ap_trab.concepto_id.code == '107':
						con_ap_trab.monto = 0
					if con_ap_trab.concepto_id.code == '108':
						con_ap_trab.monto = 0

					#INTEGRA

					if con_ap_trab.concepto_id.code == '109':
						con_ap_trab.monto = 0
					if con_ap_trab.concepto_id.code == '110':
						con_ap_trab.monto = 0
					if con_ap_trab.concepto_id.code == '111':
						con_ap_trab.monto = 0

					#PROFUTURO
					if con_ap_trab.concepto_id.code == '112':
						con_ap_trab.monto = 0
					if con_ap_trab.concepto_id.code == '113':
						con_ap_trab.monto = 0
					if con_ap_trab.concepto_id.code == '114':
						con_ap_trab.monto = 0

			if con_ap_trab.concepto_id.code == '033':
				res = 0
				hfcdl = self.env['hr.five.category.devolucion.lines'].search([('devolucion_id.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
				if False: #len(hfcdl):
					hfcdl = hfcdl[0]
					if hfcdl.monto_devolver >= 0:
						res = hfcdl.monto_devolver
				else:
					hfcl = self.env['hr.five.category.lines'].search([('five_category_id.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
					for line in hfcl:
						res += line.monto
				con_ap_trab.monto = res

			if con_ap_trab.concepto_id.code == '034': #EsSalud Vida
				if htl.employee_id.essalud_vida:
					con_ap_trab.monto = self.env['hr.parameters'].search([('num_tipo','=',2)])[0].monto/100.00

			if con_ap_trab.concepto_id.code == '036': #Fondo Jubilaci??n
				if htl.employee_id.fondo_jub:
					raw_base = 0
					for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
						hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
						if len(hcrl) > 0:

							hcrl = hcrl[0]
							if hcrl.jubilacion:
								raw_base += item.monto
					resta = 0
					for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
						hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
						if len(hcrl) > 0:
							hcrl = hcrl[0]
							if hcrl.jubilacion:
								resta = resta +item.monto
								raw_base -= item.monto
					raw_base *= self.env['hr.parameters'].search([('num_tipo','=',3)])[0].monto/100.00
					# si el campo tiene un valor que no sea cero lo va a respetar
					# puesto para el empleado Merma 2018-01-19
					con_ap_trab.monto = raw_base

			if con_ap_trab.concepto_id.code == '055' and htl.afiliacion.code=='AFP PRIMA': #AFP 2%
				if htl.employee_id.afp_2p:
					if htl.afiliacion.mem_type == 'private':
						raw_base = 0
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base -= item.monto
						raw_base *= self.env['hr.parameters'].search([('num_tipo','=',8)])[0].monto/100.00
						con_ap_trab.monto = raw_base
						
						
						
			if con_ap_trab.concepto_id.code == '115' and htl.afiliacion.code=='AFP HABITAT': #AFP 2% HABITAT
				if htl.employee_id.afp_2p:
					if htl.afiliacion.mem_type == 'private':
						raw_base = 0
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base -= item.monto
						
						raw_base *= self.env['hr.parameters'].search([('num_tipo','=',8)])[0].monto/100.00
						con_ap_trab.monto = raw_base

			if con_ap_trab.concepto_id.code == '116' and htl.afiliacion.code=='AFP INTEGRA': #AFP 2% INTEGRA
				if htl.employee_id.afp_2p:
					if htl.afiliacion.mem_type == 'private':
						raw_base = 0
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base -= item.monto
						raw_base *= self.env['hr.parameters'].search([('num_tipo','=',8)])[0].monto/100.00
						con_ap_trab.monto = raw_base

			if con_ap_trab.concepto_id.code == '117' and htl.afiliacion.code=='AFP PROFUTURO': #AFP 2% PROFUTRO
				if htl.employee_id.afp_2p:
					if htl.afiliacion.mem_type == 'private':
						raw_base = 0
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base -= item.monto
						raw_base *= self.env['hr.parameters'].search([('num_tipo','=',8)])[0].monto/100.00
						con_ap_trab.monto = raw_base

		for con_ap_empl in htl.conceptos_aportes_empleador_lines:
			if con_ap_empl.concepto_id.code == '038': #EsSalud

				if not htl.employee_id.is_practicant:
					raw_base = 0
					cond 	 = 0
					if (htl.dias_trabajador == htl.dias_suspension_perfecta) and (htl.dias_vacaciones==0):
						con_ap_empl.monto = 0
					else:
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.essalud:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.essalud:
									raw_base -= item.monto

						if htl.employee_id.use_eps:
							raw_base *= self.env['hr.parameters'].search([('num_tipo','=',9)])[0].monto/100.00
							cond = self.env['hr.parameters'].search([('num_tipo','=',10000)])[0].monto * self.env['hr.parameters'].search([('num_tipo','=',9)])[0].monto/100.00
						else:
							raw_base *= self.env['hr.parameters'].search([('num_tipo','=',4)])[0].monto/100.00
							cond = self.env['hr.parameters'].search([('num_tipo','=',10000)])[0].monto * self.env['hr.parameters'].search([('num_tipo','=',4)])[0].monto/100.00
						
						con_ap_empl.monto = max(cond, raw_base)
				else:
					con_ap_empl.monto = 0
			
			

			if con_ap_empl.concepto_id.code == '041': #SENATI
				if self.env['res.company'].search([])[0].senati:
					raw_base = 0
					for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
						hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
						if len(hcrl) > 0:
							hcrl = hcrl[0]
							if hcrl.senati:
								raw_base += item.monto
					for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
						hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
						if len(hcrl) > 0:
							hcrl = hcrl[0]
							if hcrl.senati:
								raw_base -= item.monto
					raw_base *= self.env['hr.parameters'].search([('num_tipo','=',7)])[0].monto/100.00
					con_ap_empl.monto = raw_base

			if con_ap_empl.concepto_id.code == '044' and htl.afiliacion.code=='AFP PRIMA': #AFP 2%
				if htl.employee_id.afp_2p:
					if htl.afiliacion.mem_type == 'private':
						raw_base = 0
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base -= item.monto
						raw_base *= self.env['hr.parameters'].search([('num_tipo','=',8)])[0].monto/100.00
						con_ap_empl.monto = raw_base
						
						
						
			if con_ap_empl.concepto_id.code == '118' and htl.afiliacion.code=='AFP HABITAT': #AFP 2% HABITAT
				if htl.employee_id.afp_2p:
					if htl.afiliacion.mem_type == 'private':
						raw_base = 0
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base -= item.monto
						raw_base *= self.env['hr.parameters'].search([('num_tipo','=',8)])[0].monto/100.00
						con_ap_empl.monto = raw_base

			if con_ap_empl.concepto_id.code == '119' and htl.afiliacion.code=='AFP INTEGRA': #AFP 2% INTEGRA
				if htl.employee_id.afp_2p:
					if htl.afiliacion.mem_type == 'private':
						raw_base = 0
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base -= item.monto
						raw_base *= self.env['hr.parameters'].search([('num_tipo','=',8)])[0].monto/100.00
						con_ap_empl.monto = raw_base

			if con_ap_empl.concepto_id.code == '120' and htl.afiliacion.code=='AFP PROFUTURO': #AFP 2% PROFUTURO
				if htl.employee_id.afp_2p:
					if htl.afiliacion.mem_type == 'private':
						raw_base = 0
						for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base += item.monto
						for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
							hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
							if len(hcrl) > 0:
								hcrl = hcrl[0]
								if hcrl.afp_2p:
									raw_base -= item.monto
						raw_base *= self.env['hr.parameters'].search([('num_tipo','=',8)])[0].monto/100.00
						con_ap_empl.monto = raw_base

		for con_desc_n in htl.conceptos_descuentos_neto_lines:
			if con_desc_n.concepto_id.code == '045': #ADELANTOS
				t_adel   = self.env['hr.table.adelanto'].search([('is_basket','=',False),('reward_dicount_type','=',False)])
				ids_adel = []
				for ade in t_adel:
					ids_adel.append(ade.id)
				ha  = self.env['hr.adelanto'].search([('fecha','>=',htl.tareo_id.periodo.date_start),('fecha','<=',htl.tareo_id.periodo.date_stop),('employee','=',htl.employee_id.id),('adelanto_id','in',ids_adel)])
				res = 0
				for item in ha:
					res += item.monto
				con_desc_n.monto = res

			if con_desc_n.concepto_id.code == '080': #ADELANTOS CANASTA
				t_adel   = self.env['hr.table.adelanto'].search([('is_basket','=',True)])
				ids_adel = []
				for ade in t_adel:
					ids_adel.append(ade.id)
				ha  = self.env['hr.adelanto'].search([('fecha','>=',htl.tareo_id.periodo.date_start),('fecha','<=',htl.tareo_id.periodo.date_stop),('employee','=',htl.employee_id.id),('adelanto_id','in',ids_adel)])
				res = 0
				for item in ha:
					res += item.monto
				con_desc_n.monto = res

			if con_desc_n.concepto_id.code == '046': #PRESTAMOS
				ha = self.env['hr.prestamo.lines'].search([('fecha_pago','>=',htl.tareo_id.periodo.date_start),('fecha_pago','<=',htl.tareo_id.periodo.date_stop),('prestamo_id.employee_id','=',htl.employee_id.id),('validacion','=','2')])
				res = 0
				for item in ha:
					res += item.monto
				con_desc_n.monto = res

			if con_desc_n.concepto_id.code == '072': #ADELANTO GRATIFICACIONES
				hrl = self.env['hr.reward.line'].search([('reward.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
				res = 0
				if len(hrl):					
					for item in hrl:
						res += (item.total+item.adelanto)
				else:
					hllg = self.env['hr.liquidaciones.lines.grat'].search([('liquidacion_id.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
					for item in hllg:
						res += item.adelanto
				con_desc_n.monto = res

		for con_neto in htl.conceptos_neto_lines:
			if con_neto.concepto_id.code == '047': #RMB
				raw_base = 0
				for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
					hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
					if len(hcrl) > 0:
						hcrl = hcrl[0]
						if hcrl.rmb:
							raw_base += item.monto
				for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
					hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
					if len(hcrl) > 0:
						hcrl = hcrl[0]
						if hcrl.rmb:
							raw_base -= item.monto
				con_neto.monto = raw_base

			if con_neto.concepto_id.code == '048': #Total descuentos
				otrin = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','072')])
				con_neto.monto = htl.total_aportes_trabajador + htl.total_descuento_neto - (otrin[0].monto if len(otrin) else 0)

			if con_neto.concepto_id.code == '049': #NETO
				rmb = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.env.context['active_id']),('concepto_id.code','=','047')])
				tot_desc = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.env.context['active_id']),('concepto_id.code','=','048')])
				res = 0
				if len(rmb) > 0:
					rmb = rmb[0]
					res += rmb.monto
				if len(tot_desc) > 0:
					tot_desc = tot_desc[0]
					res -= tot_desc.monto
				con_neto.monto = res

			if con_neto.concepto_id.code == '054': #APORTES EMPLEADO
				con_neto.monto = htl.total_aportes_empleador
		for con_det_neto in htl.conceptos_detalle_neto_lines:
			if con_det_neto.concepto_id.code in ['050','051']: #NETO (SUELDOS, VACACIONES)
				raw_base = 0
				for item in htl.conceptos_ingresos_lines: #SUMA DE INGRESOS
					hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
					if len(hcrl) > 0:
						hcrl = hcrl[0]
						if hcrl.neto_vac:
							raw_base += item.monto
				for item in htl.conceptos_descuentos_base_lines: #RESTA DE DESCUENTOS
					hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.id','=',item.concepto_id.id)])
					if len(hcrl) > 0:
						hcrl = hcrl[0]
						if hcrl.neto_vac:
							raw_base -= item.monto
				rmb      = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.env.context['active_id']),('concepto_id.code','=','047')])
				tot_desc = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.env.context['active_id']),('concepto_id.code','=','048')])
				net_c = 0
				if len(rmb) > 0:
					rmb = rmb[0]
					net_c += rmb.monto
				if len(tot_desc) > 0:
					tot_desc = tot_desc[0]
					net_c -= tot_desc.monto
				vf = raw_base/rmb[0].monto if len(rmb) > 0 and rmb[0].monto != 0 else 0
				sf = 1-vf

				if con_det_neto.concepto_id.code == '050': #Neto Sueldos
					con_det_neto.monto = (net_c*sf)
				if con_det_neto.concepto_id.code == '051': #Neto Vacaciones
					con_det_neto.monto = (net_c*vf)

			if con_det_neto.concepto_id.code == '053': #OTROS INGRESOS
				rmb = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.env.context['active_id']),('concepto_id.code','=','047')])
				otrin = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','072')])
				con_det_neto.monto = htl.total_ingresos - (rmb[0].monto if len(rmb) > 0 else 0) - htl.total_descuentos_base - (otrin[0].monto if len(otrin) else 0)
		# traemos los montos de las liquidaciones para todos los conceptos que le corresponden
		# estoy poniendo que si el concepto tiene valor cero traiga el valor de la liquidaci??n 
		# si este no es cero pues lo va a preservar 2018-01-19
		for con_liquida in self.env['hr.concepto.empleado.relacion'].search([('period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)]): #CONCEPTOS QUE TIENEN EL CHECK LIQUIDADO
			for con in self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',con_liquida.concepto_id.code)]):
				if con.monto==0:
					con.monto = con_liquida.monto

		#VACACIONES INICIO Y RETORNO
		vrl = self.env['vacation.role.line'].search([('parent.period_id','=',htl.tareo_id.periodo.id),('employee_id','=',htl.employee_id.id)])
		ivac = False
		rvac = False
		if len(vrl):
			pvl = self.env['partial.vacation.line'].search([('parent','=',vrl.id)])
			htl.vacaciones_inicio  = pvl[0].init_date if len(pvl) else False
			htl.vacaciones_retorno = pvl[0].end_date if len(pvl) else False

	@api.multi
	def actualizar_resumen(self):
		htl = self.env['hr.tareo.line'].search([('id','=',self.env.context['active_id'])])[0]
		hhe = self.env['hr.horas.extra'].search([])[0]
		# hpt = self.env['hr.parametros.tareo'].search([])[0]


		# PARTE UTILIZADA PARA EL ACUMULADO DE PROVISIONES
		for line in htl.resumen_provisiones_lines:
			line.unlink()
		tareo_mes = htl.tareo_id.periodo.code.split("/")[0]
		# ENERO
		if tareo_mes == '01':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=2)
			ff = fi + relativedelta.relativedelta(months=1)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_cts_con,
					'acumulado'             : monto_cts,
					'diferencia'            : monto_cts_con - monto_cts,
					'concept_type'          : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			monto_grat_con = 0
			monto_bono_con = 0
			grati_account_provision = False
			bono_account_provision = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','019')])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','020')])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : 0,
					'diferencia'   : monto_grat_con - 0,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : 0,
					'diferencia'   : monto_bono_con - 0,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False
			vac_concepto_id = False		
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# FEBRERO
		if tareo_mes == '02':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=3)
			ff = fi + relativedelta.relativedelta(months=2)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_cts_con,
					'acumulado'             : monto_cts,
					'diferencia'            : monto_cts_con - monto_cts,
					'concept_type'          : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=1)
			ff = fi + relativedelta.relativedelta(months=0)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id'           : htl.id,
					'tareo_id'                : htl.tareo_id.id,
					'dni'                     : htl.employee_id.identification_id,
					'pagado'                  : monto_grat_con,
					'acumulado'               : monto_grat,
					'diferencia'              : monto_grat_con - monto_grat,
					'concept_type'            : 'grati',
					'haber_provision_id': grati_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id'          : htl.id,
					'tareo_id'               : htl.tareo_id.id,
					'dni'                    : htl.employee_id.identification_id,
					'pagado'                 : monto_bono_con,
					'acumulado'              : monto_bono,
					'diferencia'             : monto_bono_con - monto_bono,
					'concept_type'           : 'bono',
					'haber_provision_id': bono_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False
			vac_concepto_id = False		
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# MARZO
		if tareo_mes == '03':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=4)
			ff = fi + relativedelta.relativedelta(months=3)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=2)
			ff = fi + relativedelta.relativedelta(months=1)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False
			vac_concepto_id = False		
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# ABRIL
		if tareo_mes == '04':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=5)
			ff = fi + relativedelta.relativedelta(months=5)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=3)
			ff = fi + relativedelta.relativedelta(months=2)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False	
			vac_concepto_id = False		
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# MAYO
		if tareo_mes == '05':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=5)
			ff = fi + relativedelta.relativedelta(months=5)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=4)
			ff = fi + relativedelta.relativedelta(months=3)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False			
			vac_concepto_id = False
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# JUNIO
		if tareo_mes == '06':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=1)
			ff = fi + relativedelta.relativedelta(months=0)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=5)
			ff = fi + relativedelta.relativedelta(months=4)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False
			vac_concepto_id = False			
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# JULIO
		if tareo_mes == '07':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=2)
			ff = fi + relativedelta.relativedelta(months=1)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=6)
			ff = fi + relativedelta.relativedelta(months=5)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False
			vac_concepto_id = False
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vac_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# AGOSTO
		if tareo_mes == '08':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=3)
			ff = fi + relativedelta.relativedelta(months=2)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=1)
			ff = fi + relativedelta.relativedelta(months=0)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False			
			vac_concepto_id = False
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# SETIEMBRE
		if tareo_mes == '09':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=4)
			ff = fi + relativedelta.relativedelta(months=3)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=2)
			ff = fi + relativedelta.relativedelta(months=1)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False			
			vac_concepto_id = False
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vaca_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# OCTUBRE
		if tareo_mes == '10':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=5)
			ff = fi + relativedelta.relativedelta(months=4)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=3)
			ff = fi + relativedelta.relativedelta(months=2)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False			
			vac_concepto_id = False
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# NOVIEMBRE
		if tareo_mes == '11':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=6)
			ff = fi + relativedelta.relativedelta(months=5)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provision_id.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=4)
			ff = fi + relativedelta.relativedelta(months=3)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_concepto_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False			
			vac_concepto_id = False
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		# DICIEMBRE
		if tareo_mes == '12':
			#CTS
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=1)
			ff = fi + relativedelta.relativedelta(months=0)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_cts = 0
			monto_cts_con = 0
			cts_account_provision = False
			cts_concepto_id = False
			hplc = self.env['hr.provisiones.lines.cts'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplc:
				monto_cts += line.provision
				cts_account_provision = line.provision_id.cts_account_haber_id.id
				cts_concepto_id = line.provisiones.cts_concepto_id.code
			hcl  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',cts_concepto_id)])
			if len(hcl) > 0:
				hcl = hcl[0]
				monto_cts_con = hcl.monto
			if cts_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_cts_con,
					'acumulado'    : monto_cts,
					'diferencia'   : monto_cts_con - monto_cts,
					'concept_type' : 'cts',
					'haber_provision_id': cts_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
				
			#GRATIFICACIONES Y BONIFICACIONES
			fi = datetime.strptime(htl.tareo_id.periodo.date_start, "%Y-%m-%d")
			fi -= relativedelta.relativedelta(months=5)
			ff = fi + relativedelta.relativedelta(months=4)
			ff += relativedelta.relativedelta(days=monthrange(ff.year,ff.month)[1]-1)
			monto_grat = 0
			monto_grat_con = 0
			grati_account_provision = False
			grat_concepto_id = False
			monto_bono = 0
			monto_bono_con = 0
			bono_account_provision = False
			bono_account_haber_id = False
			hplg = self.env['hr.provisiones.lines.grat'].search([('provision_id.period_id.date_start','>=',fi),('provision_id.period_id.date_stop','<=',ff),('employee_id','=',htl.employee_id.id)])
			for line in hplg:
				monto_grat += line.provision
				monto_bono += line.bonus
				grati_account_provision = line.provision_id.grati_account_haber_id.id
				bono_account_provision = line.provision_id.bono_account_haber_id.id
				grat_concepto_id = line.provision_id.grat_concepto_id.code
				bono_concepto_id = line.provision_id.bono_concepto_id.code
			hclg = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',grat_concepto_id)])
			hclb = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',bono_concepto_id)])
			if len(hclg) > 0:
				hclg = hclg[0]
				monto_grat_con = hclg.monto
			if len(hclb) > 0:
				hclb = hclb[0]
				monto_bono_con = hclb.monto
			if grati_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_grat_con,
					'acumulado'    : monto_grat,
					'diferencia'   : monto_grat_con - monto_grat,
					'concept_type' : 'grati',
					'haber_provision_id': grati_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)
			if bono_account_provision:
				res_vals = {
					'tareo_line_id': htl.id,
					'tareo_id'     : htl.tareo_id.id,
					'dni'          : htl.employee_id.identification_id,
					'pagado'       : monto_bono_con,
					'acumulado'    : monto_bono,
					'diferencia'   : monto_bono_con - monto_bono,
					'concept_type' : 'bono',
					'haber_provision_id': bono_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

			#VACACIONES
			monto_vac = 0
			monto_vac_con = 0
			vac_account_provision = False			
			vac_concepto_id = False
			hplv = self.env['hr.provisiones.lines.vac'].search([('mes_vacacion_id.name','=',htl.tareo_id.periodo.code),('employee_id','=',htl.employee_id.id)])
			for line in hplv:
				monto_vac += line.provision
				vac_account_provision = line.provision_id.vaca_account_haber_id.id
				vac_concepto_id = line.provision_id.vaca_concepto_id.code
			hclv = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=',vac_concepto_id)])
			if len(hclv) > 0:
				hclv = hclv[0]
				monto_vac_con = hclv.monto
			if vac_account_provision:
				res_vals = {
					'tareo_line_id'         : htl.id,
					'tareo_id'              : htl.tareo_id.id,
					'dni'                   : htl.employee_id.identification_id,
					'pagado'                : monto_vac_con,
					'acumulado'             : monto_vac,
					'diferencia'            : monto_vac_con - monto_vac,
					'concept_type'          : 'vaca',
					'haber_provision_id': vac_account_provision,
				}
				self.env['hr.resumen.provisiones'].create(res_vals)

		return {
			'type': 'ir.actions.act_window',
			'name': "Detalle Tareo",
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.tareo.line',
			'res_id': htl.id,
			'target': 'new',
		}

	@api.multi
	def open_wizard(self):
		return {
			'type': 'ir.actions.act_window',
			'name': "Detalle Tareo",
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.tareo.line',
			'res_id': self.id,
			'target': 'new',
			'context': {'default_dias_trabajador': 30},
		}

	@api.model
	def create(self, vals):
		t = super(hr_tareo_line, self).create(vals)

		hlc = self.env['hr.lista.conceptos'].search([])
		for concepto in hlc:
			hcl = self.env['hr.concepto.line'].create({
				'concepto_id'  : concepto.id,
				'monto'        : 0,
				'tareo_line_id': t.id,
			})

		return t

	@api.one
	def write(self,vals):
		htl = self.env['hr.tareo.line'].search([('id','=',self.id)])[0]
		t = super(hr_tareo_line,self).write(vals)
		self.refresh()
		# self.with_context({'active_id':self.id}).onchange_all()

		if 'avoid_recursion' in vals:
			pass
		else:
			basica   = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.id),('concepto_id.code','=','001')])
			asig_fam = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.id),('concepto_id.code','=','002')])
			vacacion = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.id),('concepto_id.code','=','004')])
			subs_mat = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.id),('concepto_id.code','=','022')])
			subs_inc = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.id),('concepto_id.code','=','023')])
			rmb      = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.id),('concepto_id.code','=','047')])
			tot_desc = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.id),('concepto_id.code','=','048')])
			net_c = sum([lnd.monto for lnd in htl.conceptos_detalle_neto_lines])
			# if len(rmb) > 0:
			# 	rmb = rmb[0]
			# 	net_c += rmb.monto
			# if len(tot_desc) > 0:
			# 	tot_desc = tot_desc[0]
			# 	net_c -= tot_desc.monto
			self.write({
				'avoid_recursion'    : 1,
				'basica'             : basica[0].monto if len(basica) > 0 else 0,
				'a_familiar'         : asig_fam[0].monto if len(asig_fam) > 0 else 0,
				'vacaciones'         : vacacion[0].monto if len(vacacion) > 0 else 0,
				'subsidiomaternidad' : subs_mat[0].monto if len(subs_mat) > 0 else 0,
				'subsidioincapacidad': subs_inc[0].monto if len(subs_inc) > 0 else 0,
				'neto'               : net_c,
			})

		# if 'nohacernada' in vals:
		# 	pass
		# else:

		# 	tmp__1 = (self.basica_first /30) * self.dias_trabajador
		# 	self.write({'nohacernada':1,'basica': tmp__1})
			
		# 	tmp__2 = (self.a_familiar)
		# 	# if self.vacaciones>0:
		# 		# tmp__2=0
				

		# 	self.write({'nohacernada':1,'a_familiar': tmp__2})
		# 	self.refresh()

		# 	tmp__3 =  ((self.total_remunerable/30) /8 )* self.horas_extra_diurna* self.env['hr.parameters'].search([])[0].he_diurnas
		# 	self.write({'nohacernada':1,'h_25': tmp__3})

		# 	tmp__4 =  ((self.total_remunerable/30) /8 )* self.horas_extra_nocturna* self.env['hr.parameters'].search([])[0].he_nocturnas
		# 	self.write({'nohacernada':1,'h_35': tmp__4})

		# 	tmp__5 =  ((self.total_remunerable/30) /8 )* self.horas_extra_feriado* self.env['hr.parameters'].search([])[0].he_feriados
		# 	tmp__11 =  ((self.total_remunerable/30) /8 )* self.horas_extra_descanso* self.env['hr.parameters'].search([])[0].he_descansos
		# 	tmp__111 =  ((self.total_remunerable/30) /8 )* self.env['hr.parameters'].search([])[0].he_diurnas* self.env['hr.parameters'].search([])[0].he_descansos_diurno * self.horas_extra_descanso_diurnas
		# 	tmp__112 =  ((self.total_remunerable/30) /8 )* self.env['hr.parameters'].search([])[0].he_nocturnas* self.env['hr.parameters'].search([])[0].he_descansos_nocturno * self.horas_extra_descanso_nocturnas
		# 	self.write({'nohacernada':1,'h_100': tmp__5})
		# 	apara=str(self.env['hr.parameters'].search([])[0].he_fer_noct).split('.')
		# 	montodia= (self.total_remunerable/30) /8 
		# 	montodiaso=montodia*int(apara[0])
		# 	montodiaso=montodiaso+montodiaso*(float(apara[1])/100)
		# 	tmp__5+=   self.horas_extra_feriado_noct* montodiaso

		# 	apara=str(self.env['hr.parameters'].search([])[0].he_fer_diur).split('.')
		# 	montodia= (self.total_remunerable/30) /8 
		# 	montodiaso=montodia*int(apara[0])
		# 	montodiaso=montodiaso+montodiaso*(float(apara[1])/100)
		# 	tmp__5 += self.horas_extra_feriado_diur*montodiaso
		# 	tmp__5 += tmp__11 + tmp__111 + tmp__112

		# 	self.write({'nohacernada':1,'h_100': tmp__5})

		# 	tmp__6 =  round( ((self.total_remunerable/30) /8 )+0.0001,2)* self.tardanza_horas
		# 	self.write({'nohacernada':1,'tardanzas': tmp__6})
		# 	tmp__7 =0
		# 	if self.dias_suspension_perfecta:
		# 		if self.dias_suspension_perfecta>0:
		# 			tmp__7 =  (((self.basica_first/30) )* self.dias_suspension_perfecta)
		# 			# tmp__7 =  (((self.basica_first/30) )* self.dias_suspension_perfecta)+self.a_familiar_first
			
		# 	self.write({'nohacernada':1,'inasistencias': tmp__7})

		# 	tmp__8 = self.horas_extra_diurna + self.horas_extra_nocturna + self.horas_extra_feriado+self.horas_extra_feriado_diur+self.horas_extra_feriado_noct
		# 	self.write({'nohacernada':1,'total_horas_extras': tmp__8})
		# 	self.refresh()

		# 	tmp__9 = int(self.total_horas_extras)
		# 	self.write({'nohacernada':1,'total_horas_extras_horas': tmp__9})
		# 	self.refresh()

		# 	tmp__10 = (self.total_horas_extras - int(self.total_horas_extras) )*60
		# 	self.write({'nohacernada':1,'total_horas_extras_minutos': tmp__10})
			

		# 	self.refresh()

		# 	tmp_1 = self.basica + self.a_familiar + self.vacaciones + self.vacaciones_trunca + self.subsidiomaternidad+self.bonificacion+self.comision
		# 	tmp_1 += self.subsidioincapacidad + self.h_25 + self.h_35 + self.h_100 + self.otros_ingreso 
		# 	self.write({'nohacernada':1,'total_ingreso': tmp_1})
		# 	tmp_2 = tmp_1 - self.tardanzas - self.inasistencias - self.dscto_domi
		# 	self.write({'nohacernada':1,'rmb': tmp_2})

		# 	####
			
		# 	trib_1= 0
		# 	for iij in self.env['hr.concepto.remunerativo.line'].search([('afecto_tributo','=',True)]):
		# 		if iij.concepto.code == '001':
		# 			trib_1 += self.basica
		# 		if iij.concepto.code == '002':
		# 			trib_1 += self.a_familiar
		# 		if iij.concepto.code == '003':
		# 			trib_1 += self.vacaciones
		# 		if iij.concepto.code == '004':
		# 			trib_1 += self.vacaciones_trunca
		# 		if iij.concepto.code == '005':
		# 			trib_1 += self.gratificacion
		# 		if iij.concepto.code == '006':
		# 			trib_1 += self.subsidiomaternidad
		# 		if iij.concepto.code == '007':
		# 			trib_1 += self.gratificacion_extraordinaria
		# 		if iij.concepto.code == '008':
		# 			trib_1 += self.bonificacion
		# 		if iij.concepto.code == '009':
		# 			trib_1 += self.comision
		# 		if iij.concepto.code == '010':
		# 			trib_1 += self.boni_grati

		# 	trib_2= 0
		# 	for iij in self.env['hr.concepto.remunerativo.line'].search([('afecto_afp','=',True)]):
		# 		if iij.concepto.code == '001':
		# 			trib_2 += self.basica
		# 		if iij.concepto.code == '002':
		# 			trib_2 += self.a_familiar
		# 		if iij.concepto.code == '003':
		# 			trib_2 += self.vacaciones
		# 		if iij.concepto.code == '004':
		# 			trib_2 += self.vacaciones_trunca
		# 		if iij.concepto.code == '005':
		# 			trib_2 += self.gratificacion
		# 		if iij.concepto.code == '006':
		# 			trib_2 += self.subsidiomaternidad
		# 		if iij.concepto.code == '007':
		# 			trib_2 += self.gratificacion_extraordinaria
		# 		if iij.concepto.code == '008':
		# 			trib_2 += self.bonificacion
		# 		if iij.concepto.code == '009':
		# 			trib_2 += self.comision
		# 		if iij.concepto.code == '010':
		# 			trib_2 += self.boni_grati			

		# 	trib_3= 0
		# 	for iij in self.env['hr.concepto.remunerativo.line'].search([('afecto_aportes','=',True)]):
		# 		if iij.concepto.code == '001':
		# 			trib_3 += self.basica
		# 		if iij.concepto.code == '002':
		# 			trib_3 += self.a_familiar
		# 		if iij.concepto.code == '003':
		# 			trib_3 += self.vacaciones
		# 		if iij.concepto.code == '004':
		# 			trib_3 += self.vacaciones_trunca
		# 		if iij.concepto.code == '005':
		# 			trib_3 += self.gratificacion
		# 		if iij.concepto.code == '006':
		# 			trib_3 += self.subsidiomaternidad
		# 		if iij.concepto.code == '007':
		# 			trib_3 += self.gratificacion_extraordinaria
		# 		if iij.concepto.code == '008':
		# 			trib_3 += self.bonificacion
		# 		if iij.concepto.code == '009':
		# 			trib_3 += self.comision
		# 		if iij.concepto.code == '010':
		# 			trib_3 += self.boni_grati					

		# 	if self.afiliacion.id:
		# 		t_opm=self.env['hr.membership.line'].search( [('periodo','=',self.tareo_id.periodo.id),('membership','=',self.afiliacion.id)] )
		# 		if len(t_opm)>0:
		# 			t_opm = t_opm[0]
		# 			if self.afiliacion.code == '4':
		# 				self.write({'nohacernada':1,'onp': (trib_1+self.h_100+self.h_25+self.h_35 - self.tardanzas - self.inasistencias - self.dscto_domi) * ( t_opm.tasa_pensiones /100.0)  })
		# 			else:
		# 				self.write({'nohacernada':1,'afp_jub': (trib_2+self.h_100+self.h_25+self.h_35 - self.tardanzas - self.inasistencias - self.dscto_domi) * ( t_opm.tasa_pensiones /100.0)  })
		# 				self.write({'nohacernada':1,'afp_psi': ((trib_2+self.h_100+self.h_25+self.h_35 - self.tardanzas - self.inasistencias - self.dscto_domi) * ( t_opm.prima /100.0) ) if trib_2 < t_opm.rma else (t_opm.rma * ( t_opm.prima /100.0) ) })
		# 				self.write({'nohacernada':1,'afp_com': ( (trib_2+self.h_100+self.h_25+self.h_35 - self.tardanzas - self.inasistencias - self.dscto_domi) * ( t_opm.c_mixta /100.0) ) if self.tipo_comision == True else ((trib_2+self.h_100+self.h_25+self.h_35-self.tardanzas - self.inasistencias - self.dscto_domi) * ( t_opm.c_variable /100.0) ) })
					
		# 			self.write({'nohacernada':1,'rma_pi': t_opm.rma })
		# 		else:
		# 			self.write({'nohacernada':1,'afp_jub': 0 })
		# 			self.write({'nohacernada':1,'afp_psi': 0 })
		# 			self.write({'nohacernada':1,'afp_com': 0 })
		# 			self.write({'nohacernada':1,'rma_pi': 0 })
			
		# 	subcidios=self.subsidiomaternidad+self.subsidioincapacidad
		# 	if trib_3+self.h_100+self.h_25+self.h_35-self.tardanzas - self.inasistencias - self.dscto_domi+subcidios<self.env['hr.parameters'].search([])[0].rmv:
		# 		if self.rmb>0:
		# 			self.write({'nohacernada':1,'essalud': (self.env['hr.parameters'].search([])[0].essalud /100.0) *self.env['hr.parameters'].search([])[0].rmv})
		# 		else:
		# 			self.write({'nohacernada':1,'essalud': 0})
		# 	else:
		# 		self.write({'nohacernada':1,'essalud': (self.env['hr.parameters'].search([])[0].essalud /100.0) *(trib_3+self.h_100+self.h_25+self.h_35-self.tardanzas - self.inasistencias - self.dscto_domi) })
		# 	# self.essalud = (self.env['hr.parameters'].search([])[0].essalud /100.0)*trib_3 
		# 	# self.eps=0
		# 	emp_tmp = self.env['hr.employee'].search( [('identification_id','=',self.dni)] )
		# 	if emp_tmp.use_eps:
		# 		if self.rmb>0:
		# 			eps1=(self.env['hr.parameters'].search([])[0].eps_percent /100.0)*(trib_3 +self.h_100+self.h_25+self.h_35-self.tardanzas - self.inasistencias - self.dscto_domi)
		# 			esalud1 = (self.env['hr.parameters'].search([])[0].essalud /100.0)*(trib_3+self.h_100+self.h_25+self.h_35-self.tardanzas - self.inasistencias - self.dscto_domi)
		# 		else:
		# 			eps1=0
		# 			esalud1 =0
		# 		self.write({'nohacernada':1,'essalud': esalud1-eps1,'eps':eps1})

		# 	self.write({'nohacernada':1,'senaty': (self.env['hr.parameters'].search([])[0].senati /100.0) *(trib_3+self.h_100+self.h_25+self.h_35-self.tardanzas - self.inasistencias - self.dscto_domi) })
		# 	self.write({'nohacernada':1,'sctr':self.sctr })
		# 	self.refresh()
		# 	tmp_3 = self.onp + self.afp_jub + self.afp_psi + self.afp_com + self.quinta_cat
		# 	self.write({'nohacernada':1,'total_descuento': tmp_3})
		# 	tmp_4 = tmp_2 - tmp_3
			
		# 	s_porc =  (self.basica + self.a_familiar ) / (self.basica + self.a_familiar + self.vacaciones + self.vacaciones_trunca)  if (self.basica + self.a_familiar + self.vacaciones + self.vacaciones_trunca) != 0 else 0
		# 	v_porc = (1- s_porc)
		# 	tmp_5 = round( (tmp_4 * s_porc)+ 0.000001,2)

		# 	montovaca=self.vacaciones+self.vacaciones_trunca
		# 	if self.vacaciones+self.vacaciones_trunca>0:
		# 		montovaca = self.vacaciones+self.vacaciones_trunca+self.otros_ingreso
		# 	motosueldo = self.total_ingreso-montovaca-self.comision
		# 	montocomision = self.comision
		# 	factorsuel = 0
		# 	factorvaca = 0
		# 	factorcomi = 0

		# 	if self.total_ingreso!=0:
		# 		factorsuel = motosueldo/self.total_ingreso
		# 		factorvaca = montovaca/self.total_ingreso
		# 		factorcomi = montocomision/self.total_ingreso

		# 	tmp_5 = tmp_4*factorsuel
		# 	tmp_6 = tmp_4*factorvaca
		# 	tmp_comi = tmp_4*factorcomi
		# 	self.write({'nohacernada':1,'neto_sueldo': tmp_5})
		# 	# tmp_6 = tmp_4 - tmp_5
		# 	self.write({'nohacernada':1,'neto_vacaciones': tmp_6})

		# 	######
		# 	prest_tmp = 0
		# 	emp_tmp = self.env['hr.employee'].search( [('identification_id','=',self.dni)] )
		# 	if len(emp_tmp) > 0:
		# 		emp_tmp = emp_tmp[0]
		# 		for iomn in self.env['hr.adelanto'].search( [('employee','=',emp_tmp.id),('fecha','>=',self.tareo_id.periodo.date_start),('fecha','<=',self.tareo_id.periodo.date_stop)] ):
		# 			prest_tmp+= iomn.monto

		# 	self.write({'nohacernada':1,'adelantos': prest_tmp})
		# 	self.refresh()
		# 	######
		# 	# tmp_7 = tmp_5 - self.adelantos - self.prestamos - self.otros_dct
		# 	# self.write({'nohacernada':1,'saldo_sueldo': tmp_7})
		# 	tmp_8 = self.afp_jub + self.afp_psi + self.afp_com 
		# 	self.write({'nohacernada':1,'dsc_afp': tmp_8})
		# 	self.write({'nohacernada':1,'neto': tmp_4})
		# 	# valor = self.neto+self.cts+self.gratificacion_extraordinaria+self.gratificacion_extraordinaria_real-prest_tmp-self.prestamos
		# 	valor = self.neto+self.cts+self.gratificacion_extraordinaria+self.gratificacion+self.gratificacion_extraordinaria_real++self.boni_grati-prest_tmp-self.prestamos-self.otros_dct
		# 	self.write({'nohacernada':1,'saldo_sueldo': valor})
		# 	trabajador = self.env['hr.employee'].search( [('identification_id','=',self.dni)] )
		# 	valtbol = self.neto-self.adelantos-self.prestamos-self.otros_dct
		# 	self.write({'nohacernada':1,'total_boleta': valtbol})
		# 	self.write({'nohacernada':1,'centro_costo': trabajador.dist_c.id})

			
		# 	# encontrar el actual en la tabla grabada vertical concepto por concepto
		# 	for concepto in self.env['hr.concepto.remunerativo.line'].search([]):
		# 		tareoconcepto=self.env['hr.tareo.concepto'].search([('concepto_id','=',concepto.id),('tareo_id','=',self.tareo_id.id),('employee_id','=',trabajador.id)])
		# 		vals={}
		# 		lcrear = True
		# 		if len(tareoconcepto)>0:
		# 			afp_code = tareoconcepto.membership_id.code
		# 			lcrear=False
		# 		else:
		# 			afp_code = trabajador.afiliacion.code

		# 		if concepto.codigo=='001':
		# 			vals.update({'amount':self.basica})
		# 		if concepto.codigo=='002':
		# 			vals.update({'amount':self.a_familiar})
		# 		if concepto.codigo=='003': # ,'Vacaciones'),
		# 			vals.update({'amount':self.vacaciones})
		# 		if concepto.codigo=='004': #,'Vacaciones Truncas'),
		# 			vals.update({'amount':self.vacaciones_trunca})
		# 		if concepto.codigo=='005': #,'Gratificaci??n'),
		# 			vals.update({'amount':self.gratificacion})
		# 		if concepto.codigo=='006': #,'Subsidio Maternidad'),
		# 			vals.update({'amount':self.subsidiomaternidad})
		# 		if concepto.codigo=='007': #,'Gratificacion Extraordinari'),
		# 			vals.update({'amount':self.gratificacion_extraordinaria_real})
		# 		if concepto.codigo=='008': #,'Bonificaci??n'),
		# 			vals.update({'amount':self.bonificacion})
		# 		if concepto.codigo=='009': #,'Comsi??n'),
		# 			vals.update({'amount':self.comision})
		# 		if concepto.codigo=='010': #,'Bonificaci??n de Gratificaci??n'),
		# 			vals.update({'amount':self.boni_grati})
		# 		if concepto.codigo=='916': #,'Subsidio incapacidad'),
		# 			vals.update({'amount':self.subsidioincapacidad})
		# 		if concepto.codigo=='105': #,'H25'),
		# 			vals.update({'amount':self.h_25})
		# 		if concepto.codigo=='106': #,'H35'),
		# 			vals.update({'amount':self.h_35})
		# 		if concepto.codigo=='107': #,'H100'),
		# 			vals.update({'amount':self.h_100})
		# 		if concepto.codigo=='504': #,'Indemnizaci??n por vacaciones'),
		# 			vals.update({'amount':self.otros_ingreso})
		# 		if concepto.codigo=='10': #,'Total de ingreso'),
		# 			vals.update({'amount':self.total_ingreso})
		# 		if concepto.codigo=='704': #,'Tardanzas'),
		# 			vals.update({'amount':self.tardanzas})
		# 		if concepto.codigo=='705': #,'Inasistencias'),
		# 			vals.update({'amount':self.inasistencias})
		# 		if concepto.codigo=='706': #,'Descuento dominical'),
		# 			vals.update({'amount':self.descuento_dominical})
		# 		if concepto.codigo=='607': #,'ONP'),
		# 			vals.update({'amount':self.onp})
		# 		if concepto.codigo=='605': #,'Retenci??n de 5ta categor??a'),
		# 			vals.update({'amount':self.quinta_cat})
		# 		if concepto.codigo=='701': #,'Adelantos'),
		# 			vals.update({'amount':self.adelantos})
		# 		if concepto.codigo=='610': #,'ESSALUD'),
		# 			vals.update({'amount':self.essalud})
		# 		if concepto.codigo=='810': #,'EPS'),
		# 			vals.update({'amount':self.eps})
		# 		if concepto.codigo=='807': #,'SENATI'),
		# 			vals.update({'amount':self.senaty})
		# 		if concepto.codigo=='811': #,'SCTR'),
		# 			vals.update({'amount':self.sctr})
		# 		if concepto.codigo=='505': #,'CTS'),
		# 			vals.update({'amount':self.cts})
		# 		if concepto.codigo=='407': #,'Gratificaci??n trunca'),
		# 			vals.update({'amount':self.gratificacion_extraordinaria})
		# 		#conceptos propios del c??culo
		# 		if concepto.codigo=='12': #,'RMB'),
		# 			vals.update({'amount':self.rmb})
		# 		# afps
		# 		if concepto.codigo=='13': #,'AFP INTEGRA'),
		# 			if afp_code=='AFP INTEGRA':
		# 				valor=self.afp_com+self.afp_psi+self.afp_jub
		# 				vals.update({'amount':valor})
		# 		if concepto.codigo=='14': #,'AFP PRIMA'),
		# 			if afp_code=='AFP PRIMA':
		# 				valor=self.afp_com+self.afp_psi+self.afp_jub
		# 				vals.update({'amount':valor})
		# 		if concepto.codigo=='15': #,'AFP PROFUTURO'),
		# 			if afp_code=='AFP PROFUTURO':
		# 				valor=self.afp_com+self.afp_psi+self.afp_jub
		# 				vals.update({'amount':valor})
		# 		if concepto.codigo=='16': #,'AFP HABITAD'),
		# 			if afp_code=='AFP HABITAD':
		# 				valor=self.afp_com+self.afp_psi+self.afp_jub
		# 				vals.update({'amount':valor})
		# 		if concepto.codigo=='17': #,'Total descuentos'),
		# 			vals.update({'amount':self.total_descuento})
		# 		if concepto.codigo=='18': #,'NETO'),
		# 			vals.update({'amount':self.neto})
		# 		if concepto.codigo=='19': #,'NETO SUELDOS'),
		# 			vals.update({'amount':self.neto_sueldo})
		# 		if concepto.codigo=='20': #,'NETO VACACIONES'),
		# 			vals.update({'amount':self.neto_vacaciones})
		# 		if concepto.codigo=='21': #,'Pr??stamos'),
		# 			vals.update({'amount':self.prestamos})
		# 			vals.update({'cta_prestamo':self.cta_prestamo.id})
		# 		if concepto.codigo=='22': #,'Otros descuentos'),
		# 			vals.update({'amount':self.otros_dct})
		# 		if concepto.codigo=='23': #,'Saldo a pagar sueldo'),
		# 			vals.update({'amount':self.saldo_sueldo})
		# 		# conceptos solo para el c??culo del asiento contable
		# 		if concepto.codigo=='24': #,'Sueldo asiento'),
		# 			valor = self.basica+self.a_familiar-self.tardanzas-self.inasistencias
		# 			vals.update({'amount':valor})
		# 		if concepto.codigo=='25': #,'Horas extra asiento'),
		# 			valor = self.h_25+self.h_35+self.h_100
		# 			vals.update({'amount':valor})
		# 		if concepto.codigo=='26': #,'Vacaciones asiento'),
		# 			valor = self.vacaciones+self.vacaciones_trunca
		# 			vals.update({'amount':valor})
		# 		if concepto.codigo=='27': #,'Total descuento inafectos asiento'),
		# 			valor = self.adelantos+self.prestamos+self.otros_dct
		# 			vals.update({'amount':valor})
		# 		if concepto.codigo=='28': #,'Neto - Descuentos inafectos asiento'),
		# 			valor = self.neto-(self.adelantos+self.prestamos+self.otros_dct)
		# 			vals.update({'amount':valor})
		# 		if concepto.codigo=='29': #,'Descuentos AFP asiento'),
		# 			vals.update({'amount':self.dsc_afp})
		# 		if concepto.codigo=='30': #,'Total Gratificanoes asiento'),
		# 			valor = self.gratificacion+self.gratificacion_extraordinaria+self.boni_grati+self.gratificacion_extraordinaria_real
		# 			vals.update({'amount':valor})
		# 		if concepto.codigo=='31': # ,'basica_first'),
		# 			vals.update({'amount':self.basica_first})
		# 		if concepto.codigo=='32': # ,'a_familiar_first'),
		# 			vals.update({'amount':self.a_familiar})
		# 		if concepto.codigo=='33': # ,'total_remunerable'),
		# 			vals.update({'amount':self.total_remunerable})
		# 		if concepto.codigo=='34': # ,'dias_trabajador'),
		# 			vals.update({'amount':self.dias_trabajador})
		# 		if concepto.codigo=='35': # ,'tipo_suspension_perfecta'),
		# 			vals.update({'amount':0,'descripcion':self.tipo_suspension_perfecta

		# 				# self.tipo_suspension_perfecta
		# 				})
		# 		if concepto.codigo=='36': # ,'tipo_suspension_imperfecta'),
		# 			vals.update({'amount':0,'descripcion':self.tipo_suspension_imperfecta
		# 				# self.tipo_suspension_imperfecta
		# 				})
		# 		if concepto.codigo=='37': # ,'dias_suspension_perfecta'),
		# 			vals.update({'amount':self.dias_suspension_perfecta})
		# 		if concepto.codigo=='38': # ,'tardanza_horas'),
		# 			vals.update({'amount':self.tardanza_horas})
		# 		if concepto.codigo=='39': # ,'horas_extra_diurna'),
		# 			vals.update({'amount':self.horas_extra_diurna})
		# 		if concepto.codigo=='40': # ,'horas_extra_nocturna'),
		# 			vals.update({'amount':self.horas_extra_nocturna})
		# 		if concepto.codigo=='41': # ,'horas_extra_feriado'),
		# 			vals.update({'amount':self.horas_extra_feriado})
		# 		if concepto.codigo=='42': # ,'horas_extra_feriado_diur'),
		# 			vals.update({'amount':self.horas_extra_feriado_diur})
		# 		if concepto.codigo=='43': # ,'horas_extra_feriado_noct'),
		# 			vals.update({'amount':self.horas_extra_feriado_noct})
		# 		if concepto.codigo=='44': # ,'total_horas_extras'),
		# 			vals.update({'amount':self.total_horas_extras})
		# 		if concepto.codigo=='45': # ,'total_horas_extras_horas'),
		# 			vals.update({'amount':self.total_horas_extras_horas})
		# 		if concepto.codigo=='46': # ,'total_horas_extras_minutos'),
		# 			vals.update({'amount':self.total_horas_extras_minutos})
		# 		if concepto.codigo=='47': # ,'otros_ingreso'),
		# 			vals.update({'amount':self.otros_ingreso})
		# 		if concepto.codigo=='48': # ,'total_ingreso'),
		# 			vals.update({'amount':self.total_ingreso})
		# 		if concepto.codigo=='49': # ,'afp_jub'),
		# 			vals.update({'amount':self.afp_jub})
		# 		if concepto.codigo=='50': # ,'afp_psi'),
		# 			vals.update({'amount':self.afp_psi})
		# 		if concepto.codigo=='51': # ,'afp_com'),
		# 			vals.update({'amount':self.afp_com})
		# 		if concepto.codigo=='52': # ,'quinta_cat'),
		# 			vals.update({'amount':self.quinta_cat})
		# 		if concepto.codigo=='53': # ,'rma_pi'),
		# 			vals.update({'amount':self.rma_pi})
		# 		if concepto.codigo=='54': # ,'centro_costo'),
		# 			vals.update({'amount':0
		# 				# self.centro_costo.id
		# 				})
		# 		if self.total_ingreso>0:

		# 			if concepto.codigo=='55': # ,'neto sueldo asiento'),
		# 				factorvacaciones= (self.vacaciones+self.vacaciones_trunca)/self.total_ingreso
		# 				factorcomision = self.comision/self.total_ingreso
		# 				factorsueldo=1-(factorvacaciones+factorcomision)					
		# 				ndi = self.neto-(self.adelantos+self.prestamos+self.otros_dct)
		# 				vals.update({'amount':ndi*factorsueldo})
		# 			if concepto.codigo=='56': # ,'neto vacaciones asiento'),
		# 				factorvacaciones= (self.vacaciones+self.vacaciones_trunca)/self.total_ingreso
		# 				factorcomision = self.comision/self.total_ingreso
		# 				factorsueldo=1-(factorvacaciones+factorcomision)					
		# 				ndi = self.neto-(self.adelantos+self.prestamos+self.otros_dct)
		# 				vals.update({'amount':ndi*factorvacaciones})					
		# 			if concepto.codigo=='57': # ,'neto comisiones asiento'),
		# 				factorvacaciones= (self.vacaciones+self.vacaciones_trunca)/self.total_ingreso
		# 				factorcomision = self.comision/self.total_ingreso
		# 				factorsueldo=1-(factorvacaciones+factorcomision)					
		# 				ndi = self.neto-(self.adelantos+self.prestamos+self.otros_dct)
		# 				vals.update({'amount':ndi*factorcomision})	
		# 		else:
		# 			vals.update({'amount':0})
		# 		if concepto.account_credit:
		# 			vals.update({'cuenta_haber':concepto.account_credit.id})	
		# 		else:
		# 			vals.update({'cuenta_haber':None})	
		# 		if self.centro_costo:
		# 			valor = 0
		# 			vals.update({'extraccion_acc_a':valor})
		# 			vals.update({'trituracion_acc_a':valor})
		# 			vals.update({'calcinacion_acc_a':valor})
		# 			vals.update({'micronizado_acc_a':valor})
		# 			vals.update({'administracion_acc_a':valor})
		# 			vals.update({'ventas_acc_a':valor})
		# 			vals.update({'capacitacion_acc_a':valor})
		# 			vals.update({'promocion_acc_a':valor})
		# 			vals.update({'gastos_acc_a':valor})
		# 			vals.update({'extraccion_acc_m':valor})
		# 			vals.update({'trituracion_acc_m':valor})
		# 			vals.update({'calcinacion_acc_m':valor})
		# 			vals.update({'micronizado_acc_m':valor})
		# 			vals.update({'administracion_acc_m':valor})
		# 			vals.update({'ventas_acc_m':valor})
		# 			vals.update({'capacitacion_acc_m':valor})
		# 			vals.update({'promocion_acc_m':valor})
		# 			vals.update({'gastos_acc_m':valor})										
		# 			vals.update({'extraccion_acc_o':valor})
		# 			vals.update({'trituracion_acc_o':valor})
		# 			vals.update({'calcinacion_acc_o':valor})
		# 			vals.update({'micronizado_acc_o':valor})
		# 			vals.update({'administracion_acc_o':valor})
		# 			vals.update({'ventas_acc_o':valor})
		# 			vals.update({'capacitacion_acc_o':valor})
		# 			vals.update({'promocion_acc_o':valor})
		# 			vals.update({'gastos_acc_o':valor})																				
		# 			vals.update({'extraccion_acc_v':valor})
		# 			vals.update({'trituracion_acc_v':valor})
		# 			vals.update({'calcinacion_acc_v':valor})
		# 			vals.update({'micronizado_acc_v':valor})
		# 			vals.update({'administracion_acc_v':valor})
		# 			vals.update({'ventas_acc_v':valor})
		# 			vals.update({'capacitacion_acc_v':valor})
		# 			vals.update({'promocion_acc_v':valor})
		# 			vals.update({'gastos_acc_v':valor})				

		# 			valor = None
		# 			vals.update({'extraccion_acc_a_d':valor})
		# 			vals.update({'trituracion_acc_a_d':valor})
		# 			vals.update({'calcinacion_acc_a_d':valor})
		# 			vals.update({'micronizado_acc_a_d':valor})
		# 			vals.update({'administracion_acc_a_d':valor})
		# 			vals.update({'ventas_acc_a_d':valor})
		# 			vals.update({'capacitacion_acc_a_d':valor})
		# 			vals.update({'promocion_acc_a_d':valor})
		# 			vals.update({'gastos_acc_a_d':valor})
		# 			vals.update({'extraccion_acc_m_d':valor})
		# 			vals.update({'trituracion_acc_m_d':valor})
		# 			vals.update({'calcinacion_acc_m_d':valor})
		# 			vals.update({'micronizado_acc_m_d':valor})
		# 			vals.update({'administracion_acc_m_d':valor})
		# 			vals.update({'ventas_acc_m_d':valor})
		# 			vals.update({'capacitacion_acc_m_d':valor})
		# 			vals.update({'promocion_acc_m_d':valor})
		# 			vals.update({'gastos_acc_m_d':valor})										
		# 			vals.update({'extraccion_acc_o_d':valor})
		# 			vals.update({'trituracion_acc_o_d':valor})
		# 			vals.update({'calcinacion_acc_o_d':valor})
		# 			vals.update({'micronizado_acc_o_d':valor})
		# 			vals.update({'administracion_acc_o_d':valor})
		# 			vals.update({'ventas_acc_o_d':valor})
		# 			vals.update({'capacitacion_acc_o_d':valor})
		# 			vals.update({'promocion_acc_o_d':valor})
		# 			vals.update({'gastos_acc_o_d':valor})																				
		# 			vals.update({'extraccion_acc_v_d':valor})
		# 			vals.update({'trituracion_acc_v_d':valor})
		# 			vals.update({'calcinacion_acc_v_d':valor})
		# 			vals.update({'micronizado_acc_v_d':valor})
		# 			vals.update({'administracion_acc_v_d':valor})
		# 			vals.update({'ventas_acc_v_d':valor})
		# 			vals.update({'capacitacion_acc_v_d':valor})
		# 			vals.update({'promocion_acc_v_d':valor})
		# 			vals.update({'gastos_acc_v_d':valor})				
		# 			convalores=[]
		# 			for lineadist in self.centro_costo.distribucion_lines:
						
						
		# 				if 'amount' in vals:
							
		# 					if vals['amount']>0:
								
		# 						# inicializamos cada uno con cero por si se cambia
		# 						# de cc y luego los vamos a recalcular todos
								

		# 						valor =(lineadist.porcentaje/100)*vals['amount']
		# 						valor = float(decimal.Decimal(str(valor)).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))

		# 						if trabajador.tipo_contab=='administracion':
		# 							if lineadist.analitica.cost_center_id.columna=='1' and concepto.extraccion_acc_a:
		# 								vals.update({'extraccion_acc_a':valor,'extraccion_acc_a_d':concepto.extraccion_acc_a.id})
		# 							if lineadist.analitica.cost_center_id.columna=='2' and concepto.trituracion_acc_a:
		# 								vals.update({'trituracion_acc_a':valor,'trituracion_acc_a_d':concepto.trituracion_acc_a.id})
		# 							if lineadist.analitica.cost_center_id.columna=='3' and concepto.calcinacion_acc_a:
		# 								vals.update({'calcinacion_acc_a':valor,'calcinacion_acc_a_d':concepto.calcinacion_acc_a.id})
		# 							if lineadist.analitica.cost_center_id.columna=='4' and concepto.micronizado_acc_a:
		# 								vals.update({'micronizado_acc_a':valor,'micronizado_acc_a_d':concepto.micronizado_acc_a.id})
		# 							if lineadist.analitica.cost_center_id.columna=='5' and concepto.administracion_acc_a:
		# 								vals.update({'administracion_acc_a':valor,'administracion_acc_a_d':concepto.administracion_acc_a.id})
		# 							if lineadist.analitica.cost_center_id.columna=='6' and concepto.ventas_acc_a:
		# 								vals.update({'ventas_acc_a':valor,'ventas_acc_a_d':concepto.ventas_acc_a.id})
		# 							if lineadist.analitica.cost_center_id.columna=='7' and concepto.capacitacion_acc_a:
		# 								vals.update({'capacitacion_acc_a':valor,'capacitacion_acc_a_d':concepto.capacitacion_acc_a.id})
		# 							if lineadist.analitica.cost_center_id.columna=='8' and concepto.promocion_acc_a:
		# 								vals.update({'promocion_acc_a':valor,'promocion_acc_a_d':concepto.promocion_acc_a.id})
		# 							if lineadist.analitica.cost_center_id.columna=='9' and concepto.gastos_acc_a:
		# 								vals.update({'gastos_acc_a':valor,'gastos_acc_a_d':concepto.gastos_acc_a.id})
		# 						if trabajador.tipo_contab=='mantenimiento':
		# 							if lineadist.analitica.cost_center_id.columna=='1' and concepto.extraccion_acc_m:
		# 								vals.update({'extraccion_acc_m':valor,'extraccion_acc_m_d':concepto.extraccion_acc_m.id})
		# 							if lineadist.analitica.cost_center_id.columna=='2' and concepto.trituracion_acc_m:
		# 								vals.update({'trituracion_acc_m':valor,'trituracion_acc_m_d':concepto.trituracion_acc_m.id})
		# 							if lineadist.analitica.cost_center_id.columna=='3' and concepto.calcinacion_acc_m:
		# 								vals.update({'calcinacion_acc_m':valor,'calcinacion_acc_m_d':concepto.calcinacion_acc_m.id})
		# 							if lineadist.analitica.cost_center_id.columna=='4' and concepto.micronizado_acc_m:
		# 								vals.update({'micronizado_acc_m':valor,'micronizado_acc_m_d':concepto.micronizado_acc_m.id})
		# 							if lineadist.analitica.cost_center_id.columna=='5' and concepto.administracion_acc_m:
		# 								vals.update({'administracion_acc_m':valor,'administracion_acc_m_d':concepto.administracion_acc_m.id})
		# 							if lineadist.analitica.cost_center_id.columna=='6' and concepto.ventas_acc_m:
		# 								vals.update({'ventas_acc_m':valor,'ventas_acc_m_d':concepto.ventas_acc_m.id})
		# 							if lineadist.analitica.cost_center_id.columna=='7' and concepto.capacitacion_acc_m:
		# 								vals.update({'capacitacion_acc_m':valor,'capacitacion_acc_m_d':concepto.capacitacion_acc_m.id})
		# 							if lineadist.analitica.cost_center_id.columna=='8' and concepto.promocion_acc_m:
		# 								vals.update({'promocion_acc_m':valor,'promocion_acc_m_d':concepto.promocion_acc_m.id})
		# 							if lineadist.analitica.cost_center_id.columna=='9' and concepto.gastos_acc_m:
		# 								convalores.append({'campo':'gastos_acc_m','valor':valor})
		# 								vals.update({'gastos_acc_m':valor,'gastos_acc_m_d':concepto.gastos_acc_m.id})										
		# 						if trabajador.tipo_contab=='operario':
		# 							if lineadist.analitica.cost_center_id.columna=='1'and concepto.extraccion_acc_o:
		# 								vals.update({'extraccion_acc_o':valor,'extraccion_acc_o_d':concepto.extraccion_acc_o.id})
		# 							if lineadist.analitica.cost_center_id.columna=='2' and concepto.trituracion_acc_o:
		# 								vals.update({'trituracion_acc_o':valor,'trituracion_acc_o_d':concepto.trituracion_acc_o.id})
		# 							if lineadist.analitica.cost_center_id.columna=='3' and concepto.calcinacion_acc_o:
		# 								vals.update({'calcinacion_acc_o':valor,'calcinacion_acc_o_d':concepto.calcinacion_acc_o.id})
		# 							if lineadist.analitica.cost_center_id.columna=='4' and concepto.micronizado_acc_o:
		# 								vals.update({'micronizado_acc_o':valor,'micronizado_acc_o_d':concepto.micronizado_acc_o.id})
		# 							if lineadist.analitica.cost_center_id.columna=='5' and concepto.administracion_acc_o:
		# 								vals.update({'administracion_acc_o':valor,'administracion_acc_o_d':concepto.administracion_acc_o.id})
		# 							if lineadist.analitica.cost_center_id.columna=='6' and concepto.ventas_acc_o:
		# 								vals.update({'ventas_acc_o':valor,'ventas_acc_o_d':concepto.ventas_acc_o.id})
		# 							if lineadist.analitica.cost_center_id.columna=='7' and concepto.capacitacion_acc_o:
		# 								vals.update({'capacitacion_acc_o':valor,'capacitacion_acc_o_d':concepto.capacitacion_acc_o.id})
		# 							if lineadist.analitica.cost_center_id.columna=='8' and concepto.promocion_acc_o:
		# 								vals.update({'promocion_acc_o':valor,'promocion_acc_o_d':concepto.promocion_acc_o.id})
		# 							if lineadist.analitica.cost_center_id.columna=='9' and concepto.gastos_acc_o:
		# 								convalores.append({'campo':'gastos_acc_o','valor':valor})
		# 								vals.update({'gastos_acc_o':valor,'gastos_acc_o_d':concepto.gastos_acc_o.id})
		# 						if trabajador.tipo_contab=='ventas':
		# 							if lineadist.analitica.cost_center_id.columna=='1' and concepto.extraccion_acc_v:
		# 								vals.update({'extraccion_acc_v':valor,'extraccion_acc_v_d':concepto.extraccion_acc_v.id})
		# 							if lineadist.analitica.cost_center_id.columna=='2' and concepto.trituracion_acc_v:
		# 								vals.update({'trituracion_acc_v':valor,'trituracion_acc_v_d':concepto.trituracion_acc_v.id})
		# 							if lineadist.analitica.cost_center_id.columna=='3' and concepto.calcinacion_acc_v:
		# 								vals.update({'calcinacion_acc_v':valor,'calcinacion_acc_v_d':concepto.calcinacion_acc_v.id})
		# 							if lineadist.analitica.cost_center_id.columna=='4' and concepto.micronizado_acc_v:
		# 								vals.update({'micronizado_acc_v':valor,'micronizado_acc_v_d':concepto.micronizado_acc_v.id})
		# 							if lineadist.analitica.cost_center_id.columna=='5' and concepto.administracion_acc_v:
		# 								vals.update({'administracion_acc_v':valor,'administracion_acc_v_d':concepto.administracion_acc_v.id})
		# 							if lineadist.analitica.cost_center_id.columna=='6' and concepto.ventas_acc_v:
		# 								vals.update({'ventas_acc_v':valor,'ventas_acc_v_d':concepto.ventas_acc_v.id})
		# 							if lineadist.analitica.cost_center_id.columna=='7' and concepto.capacitacion_acc_v:
		# 								vals.update({'capacitacion_acc_v':valor,'capacitacion_acc_v_d':concepto.capacitacion_acc_v.id})
		# 							if lineadist.analitica.cost_center_id.columna=='8' and concepto.promocion_acc_v:
		# 								vals.update({'promocion_acc_v':valor,'promocion_acc_v_d':concepto.promocion_acc_v.id})
		# 							if lineadist.analitica.cost_center_id.columna=='9' and concepto.gastos_acc_v:
		# 								vals.update({'gastos_acc_v':valor,'gastos_acc_v_d':concepto.gastos_acc_v.id})



		# 		vals.update({'tipo_contab':trabajador.tipo_contab})
		# 		vals.update({'membership_id':trabajador.afiliacion.id})
		# 		vals.update({'distribucion_id':trabajador.dist_c.id if trabajador.dist_c else None})
		# 		if lcrear:
		# 			vals.update({'tareo_id':self.tareo_id.id})
		# 			vals.update({'employee_id':trabajador.id})
		# 			vals.update({'concepto_id':concepto.id})
		# 			# print vals
		# 			self.env['hr.tareo.concepto'].create(vals)
		# 		else:
		# 			# print 'editando'
		# 			tareoconcepto.write(vals)

		return t

	@api.multi
	def save_data(self):
		self.write({})
		return

	@api.multi
	def refresh_data(self):
		self.write({})
		self.with_context({'active_id':self.env.context['active_id']}).onchange_all()
		return {
			'type': 'ir.actions.act_window',
			'name': "Detalle Tareo",
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.tareo.line',
			'res_id': self.env.context['active_id'],
			'target': 'new',
			'context': {'default_dias_trabajador': 30},
		}

	@api.one
	def unlink(self):
		empl      = self.env['hr.employee'].search([('identification_id','=',self.dni)])
		conceptos = self.env['hr.concepto.line'].search([('tareo_line_id','=',self.id)])
		mes_vaca  = self.env['hr.resumen.provisiones'].search([('tareo_line_id','=',self.id)])
		elems     = self.env['hr.tareo.concepto'].search([('tareo_id','=',self.tareo_id.id),('employee_id','=',empl.id)])
		for con in conceptos:
			con.unlink()
		for res in mes_vaca:
			res.unlink()
		elems.unlink()
		return super(hr_tareo_line,self).unlink()
class hr_tareo(models.Model):
	_name = 'hr.tareo'
	
	periodo        = fields.Many2one('account.period', 'Tareo')
	detalle        = fields.One2many('hr.tareo.line', 'tareo_id','lineas')
	asiento        = fields.Many2one('account.move', 'Asiento Contable')
	d_asiento      = fields.Many2one('account.move', 'Asiento Distribuido')
	fecha_deposito = fields.Date(u'Fecha dep??sito')
	state          = fields.Selection([('close','Cerrado'),('open','Abierto')],default='open')
	calendary_days = fields.Integer(u'D??as Calendario', compute="compute_calendary_days")
	sundays        = fields.Integer(u'Feriados y Domingos')
	sunat_hours    = fields.Integer('Horas SUNAT', compute="compute_sunat_hours")
	
	detallev  = fields.One2many('hr.tareo.concepto', 'tareo_id','Detalle vertical')
	deta_cant = fields.Float('Nro. Trabajadores',compute='cuenta_trab',store=False)


	_rec_name = 'periodo'
	conceptoact = ''
	trabajador_act = ''

	@api.one
	def compute_calendary_days(self):
		if self.periodo.id:
			ye = int(self.periodo.code.split("/")[1])
			mo = int(self.periodo.code.split("/")[0])
			self.calendary_days = monthrange(ye, mo)[1]

	@api.one
	def compute_sunat_hours(self):
		if self.periodo.id:
			self.sunat_hours = (self.calendary_days - self.sundays) * 8

	@api.one
	def unlink(self):
		for con in self.detalle:
			con.unlink()
		return super(hr_tareo,self).unlink()
	
	@api.one
	def cuenta_trab(self):
		n = 0
		for linea in self.detalle:
			n=n+1
		self.deta_cant = n

	@api.one
	def close_tareo(self):
		for deta in self.detalle:
			empl=self.env['hr.employee'].search([('identification_id','=',deta.dni)])
			prestamosheader=self.env['hr.prestamo.header'].search([('employee_id','=',empl.id)])
			if len(prestamosheader)>0:
				for deta in prestamosheader.prestamo_lines_ids:
					if deta.validacion=='2':
						aperioddate=deta.fecha_pago.split('-')
						if aperioddate[1]+'/'+aperioddate[0]==self.periodo.code:
							deta.validacion='1'
		self.state='close'


	@api.one
	def open_tareo(self):
		for deta in self.detalle:
			empl=self.env['hr.employee'].search([('identification_id','=',deta.dni)])
			prestamosheader=self.env['hr.prestamo.header'].search([('employee_id','=',empl.id)])
			if len(prestamosheader)>0:
				for deta in prestamosheader.prestamo_lines_ids:
					if deta.validacion=='1':
						aperioddate=deta.fecha_pago.split('-')
						if aperioddate[1]+'/'+aperioddate[0]==self.periodo.code:
							deta.validacion='2'
		self.state='open'

	def add_dict(self,dtotales,lstkeys,valor,cuenta,debe_l):
		if cuenta and valor:
			nombre = cuenta.code+" - "+cuenta.name
			cuenta_id = cuenta.id
			debe =0
			haber =0

			if debe_l:
				debe = valor
			else:
				haber = valor
			debe=float(decimal.Decimal(str(debe)).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
			haber=float(decimal.Decimal(str(haber)).quantize(decimal.Decimal('1.11'),rounding=decimal.ROUND_HALF_UP))
			if cuenta_id not in lstkeys:
				d1 = {
					'cuenta':nombre,
					'account_id':cuenta_id,
					'debit': debe,
					'credit': haber,
				}
				dtotales.update({cuenta_id:d1})
				lstkeys.append(cuenta_id)
			else:
				dtotales[cuenta_id]['debit']=dtotales[cuenta_id]['debit']+debe
				dtotales[cuenta_id]['credit']=dtotales[cuenta_id]['credit']+haber				
		return dtotales

	@api.one
	def actualizar_resumen_todo(self):
		for i in self.detalle:
			i.with_context({'active_id':i.id}).actualizar_resumen()
		
	@api.one
	def recalcular(self,period_pla):
		for line in self.detalle:
			line.with_context({'active_id':line.id}).onchange_all()	

	@api.one
	def make_account_move2(self,period_pla):
		if self.asiento:
			self.env.cr.execute("""
				ALTER TABLE account_move_line DISABLE TRIGGER ALL;
				ALTER TABLE account_move DISABLE TRIGGER ALL;
				delete from account_move_line where move_id = """+str(self.asiento.id)+""";
				delete from account_move where id = """+str(self.asiento.id)+""";
				ALTER TABLE account_move_line ENABLE TRIGGER ALL;
				ALTER TABLE account_move ENABLE TRIGGER ALL;
			""")
		self.asiento = False

		aj = self.env['account.journal'].search([('code','=','11')])
		if len(aj) == 0:
			raise osv.except_osv("Alerta!", u"No existe el diario PLANILLA")

		name = ""
		asf = self.env['account.sequence.fiscalyear'].search([('sequence_main_id','=',aj[0].sequence_id.id),('period_id','=',self.periodo.id)]) 
		name = 'Planilla '+self.periodo.code
		if len(asf):
			name = self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, asf[0].sequence_id.id, self.env.context)

		self.env.cr.execute(""" 
			INSERT INTO account_move(period_id,partner_id,date,name,state,journal_id,ref,company_id,ple_diariomayor) 
			select """+str(self.periodo.id)+""",null,'"""+str(self.periodo.date_stop)+"""'::date,'"""+name+"""','posted', """+str(aj[0].id)+""",'tareo_"""+str(self.periodo.code)+"-"+str(aj[0].name)+"""',1,'1';		
		""")


		cadsql = """ 
			INSERT INTO account_move_line(name,account_id,debit,credit,analytic_account_id,journal_id,period_id,date,company_id,state, move_id)

			select d.name, d.cuenta, d.debe, d.haber, d.cta_an, """+str(aj[0].id)+""" as journai_id, """+str(self.periodo.id)+""" as period_id, '"""+str(self.periodo.date_stop)+"""' as date, d.company_id, d.state, am.id from(
			select * from(
			-- parte 1 del debe  
			select 'Asiento planilla' as name, cta_debe as cuenta,debe,0 as haber,cta_an,1 as company_id,'valid' as state from (
			select cta_debe,cta_an,sum(debe)as debe from
			(
			select 
			htl.employee_id as employee_id,
			htl.dni as dni,
			htl.nombre || ' ' || htl.apellido_paterno || ' ' || htl.apellido_materno as nombre,
			ap.code as periodo,
			hcl.concepto_id as concepto_id,
			hlc.name as nombre_concepto,
			aa_d.id as cta_debe,
			--aa_h.code || ' ' || aa_h.name as cta_haber,
			hcl.monto as monto,
			a4.id::integer as cta_an,
			--a3.porcentaje,
			case when a4.code is not null then hcl.monto*(a3.porcentaje/100) else hcl.monto end as debe
			from hr_tareo ht
			left join account_period ap on ht.periodo = ap.id
			left join hr_tareo_line htl on htl.tareo_id = ht.id
			left join hr_concepto_line hcl on hcl.tareo_line_id = htl.id
			left join hr_lista_conceptos hlc on hcl.concepto_id = hlc.id
			left join account_account aa_d on hlc.account_debe_id = aa_d.id
			left join account_account aa_h on hlc.account_haber_id = aa_h.id
			left join hr_employee a1 on a1.id=htl.employee_id 
			left join hr_distribucion_gastos a2 on a2.id=a1.dist_c
			left join hr_distribucion_gastos_linea a3 on a3.distribucion_gastos_id=a2.id
			left join account_analytic_account a4 on a4.id=a3.analitica 
			where monto<>0 and aa_d.code is not null and ap.id="""+str(self.periodo.id)+""" and left(aa_d.code,2)='62' 
			union all
			select 
			htl.employee_id as employee_id,
			htl.dni as dni,
			htl.nombre || ' ' || htl.apellido_paterno || ' ' || htl.apellido_materno as nombre,
			ap.code as periodo,
			hcl.concepto_id as concepto_id,
			hlc.name as nombre_concepto,
			aa_h.id as cta_debe,
			hcl.monto as monto,
			a4.id::integer as cta_an,
			--a3.porcentaje,
			case when a4.code is not null then hcl.monto*(a3.porcentaje/100) else hcl.monto end*-1 as debe
			from hr_tareo ht
			left join account_period ap on ht.periodo = ap.id
			left join hr_tareo_line htl on htl.tareo_id = ht.id
			left join hr_concepto_line hcl on hcl.tareo_line_id = htl.id
			left join hr_lista_conceptos hlc on hcl.concepto_id = hlc.id
			left join account_account aa_d on hlc.account_debe_id = aa_d.id
			left join account_account aa_h on hlc.account_haber_id = aa_h.id
			left join hr_employee a1 on a1.id=htl.employee_id 
			left join hr_distribucion_gastos a2 on a2.id=a1.dist_c
			left join hr_distribucion_gastos_linea a3 on a3.distribucion_gastos_id=a2.id
			left join account_analytic_account a4 on a4.id=a3.analitica 
			where monto<>0 and aa_h.code is not null and ap.id="""+str(self.periodo.id)+""" and (hlc.code in ('024','025','026','027','102','105'))
			) tt
			group by cta_debe,cta_an
			order by cta_debe)tt
			union all
			--- parte 2 del debe 

			select 'Asiento planilla' as name,cta_debe as cuenta ,debe,0 as haber,null::integer cta_an,1 as company_id,'valid' as state  from (
			select cta_debe,sum(debe)as debe from
			(
			select 
			htl.employee_id as employee_id,
			htl.dni as dni,
			htl.nombre || ' ' || htl.apellido_paterno || ' ' || htl.apellido_materno as nombre,
			ap.code as periodo,
			hcl.concepto_id as concepto_id,
			hlc.name as nombre_concepto,
			aa_d.id as cta_debe,
			--aa_h.code || ' ' || aa_h.name as cta_haber,
			hcl.monto as monto,
			hcl.monto as debe
			from hr_tareo ht
			left join account_period ap on ht.periodo = ap.id
			left join hr_tareo_line htl on htl.tareo_id = ht.id
			left join hr_concepto_line hcl on hcl.tareo_line_id = htl.id
			left join hr_lista_conceptos hlc on hcl.concepto_id = hlc.id
			left join account_account aa_d on hlc.account_debe_id = aa_d.id
			left join account_account aa_h on hlc.account_haber_id = aa_h.id
			left join hr_employee a1 on a1.id=htl.employee_id 
			where monto<>0 and aa_d.code is not null and ap.id="""+str(self.periodo.id)+""" and left(aa_d.code,2)<>'62'
			order by ht.periodo, htl.apellido_paterno, hlc.name,aa_d.code) tt
			group by cta_debe
			order by cta_debe)tt

			-- parte 3 haber 

			union all

			select 'Asiento planilla' as name,cuenta,debe,haber,null::integer as cta_an,1 as company_id,'valid' as state from ( 
			select cta_haber as cuenta,sum(debe) as debe,sum(haber) as haber from (
			select 
			htl.employee_id as employee_id,
			htl.dni as dni,
			htl.nombre || ' ' || htl.apellido_paterno || ' ' || htl.apellido_materno as nombre,
			ap.code as periodo,
			hcl.concepto_id as concepto_id,
			hlc.name as nombre_concepto,
			aa_d.id as cta_debe,
			aa_h.id as cta_haber,
			hcl.monto as haber,
			0 as debe
			from hr_tareo ht
			left join account_period ap on ht.periodo = ap.id
			left join hr_tareo_line htl on htl.tareo_id = ht.id
			left join hr_concepto_line hcl on hcl.tareo_line_id = htl.id
			left join hr_lista_conceptos hlc on hcl.concepto_id = hlc.id
			left join account_account aa_d on hlc.account_debe_id = aa_d.id
			left join account_account aa_h on hlc.account_haber_id = aa_h.id
			where monto<>0 and aa_h.code is not null and ap.id="""+str(self.periodo.id)+"""  and (hlc.code not in ('024','025','026','027','102','105')) 
			order by ht.periodo, htl.apellido_paterno, hlc.name) tt
			 group by cta_haber)tt) c) d
			inner join account_move am on am.ref = 'tareo_"""+str(self.periodo.code)+"-"+str(aj[0].name)+"""';
		"""

		# raise osv.except_osv("Alerta!", cadsql)
		self.env.cr.execute(cadsql)

		self.env.cr.execute("""
			update hr_tareo set asiento = (select id from account_move where ref = 'tareo_"""+str(self.periodo.code)+"-"+str(aj[0].name)+"""') where id = """+str(self.id)+"""
		""")
		
	@api.one
	def make_account_move2_asiento2(self,period_pla):
		# hlc = self.env['hr.lista.conceptos'].search([('account_debe_id','=',False),('account_haber_id','=',False)])
		# if len(hlc) > 0:
		# 	raise osv.except_osv("Alerta!", u"Todos los conceptos deben tener una cuenta debe o haber.")

		dis_d_dict = {}
		dis_h_dict = {}

		error_msg = ""

		for line in self.detalle:
			#PARA LA COLUMNA DEBE DEL ASIENTO CONTABLE
			hlc_d = self.env['hr.lista.conceptos'].search([('account_debe_id','!=',False)])
			hcl_d = self.env['hr.concepto.line'].search([('tareo_line_id','=',line.id),('concepto_id','in',hlc_d.ids)])
			for con in hcl_d:
				#ASIENTO DISTRIBUIDO
				for analytic in line.employee_id.dist_c.distribucion_lines:
					if analytic.analitica.account_account_moorage_id.id:
						if analytic.analitica.account_account_moorage_id.id not in dis_d_dict:
							if con.concepto_id.payroll_group in ['1','4']:
								dis_d_dict[analytic.analitica.account_account_moorage_id.id] = con.monto*analytic.porcentaje/100.00
							elif con.concepto_id.payroll_group == '2':
								dis_d_dict[analytic.analitica.account_account_moorage_id.id] = con.monto*analytic.porcentaje/100.00*-1
						else:
							if con.concepto_id.payroll_group in ['1','4']:
								dis_d_dict[analytic.analitica.account_account_moorage_id.id] += con.monto*analytic.porcentaje/100.00
							elif con.concepto_id.payroll_group == '2':
								dis_d_dict[analytic.analitica.account_account_moorage_id.id] -= con.monto*analytic.porcentaje/100.00*-1
					else:
						error_msg += (analytic.analitica.name if analytic.analitica.name else '') + "->" + con.concepto_id.name + "\n"
			#PARA LA COLUMNA HABER DEL ASIENTO CONTABLE
			hlc_h = self.env['hr.lista.conceptos'].search([('account_debe_id','!=',False)])
			hcl_h = self.env['hr.concepto.line'].search([('tareo_line_id','=',line.id),('concepto_id','in',hlc_h.ids)])
			ad_hcl_h = self.env['hr.concepto.line'].search([('tareo_line_id','=',line.id),('concepto_id.code','in',['045'])])
			pr_hcl_h = self.env['hr.concepto.line'].search([('tareo_line_id','=',line.id),('concepto_id.code','in',['046'])])
			c_hcl_h = self.env['hr.concepto.line'].search([('tareo_line_id','=',line.id),('concepto_id.code','in',['028','029','030','031'])])
			# for con in pr_hcl_h:
			# 	#ASIENTO CONTABLE
			# 	#CONDICION ESPECIAL PARA PRESTAMOS
			# 	hpl = self.env['hr.prestamo.lines'].search([('fecha_pago','>=',line.tareo_id.periodo.date_start),('fecha_pago','<=',line.tareo_id.periodo.date_stop),('prestamo_id.employee_id','=',line.employee_id.id),('validacion','=','2')])
			# 	for pr_line in hpl:
			# 		if pr_line.prestamo_id.prestamo_id.account_id.id:
			# 			if pr_line.prestamo_id.prestamo_id.account_id.id not in dis_h_dict:
			# 				dis_h_dict[pr_line.prestamo_id.prestamo_id.account_id.id] = pr_line.monto
			# 			else:
			# 				dis_h_dict[pr_line.prestamo_id.prestamo_id.account_id.id] += pr_line.monto
			# for con in ad_hcl_h:
			# 	#ASIENTO CONTABLE
			# 	#CONDICION ESPECIAL PARA ADELANTOS
			# 	hta = self.env['hr.adelanto'].search([('fecha','>=',line.tareo_id.periodo.date_start),('fecha','<=',line.tareo_id.periodo.date_stop),('employee','=',line.employee_id.id)])
			# 	for adelanto in hta:
			# 		if adelanto.adelanto_id.account_id.id:
			# 			if adelanto.adelanto_id.account_id.id not in dis_h_dict:
			# 				dis_h_dict[adelanto.adelanto_id.account_id.id] = adelanto.monto
			# 			else:
			# 				dis_h_dict[adelanto.adelanto_id.account_id.id] += adelanto.monto
			# for con in c_hcl_h:
			# 	#ASIENTO CONTABLE 
			# 	#CONDICION ESPECIAL PARA AFILIACIONES
			# 	htm = self.env['hr.table.membership'].search([('id','=',line.employee_id.afiliacion.id)])
			# 	if len(htm) > 0:
			# 		htm = htm[0]
			# 		if htm.account_id.id:
			# 			if htm.account_id.id not in dis_h_dict:
			# 				dis_h_dict[htm.account_id.id] = con.monto
			# 			else:
			# 				dis_h_dict[htm.account_id.id] += con.monto

			for con in hcl_h:
				#ASIENTO DISTRIBUIDO
				for analytic in line.employee_id.dist_c.distribucion_lines:
					if analytic.analitica.account_account_moorage_credit_id.id:
						if analytic.analitica.account_account_moorage_credit_id.id not in dis_h_dict:
							if con.concepto_id.payroll_group in ['1','4']:
								dis_h_dict[analytic.analitica.account_account_moorage_credit_id.id] = con.monto*analytic.porcentaje/100.00
							elif con.concepto_id.payroll_group == '2':
								dis_h_dict[analytic.analitica.account_account_moorage_credit_id.id] = con.monto*analytic.porcentaje/100.00*-1
						else:
							if con.concepto_id.payroll_group in ['1','4']:
								dis_h_dict[analytic.analitica.account_account_moorage_credit_id.id] += con.monto*analytic.porcentaje/100.00
							elif con.concepto_id.payroll_group == '2':
								dis_h_dict[analytic.analitica.account_account_moorage_credit_id.id] -= con.monto*analytic.porcentaje/100.00*-1
					else:
						error_msg += (analytic.analitica.name if analytic.analitica.name else '') + "->" + con.concepto_id.name + "\n"

		if len(error_msg) > 0:
				raise osv.except_osv("Alerta!", u"No existen las cuentas debe y/o haber en las siguientes cuentas anal??ticas:\n         Cta. Anal??tica -> Concepto\n"+error_msg)

		aj = self.env['account.journal'].search([('code','=','11')])
		if len(aj) == 0:
			raise osv.except_osv("Alerta!", u"No existe el diario PLANILLA")

		error_cuentas_opcional = ""
		error_numeros_negativo = ""
		error_tipo_cuenta      = ""
		for k,v in dis_d_dict.items():
			aa = self.env['account.account'].search([('id','=',k)])[0]
			if aa.user_type.analytic_policy != 'optional':
				error_cuentas_opcional += aa.code + " " + aa.name + " / " + aa.user_type.name + "\n"
			if v < 0:
				error_numeros_negativo += aa.code + " " + aa.name + " / " + str(v) + "\n"
			if aa.type == 'view':
				error_tipo_cuenta += aa.code + " " + aa.name + "\n"
		if len(error_cuentas_opcional):
			raise osv.except_osv("Alerta!", u"Las siguientes cuentas no tienen el tipo contable 'opcional'.\n"+error_cuentas_opcional)
		if len(error_numeros_negativo):
			raise osv.except_osv("Alerta!", u"Las siguientes cuentas tienen debe negativo.\n"+error_numeros_negativo)
		if len(error_tipo_cuenta):
			raise osv.except_osv("Alerta!", u"Las siguientes cuentas son de tipo vista.\n"+error_tipo_cuenta)

		error_cuentas_opcional = ""
		error_numeros_negativo = ""
		error_tipo_cuenta      = ""
		for k,v in dis_h_dict.items():
			aa = self.env['account.account'].search([('id','=',k)])[0]
			if aa.user_type.analytic_policy != 'optional':
				error_cuentas_opcional += aa.code + " " + aa.name + " / " + aa.user_type.name + "\n"
			if v < 0:
				error_numeros_negativo += aa.code + " " + aa.name + " / " + str(v) + "\n"
			if aa.type == 'view':
				error_tipo_cuenta += aa.code + " " + aa.name + "\n"
		if len(error_cuentas_opcional):
			raise osv.except_osv("Alerta!", u"Las siguientes cuentas no tienen el tipo contable 'opcional'.\n"+error_cuentas_opcional)
		if len(error_numeros_negativo):
			raise osv.except_osv("Alerta!", u"Las siguientes cuentas tienen debe negativo.\n"+error_numeros_negativo)
		if len(error_tipo_cuenta):
			raise osv.except_osv("Alerta!", u"Las siguientes cuentas son de tipo vista.\n"+error_tipo_cuenta)

		#ASIENTO DISTRIBUIDO
		if not self.d_asiento.id:
			n_vals = {
				'journal_id': aj[0].id,
				'period_id' : self.periodo.id,
				'date'      : self.periodo.date_stop,
				'name'      : 'Planilla '+self.periodo.code,
			}
			n_am = self.env['account.move'].create(n_vals)

			for k,v in dis_d_dict.items():
				nl_vals = {
					'move_id'   : n_am.id,
					'account_id': k,
					'debit'     : float(decimal.Decimal(str( v )).quantize(decimal.Decimal('1.111111'),rounding=decimal.ROUND_HALF_UP)),
					'credit'    : 0,
					'name'      : 'Planilla '+self.periodo.code,
				}
				n_aml = self.env['account.move.line'].create(nl_vals)

			for k,v in dis_h_dict.items():
				nl_vals = {
					'move_id'   : n_am.id,
					'account_id': k,
					'debit'     : 0,
					'credit'    : float(decimal.Decimal(str( v )).quantize(decimal.Decimal('1.111111'),rounding=decimal.ROUND_HALF_UP)),
					'name'      : 'Planilla '+self.periodo.code,
				}
				n_aml = self.env['account.move.line'].create(nl_vals)

			self.d_asiento = n_am.id

		else:
			n_vals = {
				'journal_id': aj[0].id,
				'period_id' : self.periodo.id,
				'date'      : self.periodo.date_stop,
				'name'      : 'Planilla '+self.periodo.code,
			}
			self.asiento.write(n_vals)

			for line in self.d_asiento.line_id:
				line.unlink()

			for k,v in dis_d_dict.items():
				nl_vals = {
					'move_id'   : self.d_asiento.id,
					'account_id': k,
					'debit'     : float(decimal.Decimal(str( v )).quantize(decimal.Decimal('1.111111'),rounding=decimal.ROUND_HALF_UP)),
					'credit'    : 0,
					'name'      : 'Planilla '+self.periodo.code,
				}
				n_aml = self.env['account.move.line'].create(nl_vals)

			for k,v in dis_h_dict.items():
				nl_vals = {
					'move_id'   : self.d_asiento.id,
					'account_id': k,
					'debit'     : 0,
					'credit'    : float(decimal.Decimal(str( v )).quantize(decimal.Decimal('1.111111'),rounding=decimal.ROUND_HALF_UP)),
					'name'      : 'Planilla '+self.periodo.code,
				}
				n_aml = self.env['account.move.line'].create(nl_vals)

	@api.multi
	def make_plame(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		rc        = self.env['res.company'].search([])[0]
		hlc       = self.env['hr.lista.conceptos'].search([('sunat_code','!=',False)]).sorted(key=lambda r: r.position)
		title     = "0601" + self.periodo.code.split("/")[1] + self.periodo.code.split("/")[0] + rc.partner_id.type_number + ".rem"

		conceptos_puestos = []
		f = open(direccion + title, 'w')
		txt = ""
		for concepto in hlc:
			for line in self.detalle:
				if not line.employee_id.is_practicant:
					if concepto.sunat_code not in conceptos_puestos:
						txt += (line.employee_id.type_document_id.code if line.employee_id.type_document_id.code else '') + "|"
						txt += (line.employee_id.identification_id if line.employee_id.identification_id else '') + "|"
						hcl = self.env['hr.concepto.line'].search([('tareo_line_id','=',line.id),('concepto_id.sunat_code','=',concepto.sunat_code)])
						if len(hcl) == 0:
							txt += ("|"*3)+"\n"
						else:
							res = 0
							for con in hcl:
								res += con.monto
							txt += (concepto.sunat_code) + "|" + (str(round(res,2)) if res != 0 else "0.00") + "|" + (str(round(res,2)) if res != 0 else "0.00") + "|"
							txt += "\r\n"
			conceptos_puestos.append(concepto.sunat_code)

		f.write(txt)
		f.close

		f = open(direccion + title, 'rb')
		vals = {
			'output_name': title,
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type"     : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"    : [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
		}

	@api.multi
	def make_plame_practicante(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		rc        = self.env['res.company'].search([])[0]
		title     = "0601" + self.periodo.code.split("/")[1] + self.periodo.code.split("/")[0] + rc.partner_id.type_number + ".for"

		f = open(direccion + title, 'w')
		txt = ""
		for line in self.detalle:
			if line.employee_id.is_practicant:
				txt += (line.employee_id.type_document_id.code if line.employee_id.type_document_id.code else '') + "|"
				txt += (line.employee_id.identification_id if line.employee_id.identification_id else '') + "|"
				hcl = self.env['hr.concepto.line'].search([('tareo_line_id','=',line.id),('concepto_id.code','=','012')])
				if len(hcl) == 0:
					txt += ("|")+"\n"
				else:
					res = 0
					for con in hcl:
						res += con.monto
					txt += (str(round(res,2)) if res != 0 else "0.00") + "|"
					txt += "\r\n"
		f.write(txt)
		f.close

		f = open(direccion + title, 'rb')
		vals = {
			'output_name': title,
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type"     : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"    : [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
		}

	@api.multi
	def make_plame_hours(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		rc        = self.env['res.company'].search([])[0]
		title     = "0601" + self.periodo.code.split("/")[1] + self.periodo.code.split("/")[0] + rc.partner_id.type_number + ".jor"

		f = open(direccion + title, 'w')
		txt = ""
		for line in self.detalle:
			txt += (line.employee_id.type_document_id.code if line.employee_id.type_document_id.code else '') + "|"
			txt += (line.employee_id.identification_id if line.employee_id.identification_id else '') + "|"
			# txt += str(int(line.horas_ordinarias_trabajadas)) + "|"
			# dec = (int(str(line.horas_ordinarias_trabajadas).split(".")[1])*60)-(int(str(line.tardanza_horas).split(".")[1]))
			# txt += str(dec) + "|"
			x=frmt(line.horas_ordinarias_trabajadas-line.tardanza_horas)
			
			horas = x.split(':')[0] 
			minutos = int(x.split(':')[1] )
			if int(x.split(':')[2])>30:
				minutos = minutos+1
			minutos = str(minutos)
			

			txt = txt +horas+'|'+minutos+'|'
			

			res = 0
			res += line.horas_extra_diurna
			res += line.horas_extra_nocturna
			res += line.horas_extra_descanso
			res += line.horas_extra_feriado_diur
			res += line.horas_extra_feriado_noct
			res += line.horas_extra_feriado
			res += line.horas_extra_descanso_diurnas
			res += line.horas_extra_descanso_nocturnas


			x=frmt(res)

			horas = x.split(':')[0] 
			minutos = int(x.split(':')[1] )
			if int(x.split(':')[2])>30:
				minutos = minutos+1
			minutos = str(minutos)


			res = str(res).split(".")
			txt += horas + "|"
			txt += minutos + "|"

			txt += "\r\n"

		f.write(txt)
		f.close

		f = open(direccion + title, 'rb')
		vals = {
			'output_name': title,
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type"     : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"    : [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
		}

	@api.multi
	def open_email_boleta_wizard(self):
		view_id = self.env.ref('hr_nomina_it.view_boleta_empleado_wizard_form',False)
		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'boleta.empleado.wizard',
			# 'res_id'   : self.id,
			'view_id'  : view_id.id,
			'view_type': 'form',
			'view_mode': 'form',
			'views'    : [(view_id.id, 'form')],
			'target'   : 'new',
			#'flags'    : {'form': {'action_buttons': True}},
			'context'  : {'employees' : [line.employee_id.id for line in self.detalle],
						  'comes_from': 'generar_email',},
		}
	
	@api.multi
	def make_email(self, htl_id, digital_sgn):
		if not hasattr(htl_id, '__iter__'):
			htl_id = [htl_id]

		to_send = []
		error_msg = ""
		for tareo_line in self.env['hr.tareo.line'].search([('id','in',htl_id)]):
			em_pdf = self.make_pdf(tareo_line.id, digital_sgn)
			if 'title_pdf' in em_pdf:
				f   = open(em_pdf['title_pdf'],'rb')
				em  = tareo_line.employee_id.work_email if tareo_line.employee_id.work_email else False
				if not em:
					error_msg += tareo_line.employee_id.name_related + "\n"
				txt = u"""
					<h2>Boleta de Pago</h2>
					<p>-------------------------------------------------</p>
				"""
				att = {
					'name'       : u"Boleta "+tareo_line.employee_id.name_related+".pdf",
					'type'       : 'binary',
					'datas'      : base64.encodestring(''.join(f.readlines())),
					'datas_fname': u"Boleta "+tareo_line.employee_id.name_related+".pdf",
				}
				att_id = self.pool.get('ir.attachment').create(self.env.cr,self.env.uid,att,self.env.context)

				values                   = {}
				values['subject']        = u"Boleta "+tareo_line.employee_id.name_related
				values['email_to']       = em
				values['body_html']      = txt
				values['res_id']         = False
				values['attachment_ids'] = [(6,0,[att_id])]

				to_send.append(values)

		if len(error_msg):
			raise osv.except_osv("Alerta!", u"Todos los empleados deben tener un email asignado\n"+error_msg)

		for item in to_send:
			msg_id = self.env['mail.mail'].create(item)
			if msg_id:
				msg_id.send()

	@api.multi
	def open_boleta_empleado_wizard(self):
		view_id = self.env.ref('hr_nomina_it.view_boleta_empleado_wizard_form',False)
		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'boleta.empleado.wizard',
			# 'res_id'   : self.id,
			'view_id'  : view_id.id,
			'view_type': 'form',
			'view_mode': 'form',
			'views'    : [(view_id.id, 'form')],
			'target'   : 'new',
			#'flags'    : {'form': {'action_buttons': True}},
			'context'  : {'employees' : [line.employee_id.id for line in self.detalle],
						  'comes_from': 'generar_pdf',},
		}

	@api.multi
	def make_pdf(self, htl_id, digital_sgn):
		d= False
		import sys	
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = width
		hReal = height - 40
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		doc = BaseDocTemplate(direccion+"reporte_boletas.pdf", pagesize=A4,bottomMargin=0.5*cm, topMargin=0.5*cm, rightMargin=0.5*cm, leftMargin=0.5*cm)
		column_gap = 0 * cm

		pdfmetrics.registerFont(TTFont('Arimo-Bold', 'Arimo-Bold.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-BoldItalic', 'Arimo-BoldItalic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Italic', 'Arimo-Italic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Regular', 'Arimo-Regular.ttf'))

		if not hasattr(htl_id, '__iter__'):
			htl_id = [htl_id]

		IDGS = False
		if digital_sgn:
			fim = open(direccion+'tmp.png','wb')
			fim.write(digital_sgn.decode('base64'))
			fim.close()
			IDGS = Image(direccion+'tmp.png')
			IDGS.drawHeight = 40
			IDGS.drawWidth = 120

		elements=[]
		for tareo_line in self.env['hr.tareo.line'].search([('id','in',htl_id)]).sorted(key=lambda r: r.employee_id.codigo_trabajador):

			doc.addPageTemplates(
			[
				PageTemplate(
					frames=[
						Frame(
							doc.leftMargin,
							doc.bottomMargin,
							doc.width,
							doc.height,
							id = None
						),
						]
					),
				]
			)
			
			colorfondo = colors.lightblue
			elements.append(platypus.flowables.Macro('canvas.saveState()'))
			elements.append(platypus.flowables.Macro('canvas.restoreState()'))

			styles = getSampleStyleSheet()
			styleN = styles["Normal"]
			styleN.leading = 12
			styleN.alignment = 4

			empl       = self.env['hr.employee'].search([('id','=',tareo_line.employee_id.id)])
			tdoc       = empl.type_document_id.code
			company    = self.env['res.users'].browse(self.env.uid).company_id

			dtm = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayp', 6:'Junio', 7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}

			td = self.periodo.code.split('/')
			rc = self.env['res.company'].search([])[0]

			I = ''
			if rc.logo:
				fim = open(direccion+'tmp.png','wb')
				fim.write(rc.logo.decode('base64'))
				fim.close()
				I            = Image(direccion+"tmp.png")
				I.drawHeight = 35
				I.drawWidth  = 150

			data   = []
			estilo = []

			estilo.append(('VALIGN',(0,0),(-1,-1),'MIDDLE'))
			estilo.append(('ALIGN',(0,0),(-1,-1),'CENTER'))
			estilo.append(('FONTSIZE', (0, 0), (-1, -1), 6))
			estilo.append(('FONT', (0, 0), (-1,-1),'Arimo-Regular'))

			data.append([I,'','','',u'Boleta de Pago de Remuneraciones','','',u'N??',tareo_line.employee_id.codigo_trabajador if tareo_line.employee_id.codigo_trabajador else ''])
			data.append(['','','','',dtm[int(td[0])]+" "+td[1],'','','RUC: '+rc.partner_id.type_number,''])
			data.append(['','','','',u'Art. 18/D.S. N?? 001-98-TR; D.S. N?? 017-2001-TR','','',Paragraph("<font size=6>"+rc.street.capitalize().replace('arequipa','Arequipa')+"</font>",styleN),''])
			estilo.append(('SPAN',(0,0),(3,2)))
			estilo.append(('SPAN',(4,0),(6,0)))
			estilo.append(('SPAN',(4,1),(6,1)))
			estilo.append(('SPAN',(4,2),(6,2)))
			estilo.append(('SPAN',(7,1),(8,1)))
			estilo.append(('SPAN',(7,2),(8,2)))
			estilo.append(('FONT',(0,0),(8,2),'Arimo-Bold'))
			estilo.append(('ALIGN',(0,0),(0,0),'LEFT'))
			estilo.append(('ALIGN',(7,0),(7,0),'RIGHT'))
			estilo.append(('ALIGN',(8,0),(8,0),'LEFT'))
			estilo.append(('LINEABOVE',(0,0),(8,0),0.5,black))
			estilo.append(('LINEBELOW',(0,2),(8,2),0.5,black))
			estilo.append(('LINEBEFORE',(0,0),(0,2),0.5,black))
			estilo.append(('LINEAFTER',(8,0),(8,2),0.5,black))

			row_pos = 3
			data.append([u'Nombres y Apellidos:','',tareo_line.employee_id.name_related,'','','','',u'C??digo:',(tareo_line.employee_id.codigo_trabajador if tareo_line.employee_id.codigo_trabajador else '')])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(2,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(0,row_pos),(8,row_pos),'LEFT'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))
			row_pos += 1
			ff_ing = tareo_line.employee_id.fecha_ingreso.split('-')
			ff_ing = "-".join([ff_ing[2],ff_ing[1],ff_ing[0]])
			data.append([u'Categor??a:','',(tareo_line.employee_id.tipo_trabajador.name if tareo_line.employee_id.tipo_trabajador.name else ''),'',u'D??as Subsidiados por Enfermedad:','',str(tareo_line.num_days_subs if tareo_line.num_days_subs else '0'),u'Fecha de Ingreso:',(ff_ing if tareo_line.employee_id.fecha_ingreso else '')])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(2,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(0,row_pos),(8,row_pos),'LEFT'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))
			row_pos += 1
			data.append([u'Cargo u Ocupaci??n:','',(tareo_line.employee_id.job_id.name if tareo_line.employee_id.job_id.name else ''),'',u'D??as Subsidiados por Maternidad','',str(tareo_line.num_days_subs_mater if tareo_line.num_days_subs_mater else '0'),u'D??as Trabajados Efectivas:',str(tareo_line.dias_trabajador if tareo_line.dias_trabajador else '0')])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(2,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(0,row_pos),(8,row_pos),'LEFT'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))
			row_pos += 1
			data.append([u'DNI:','',(tareo_line.employee_id.identification_id if tareo_line.employee_id.identification_id else ''),'',u'Faltas Injustificadas o Suspenciones:','',str(tareo_line.dias_suspension_perfecta if tareo_line.dias_suspension_perfecta else '0'),u'Horas Ordinarias Trabajadas:',str('{:,.2f}'.format(decimal.Decimal("%0.2f" % tareo_line.horas_ordinarias_trabajadas )) if tareo_line.horas_ordinarias_trabajadas else '0')])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(2,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(0,row_pos),(8,row_pos),'LEFT'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))
			row_pos += 1
			all_he = tareo_line.horas_extra_diurna+tareo_line.horas_extra_nocturna+tareo_line.horas_extra_descanso+tareo_line.horas_extra_descanso_diurnas+tareo_line.horas_extra_descanso_nocturnas+tareo_line.horas_extra_feriado+tareo_line.horas_extra_feriado_diur+tareo_line.horas_extra_feriado_noct
			data.append([u'R??gimen Pensionario:','',(tareo_line.employee_id.afiliacion.name if tareo_line.employee_id.afiliacion.name else ''),'',
				u'D??as no Subsidiados o Permisos:','',str(tareo_line.num_days_not_subs if tareo_line.num_days_not_subs else '0'),
				u'Tardanzas:',str(tareo_line.tardanza_horas if tareo_line.tardanza_horas else '0')
				])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(2,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(0,row_pos),(8,row_pos),'LEFT'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))
			row_pos += 1
			data.append(['Lic. sin goce:','',(tareo_line.licencia_sin_goce if tareo_line.licencia_sin_goce else '0'),'',
				u'Vacaciones Inicio:','',(tareo_line.vacaciones_inicio if tareo_line.vacaciones_inicio else ''),
				u'Horas Extras:',str(all_he if all_he else '0')])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(2,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(0,row_pos),(8,row_pos),'LEFT'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))
			row_pos += 1
			data.append([u'CUPSS','',(tareo_line.employee_id.cusspp if tareo_line.employee_id.cusspp else ''),'',
				u'Vacaciones Retorno:','',(tareo_line.vacaciones_retorno if tareo_line.vacaciones_retorno else ''),
				u'D??as Feriados Trabajados',str(int(tareo_line.dias_feriados_trabajados) if tareo_line.dias_feriados_trabajados else '0')])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(2,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(0,row_pos),(8,row_pos),'LEFT'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))



			row_pos += 1
			data.append([u'','','','',
				u'Cese:','',str(tareo_line.employee_id.fecha_cese if tareo_line.employee_id.fecha_cese else ''),
				u'Domingos y Feriados:',str(self.sundays if self.sundays else '0')
				])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(2,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(0,row_pos),(8,row_pos),'LEFT'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))







			
			row_pos += 1
			data.append([u'Ingresos (S/.)','','','',u'Aportes del Empleador (S/.)','','',u'Aportes ?? Descuentos del Trabajador (S/.)',''])
			estilo.append(('SPAN',(0,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(6,row_pos)))
			estilo.append(('SPAN',(7,row_pos),(8,row_pos)))
			estilo.append(('FONT',(0,row_pos),(8,row_pos),'Arimo-Bold'))
			estilo.append(('GRID',(0,row_pos),(8,row_pos),0.5, black))
			row_pos += 1

			in_con_ids = [i.id for i in self.env['hr.lista.conceptos'].search([('payroll_group','=','1')])]
			ae_con_ids = [i.id for i in self.env['hr.lista.conceptos'].search([('payroll_group','=','4')])]
			at_con_ids = [i.id for i in self.env['hr.lista.conceptos'].search([('payroll_group','in',['2','3','5'])])]
			in_con = self.env['hr.concepto.line'].search([('concepto_id','in',in_con_ids),('tareo_line_id','=',tareo_line.id)])
			ae_con = self.env['hr.concepto.line'].search([('concepto_id','in',ae_con_ids),('tareo_line_id','=',tareo_line.id)])
			at_con = self.env['hr.concepto.line'].search([('concepto_id','in',at_con_ids),('tareo_line_id','=',tareo_line.id)])

			tot_in = 0
			tot_ae = 0
			tot_at = 0

			in_con_data = []
			ae_con_data = []
			at_con_data = []
			for i in in_con:
				if i.monto != 0 and i.concepto_id.check_boleta:
					in_con_data.append([i.concepto_id.name, '{:,.2f}'.format(decimal.Decimal("%0.2f" % i.monto ))])
					tot_in += i.monto
			for i in ae_con:
				if i.monto != 0 and i.concepto_id.check_boleta:
					ae_con_data.append([i.concepto_id.name, '{:,.2f}'.format(decimal.Decimal("%0.2f" % i.monto ))])
					tot_ae += i.monto
			for i in at_con:
				if i.monto != 0 and i.concepto_id.check_boleta:
					if i.concepto_id.code == '045':
						ha = self.env['hr.adelanto'].search([('employee','=',tareo_line.employee_id.id),('fecha','>=',self.periodo.date_start),('fecha','<=',self.periodo.date_stop)])
						adelantos_dict = {}
						for ad_line in ha:
							if ad_line.adelanto_id.id not in adelantos_dict:
								adelantos_dict[ad_line.adelanto_id.id] = ad_line.monto
							else:
								adelantos_dict[ad_line.adelanto_id.id] += ad_line.monto
						for k,v in adelantos_dict.items():
							at_con_data.append([self.env['hr.table.adelanto'].search([('id','=',k)])[0].name, v])
							tot_at += v
					elif i.concepto_id.code == '046':
						hpl = self.env['hr.prestamo.lines'].search([('prestamo_id.employee_id','=',tareo_line.employee_id.id),('fecha_pago','>=',self.periodo.date_start),('fecha_pago','<=',self.periodo.date_stop),('validacion','=','2')])
						prestamos_dict = {}
						for pr_line in hpl:
							if pr_line.prestamo_id.prestamo_id.id not in prestamos_dict:
								prestamos_dict[pr_line.prestamo_id.prestamo_id.id] = pr_line.monto
							else:
								prestamos_dict[pr_line.prestamo_id.prestamo_id.id] += pr_line.monto
						for k,v in prestamos_dict.items():
							at_con_data.append([self.env['hr.table.prestamo'].search([('id','=',k)])[0].name, v])
							tot_at += v
					else:
						at_con_data.append([i.concepto_id.name, '{:,.2f}'.format(decimal.Decimal("%0.2f" % i.monto ))])
						tot_at += i.monto

			max_size = max(len(in_con_data),len(ae_con_data),len(at_con_data))

			in_con_data += [['','']]*(max_size-len(in_con_data))
			ae_con_data += [['','']]*(max_size-len(ae_con_data))
			at_con_data += [['','']]*(max_size-len(at_con_data))

			all_data = zip(in_con_data,ae_con_data,at_con_data)
			for i in all_data:
				data.append([i[0][0],'','',i[0][1],i[1][0],'',i[1][1],i[2][0],i[2][1]])
				estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
				estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
				estilo.append(('ALIGN',(0,row_pos),(2,row_pos),'LEFT'))
				estilo.append(('ALIGN',(3,row_pos),(3,row_pos),'RIGHT'))
				estilo.append(('ALIGN',(4,row_pos),(5,row_pos),'LEFT'))
				estilo.append(('ALIGN',(6,row_pos),(6,row_pos),'RIGHT'))
				estilo.append(('ALIGN',(7,row_pos),(7,row_pos),'LEFT'))
				estilo.append(('ALIGN',(8,row_pos),(8,row_pos),'RIGHT'))
				estilo.append(('LINEBEFORE',(0,row_pos),(2,row_pos),0.5, black))
				estilo.append(('LINEAFTER',(3,row_pos),(3,row_pos),0.5, black))
				estilo.append(('LINEAFTER',(6,row_pos),(6,row_pos),0.5, black))
				estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5, black))
				row_pos += 1

			data.append([u'Total Ingresos:','','','{:,.2f}'.format(decimal.Decimal("%0.2f" % tot_in )),u'Total Aportes del Empleador:','','{:,.2f}'.format(decimal.Decimal("%0.2f" % tot_ae )),u'Total Descuentos:','{:,.2f}'.format(decimal.Decimal("%0.2f" % tot_at ))])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(3,row_pos),(3,row_pos),'RIGHT'))
			estilo.append(('ALIGN',(6,row_pos),(6,row_pos),'RIGHT'))
			estilo.append(('ALIGN',(8,row_pos),(8,row_pos),'RIGHT'))
			estilo.append(('FONT',(0,row_pos),(8,row_pos),'Arimo-Bold'))
			estilo.append(('GRID',(0,row_pos),(8,row_pos),0.5, black))
			row_pos += 1

			data.append(['','','','',u'Subsidio Alimentario:','','0.00',u'Neto a Pagar:','{:,.2f}'.format(decimal.Decimal("%0.2f" % (tot_in-tot_at) ))])
			estilo.append(('SPAN',(0,row_pos),(3,row_pos)))
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('ALIGN',(3,row_pos),(3,row_pos),'RIGHT'))
			estilo.append(('ALIGN',(6,row_pos),(6,row_pos),'RIGHT'))
			estilo.append(('ALIGN',(8,row_pos),(8,row_pos),'RIGHT'))
			estilo.append(('FONT',(7,row_pos),(8,row_pos),'Arimo-Bold'))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('GRID',(4,row_pos),(8,row_pos),0.5, black))
			row_pos += 1

			data.append(['','','','',IDGS if IDGS else '','','','',''])
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))
			row_pos += 1

			data.append([u'*Expresado en Soles','','','',u'P. el Empleador','','',tareo_line.employee_id.name_related,''])
			estilo.append(('SPAN',(4,row_pos),(5,row_pos)))
			estilo.append(('LINEABOVE',(4,row_pos),(5,row_pos),0.5,black))
			estilo.append(('LINEABOVE',(7,row_pos),(7,row_pos),0.5,black))
			estilo.append(('LINEBEFORE',(0,row_pos),(0,row_pos),0.5,black))
			estilo.append(('LINEAFTER',(8,row_pos),(8,row_pos),0.5,black))
			estilo.append(('LINEBELOW',(0,row_pos),(8,row_pos),0.5,black))
			row_pos += 1
			data.append(['','','','','','','','',''])
			row_pos += 1

			rowh = [10]*row_pos
			rowh[2] = 20
			rowh[-3] = 60
			t=Table(data, colWidths=[57,57,57,40,10,123,45,110,57],rowHeights=rowh,style=estilo)		
			elements.append(t)
			elements.append(Spacer(1,160-row_pos))
			elements.append(t)
			elements.append(PageBreak())
		doc.build(elements)


		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		import os
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		vals = {
			'output_name': 'Boletas.pdf',
			'output_file': open(direccion + "reporte_boletas.pdf", "rb").read().encode("base64"),	
		}
		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
			"title_pdf": direccion+"reporte_boletas.pdf",
			"only_file": "reporte_boletas.pdf",
		}

	@api.multi
	def resumen_pago(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo    = u'Resumen_pago_'+self.periodo.code.replace("/","")
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

		dts = {0:"lunes", 1:"martes", 2:"mi??rcoles", 3:"jueves", 4:"viernes", 5:"s??bado", 6:"domingo"}
		mts = {1:"enero", 2:"febrero", 3:"marzo", 4:"abril", 5:"mayo", 6:"junio", 7:"julio", 8:"agosto", 9:"septiembre", 10:"octubre", 11:"noviembre", 12:"diciembre"}

		rc = self.env['res.company'].search([])[0]
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', ("RUC: "+rc.partner_id.type_number) if rc.partner_id.type_number else 'RUC: ', title_format)
		
		row = 5
		worksheet.merge_range(row,0,row,6, 'Pago planilla '+mts[datetime.strptime(self.periodo.date_start,"%Y-%m-%d").month]+' '+self.periodo.fiscalyear_id.code, header_format)
		
		row += 1
		col = 0
		pago_headers = [u'', u'Fecha dep??sito', u'Trabajador', u'DNI', u'BCO', u'Cuenta', u'Total a depositar']
		for ph in pago_headers:
			worksheet.write(row, col, ph, header_w_format)
			col += 1

		row += 1
		item = 1
		for i in self.detalle:
			col = 0
			worksheet.write(row, col, item, numeric_int_format)
			col += 1
			worksheet.write(row, col, self.fecha_deposito if self.fecha_deposito else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.name_related if i.employee_id.name_related else '', basic_format)
			col += 1
			worksheet.write(row, col, i.dni if i.dni else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.banco_rem if i.employee_id.banco_rem else '', basic_format)
			col += 1
			worksheet.write(row, col, i.employee_id.cta_rem if i.employee_id.cta_rem else '', basic_format)
			col += 1
			worksheet.write(row, col, sum([np.monto for np in i.conceptos_detalle_neto_lines]), numeric_format)
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
	def extraer_datos(self):
		# existentes = []
		for line in self.detalle:
			# existentes.append(line.codigo_trabajador)
			line.unlink()

		he = self.env['hr.employee'].search( [('fecha_ingreso','<=',self.periodo.date_stop), '|',('fecha_cese','>=',self.periodo.date_start),('fecha_cese','=',False)] )
		for i in he:
			# if i.codigo_trabajador in existentes:
			# 	continue
			monto_grati          = 0
			monto_grati_real     = 0
			monto_boni_grati     = 0
			monto_cts            = 0
			monto_5category      = 0
			vacaciones           = 0
			vacaciones_trunca    = 0
			vacaciones_indem     = 0
			prestamos            = 0
			adelantos            = 0
			monto_grati_trun     = 0
			monto_boni_grati_liq = 0
			cta_prestamo         = None

			hpaf = self.env['hr.parameters'].search([('num_tipo','=','10001')])
			a_f = hpaf[0].monto if i.children_number>0 and len(hpaf) > 0 else 0

			grati = False
			if self.periodo.code[0:2]=='07':
				grati = self.env['hr.reward'].search([('year','=',self.periodo.fiscalyear_id.id),('period','=','07')])
			if self.periodo.code[0:2]=='12':
				grati = self.env['hr.reward'].search([('year','=',self.periodo.fiscalyear_id.id),('period','=','12')])

			gratie = False
			if grati:
				gratie = self.env['hr.reward.line'].search([('reward','=',grati.id),('employee_id','=',i.id)])
			if gratie:
				monto_grati      = gratie.total_reward
				monto_boni_grati += gratie.plus_9

			periodo = False
			if self.periodo.code[0:2]=='05':
				periodo = '05'
			if self.periodo.code[0:2]=='11':
				periodo = '11'

			ctsheader = False
			ctsline = False
			ctsheader = self.env['hr.cts'].search([('year','=',self.periodo.fiscalyear_id.id),('period','=',periodo)])
			if len(ctsheader) > 0:
				ctsline = self.env['hr.cts.line'].search([('cts','=',ctsheader.id),('employee_id','=',i.id)])
				if len(ctsline) > 0:
					monto_cts = ctsline.cts_soles

			liquidaciones = self.env['hr.liquidaciones'].search([('period_id','=',self.periodo.id)])
			if len(liquidaciones) > 0:
				ctsliq = self.env['hr.liquidaciones.lines.cts'].search([('liquidacion_id','=',liquidaciones.id),('employee_id','=',i.id)])
				if len(ctsliq) > 0:
					monto_cts = ctsliq.total_payment

				gratiliq = self.env['hr.liquidaciones.lines.grat'].search([('liquidacion_id','=',liquidaciones.id),('employee_id','=',i.id)])
				if len(ctsliq) > 0:
					monto_grati_trun     = gratiliq.total_months				
					monto_boni_grati     += gratiliq.bonus
					monto_boni_grati_liq = gratiliq.bonus

				vacailiq = self.env['hr.liquidaciones.lines.vac'].search([('liquidacion_id','=',liquidaciones.id),('employee_id','=',i.id)])
				if len(ctsliq) > 0:
					vacaciones        = vacailiq.fall_due_holidays
					vacaciones_trunca = vacailiq.total_holidays_sinva
					vacaciones_indem  = vacailiq.compensation

			# prestamosheader = self.env['hr.prestamo.header'].search([('employee_id','=',i.id)])
			# if len(prestamosheader) > 0:
			# 	cta_prestamo = prestamosheader.account_id.id
			# 	for deta in prestamosheader.prestamo_lines_ids:
			# 		if deta.validacion == '2':
			# 			aperioddate = deta.fecha_pago.split('-')
			# 			if aperioddate[1] + '/' + aperioddate[0] == self.periodo.code:
			# 				prestamos += deta.monto

			adelantosheader=self.env['hr.adelanto'].search([('employee','=',i.id)])
			if len(adelantosheader) > 0:
				for deta in adelantosheader:
					aperioddate=deta.fecha.split('-')
					if aperioddate[1] + '/' + aperioddate[0] == self.periodo.code:
						adelantos += deta.monto

			vrl = self.env['vacation.role.line'].search([('parent.period_id','=',self.periodo.id),('employee_id','=',i.id)])
			ivac = False
			rvac = False
			if len(vrl):
				pvl = self.env['partial.vacation.line'].search([('parent','=',vrl.id)])
				ivac = pvl[0].init_date if len(pvl) else False
				rvac = pvl[0].end_date if len(pvl) else False

			ye = int(self.periodo.code.split("/")[1])
			mo = int(self.periodo.code.split("/")[0])

			vals = {
				'employee_id'						 : i.id,
				'dni'                                : i.identification_id,
				'codigo_trabajador'                  : i.codigo_trabajador,
				'apellido_paterno'                   : i.last_name_father,
				'apellido_materno'                   : i.last_name_mother,
				'nombre'                             : i.first_name_complete,
				'cargo'                              : i.job_id.id,
				'afiliacion'                         : i.afiliacion.id,
				'zona'                               : i.zona_contab,
				'tipo_comision'                      : i.c_mixta, 
				'basica_first'                       : i.basica,
				'dias_mes'							 : monthrange(ye, mo)[1],
				'dias_trabajador' 					 : 30,
				'dias_vacaciones'					 : vrl[0].days if len(vrl) > 0 else 0,
				'a_familiar_first'                   : a_f,
				'a_familiar'                         : a_f,
				'horas_ordinarias_trabajadas'        : self.sunat_hours,
				'total_remunerable'                  : i.basica + a_f,
				'vacaciones'                         : vacaciones,
				'vacaciones_inicio'                  : ivac,
				'vacaciones_retorno'                 : rvac,
				'vacaciones_trunca'                  : vacaciones_trunca,
				'otros_ingreso'                      : vacaciones_indem,
				#'quinta_cat'                         : monto_5category,
				'cts'                                : monto_cts,
				'gratificacion'                      : monto_grati ,
				'gratificacion_extraordinaria'       : monto_grati_trun,
				'gratificacion_extraordinaria_real'  : monto_grati_real,
				'boni_grati'                         : monto_boni_grati,
				'adelantos'                          : adelantos,
				'prestamos'                          : prestamos,
				'centro_costo'                       : i.dist_c.id,
				'tareo_id'                           : self.id,
				# 'cta_prestamo'                       : cta_prestamo
			}
			i = self.env['hr.tareo.line'].create(vals)
			i.with_context({'active_id':i.id}).onchange_all()
			i.save_data()
