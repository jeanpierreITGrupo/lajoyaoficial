# -*- encoding: utf-8 -*-
from openerp import models, fields, api
from openerp.osv import osv, expression
from datetime import datetime, timedelta
import pprint
import codecs
import base64
import decimal
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, PageBreak, Spacer
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
from reportlab import platypus

class hr_tareo_concepto(models.Model):
	_name = 'hr.tareo.concepto'

	tareo_id = fields.Many2one('hr.tareo','Tareo')
	employee_id = fields.Many2one('hr.employee','Trabajador')
	tipo_contab = fields.Selection([
		('operario','Operario'),
		('mantenimiento','Mantenimiento'),
		('administracion','Administración'),
		('ventas','Ventas')],'Tipo')
	membership_id = fields.Many2one('hr.table.membership','Afiliación')
	distribucion_id = fields.Many2one('hr.distribucion.gastos','Distribución')
	concepto_id = fields.Many2one('hr.concepto.remunerativo.line','Concepto')
	amount=fields.Float('Monto',digits=(12,2))
	cuenta_debe = fields.Many2one('account.account','Cuenta contable debe')
	cuenta_haber = fields.Many2one('account.account','Cuenta contable haber')
	descripcion = fields.Char('Descripcion')

	# cuentas analíticas
	# operario
	extraccion_acc_o = fields.Float('Cuenta para Extracción',digits=(20,6))
	trituracion_acc_o = fields.Float('Cuenta para Trituración',digits=(20,6))
	calcinacion_acc_o = fields.Float('Cuenta para Calcinación',digits=(20,6))
	micronizado_acc_o = fields.Float('Cuenta para Micronizado',digits=(20,6))

	administracion_acc_o = fields.Float('Cuenta para Administración',digits=(20,6))
	ventas_acc_o = fields.Float('Cuenta para Ventas',digits=(20,6))
	capacitacion_acc_o = fields.Float('Cuenta para Capacitación',digits=(20,6))
	promocion_acc_o = fields.Float('Cuenta para Promoción',digits=(20,6))
	gastos_acc_o = fields.Float('Cuenta para Gastos Corporativos',digits=(20,6))

	# cuentas analíticas
	# mantenimiento
	extraccion_acc_m = fields.Float('Cuenta para Extracción',digits=(20,6))
	trituracion_acc_m = fields.Float('Cuenta para Trituración',digits=(20,6))
	calcinacion_acc_m = fields.Float('Cuenta para Calcinación',digits=(20,6))
	micronizado_acc_m = fields.Float('Cuenta para Micronizado',digits=(20,6))

	administracion_acc_m = fields.Float('Cuenta para Administración',digits=(20,6))
	ventas_acc_m = fields.Float('Cuenta para Ventas',digits=(20,6))
	capacitacion_acc_m = fields.Float('Cuenta para Capacitación',digits=(20,6))
	promocion_acc_m = fields.Float('Cuenta para Promoción',digits=(20,6))
	gastos_acc_m = fields.Float('Cuenta para Gastos Corporativos',digits=(20,6))

	# cuentas analíticas
	# Administrativo
	extraccion_acc_a = fields.Float('Cuenta para Extracción',digits=(20,6))
	trituracion_acc_a = fields.Float('Cuenta para Trituración',digits=(20,6))
	calcinacion_acc_a = fields.Float('Cuenta para Calcinación',digits=(20,6))
	micronizado_acc_a = fields.Float('Cuenta para Micronizado',digits=(20,6))

	administracion_acc_a = fields.Float('Cuenta para Administración',digits=(20,6))
	ventas_acc_a = fields.Float('Cuenta para Ventas',digits=(20,6))
	capacitacion_acc_a = fields.Float('Cuenta para Capacitación',digits=(20,6))
	promocion_acc_a = fields.Float('Cuenta para Promoción',digits=(20,6))
	gastos_acc_a = fields.Float('Cuenta para Gastos Corporativos',digits=(20,6))

	# cuentas analíticas
	# Ventas
	extraccion_acc_v = fields.Float('Cuenta para Extracción',digits=(20,6))
	trituracion_acc_v = fields.Float('Cuenta para Trituración',digits=(20,6))
	calcinacion_acc_v = fields.Float('Cuenta para Calcinación',digits=(20,6))
	micronizado_acc_v = fields.Float('Cuenta para Micronizado',digits=(20,6))

	administracion_acc_v = fields.Float('Cuenta para Administración',digits=(20,6))
	ventas_acc_v = fields.Float('Cuenta para Ventas',digits=(20,6))
	capacitacion_acc_v = fields.Float('Cuenta para Capacitación',digits=(20,6))
	promocion_acc_v = fields.Float('Cuenta para Promoción',digits=(20,6))
	gastos_acc_v = fields.Float('Cuenta para Gastos Corporativos',digits=(20,6))






	# operario
	extraccion_acc_o_d = fields.Many2one('account.account')
	trituracion_acc_o_d = fields.Many2one('account.account')
	calcinacion_acc_o_d = fields.Many2one('account.account')
	micronizado_acc_o_d = fields.Many2one('account.account')

	administracion_acc_o_d = fields.Many2one('account.account')
	ventas_acc_o_d = fields.Many2one('account.account')
	capacitacion_acc_o_d = fields.Many2one('account.account')
	promocion_acc_o_d = fields.Many2one('account.account')
	gastos_acc_o_d = fields.Many2one('account.account')

	# cuentas analíticas
	# mantenimiento
	extraccion_acc_m_d = fields.Many2one('account.account')
	trituracion_acc_m_d = fields.Many2one('account.account')
	calcinacion_acc_m_d = fields.Many2one('account.account')
	micronizado_acc_m_d = fields.Many2one('account.account')

	administracion_acc_m_d = fields.Many2one('account.account')
	ventas_acc_m_d = fields.Many2one('account.account')
	capacitacion_acc_m_d = fields.Many2one('account.account')
	promocion_acc_m_d = fields.Many2one('account.account')
	gastos_acc_m_d = fields.Many2one('account.account')

	# cuentas analíticas
	# Administrativo
	extraccion_acc_a_d = fields.Many2one('account.account')
	trituracion_acc_a_d = fields.Many2one('account.account')
	calcinacion_acc_a_d = fields.Many2one('account.account')
	micronizado_acc_a_d = fields.Many2one('account.account')

	administracion_acc_a_d = fields.Many2one('account.account')
	ventas_acc_a_d = fields.Many2one('account.account')
	capacitacion_acc_a_d = fields.Many2one('account.account')
	promocion_acc_a_d = fields.Many2one('account.account')
	gastos_acc_a_d = fields.Many2one('account.account')

	# cuentas analíticas
	# Ventas
	extraccion_acc_v_d = fields.Many2one('account.account')
	trituracion_acc_v_d = fields.Many2one('account.account')
	calcinacion_acc_v_d = fields.Many2one('account.account')
	micronizado_acc_v_d = fields.Many2one('account.account')

	administracion_acc_v_d = fields.Many2one('account.account')
	ventas_acc_v_d = fields.Many2one('account.account')
	capacitacion_acc_v_d = fields.Many2one('account.account')
	promocion_acc_v_d = fields.Many2one('account.account')
	gastos_acc_v_d = fields.Many2one('account.account')

	cta_prestamo = fields.Many2one('account.account','ctaprestamo')	
	total_boleta = fields.Float('Total boleta', digits=(12,2))
