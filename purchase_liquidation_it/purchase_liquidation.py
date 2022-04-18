# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api, exceptions , _
from openerp.osv import osv
from openerp.exceptions import ValidationError

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
import decimal
import datetime

from xlsxwriter.workbook import Workbook
import io
import os
import sys

class purchase_liquidation_print_wizard(models.TransientModel):
	_name = 'purchase.liquidation.print.wizard'

	tipo = fields.Selection([('1','Consumo Adicional'),('2','Consumo kg/TM')],u'Tipo de Impresión', required=True)
	mostrar = fields.Selection([('1','Negociado'),('2','Renegociado')],u'Linea Liquidación',required=True)

	@api.multi
	def do_rebuild(self):
		pl = self.env['purchase.liquidation'].search([('id','=',self.env.context['active_id'])])[0]
		pl.message_post(body=u"<p>Reporte generado.</p>")
		if self.mostrar == '1':
			return pl.do_pdf(self.tipo)
		else:
			return pl.do_pdfr(self.tipo)


class purchase_liquidation(models.Model):
	_name = 'purchase.liquidation'
	_inherit = 'mail.thread'
	_order = 'id desc'

	state               = fields.Selection([('draft','Dato'),('proposal','Propuesta'),('negotiated','Negociado'),('done','Renegociado'),('to_pay','Solic. Presupuesto')], "Estado", default='draft')
	mineral_type        = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo Mineral")
	name                = fields.Char("Nombre")
	in_date             = fields.Date("Fecha Recepción")
	sample_date         = fields.Date("Fecha Recepción")
	source_zone         = fields.Many2one('table.zone',"Origen", required=1)

	subsource_zone      = fields.Many2one('table.zone',"SubOrigen", required=0)
	code_subsource_zone = fields.Char('SubOrigen',related="subsource_zone.code",readonly=1)
	ubigeo_subsource_zone = fields.Char('Ubigeo',related="subsource_zone.ubigeo",readonly=1)

	currency_id			= fields.Many2one('res.currency', "Moneda")
	lot                 = fields.Selection([('L','L'),('LJ','LJ')],"Lote")
	material            = fields.Many2one('product.product',"Material")
	presentation        = fields.Selection([('Granel','Granel'),('Sacos','Sacos')],"Presentación")
	qty                 = fields.Integer("Cantidad")
	tmh                 = fields.Float("TMH", digits=(10,3))
	tms                 = fields.Float("TMS", digits=(10,3), compute='_get_tms')
	gr_gold             = fields.Float("Fino Au Gr", digits=(10,3), compute='_get_gold_gr')
	gr_silver           = fields.Float("Fino Ag Gr", digits=(10,3), compute='_get_silver_gr')
	h2o                 = fields.Float("%_H2O", digits=(10,3))
	ley_oz_au           = fields.Float("Ley Oz Oro", digits=(10,3))
	ley_oz_ag           = fields.Float("Ley Oz Plata", digits=(10,3))
	percentage_recovery = fields.Float("%_Recup. (Au)", digits=(10,2))
	percentage_recovery_ag = fields.Float("%_Recup. (Ag)", digits=(10,2))
	maquila             = fields.Float("Maquila", digits=(10,2))
	soda                = fields.Float("NaOH kg/TN", digits=(10,2))
	cianuro             = fields.Float("NaCN kg/TN", digits=(10,2))
	value_consumed      = fields.Float("Consumo Q Valorado", digits=(10,2))
	g_adm               = fields.Float("G Adm", digits=(10,2))
	acopiador           = fields.Many2one('table.acopiador', 'Acopiador', required=1)
	supplier_id         = fields.Many2one('res.partner', "Proveedor", domain=[('supplier','=',True)], required=1)
	utilidad_bru        = fields.Float("Utilidad bru (Au)", compute="_get_utilidad_bru")
	margen_bru          = fields.Float("Margen bru (Au)", compute="_get_margen_bru")
	utilidad_bru_ag     = fields.Float("Utilidad bru (Ag)", compute="_get_utilidad_bru_ag")
	margen_bru_ag       = fields.Float("Margen bru (Ag)", compute="_get_margen_bru_ag")
	is_especial         = fields.Boolean("Cálculo especial")
	lines               = fields.One2many('purchase.liquidation.line', 'parent', "Lines")
	forzar_nombre       = fields.Char('Forzar Nombre')

	#adicional
	fecha_botonaso = fields.Date('Fecha Boton Negociar')

	#Datos para auditoría
	date_lab = fields.Datetime("Última Modificación Laboratorio", compute='_get_lab_time', store=True)
	date_bal = fields.Datetime("Última Modificación Balanza", compute='_get_bal_time', store=True)
	date_neg = fields.Datetime("Última Modificación Negociación", compute='_get_neg_time', store=True)

	#Datos modificaciones
	vsdolar = fields.Float('Valor V Dolares',digits=(12,2))
	vssoles = fields.Float('Valor V Soles',digits=(12,2))
	proveedorvs = fields.Many2one('res.partner','Proveedor Alterno')
	user_vs = fields.Many2one('res.users','Usuario', readonly=True)
	fecha_vs = fields.Date('Fecha Modificación',readonly=True)

	#Datos permiso de lectura
	check_balanza = fields.Boolean('check_balanza', compute="compute_check_balanza")

	mes = fields.Char('Mes')

	#nuevos datos requeridos
	fecha_retiro = fields.Date('Fecha Retiro de Lote')
	fletero = fields.Char('Nombre de Fletero')
	nro_placa = fields.Char('Nro Placa')
	guia_remitente = fields.Char('Guia Remitente')
	guia_transp = fields.Char('Guia Transportista')
	cod_compro = fields.Char('Codigo Compromiso')
	cod_conces = fields.Char('Codigo Concesion')
	nombre_conces = fields.Char('Nombre Concesion')

	precio_dol = fields.Float('Precio US$/TC')
	maquila_dol = fields.Float('Maquila US$/TC')
	penalidad = fields.Float('Penalidad')
	flete = fields.Float('Flete')
	precio_tm_dol = fields.Float('Precio x TM / US$/TM')
	importe_dol = fields.Float('Importe Total US$')
	reintegro_dol = fields.Float('Reintegro US$')
	nuevo_importe_dol = fields.Float('Nuevo Importe US$')

	@api.one
	def compute_check_balanza(self):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']

		g1_ids = all_groups.search([('name','=',u'Informacion Laboratorio')])

		if not g1_ids:
			raise osv.except_osv('Alerta!', "No existe el grupo 'Informacion Laboratorio' creado.")

		if g1_ids in all_users.search([('id','=',self.env.uid)])[0].groups_id: #in ['dsalas@lajoyamining.com','ecollanque@lajoyamining.com','balanzaplanta@lajoyamining.com','laboratorio@lajoyamining.com']
			self.check_balanza = False
		else:
			self.check_balanza = True


	@api.one
	@api.constrains('name')
	def constrains_name_iof_purchase_liquidation(self):
		if self.name:
			filtro = []
			filtro.append( ('id','!=',self.id) )
			filtro.append( ('name','=',self.name) )
			m = self.env['purchase.liquidation'].search( filtro )
			if len(m) > 0:
				raise exceptions.Warning( ("Numero de Lote Duplicado ("+self.name+")."))



	@api.one
	def write(self,vals):
		import datetime
		if 'vsdolar' in vals or 'vssoles' in vals or 'proveedorvs' in vals:
			vals['user_vs'] = self.env.uid
			vals['fecha_vs'] = str(datetime.datetime.now())[:10]
		if 'in_date' in vals:
			if vals['in_date']:
				vals['mes'] = vals['in_date'].split('-')[1] + '/' + vals['in_date'].split('-')[0]
			else:
				vals['mes'] = False

		seg_msg = "<b>"
		mod_fields = []
		if 'h2o' in vals:
			mod_fields.append("% H2O")
		if 'ley_oz_au' in vals:
			mod_fields.append("Ley Oz Oro")
		if 'ley_oz_ag' in vals:
			mod_fields.append("Ley Oz Plata")
		if 'soda' in vals:
			mod_fields.append("NaOH kg/TN")
		if 'cianuro' in vals:
			mod_fields.append("NaCN kg/TN")
		if 'percentage_recovery' in vals:
			mod_fields.append("% Recpup.")

		if len(mod_fields):
			seg_msg = ", ".join(mod_fields)
			seg_msg += "</b> (Laboratorio) modificado(s)."
			self.message_post(body=u"<p>"+seg_msg+"</p>")

		t = super(purchase_liquidation,self).write(vals)
		return t

	@api.depends('tmh','h2o')
	def _get_tms(self):
		for line in self:
			line.tms = round(((100-line.h2o)/100)*line.tmh,3)

	@api.depends('tms','ley_oz_au')
	def _get_gold_gr(self):
		for line in self:
			line.gr_gold = round(line.tms*line.ley_oz_au*34.285,3)

	@api.depends('tms','ley_oz_ag')
	def _get_silver_gr(self):
		for line in self:
			line.gr_silver = round(line.tms*line.ley_oz_ag*34.285,3)

	@api.model
	def create(self, vals):
		if 'forzar_nombre' in vals and vals['forzar_nombre'] and  vals['forzar_nombre']!= '' and vals['forzar_nombre'].strip() != '':
			vals['name']= vals['forzar_nombre']
		else:
			sequence_id = self.env['ir.sequence'].search([('name','=','Liquidation')])
			vals['name'] = self.env['ir.sequence'].get_id(sequence_id.id, 'id')
		vals['in_date'] = fields.Date.today()
		vals['sample_date'] = vals['in_date']


		if 'in_date' in vals:
			if vals['in_date']:
				vals['mes'] = vals['in_date'].split('-')[1] + '/' + vals['in_date'].split('-')[0]
			else:
				vals['mes'] = False

		return super(purchase_liquidation, self).create(vals)

	@api.one
	@api.depends('lot','material', 'presentation', 'tmh', 'qty')
	def _get_lab_time(self):
		self.date_lab = fields.Datetime.now()

	@api.one
	@api.depends('h2o','ley_oz_au', 'ley_oz_ag', 'soda', 'cianuro', 'percentage_recovery')
	def _get_bal_time(self):
		self.date_bal = fields.Datetime.now()

	@api.one
	@api.depends('lines')
	def _get_neg_time(self):
		self.date_neg = fields.Datetime.now()

	@api.one
	def _get_utilidad_bru(self):
		data_line     = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','oro')])
		negotiatied_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Negociado'),('mineral','=','oro')])
		sale_line     = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Venta'),('mineral','=','oro')])
		if len(data_line) and len(negotiatied_line) and len(sale_line):
			data_line     = data_line[0]
			negotiatied_line = negotiatied_line[0]
			sale_line     = sale_line[0]
			self.utilidad_bru = sale_line.cost_to_pay - negotiatied_line.cost_to_pay - (data_line.maquila + data_line.value_consumed + data_line.g_adm) * data_line.tms

	@api.one
	def _get_margen_bru(self):
		sale_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Venta'),('mineral','=','oro')])
		if len(sale_line):
			sale_line = sale_line[0]
			self.margen_bru = self.utilidad_bru/sale_line.cost_to_pay if sale_line.cost_to_pay != 0 else 0

	@api.one
	def _get_utilidad_bru_ag(self):
		data_line     = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','plata')])
		proposal_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Propuesta'),('mineral','=','plata')])
		if len(data_line) and len(proposal_line):
			self.utilidad_bru_ag = data_line.cost_to_pay - proposal_line.cost_to_pay

	@api.one
	def _get_margen_bru_ag(self):
		data_line     = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','plata')])
		if len(data_line):
			self.margen_bru_ag = self.utilidad_bru_ag/data_line.cost_to_pay if data_line.cost_to_pay != 0 else 0


	@api.onchange('lot','material', 'presentation', 'tmh', 'qty', 'lines')
	def onchange_parameter_id(self):
		pr_ids = []
		pp = self.env['production.parameter'].search([])[0]
		for line in pp.product_ids:
			pr_ids.append(line.product_id.id)
		return{
			'domain':{
				'material': [('id','in',pr_ids)]
			}
		}


	@api.one
	def generate_lines(self):
		if not len(self.env['hr.employee'].search([('user_id','=',self.env.uid)])):
			ru = self.env['res.users'].search([('id','=',self.env.uid)])[0]
			raise osv.except_osv('Alerta!',"El usuario "+ru.name+" no puede generar propuesta. Falta configurar empleado.")

		if self.ley_oz_au == 0 and self.ley_oz_ag == 0:
			raise osv.except_osv('Alerta!',"No se tiene Ley de oro/plata. No se generó propuesta")

		##################
		#       ORO
		##################
		if self.ley_oz_au > 0:
			types = ['Datos','Propuesta','Venta']
			liquidation_line = self.env['purchase.liquidation.line']
			empl = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
			lot_text = ''
			if self.lot:
				lot_text = self.lot
			if 	self.name:
				lot_text += '-' + self.name
			for typel in types:
				vals = {
					'parent'					: self.id,
					'line_type'					: typel,
					'mineral'					: 'oro',
					'in_date'					: self.in_date,
					'employee'					: empl[0].id if len(empl) else False,
					'source_zone'				: self.source_zone.id,
					'lot'						: lot_text,
					'material'					: self.material.name_template,
					'presentation'				: str(self.qty) + ' ' + self.presentation if self.presentation == 'Sacos' else self.presentation,
					'tmh'						: self.tmh,
					'h2o'						: self.h2o,
					'ley_oz'					: self.ley_oz_au,
					'percentage_recovery'		: self.percentage_recovery,
					'maquila'					: self.maquila,
					'soda'						: self.soda,
					'cianuro'					: self.cianuro,
					'value_consumed'			: self.value_consumed,
					'g_adm'						: self.g_adm,
				}

				#LINEA DE DATOS
				if typel == 'Datos':
					p_intern = self.env['table.international.price'].search([('mineral_type','=', vals['mineral']),('date_price','=',self.in_date)])
					if p_intern:
						vals['int_price'] = p_intern.price
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para Precio Internacional. (ORO)")

				#LINEA DE PROPUESTA
				elif typel == 'Propuesta':
					data_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','oro')])
					#Calculo h20
					temp = data_line.h2o
					table_obj = self.env['table.humidity'].search([('mineral_type','=', vals['mineral']),('h2o','<=',temp)], order='date desc, h2o desc')
					if table_obj:
						humidity = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para esta humedad. (ORO)")
					vals['h2o'] = data_line.h2o + humidity.increase
					#calculo ley
					temp = data_line.ley_oz
					table_obj = self.env['table.ley.onz'].search([('mineral_type','=', vals['mineral']),('param1','<=',temp),('param2','>',temp),('zone_id','=',self.source_zone.id)], order='date desc')
					# table_obj = self.env['table.ley.onz'].search([('mineral_type','=', vals['mineral']),('param1','<=',temp),('param2','>',temp)], order='date desc')
					if table_obj:
						ley = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para esta Ley. (ORO)")
					vals['percentage_param_ley'] = ley.percentage
					vals['ley_oz'] = temp*vals['percentage_param_ley']/100
					#Calculo % recuperacion
					temp = data_line.percentage_recovery
					table_obj = self.env['table.recover.percentage'].search([('mineral_type','=', vals['mineral']),('rec_lab','<=',temp),('zone_id','=',self.source_zone.id)]).sorted(key=lambda r: r.rec_lab, reverse=True)
					# table_obj = self.env['table.recover.percentage'].search([('mineral_type','=', vals['mineral']),('rec_lab','<=',temp)]).sorted(key=lambda r: r.rec_lab, reverse=True)
					if table_obj:
						recovery = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para este Porcentaje de recuperación. (ORO)")
					vals['points_param'] = 0
					vals['percentage_param'] = 0
					for recover in recovery:
						if recover.rec_lab <= temp:
							vals['points_param'] = recovery.adjust
							vals['percentage_param'] = recovery.consider
							break
					vals['percentage_recovery'] = temp*recovery.rec_lab/100.00#((int(((temp-vals['points_param'])*vals['percentage_param'])*100))/100)/100
					#Calculo precio internacional
					table_obj = self.env['table.international.price'].search([('mineral_type','=', vals['mineral']),('date_price','=',self.in_date)])
					if table_obj:
						p_intern = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para este Precio Internacional. (ORO)")
					table_obj = self.env['table.international.price.adjust'].search([('mineral_type','=', vals['mineral']),('date_valid','<=', fields.Date.today()),('zone_id','=',self.source_zone.id)], order='date_param desc')
					# table_obj = self.env['table.international.price.adjust'].search([('mineral_type','=', vals['mineral']),('date_valid','<=', fields.Date.today())], order='date_param desc')
					if table_obj:
						temp = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para este Ajuste. (ORO)")
					vals['real_int_price'] = p_intern.price
					vals['int_price_margin'] = temp.adjustment
					vals['int_price'] = vals['real_int_price'] - vals['int_price_margin']
					#Calculo maquila
					temp = data_line.ley_oz
					table_obj = self.env['table.maquila'].search([('mineral_type','=', vals['mineral']),('zone_id','=',self.source_zone.id)], order='date desc,ley desc')
					# table_obj = self.env['table.maquila'].search([('mineral_type','=', vals['mineral'])], order='date desc,ley desc')
					if table_obj:
						params = table_obj
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para este Costo de Maquila. (ORO)")
					vals['maquila'] = 0
					for param in params:
						if param.ley <= temp:
							vals['maquila'] = param.maquila
							break
					#Calculo consumo valorado
					temp = data_line.soda
					table_obj = self.env['table.soda'].search([('mineral_type','=', vals['mineral']),('param1','<=',temp),('param2','>',temp)], order='date desc')
					if table_obj:
						soda_param = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para esta cantidad de Soda Cáustica. (ORO)")
					temp = data_line.cianuro
					table_obj = self.env['table.cianuro'].search([('mineral_type','=', vals['mineral']),('param1','<=',temp),('param2','>',temp)], order='date desc')
					if table_obj:
						cianuro_param = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para esta cantidad de Cianuro. (ORO)")
					vals['value_consumed'] = soda_param.value_consumed + cianuro_param.value_consumed
					#Calculo gastos gestion
					vals['g_adm'] = self.source_zone.param

				elif typel == 'Venta':
					data_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','oro')])
					proposal_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Propuesta'),('mineral','=','oro')])
					vals['tmh'] = data_line.tmh
					vals['h2o'] = data_line.h2o
					vals['tms'] = vals['tmh'] - vals['h2o'] * vals['tmh'] / 100.00
					vals['percentage_recovery'] = data_line.percentage_recovery
					vals['ley_oz'] = data_line.ley_oz
					vals['int_price'] = proposal_line.int_price

				vals['tms'] = round((100 - vals['h2o'])/100*vals['tmh'],3)
				line_obj = liquidation_line.create(vals)

			#Actualización del porcentaje conseguido.
			data_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','oro')])
			for line in self.lines:
				if data_line.cost_to_pay == 0:
					raise osv.except_osv('Alerta!','Precio Intenacional no debe estar en cero. (ORO)')
				else:
					line.comparative_index =  line.cost_to_pay/data_line.cost_to_pay*100

		####################
		#       PLATA
		####################
		if self.ley_oz_ag > 0:
			types = ['Datos','Propuesta']
			liquidation_line = self.env['purchase.liquidation.line']
			empl = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
			for typel in types:
				vals = {
					'parent'					: self.id,
					'line_type'					: typel,
					'mineral'					: 'plata',
					'in_date'					: self.in_date,
					'employee'					: empl[0].id if len(empl) else False,
					'source_zone'				: self.source_zone.id,
					'lot'						: self.lot + '-' + self.name,
					'material'					: self.material.name_template,
					'presentation'				: str(self.qty) + ' ' + self.presentation if self.presentation == 'Sacos' else self.presentation,
					'tmh'						: self.tmh,
					'h2o'						: self.h2o,
					'ley_oz'					: self.ley_oz_ag,
					'percentage_recovery'		: self.percentage_recovery_ag,
					'maquila'					: self.maquila,
					'soda'						: self.soda,
					'cianuro'					: self.cianuro,
					'value_consumed'			: self.value_consumed,
					'g_adm'						: self.g_adm,
				}

				#LINEA DE DATOS
				if typel == 'Datos':
					p_intern = self.env['table.international.price'].search([('mineral_type','=', vals['mineral']),('date_price','=',self.in_date)])
					if p_intern:
						vals['int_price'] = p_intern.price
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para Precio Internacional. (PLATA)")

				#LINEA DE PROPUESTA
				elif typel == 'Propuesta':
					data_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','plata')])
					#Calculo h20
					temp = data_line.h2o
					table_obj = self.env['table.humidity'].search([('mineral_type','=', vals['mineral']),('h2o','<=',temp)], order='date desc, h2o desc')
					if table_obj:
						humidity = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para esta humedad. (PLATA)")
					vals['h2o'] = data_line.h2o + humidity.increase
					#calculo ley
					temp = data_line.ley_oz
					table_obj = self.env['table.ley.onz'].search([('mineral_type','=', vals['mineral']),('param1','<=',temp),('param2','>',temp),('zone_id','=',self.source_zone.id)], order='date desc')
					# table_obj = self.env['table.ley.onz'].search([('mineral_type','=', vals['mineral']),('param1','<=',temp),('param2','>',temp)], order='date desc')
					if table_obj:
						ley = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para esta Ley. (PLATA)")
					vals['percentage_param_ley'] = ley.percentage
					vals['ley_oz'] = temp*vals['percentage_param_ley']/100
					#Calculo % recuperacion
					temp = data_line.percentage_recovery
					table_obj = self.env['table.recover.percentage'].search([('mineral_type','=', vals['mineral']),('rec_lab','<=',temp),('zone_id','=',self.source_zone.id)]).sorted(key=lambda r: r.rec_lab, reverse=True)
					# table_obj = self.env['table.recover.percentage'].search([('mineral_type','=', vals['mineral']),('rec_lab','<=',temp)]).sorted(key=lambda r: r.rec_lab, reverse=True)
					if table_obj:
						recovery = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para este Porcentaje de recuperación. (PLATA)")
					vals['points_param'] = 0
					vals['percentage_param'] = 0
					for recover in recovery:
						if recover.rec_lab <= temp:
							vals['points_param'] = recovery.adjust
							vals['percentage_param'] = recovery.consider
							break
					vals['percentage_recovery'] = temp*recovery.rec_lab/100.00#((int(((temp-vals['points_param'])*vals['percentage_param'])*100))/100)/100
					#Calculo precio internacional
					table_obj = self.env['table.international.price'].search([('mineral_type','=', vals['mineral']),('date_price','=',self.in_date)])
					if table_obj:
						p_intern = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para este Precio Internacional. (PLATA)")
					table_obj = self.env['table.international.price.adjust'].search([('mineral_type','=', vals['mineral']),('date_valid','<=', fields.Date.today()),('zone_id','=',self.source_zone.id)], order='date_param desc')
					# table_obj = self.env['table.international.price.adjust'].search([('mineral_type','=', vals['mineral']),('date_valid','<=', fields.Date.today())], order='date_param desc')
					if table_obj:
						temp = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para este Ajuste. (PLATA)")
					vals['real_int_price'] = p_intern.price
					vals['int_price_margin'] = temp.adjustment
					vals['int_price'] = vals['real_int_price'] - vals['int_price_margin']
					#Calculo maquila
					temp = data_line.ley_oz
					table_obj = self.env['table.maquila'].search([('mineral_type','=', vals['mineral']),('zone_id','=',self.source_zone.id)], order='date desc,ley desc')
					# table_obj = self.env['table.maquila'].search([('mineral_type','=', vals['mineral'])], order='date desc,ley desc')
					if table_obj:
						params = table_obj
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para este Costo de Maquila. (PLATA)")
					vals['maquila'] = 0
					for param in params:
						if param.ley <= temp:
							vals['maquila'] = param.maquila
							break
					#Calculo consumo valorado
					temp = data_line.soda
					table_obj = self.env['table.soda'].search([('mineral_type','=', vals['mineral']),('param1','<=',temp),('param2','>',temp)], order='date desc')
					if table_obj:
						soda_param = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para esta cantidad de Soda Cáustica. (PLATA)")
					temp = data_line.cianuro
					table_obj = self.env['table.cianuro'].search([('mineral_type','=', vals['mineral']),('param1','<=',temp),('param2','>',temp)], order='date desc')
					if table_obj:
						cianuro_param = table_obj[0]
					else:
						raise osv.except_osv('Alerta!',"No se ha encontrado parámetros para esta cantidad de Cianuro. (PLATA)")
					vals['value_consumed'] = soda_param.value_consumed + cianuro_param.value_consumed
					#Calculo gastos gestion
					vals['g_adm'] = self.source_zone.param

				vals['tms'] = round((100 - vals['h2o'])/100*vals['tmh'],3)
				line_obj = liquidation_line.create(vals)

			#Actualización del porcentaje conseguido.
			data_line = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','plata')])
			for line in self.lines:
				if data_line.cost_to_pay == 0:
					raise osv.except_osv('Alerta!','Precio Intenacional no debe estar en cero. (PLATA)')
				else:
					line.comparative_index =  line.cost_to_pay/data_line.cost_to_pay*100

		if self.ley_oz_au > 0 or self.ley_oz_ag > 0:
			self.message_post(body=u"<p>Propuesta generada.</p>")
			self.state = 'proposal'

	@api.one
	def cancel_action(self):
		if self.state == 'proposal':
			lines = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','in',['Datos','Propuesta','Venta'])])
			self.message_post(body=u"<p>Propuesta cancelada.</p>")
			self.state = 'draft'
		elif self.state == 'negotiated':
			lines = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Negociado')])
			self.message_post(body=u"<p>Negociación cancelada.</p>")
			self.state = 'proposal'
		else:
			lines = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Renegociado')])
			self.message_post(body=u"<p>Renegociación cancelada.</p>")
			self.state = 'negotiated'
		for line in lines:
			line.unlink()


	@api.one
	def update(self):
		lines = self.env['purchase.liquidation.line'].search([('parent','=',self.id)])
		for line in lines:
			line.unlink()
		self.generate_lines()
		self.message_post(body=u"<p>Propuesta actualizada.</p>")



	@api.multi
	def do_pdf_action(self):
		return {
			"type": "ir.actions.act_window",
			"res_model": "purchase.liquidation.print.wizard",
			"view_type": "form",
			"view_mode": "form",
			"target": "new",
		}

	@api.multi
	def do_pdf(self, tip):
		self.reporteador(tip)
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		import os

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		vals = {
			'output_name': 'LiquidacionCompra.pdf',
			'output_file': open(direccion + "pa.pdf", "rb").read().encode("base64"),
		}
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}


	@api.multi
	def do_pdfr(self, tip):
		self.reporteadorRene(tip)
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		import os

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		vals = {
			'output_name': 'LiquidacionCompra.pdf',
			'output_file': open(direccion + "pa.pdf", "rb").read().encode("base64"),
		}
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}


	@api.multi
	def cabezera(self,c,wReal,hReal,tip):
		c.setFont("Times-Bold", 10)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, u"PROPUESTA DE COMPRA NRO "+ self.name)
		c.setFont("Times-Bold", 10)
		c.drawString(30,hReal-20, "Fecha Negociación:")
		c.setFont("Times-Roman", 8)
		c.drawString(130,hReal-20, str(self.fecha_botonaso) if self.fecha_botonaso else str(self.in_date))

		c.setFont("Times-Bold", 10)
		c.drawString(420,hReal-20, "Tipo Mineral:")
		c.setFont("Times-Roman", 8)
		c.drawString(520,hReal-20, u'Mineral Argentífero' if self.mineral_type == 'plata' else u'Mineral Aurífero')

		# c.setFont("Times-Bold", 10)
		# c.drawString(30,hReal-32, "Origen:")
		# c.setFont("Times-Roman", 8)
		# c.drawString(130,hReal-32, self.source_zone.name if self.source_zone.name else '' )

		c.setFont("Times-Bold", 10)
		c.drawString(420,hReal-32, "Nro de Sacos:")
		c.setFont("Times-Roman", 8)
		sacos_neg = ""
		for i in self.lines:
			if i.line_type == 'Negociado':
				sacos_neg = i.presentation
		c.drawString(520,hReal-32, sacos_neg if sacos_neg else '')

		c.setFont("Times-Bold", 10)
		c.drawString(30,hReal-32, "Proveedor:")
		c.setFont("Times-Roman", 8)
		c.drawString(130,hReal-32, self.supplier_id.name[:50] if self.supplier_id.name else '' )

		c.setFont("Times-Bold", 10)
		c.drawString(30,hReal-44, "RUC:")
		c.setFont("Times-Roman", 8)
		c.drawString(130,hReal-44, self.supplier_id.type_number if self.supplier_id.type_number else '' )

		c.setFont("Times-Bold", 10)
		c.drawString(420,hReal-44, "Lote:")
		c.setFont("Times-Roman", 8)
		n_lot = ""
		for i in self.lines:
			if i.lot:
				n_lot = i.lot
				break
		c.drawString(520,hReal-44, n_lot if n_lot else '')

		# c.setFont("Times-Bold", 10)
		# c.drawString(420,hReal-44, "Cálculo especial:")
		# c.setFont("Times-Roman", 8)
		# c.drawString(520,hReal-44, 'Si' if self.is_especial else 'No')



	@api.multi
	def reporteador(self, tip):
		import sys
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = height- 30
		hReal = width - 40
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion +"pa.pdf", pagesize=(height,width) )

		for dup in range(1):
			self.cabezera(c,wReal,hReal,tip)
			inicio = 0
			pos_inicial = hReal-80
			pagina = 1

			c.setFont("Times-Bold", 8)
			c.drawString(10+5,pos_inicial,u'Lote')
			c.drawString(80+5,pos_inicial,u'Fecha Rec.')
			c.drawString(130+5,pos_inicial,u'TMH')
			c.drawString(200-15,pos_inicial,u'%_H2O')
			c.drawString(270-25,pos_inicial,u'TMS')
			c.drawString(340-35,pos_inicial,u'Ley Oz')
			c.drawString(410-35,pos_inicial,u'%_Recup.')
			c.drawString(480-35,pos_inicial,u'Precio Intern.')
			c.drawString(550-35,pos_inicial,u'Maquila')
			c.drawString(552,pos_inicial,u'Consumo Adicional' if tip == '1' else 'Consumo Kg/TM')
			c.drawString(620+5,pos_inicial,u'Factor Ajuste')
			c.drawString(690+5,pos_inicial,u'Costo / TM')
			c.drawString(760+2,pos_inicial,u'X Pagar Costo/TM')

			c.line(10,pos_inicial-2,830,pos_inicial-2)
			c.line(10,pos_inicial+8,830,pos_inicial+8)


			c.line(10,pos_inicial+8,10,pos_inicial-2)
			c.line(80,pos_inicial+8,80,pos_inicial-2)
			c.line(130,pos_inicial+8,130,pos_inicial-2)
			c.line(200-20,pos_inicial+8,200-20,pos_inicial-2)
			c.line(270-30,pos_inicial+8,270-30,pos_inicial-2)
			c.line(340-40,pos_inicial+8,340-40,pos_inicial-2)
			c.line(410-40,pos_inicial+8,410-40,pos_inicial-2)
			c.line(480-40,pos_inicial+8,480-40,pos_inicial-2)
			c.line(550-40,pos_inicial+8,550-40,pos_inicial-2)
			c.line(620-70,pos_inicial+8,620-70,pos_inicial-2)
			c.line(620+2,pos_inicial+8,620+2,pos_inicial-2)
			c.line(690,pos_inicial+8,690,pos_inicial-2)
			c.line(760,pos_inicial+8,760,pos_inicial-2)
			c.line(830,pos_inicial+8,830,pos_inicial-2)

			negociado_id = None
			datos_id = None
			for i in self.lines:
				if i.line_type == 'Datos':
					datos_id = i
				if i.line_type == 'Negociado':
					negociado_id = i

			pos_inicial = pos_inicial-12
			c.setFont("Times-Roman", 8)

			# c.drawString(10+5,pos_inicial, negociado_id.lot)
			c.drawString(80+5,pos_inicial, str(negociado_id.in_date) )
			c.drawRightString(200-25,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.tmh)) )
			c.drawRightString(270-35,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.h2o)) )
			c.drawRightString(340-45,pos_inicial, '{:,.3f}'.format(decimal.Decimal ("%0.3f"%negociado_id.tms)) )
			c.drawRightString(410-45,pos_inicial, '{:,.3f}'.format(decimal.Decimal ("%0.3f"%negociado_id.ley_oz)) )
			c.drawRightString(480-45,pos_inicial, str(int(round(negociado_id.percentage_recovery,0))) )
			c.drawRightString(550-45,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%(negociado_id.int_price+ negociado_id.int_price_margin))) )
			c.drawRightString(620-72,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.maquila)) )

			if tip == '1':
				tot1 = negociado_id.value_consumed+negociado_id.g_adm
				c.drawRightString(690-72,pos_inicial, '{:,.4f}'.format(decimal.Decimal ("%0.4f"%tot1)) )
			elif tip == '2':
				tot2 = (negociado_id.value_consumed+negociado_id.g_adm) / float(7)
				c.drawRightString(690-72,pos_inicial, '{:,.4f}'.format(decimal.Decimal ("%0.4f"%tot2)) )

			c.drawRightString(690-5,pos_inicial, '{:,.4f}'.format(decimal.Decimal ("%0.4f"%negociado_id.adjust_factor)) )
			c.drawRightString(760-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.cost)) )
			c.drawRightString(830-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.cost_to_pay)) )

			igvline = negociado_id.cost_to_pay *0.18
			pos_inicial = pos_inicial-24
			c.setFont("Times-Bold", 8)

			c.drawString(760-75,pos_inicial, "IGV. 18%")
			c.setFont("Times-Roman", 8)

			c.drawRightString(830-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% (igvline) )) )


			pos_inicial = pos_inicial-24
			c.setFont("Times-Bold", 8)

			c.drawString(760-75,pos_inicial, "Total")
			c.setFont("Times-Roman", 8)
			c.drawRightString(830-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% (igvline+ negociado_id.cost_to_pay) )) )


			pos_inicial = pos_inicial-104
			c.setFont("Times-Bold", 8)

			c.line(210-90,pos_inicial+10,210+90,pos_inicial+10)
			c.drawCentredString(210,pos_inicial, "La Joya Mining SAC")
			usuario = self.env['res.users'].search([('id','=',self.env.uid)])[0]
			c.drawCentredString(210,pos_inicial-12, negociado_id.employee.name_related if negociado_id.employee.name_related else '')
			c.drawCentredString(210,pos_inicial-24, negociado_id.employee.user_id.partner_id.type_number if negociado_id.employee.user_id.partner_id.type_number else '')


			c.line(630-90,pos_inicial+10,630+90,pos_inicial+10)
			c.drawCentredString(630,pos_inicial, "Proveedor")
			usuario = self.env['res.users'].search([('id','=',self.env.uid)])[0]
			c.drawCentredString(630,pos_inicial-12, self.supplier_id.name)
			c.drawCentredString(630,pos_inicial-24, self.supplier_id.type_number)
			c.showPage()

		c.save()





	@api.multi
	def reporteadorRene(self, tip):
		import sys
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = height- 30
		hReal = width - 40
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion +"pa.pdf", pagesize=(height,width) )

		for dup in range(1):
			self.cabezera(c,wReal,hReal,tip)
			inicio = 0
			pos_inicial = hReal-80
			pagina = 1

			c.setFont("Times-Bold", 8)
			c.drawString(10+5,pos_inicial,u'Lote')
			c.drawString(80+5,pos_inicial,u'Fecha Rec.')
			c.drawString(130+5,pos_inicial,u'TMH')
			c.drawString(200-15,pos_inicial,u'%_H2O')
			c.drawString(270-25,pos_inicial,u'TMS')
			c.drawString(340-35,pos_inicial,u'Ley Oz')
			c.drawString(410-35,pos_inicial,u'%_Recup.')
			c.drawString(480-35,pos_inicial,u'Precio Intern.')
			c.drawString(550-35,pos_inicial,u'Maquila')
			c.drawString(552,pos_inicial,u'Consumo Adicional' if tip == '1' else 'Consumo Kg/TM')
			c.drawString(620+5,pos_inicial,u'Factor Ajuste')
			c.drawString(690+5,pos_inicial,u'Costo / TM')
			c.drawString(760+2,pos_inicial,u'X Pagar Costo/TM')

			c.line(10,pos_inicial-2,830,pos_inicial-2)
			c.line(10,pos_inicial+8,830,pos_inicial+8)


			c.line(10,pos_inicial+8,10,pos_inicial-2)
			c.line(80,pos_inicial+8,80,pos_inicial-2)
			c.line(130,pos_inicial+8,130,pos_inicial-2)
			c.line(200-20,pos_inicial+8,200-20,pos_inicial-2)
			c.line(270-30,pos_inicial+8,270-30,pos_inicial-2)
			c.line(340-40,pos_inicial+8,340-40,pos_inicial-2)
			c.line(410-40,pos_inicial+8,410-40,pos_inicial-2)
			c.line(480-40,pos_inicial+8,480-40,pos_inicial-2)
			c.line(550-40,pos_inicial+8,550-40,pos_inicial-2)
			c.line(620-70,pos_inicial+8,620-70,pos_inicial-2)
			c.line(620+2,pos_inicial+8,620+2,pos_inicial-2)
			c.line(690,pos_inicial+8,690,pos_inicial-2)
			c.line(760,pos_inicial+8,760,pos_inicial-2)
			c.line(830,pos_inicial+8,830,pos_inicial-2)

			negociado_id = None
			datos_id = None
			anterior = None
			for i in self.lines:
				if i.line_type == 'Datos':
					datos_id = i
				if i.line_type == 'Renegociado':
					negociado_id = i
				if i.line_type == 'Negociado':
					anterior = i

			if negociado_id == None or anterior == None:
				raise osv.except_osv('Alerta!',"No tiene linea de Renegociado.")
			pos_inicial = pos_inicial-12
			c.setFont("Times-Roman", 8)

			# c.drawString(10+5,pos_inicial, negociado_id.lot)
			c.drawString(80+5,pos_inicial, str(negociado_id.in_date) )
			c.drawRightString(200-25,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.tmh)) )
			c.drawRightString(270-35,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.h2o)) )
			c.drawRightString(340-45,pos_inicial, '{:,.3f}'.format(decimal.Decimal ("%0.3f"%negociado_id.tms)) )
			c.drawRightString(410-45,pos_inicial, '{:,.3f}'.format(decimal.Decimal ("%0.3f"%negociado_id.ley_oz)) )
			c.drawRightString(480-45,pos_inicial, str(int(round(negociado_id.percentage_recovery,0))) )
			c.drawRightString(550-45,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%(negociado_id.int_price+ negociado_id.int_price_margin))) )
			c.drawRightString(620-72,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.maquila)) )

			if tip == '1':
				tot1 = negociado_id.value_consumed+negociado_id.g_adm
				c.drawRightString(690-72,pos_inicial, '{:,.4f}'.format(decimal.Decimal ("%0.4f"%tot1)) )
			elif tip == '2':
				tot2 = (negociado_id.value_consumed+negociado_id.g_adm) / float(7)
				c.drawRightString(690-72,pos_inicial, '{:,.4f}'.format(decimal.Decimal ("%0.4f"%tot2)) )

			c.drawRightString(690-5,pos_inicial, '{:,.4f}'.format(decimal.Decimal ("%0.4f"%negociado_id.adjust_factor)) )
			c.drawRightString(760-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.cost)) )
			c.drawRightString(830-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%negociado_id.cost_to_pay)) )

			igvline = negociado_id.cost_to_pay *0.18

			pos_inicial = pos_inicial-24
			c.setFont("Times-Bold", 8)

			c.drawString(760-155,pos_inicial, u"Negociación Anterior")
			c.setFont("Times-Roman", 8)

			c.drawRightString(830-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% (anterior.cost_to_pay) )) )

			pos_inicial = pos_inicial-24
			c.setFont("Times-Bold", 8)

			c.drawString(760-155,pos_inicial, u"Nueva Base")
			c.setFont("Times-Roman", 8)

			nb = negociado_id.cost_to_pay-anterior.cost_to_pay
			c.drawRightString(830-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% (nb) )) )

			pos_inicial = pos_inicial-24
			c.setFont("Times-Bold", 8)

			c.drawString(760-155,pos_inicial, u"IGV. 18%")
			c.setFont("Times-Roman", 8)

			c.drawRightString(830-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% (nb*0.18) )) )

			pos_inicial = pos_inicial-24
			c.setFont("Times-Bold", 8)

			c.drawString(760-155,pos_inicial, u"Total")
			c.setFont("Times-Roman", 8)

			c.drawRightString(830-5,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% ( nb+(nb*0.18) ) )) )

			pos_inicial = pos_inicial-104
			c.setFont("Times-Bold", 8)

			c.line(210-90,pos_inicial+10,210+90,pos_inicial+10)
			c.drawCentredString(210,pos_inicial, "La Joya Mining SAC")
			usuario = self.env['res.users'].search([('id','=',self.env.uid)])[0]
			c.drawCentredString(210,pos_inicial-12, negociado_id.employee.name_related if negociado_id.employee.name_related else '')
			c.drawCentredString(210,pos_inicial-24, negociado_id.employee.user_id.partner_id.type_number if negociado_id.employee.user_id.partner_id.type_number else '')


			c.line(630-90,pos_inicial+10,630+90,pos_inicial+10)
			c.drawCentredString(630,pos_inicial, "Proveedor")
			usuario = self.env['res.users'].search([('id','=',self.env.uid)])[0]
			c.drawCentredString(630,pos_inicial-12, self.supplier_id.name)
			c.drawCentredString(630,pos_inicial-24, self.supplier_id.type_number)
			c.showPage()

		c.save()

	@api.multi
	def particionar_text(self,c):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Times-Roman',8,95)
			if len(lines)>1:
				return tet[:-1]
		return tet

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,tipo):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal,tipo)

			c.setFont("Times-Bold", 8)
			c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-100
		else:
			return pagina,posactual-valor
	@api.multi
	def verify_space(self,c,wReal,hReal,posactual,valor,pagina,tipo):
		if posactual-valor <40:
			c.showPage()
			self.cabezera(c,wReal,hReal,tipo)

			c.setFont("Times-Bold", 8)
			c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-100
		else:
			return pagina,posactual



	@api.multi
	def export_excel(self):
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
		workbook = Workbook( direccion + u'Licitaciones_con_saldo.xlsx')
		worksheet = workbook.add_worksheet(u"Liquidaciones")

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
		boldcentred = workbook.add_format({'bold': True})
		boldcentred.set_align('center')
		boldcentred.set_border(style=1)

		numbersix = workbook.add_format()
		numbersix.set_num_format('#,##0.00')
		numbersix.set_text_wrap()
		numbersix.set_border()

		numbersixred = workbook.add_format()
		numbersixred.set_num_format('#,##0.00')
		numbersixred.set_font_color('red')
		numbersixred.set_border()

		x= 6
		worksheet.write(1,0, u"Liquidaciones", bold)

		columnas = [u'Nombre',
					u'Forzar Nombre',
					u'Padre',
					u'Fecha Recepción',
					u'Proveedor',
					u'Material',
					u'TMH',
					u'%_H2O',
					u'TMS',
					u'%_Recup.',
					u'Ley Oz Oro',
					u'Fino Au Gr.',
					u'NaOH kg/TN',
					u'NaCN kg/TN',
					u'Ley Oz Plata',
					u'Fino Ag Gr.',
					u'Estado',
					u'Empleado',
					u'Fecha Impresión',
					u'Origen',
					u'Presentación',
					u'Precio Int.',
					u'Margen de Precio Int.',
					u'Maquila',
					u'Consumo Q Valorado',
					u'G Admin',
					u'Total Maquila',
					u'Factor Ajuste',
					u'Costo T/M',
					u'Por Pagar Costo T/M',
					u'Indice Comparativo',
					u'Observaciones',
					u'Vs Dolares',
					u'Vs Soles',
					u'Proveedor Alterno',
					u'Usuario',
					u'Fecha']

		worksheet.set_column('A:E', 15)
		worksheet.set_column('F:F', 30)
		worksheet.set_column('G:AZ', 23.14)

		for i in range(len(columnas)):
			worksheet.write(5,i, columnas[i], boldcentred)

		for liqui in self:
			linea = None
			tt = self.env['purchase.liquidation.line'].search([('parent','=',liqui.id),('line_type','=','Datos')])
			if len(tt)>0:
				linea = tt[0]

			tt = self.env['purchase.liquidation.line'].search([('parent','=',liqui.id),('line_type','=','Propuesta')])
			if len(tt)>0:
				linea = tt[0]

			tt = self.env['purchase.liquidation.line'].search([('parent','=',liqui.id),('line_type','=','Negociado')])
			if len(tt)>0:
				linea = tt[0]

			if linea:
				worksheet.write(x,0, liqui.name if liqui.name else '', bord)
				worksheet.write(x,1, liqui.forzar_nombre if liqui.forzar_nombre else '', bord)
				worksheet.write(x,2, liqui.padre_id.name if liqui.padre_id.name else '', bord)
				worksheet.write(x,3, str(liqui.in_date) if liqui.in_date else '', bord)
				worksheet.write(x,4, liqui.supplier_id.name if liqui.supplier_id.name else '', bord)
				worksheet.write(x,5, liqui.material.name_template if liqui.material.name_template else '', bord)
				worksheet.write(x,6, linea.tmh , numbertres)
				worksheet.write(x,7, linea.h2o , numbertres)
				worksheet.write(x,8, linea.tms , numbertres)
				worksheet.write(x,9, linea.percentage_recovery , numbertres)
				worksheet.write(x,10, liqui.ley_oz_au , numbertres)
				worksheet.write(x,11, round(linea.tms*liqui.ley_oz_au*34.285,3) , numbertres)
				worksheet.write(x,12, linea.soda , numbertres)
				worksheet.write(x,13, linea.cianuro , numbertres)
				worksheet.write(x,14, liqui.ley_oz_ag , numbertres)
				worksheet.write(x,15, round(linea.tms*liqui.ley_oz_ag*34.285,3) , numbertres)
				worksheet.write(x,16, linea.line_type , numbertres)
				worksheet.write(x,17, linea.employee.name if linea.employee.name else ''  , bord)
				worksheet.write(x,18, linea.print_date if linea.print_date else '' , bord)
				worksheet.write(x,19, linea.source_zone.name if linea.source_zone.name else '' , bord)
				worksheet.write(x,20, linea.presentation if linea.presentation else '' , bord)
				worksheet.write(x,21, linea.int_price, numbertres)
				worksheet.write(x,22, linea.int_price_margin, numbertres)
				worksheet.write(x,23, linea.maquila, numbertres)
				worksheet.write(x,24, linea.value_consumed, numbertres)
				worksheet.write(x,25, linea.g_adm, numbertres)
				worksheet.write(x,26, linea.total_maquila, numbertres)
				worksheet.write(x,27, linea.adjust_factor, numbertres)
				worksheet.write(x,28, linea.cost, numbertres)
				worksheet.write(x,29, linea.cost_to_pay, numbertres)
				worksheet.write(x,30, linea.comparative_index, numbertres)
				worksheet.write(x,31, linea.observations if linea.observations else '', bord)


				worksheet.write(x,32, liqui.vsdolar, numbertres)
				worksheet.write(x,33, liqui.vssoles, numbertres)
				worksheet.write(x,34, liqui.proveedorvs.name if liqui.proveedorvs.id else '', bord)
				worksheet.write(x,35, liqui.user_vs.name if liqui.user_vs.id else '', bord)
				worksheet.write(x,36, liqui.fecha_vs if liqui.fecha_vs else '', bord)

				x += 1
			else:
				worksheet.write(x,0, liqui.name if liqui.name else '', bord)
				worksheet.write(x,1, liqui.forzar_nombre if liqui.forzar_nombre else '', bord)
				worksheet.write(x,2, liqui.padre_id.name if liqui.padre_id.name else '', bord)
				worksheet.write(x,3, str(liqui.in_date) if liqui.in_date else '', bord)
				worksheet.write(x,4, liqui.supplier_id.name if liqui.supplier_id.name else '', bord)
				worksheet.write(x,5, liqui.material.name_template if liqui.material.name_template else '', bord)
				worksheet.write(x,6, liqui.tmh , numbertres)
				worksheet.write(x,7, liqui.h2o , numbertres)
				worksheet.write(x,8, 0, numbertres)
				worksheet.write(x,9, liqui.percentage_recovery , numbertres)
				worksheet.write(x,10, liqui.ley_oz_au , numbertres)
				worksheet.write(x,11, 0 , numbertres)
				worksheet.write(x,12, liqui.soda , numbertres)
				worksheet.write(x,13, liqui.cianuro , numbertres)
				worksheet.write(x,14, liqui.ley_oz_ag , numbertres)
				worksheet.write(x,15, 0, numbertres)
				worksheet.write(x,16, 'Datos' , numbertres)
				worksheet.write(x,17,  ''  , bord)
				worksheet.write(x,18,  '' , bord)
				worksheet.write(x,19,  '' , bord)
				worksheet.write(x,20,  '' , bord)
				worksheet.write(x,21, 0, numbertres)
				worksheet.write(x,22, 0, numbertres)
				worksheet.write(x,23, 0, numbertres)
				worksheet.write(x,24, 0, numbertres)
				worksheet.write(x,25, 0, numbertres)
				worksheet.write(x,26, 0, numbertres)
				worksheet.write(x,27, 0, numbertres)
				worksheet.write(x,28, 0, numbertres)
				worksheet.write(x,29, 0, numbertres)
				worksheet.write(x,30, 0, numbertres)
				worksheet.write(x,31,  '', bord)


				worksheet.write(x,32, liqui.vsdolar, numbertres)
				worksheet.write(x,33, liqui.vssoles, numbertres)
				worksheet.write(x,34, liqui.proveedorvs.name if liqui.proveedorvs.id else '', bord)
				worksheet.write(x,35, liqui.user_vs.name if liqui.user_vs.id else '', bord)
				worksheet.write(x,36, liqui.fecha_vs if liqui.fecha_vs else '', bord)
				x += 1


		workbook.close()


		f = open( direccion + u'Licitaciones_con_saldo.xlsx', 'rb')


		vals = {
			'output_name': u'LiquidacionesNegocio.xlsx',
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
	def make_excel_neg(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		titulo    = u'Reprte_Negociación'
		workbook  = Workbook(direccion + titulo + '.xlsx')
		worksheet = workbook.add_worksheet("Negociacion")

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

		dts = {0:"lunes", 1:"martes", 2:"miércoles", 3:"jueves", 4:"viernes", 5:"sábado", 6:"domingo"}
		mts = {1:"enero", 2:"febrero", 3:"marzo", 4:"abril", 5:"mayo", 6:"junio", 7:"julio", 8:"agosto", 9:"septiembre", 10:"octubre", 11:"noviembre", 12:"diciembre"}

		rc = self.env['res.company'].search([])[0]
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', ("RUC: "+rc.partner_id.type_number) if rc.partner_id.type_number else 'RUC: ', title_format)

		row = 5
		worksheet.merge_range(row,1,row+1,1, (self.lot+"-"+self.name) if self.lot and self.name else '', header_y_format)
		worksheet.write(row, 6, u"Factor Conversión", header_g_format)
		worksheet.write(row, 7, 1.1023, header_g_format)
		hoy = datetime.datetime.now()
		worksheet.merge_range(row-1,18,row-1,20, dts[hoy.weekday()] + ", " + format(hoy.day,'02') + " de " + mts[hoy.month] + " del " + str(hoy.year), header_w_format)

		row += 1
		col = 2
		worksheet.write(row, col, u"F. Recep", header_w_format)
		col += 1
		worksheet.write(row, col, u"F. Liqui", header_w_format)
		col += 1
		worksheet.write(row, col, u"Proced", header_w_format)
		col += 1
		worksheet.write(row, col, u"Acopiador", header_w_format)
		col += 1
		worksheet.write(row, col, u"TMH", header_w_format)
		col += 1
		worksheet.write(row, col, u"% H2O", header_w_format)
		col += 1
		worksheet.write(row, col, u"TMS", header_format)
		col += 1
		worksheet.write(row, col, u"REC", header_w_format)
		col += 1
		worksheet.write(row, col, u"Ley (Oz/TC)", header_w_format)
		col += 1
		worksheet.write(row, col, u"Inter ($)", header_w_format)
		col += 1
		worksheet.write(row, col, u"Margen ($)", header_format)
		col += 1
		worksheet.write(row, col, u"Maquila ($)", header_format)
		col += 1
		worksheet.write(row, col, u"Cons Q ($)", header_format)
		col += 1
		worksheet.write(row, col, u"Gast Adm ($)", header_format)
		col += 1
		worksheet.write(row, col, u"Precio x TMS ($)", header_w_format)
		col += 1
		worksheet.write(row, col, u"Importe ($)", header_w_format)
		col += 1
		worksheet.write(row, col, u"IGV ($)", header_w_format)
		col += 1
		worksheet.write(row, col, u"TOTAL ($)", header_w_format)
		col += 1

		row += 1
		col = 1
		oro_renegotiated = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Renegociado'),('mineral','=','oro')])
		if len(oro_renegotiated):
			worksheet.write(row, col, u"Renegociado (Au)", header_w_format)
		col += 2
		if len(oro_renegotiated):
			oro_renegotiated = oro_renegotiated[0]
			worksheet.write(row, col, oro_renegotiated.print_date if oro_renegotiated.print_date else "", basic_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.parent.source_zone.name if oro_renegotiated.parent.source_zone.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.parent.acopiador.name if oro_renegotiated.parent.acopiador.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.tmh if oro_renegotiated.tmh else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.h2o if oro_renegotiated.h2o else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.tms if oro_renegotiated.tms else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.percentage_recovery if oro_renegotiated.percentage_recovery else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.ley_oz if oro_renegotiated.ley_oz else 0, numeric_y_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.int_price if oro_renegotiated.int_price else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.int_price_margin if oro_renegotiated.int_price_margin else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.maquila if oro_renegotiated.maquila else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.value_consumed if oro_renegotiated.value_consumed else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.total_maquila if oro_renegotiated.total_maquila else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.cost if oro_renegotiated.cost else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_renegotiated.cost_to_pay if oro_renegotiated.cost_to_pay else 0, numeric_y_format)
			col += 1
			igv = oro_renegotiated.cost_to_pay * 0.18
			worksheet.write(row, col, igv if igv else 0, numeric_format)
			col += 1
			worksheet.write(row, col, (oro_renegotiated.cost_to_pay+igv), numeric_format)
			col += 1
			row += 1

		col = 1
		worksheet.write(row, col, u"Negociado (Au)", header_w_format)
		col += 2
		oro_negotiated = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Negociado'),('mineral','=','oro')])
		if len(oro_negotiated):
			oro_negotiated = oro_negotiated[0]
			worksheet.write(row, col, oro_negotiated.print_date if oro_negotiated.print_date else "", basic_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.parent.source_zone.name if oro_negotiated.parent.source_zone.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.parent.acopiador.name if oro_negotiated.parent.acopiador.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.tmh if oro_negotiated.tmh else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.h2o if oro_negotiated.h2o else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.tms if oro_negotiated.tms else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.percentage_recovery if oro_negotiated.percentage_recovery else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.ley_oz if oro_negotiated.ley_oz else 0, numeric_y_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.int_price if oro_negotiated.int_price else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.int_price_margin if oro_negotiated.int_price_margin else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.maquila if oro_negotiated.maquila else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.value_consumed if oro_negotiated.value_consumed else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.total_maquila if oro_negotiated.total_maquila else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.cost if oro_negotiated.cost else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_negotiated.cost_to_pay if oro_negotiated.cost_to_pay else 0, numeric_y_format)
			col += 1
			igv = oro_negotiated.cost_to_pay * 0.18
			worksheet.write(row, col, igv if igv else 0, numeric_format)
			col += 1
			worksheet.write(row, col, (oro_negotiated.cost_to_pay+igv), numeric_format)
			col += 1
			row += 1

		col = 1
		worksheet.write(row, col, u"Propuesta (Au)", header_w_format)
		col += 2
		oro_proposal = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Propuesta'),('mineral','=','oro')])
		if len(oro_proposal):
			oro_proposal = oro_proposal[0]
			worksheet.write(row, col, oro_proposal.print_date if oro_proposal.print_date else "", basic_format)
			col += 1
			worksheet.write(row, col, oro_proposal.parent.source_zone.name if oro_proposal.parent.source_zone.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_proposal.parent.acopiador.name if oro_proposal.parent.acopiador.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_proposal.tmh if oro_proposal.tmh else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_proposal.h2o if oro_proposal.h2o else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_proposal.tms if oro_proposal.tms else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_proposal.percentage_recovery if oro_proposal.percentage_recovery else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_proposal.ley_oz if oro_proposal.ley_oz else 0, numeric_y_format)
			col += 1
			worksheet.write(row, col, oro_proposal.int_price if oro_proposal.int_price else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_proposal.int_price_margin if oro_proposal.int_price_margin else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_proposal.maquila if oro_proposal.maquila else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_proposal.value_consumed if oro_proposal.value_consumed else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_proposal.total_maquila if oro_proposal.total_maquila else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_proposal.cost if oro_proposal.cost else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_proposal.cost_to_pay if oro_proposal.cost_to_pay else 0, numeric_y_format)
			col += 1
			igv = oro_proposal.cost_to_pay * 0.18
			worksheet.write(row, col, igv if igv else 0, numeric_format)
			col += 1
			worksheet.write(row, col, (oro_proposal.cost_to_pay+igv), numeric_format)
			col += 1
			row += 1
		col = 1

		worksheet.write(row, col, u"Liq Int (Au)", header_w_format)
		col += 2
		oro_data = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','oro')])
		if len(oro_data):
			oro_data = oro_data[0]
			worksheet.write(row, col, oro_data.print_date if oro_data.print_date else "", basic_format)
			col += 1
			worksheet.write(row, col, oro_data.parent.source_zone.name if oro_data.parent.source_zone.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_data.parent.acopiador.name if oro_data.parent.acopiador.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_data.tmh if oro_data.tmh else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_data.h2o if oro_data.h2o else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_data.tms if oro_data.tms else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_data.percentage_recovery if oro_data.percentage_recovery else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_data.ley_oz if oro_data.ley_oz else 0, numeric_y_format)
			col += 1
			worksheet.write(row, col, oro_data.int_price if oro_data.int_price else 0, numeric_format)
			col += 2
			worksheet.write(row, col, oro_data.maquila if oro_data.maquila else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_data.value_consumed if oro_data.value_consumed else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_data.total_maquila if oro_data.total_maquila else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_data.cost if oro_data.cost else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_data.cost_to_pay if oro_data.cost_to_pay else 0, numeric_y_format)
			col += 1
			row += 2
		col = 1
		worksheet.write(row, col, u"Venta (Au)", header_w_format)
		col += 2
		oro_sale = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Venta'),('mineral','=','oro')])
		if len(oro_sale):
			oro_sale = oro_sale[0]
			worksheet.write(row, col, oro_sale.print_date if oro_sale.print_date else "", basic_format)
			col += 1
			worksheet.write(row, col, oro_sale.parent.source_zone.name if oro_sale.parent.source_zone.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_sale.parent.acopiador.name if oro_sale.parent.acopiador.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, oro_sale.tmh if oro_sale.tmh else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_sale.h2o if oro_sale.h2o else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_sale.tms if oro_sale.tms else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, oro_sale.percentage_recovery if oro_sale.percentage_recovery else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_sale.ley_oz if oro_sale.ley_oz else 0, numeric_y_format)
			col += 1
			worksheet.write(row, col, oro_sale.int_price if oro_sale.int_price else 0, numeric_format)
			col += 5
			worksheet.write(row, col, oro_sale.cost if oro_sale.cost else 0, numeric_format)
			col += 1
			worksheet.write(row, col, oro_sale.cost_to_pay if oro_sale.cost_to_pay else 0, numeric_y_format)
			col += 1
			row += 2

		col = 1
		worksheet.write(row, col, u"Propuesta (Ag)", header_w_format)
		col += 2
		plata_proposal = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Propuesta'),('mineral','=','plata')])
		if len(plata_proposal):
			plata_proposal = plata_proposal[0]
			worksheet.write(row, col, plata_proposal.print_date if plata_proposal.print_date else "", basic_format)
			col += 1
			worksheet.write(row, col, plata_proposal.parent.source_zone.name if plata_proposal.parent.source_zone.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, plata_proposal.parent.acopiador.name if plata_proposal.parent.acopiador.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, plata_proposal.tmh if plata_proposal.tmh else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_proposal.h2o if plata_proposal.h2o else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_proposal.tms if plata_proposal.tms else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, plata_proposal.percentage_recovery if plata_proposal.percentage_recovery else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_proposal.ley_oz if plata_proposal.ley_oz else 0, numeric_y_format)
			col += 1
			worksheet.write(row, col, plata_proposal.int_price if plata_proposal.int_price else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_proposal.int_price_margin if plata_proposal.int_price_margin else 0, numeric_gr_format)
			col += 4
			worksheet.write(row, col, plata_proposal.cost if plata_proposal.cost else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_proposal.cost_to_pay if plata_proposal.cost_to_pay else 0, numeric_y_format)
			col += 1
			igv = plata_proposal.cost_to_pay * 0.18
			worksheet.write(row, col, igv if igv else 0, numeric_format)
			col += 1
			worksheet.write(row, col, (plata_proposal.cost_to_pay+igv), numeric_format)
			col += 1
			row += 1

		col = 1
		worksheet.write(row, col, u"Liq Int (Ag)", header_w_format)
		col += 2
		plata_data = self.env['purchase.liquidation.line'].search([('parent','=',self.id),('line_type','=','Datos'),('mineral','=','plata')])
		if len(plata_data):
			plata_data = plata_data[0]
			worksheet.write(row, col, plata_data.print_date if plata_data.print_date else "", basic_format)
			col += 1
			worksheet.write(row, col, plata_data.parent.source_zone.name if plata_data.parent.source_zone.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, plata_data.parent.acopiador.name if plata_data.parent.acopiador.name else 0, basic_format)
			col += 1
			worksheet.write(row, col, plata_data.tmh if plata_data.tmh else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_data.h2o if plata_data.h2o else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_data.tms if plata_data.tms else 0, numeric_gr_format)
			col += 1
			worksheet.write(row, col, plata_data.percentage_recovery if plata_data.percentage_recovery else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_data.ley_oz if plata_data.ley_oz else 0, numeric_y_format)
			col += 1
			worksheet.write(row, col, plata_data.int_price if plata_data.int_price else 0, numeric_format)
			col += 5
			worksheet.write(row, col, plata_data.cost if plata_data.cost else 0, numeric_format)
			col += 1
			worksheet.write(row, col, plata_data.cost_to_pay if plata_data.cost_to_pay else 0, numeric_y_format)
			col += 1
			row += 1
		worksheet.merge_range(row,15,row+1,15, "Unidad x Lote", header_w_format)

		row += 2
		if len(oro_negotiated) and len(oro_sale) and len(plata_proposal) and len(plata_data):
			worksheet.write(row, 7, "Au", header_w_format)
			worksheet.write(row, 11, "Ag", header_w_format)
			worksheet.write(row, 14, "Margen Compra", header_w_format)
			worksheet.write(row, 15, ((oro_negotiated.cost_to_pay+plata_proposal.cost_to_pay)/(oro_data.cost_to_pay+plata_data.cost_to_pay)) if (oro_data.cost_to_pay+plata_data.cost_to_pay) != 0 else 0, percentage_format)

			row += 1
			worksheet.write(row, 6, "Margen Bru", header_w_format)
			worksheet.write(row, 7, self.margen_bru, percentage_y_format)
			worksheet.write(row, 10, "Margen Bru", header_w_format)
			worksheet.write(row, 11, self.margen_bru_ag, percentage_y_format)
			worksheet.write(row, 14, "Margen Bru", header_w_format)
			worksheet.write(row, 15, ((self.utilidad_bru + self.utilidad_bru_ag)/(plata_data.cost_to_pay+oro_sale.cost_to_pay)) if (plata_data.cost_to_pay+oro_sale.cost_to_pay) else 0, percentage_format)

			row += 1
			worksheet.write(row, 6, "Utilidad Bru", header_w_format)
			worksheet.write(row, 7, self.utilidad_bru, percentage_y_format)
			worksheet.write(row, 10, "Utilidad Bru", header_w_format)
			worksheet.write(row, 11, self.utilidad_bru_ag, percentage_y_format)
			worksheet.write(row, 14, "Utilidad Bru", header_w_format)
			worksheet.write(row, 15, self.utilidad_bru + self.utilidad_bru_ag, percentage_format)

		col_sizes = [15, 20]
		worksheet.set_column('A:E', col_sizes[1])
		worksheet.set_column('F:T', col_sizes[0])

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



class purchase_liquidation_line(models.Model):
	_name = 'purchase.liquidation.line'

	parent = fields.Many2one('purchase.liquidation', "Liquidación de Compra")
	line_type = fields.Char("Estados")
	mineral = fields.Char(u'Mineral')
	in_date = fields.Date("Fecha Recepción")
	employee = fields.Many2one('hr.employee', "Responsable")
	num_liquidation = fields.Char("Num. Hoja Liq.")
	print_date = fields.Date("Fecha de Impresión")
	source_zone = fields.Many2one('table.zone',"Origen")
	lot = fields.Char("Lote")
	material = fields.Char("Material")
	presentation = fields.Char("Presentación")
	tmh = fields.Float("TMH", digits=(10,3))
	h2o = fields.Float("%_H2O", digits=(10,3))
	tms = fields.Float("TMS", digits=(10,3))
	ley_oz = fields.Float("Ley Oz", digits=(10,3))
	percentage_param_ley = fields.Float("Porcentaje Ley", digits=(10,2), invisible=1)
	percentage_recovery = fields.Float("%_Recup.",digits=(10,2))
	points_param = fields.Float("Puntos Param", digits=(10,2), invisible=1)
	percentage_param = fields.Float("Porcentaje Param", digits=(10,2), invisible=1)
	int_price = fields.Float("Precio Intern.", digits=(10,2))
	real_int_price = fields.Float("Precio Intern.", digits=(10,2), invisible=1)
	int_price_margin = fields.Float("Margen de P. Inter.", digits=(10,2))
	maquila = fields.Float("Maquila", digits=(10,2))
	soda = fields.Float("NaOH kg/TN", digits=(10,2))
	cianuro = fields.Float("NaCN kg/TN", digits=(10,2))
	value_consumed = fields.Float("Consumo Q Valorado", digits=(10,2))
	g_adm = fields.Float("G Adm", digits=(10,2))
	total_maquila = fields.Float("Total Consumo Q y G. Adm.", digits=(10,2), compute='_get_total_maquila', store=True)
	adjust_factor = fields.Float("Factor Ajuste", digits=(10,4), default=1.1023)
	cost = fields.Float("Costo/TM", digits=(10,2), compute='_get_cost', store=True)
	cost_to_pay = fields.Float("Por Pagar\nCosto/TM", digits=(10,2), compute='_get_cost_pay', store=True)
	comparative_index = fields.Float("Indice Comparativo", digits=(10,2))
	observations = fields.Text("Observaciones")

	@api.one
	@api.depends('value_consumed','g_adm')
	def _get_total_maquila(self):
		self.total_maquila = self.value_consumed + self.g_adm

	@api.one
	@api.depends('ley_oz','percentage_recovery','int_price','maquila','total_maquila','adjust_factor')
	def _get_cost(self):
		if self.line_type == 'Venta':
			taf = self.env['table.adjust.factor'].search([('mineral_type','=', self.parent.mineral_type),('date','<=',datetime.datetime.now())], order='date desc')
			taf_factor = taf[0].factor if len(taf) else 0
			self.cost = self.percentage_recovery/100.00 * self.ley_oz * self.int_price * taf_factor
		else:
			if self.parent.is_especial:
				self.cost = ((self.ley_oz*(self.percentage_recovery/100)*self.int_price)*self.adjust_factor-self.maquila-self.total_maquila)
			else:
				self.cost = ((self.ley_oz*(self.percentage_recovery/100)*self.int_price)-self.maquila-self.total_maquila)*self.adjust_factor

	@api.one
	@api.depends('cost','tms')
	def _get_cost_pay(self):
		if self.line_type == 'Venta':
			self.cost_to_pay = self.cost*self.tms*self.h2o
		else:
			self.cost_to_pay = self.cost*self.tms




class reporte_liquidation_compra(models.Model):
	_name = 'reporte.liquidation.compra'

	fecha_inicio = fields.Date('Fecha Inicio')
	fecha_final = fields.Date('Fecha Final')
	nro_lote = fields.Many2one('purchase.liquidation','Nro. Lote')
	acopiador = fields.Many2one('table.acopiador','Acopiador')
	zona = fields.Many2one('table.zone','Zona')

	@api.multi
	def do_rebuild(self):
		filtro = []

		filtro.append( ('in_date','>=',self.fecha_inicio) )
		filtro.append( ('in_date','<=',self.fecha_final) )

		if self.nro_lote.id:
			filtro.append( ('id','=',self.nro_lote.id) )
		if self.acopiador.id:
			filtro.append( ('acopiador','=',self.acopiador.id) )
		if self.zona.id:
			filtro.append( ('source_zone','=',self.zona.id) )


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
		workbook = Workbook( direccion + u'Licitacionesxtg.xlsx')
		worksheet = workbook.add_worksheet(u"Listado")

		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_font_size(10)

		numberdosespecial = workbook.add_format({'num_format':"""_ "$"* #,##0.00_ ;_ "$"* -#,##0.00_ ;_ "$"* "-"??_ ;_ @_ """})
		numberdosespecial.set_border(style=1)
		numberdosespecial.set_font_size(10)


		bordred = workbook.add_format()
		bordred.set_border(style=1)
		bordred.set_font_size(10)
		bordred.set_font_color('red')

		bordgray = workbook.add_format()
		bordgray.set_border(style=1)
		bordgray.set_font_size(10)
		bordgray.set_font_color('gray')

		numberdos.set_border(style=1)
		numberdos.set_font_size(10)

		numbertres.set_border(style=1)
		numbertres.set_font_size(10)

		boldcentred = workbook.add_format({'bold': True})
		boldcentred.set_align('center')
		boldcentred.set_align('vcenter')
		boldcentred.set_border(style=1)
		boldcentred.set_text_wrap(True)
		boldcentred.set_font_size(10)

		boldcentredred = workbook.add_format({'bold': True})
		boldcentredred.set_align('center')
		boldcentredred.set_align('vcenter')
		boldcentredred.set_border(style=1)
		boldcentredred.set_font_color('red')
		boldcentredred.set_text_wrap(True)
		boldcentredred.set_font_size(10)


		numbersix = workbook.add_format()
		numbersix.set_num_format('#,##0.00')
		numbersix.set_text_wrap()
		numbersix.set_border()

		numbersixred = workbook.add_format()
		numbersixred.set_num_format('#,##0.00')
		numbersixred.set_font_color('red')
		numbersixred.set_border()

		title = workbook.add_format()
		title.set_font_size(14)
		title.set_bold(True)

		title2 = workbook.add_format()
		title2.set_font_size(12)
		title2.set_font_color('blue')

		blanco = workbook.add_format()
		blanco.set_bg_color('white')

		worksheet.set_column('A:A', 2.86,blanco)
		worksheet.set_column('B:B', 7.71,blanco)
		worksheet.set_column('C:C', 9,blanco)
		worksheet.set_column('D:D', 9,blanco)
		worksheet.set_column('E:E', 22,blanco)
		worksheet.set_column('F:F', 13,blanco)
		worksheet.set_column('G:G', 85,blanco)
		worksheet.set_column('H:H', 25,blanco)
		worksheet.set_column('I:I', 8,blanco)
		worksheet.set_column('J:P', 10,blanco)
		worksheet.set_column('Q:Y', 13,blanco)
		worksheet.set_column('Z:Z', 21,blanco)
		worksheet.set_column('AA:AA', 14,blanco)
		worksheet.set_column('AB:AB', 14,blanco)
		worksheet.set_column('AC:AC', 14,blanco)
		worksheet.set_column('AD:AD', 14,blanco)
		worksheet.set_column('AE:AE', 14,blanco)
		worksheet.set_column('AF:AF', 14,blanco)
		worksheet.set_column('AI:AI', 10,blanco)
		worksheet.set_column('AJ:AJ', 40,blanco)
		worksheet.set_column('AR:AR', 50,blanco)

		worksheet.set_row(4,49.5)
		worksheet.set_row(3,9)
		worksheet.set_row(2,15.75)
		worksheet.set_row(1,18)


		worksheet.write(1,1, u"Resumen de Lotes", title)
		worksheet.write(2,1, u"Fecha del :" + str(self.fecha_inicio) + " al " + str(self.fecha_final), title2)

		columnas = [u'N° Lote',
					u'Fecha recepción',
					u'Fecha consumo',
					u'Procedencia',
					u'DNI/RUC',
					u'Proveedor de Mineral',
					u'Tipo Material',
					u'Mineral',
					u'Sacos',
					u'P. Húmedo TM',
					u'% Humedad',
					u'P. Seco TM',
					u'% Recuperación',
					u'Puntos Param.',
					u'Porcentaje Param.',
					u'Ley Au oz/TC',
					u'Ley Au gr/TM',
					u'Fino Au Gr',
					u'Ley Ag oz/Tc',
					u'Precio US$/OZ',
					u'Margen precio internacional',
					u'Maquila US$TC',
					u'NaOH kg/TN',
					u'NaCN kg/TN',
					u'Consumo Q. Valorado',
					u'G. Adm',
					u'Total Consumo Q y G. Adm.',
					u'Factor Ajuste',
					u'Costo/TM',
					u'Por Pagar Costo/TM',
					u'Indice comparativo',
					u'Fecha Retiro De Lote',
					u'Penalidad',
					u'Flete',
					u'Nombre de Fletero',
					u'Nro Placa',
					u'Guia Remitente',
					u'Guia Transportista',
					u'Código Compromiso',
					u'Código Concesión',
					u'Nombre Concesió',
					u'Ubigeo Concesión Distrito-Provincia-Departamento',
					u'Acopiador',
					u'Estado']

		for i in range(len(columnas)):
			worksheet.write(4,i+1, columnas[i], boldcentred)
		worksheet.write(4,1,u'N° Lote',boldcentredred)

		totales= [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		x= 5
		for liqui in self.env['purchase.liquidation'].search(filtro):
			worksheet.set_row(x,12.75)
			# linea = None
			tt = self.env['purchase.liquidation.line'].search([('parent','=',liqui.id)])
			# if len(tt)>0:
			# 	linea = tt[0]

			dic_state = {
				'draft':'Dato',
				'proposal':'Propuesta',
				'negotiated':'Negociado',
				'done':'Renegociado',
			}

			if liqui.state == 'draft':

				numberdosespecial = workbook.add_format({'num_format':"""_ "$"* #,##0.00_ ;_ "$"* -#,##0.00_ ;_ "$"* "-"??_ ;_ @_ """})
				numberdosespecial.set_border(style=1)
				numberdosespecial.set_font_size(10)
				numberdosespecial.set_font_color('red')


				numbertres = workbook.add_format({'num_format':'0.000'})
				numberdos = workbook.add_format({'num_format':'0.00'})
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_font_size(10)

				numberdos.set_border(style=1)
				numberdos.set_font_size(10)

				numbertres.set_border(style=1)
				numbertres.set_font_size(10)


				bord.set_font_color('red')
				numberdos.set_font_color('red')
				numbertres.set_font_color('red')
			elif liqui.state == 'proposal':
				numberdosespecial = workbook.add_format({'num_format':"""_ "$"* #,##0.00_ ;_ "$"* -#,##0.00_ ;_ "$"* "-"??_ ;_ @_ """})
				numberdosespecial.set_border(style=1)
				numberdosespecial.set_font_size(10)
				numberdosespecial.set_font_color('blue')


				numbertres = workbook.add_format({'num_format':'0.000'})
				numberdos = workbook.add_format({'num_format':'0.00'})
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_font_size(10)

				numberdos.set_border(style=1)
				numberdos.set_font_size(10)

				numbertres.set_border(style=1)
				numbertres.set_font_size(10)

				bord.set_font_color('blue')
				numberdos.set_font_color('blue')
				numbertres.set_font_color('blue')
			elif liqui.state == 'negotiated':
				numberdosespecial = workbook.add_format({'num_format':"""_ "$"* #,##0.00_ ;_ "$"* -#,##0.00_ ;_ "$"* "-"??_ ;_ @_ """})
				numberdosespecial.set_border(style=1)
				numberdosespecial.set_font_size(10)
				numberdosespecial.set_font_color('black')


				numbertres = workbook.add_format({'num_format':'0.000'})
				numberdos = workbook.add_format({'num_format':'0.00'})
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_font_size(10)

				numberdos.set_border(style=1)
				numberdos.set_font_size(10)

				numbertres.set_border(style=1)
				numbertres.set_font_size(10)

				bord.set_font_color('black')
				numberdos.set_font_color('black')
				numbertres.set_font_color('black')
			elif liqui.state == 'done':
				numberdosespecial = workbook.add_format({'num_format':"""_ "$"* #,##0.00_ ;_ "$"* -#,##0.00_ ;_ "$"* "-"??_ ;_ @_ """})
				numberdosespecial.set_border(style=1)
				numberdosespecial.set_font_size(10)
				numberdosespecial.set_font_color('green')

				numbertres = workbook.add_format({'num_format':'0.000'})
				numberdos = workbook.add_format({'num_format':'0.00'})
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_font_size(10)

				numberdos.set_border(style=1)
				numberdos.set_font_size(10)

				numbertres.set_border(style=1)
				numbertres.set_font_size(10)

				bord.set_font_color('green')
				numberdos.set_font_color('green')
				numbertres.set_font_color('green')

			for linea in tt:
				col = 1
				worksheet.write(x,col, liqui.name if liqui.id else '', bordred if linea.mineral == 'oro' else bordgray)
				col += 1
				worksheet.write(x,col, str(liqui.in_date) if liqui.in_date else '', bord)
				col += 1
				worksheet.write(x,col, str(liqui.fecha_consumo) if liqui.fecha_consumo else '', bord)
				col += 1
				worksheet.write(x,col, liqui.source_zone.name if liqui.source_zone.id else '', bord)
				col += 1
				worksheet.write(x,col, liqui.supplier_id.type_number if liqui.supplier_id.id else '', bord)
				col += 1
				worksheet.write(x,col, liqui.supplier_id.name if liqui.supplier_id.id else '', bord)
				col += 1
				worksheet.write(x,col, liqui.material.name_template if liqui.material.name_template else '', bord)
				col += 1
				worksheet.write(x,col, linea.mineral if linea.mineral else '', bordred if linea.mineral == 'oro' else bordgray)
				col += 1
				worksheet.write(x,col, liqui.qty , numberdos)
				col += 1
				worksheet.write(x,col, linea.tmh , numbertres)
				col += 1
				worksheet.write(x,col, linea.h2o , numbertres)
				col += 1
				worksheet.write(x,col, linea.tms , numbertres)
				col += 1
				worksheet.write(x,col, linea.percentage_recovery , numbertres)
				col += 1
				worksheet.write(x,col, linea.points_param if linea.points_param else 0.000 , numbertres)
				col += 1
				worksheet.write(x,col, linea.percentage_param if linea.percentage_param else 0.000 , numbertres)
				col += 1
				worksheet.write(x,col, linea.ley_oz if linea.mineral == 'oro' else 0.000, numbertres)
				col += 1
				worksheet.write(x,col, round(linea.ley_oz*34.285,3) if linea.mineral == 'oro' else 0.000, numbertres)
				col += 1
				worksheet.write(x,col, round(linea.tms*linea.ley_oz*34.285,3) if linea.mineral == 'oro' else 0.000, numbertres)
				col += 1
				worksheet.write(x,col, linea.ley_oz if linea.mineral == 'plata' else 0.000 , numbertres)
				col += 1

				worksheet.write(x,col, linea.int_price , numbertres)
				col += 1
				worksheet.write(x,col, linea.int_price_margin if linea.int_price_margin else 0.000, numbertres)
				col += 1
				worksheet.write(x,col, linea.maquila , numbertres)
				col += 1
				worksheet.write(x,col, linea.soda if linea.soda else 0.000 , numbertres)
				col += 1
				worksheet.write(x,col, linea.cianuro if linea.cianuro else 0.000 , numbertres)
				col += 1
				worksheet.write(x,col, linea.value_consumed if linea.value_consumed else 0.000 , numbertres)
				col += 1
				worksheet.write(x,col, linea.g_adm if linea.g_adm else 0.000 , numbertres)
				col += 1
				worksheet.write(x,col, linea.total_maquila if linea.total_maquila else 0.000 , numbertres)
				col += 1
				worksheet.write(x,col, linea.adjust_factor if linea.adjust_factor else 0.000 , numbertres)
				col += 1
				worksheet.write(x,col, linea.cost , numberdosespecial)
				col += 1
				worksheet.write(x,col, linea.cost_to_pay , numberdosespecial)
				col += 1
				worksheet.write(x,col, linea.comparative_index if linea.comparative_index else 0.000 , numberdosespecial)
				col += 1
				worksheet.write(x,col, liqui.fecha_retiro if liqui.fecha_retiro else '' , bord)
				col += 1
				worksheet.write(x,col, liqui.penalidad , numbertres)
				col += 1
				worksheet.write(x,col, liqui.flete , numbertres)
				col += 1
				worksheet.write(x,col, liqui.fletero if liqui.fletero else '' , bord)
				col += 1

				worksheet.write(x,col, liqui.nro_placa if liqui.nro_placa else '', bord)
				col += 1
				worksheet.write(x,col, liqui.guia_remitente if liqui.guia_remitente else '', bord)
				col += 1
				worksheet.write(x,col, liqui.guia_transp if liqui.guia_transp else '', bord)
				col += 1
				worksheet.write(x,col, liqui.cod_compro if liqui.cod_compro else '', bord)
				col += 1
				worksheet.write(x,col, liqui.cod_conces if liqui.cod_conces else '', bord)
				col += 1
				worksheet.write(x,col, liqui.nombre_conces if liqui.nombre_conces else '', bord)
				col += 1
				worksheet.write(x,col, liqui.subsource_zone.ubigeo if liqui.subsource_zone.ubigeo else '', bord)
				col += 1
				worksheet.write(x,col, liqui.acopiador.name if liqui.acopiador.id else '', bord)
				col += 1
				worksheet.write(x,col, linea.line_type, bord)
				col += 1

				totales[0] += linea.tmh
				totales[1] += linea.tms
				totales[2] += round(linea.ley_oz*34.285,3) if linea.mineral == 'oro' else 0.000
				totales[3] += round(linea.tms*linea.ley_oz*34.285,3) if linea.mineral == 'oro' else 0.000

				totales[4] += liqui.flete
				# totales[5] += linea.cost_to_pay
				# totales[6] += liqui.reintegro_dol
				# totales[7] += liqui.nuevo_importe_dol

				x += 1
			# else:
            #
			# 	worksheet.write(x,1, liqui.name if liqui.id else '', bordred)
			# 	worksheet.write(x,2, str(liqui.fecha_consumo) if liqui.fecha_consumo else '', bord)
			# 	worksheet.write(x,3, liqui.source_zone.name if liqui.source_zone.id else '', bord)
			# 	worksheet.write(x,4, liqui.supplier_id.type_number if liqui.supplier_id.id else '', bord)
			# 	worksheet.write(x,5, liqui.supplier_id.name if liqui.supplier_id.id else '', bord)
			# 	worksheet.write(x,6, liqui.material.name_template if liqui.material.name_template else '', bord)
			# 	worksheet.write(x,7, liqui.qty , numberdos)
			# 	worksheet.write(x,8, 0 , numbertres)
			# 	worksheet.write(x,9, 0 , numbertres)
			# 	worksheet.write(x,10, 0 , numbertres)
			# 	worksheet.write(x,11, 0 , numbertres)
			# 	worksheet.write(x,12, liqui.ley_oz_au , numbertres)
			# 	worksheet.write(x,13, round(liqui.ley_oz_au*34.285,3) , numbertres)
			# 	worksheet.write(x,14, 0 , numbertres)
			# 	worksheet.write(x,15, liqui.ley_oz_ag , numbertres)
            #
			# 	worksheet.write(x,16, liqui.precio_dol , numbertres)
			# 	worksheet.write(x,17, liqui.maquila_dol , numbertres)
			# 	worksheet.write(x,18, liqui.penalidad , numbertres)
			# 	worksheet.write(x,19, liqui.flete , numbertres)
			# 	worksheet.write(x,20, liqui.precio_tm_dol , numberdosespecial)
			# 	worksheet.write(x,21, liqui.importe_dol , numberdosespecial)
			# 	worksheet.write(x,22, liqui.reintegro_dol , numberdosespecial)
			# 	worksheet.write(x,23, liqui.nuevo_importe_dol , numberdosespecial)
			# 	worksheet.write(x,24, liqui.fecha_retiro if liqui.fecha_retiro else '' , bord)
			# 	worksheet.write(x,25, liqui.fletero if liqui.fletero else '' , bord)
            #
			# 	worksheet.write(x,26, liqui.nro_placa if liqui.nro_placa else '', bord)
			# 	worksheet.write(x,27, liqui.guia_remitente if liqui.guia_remitente else '', bord)
			# 	worksheet.write(x,28, liqui.guia_transp if liqui.guia_transp else '', bord)
			# 	worksheet.write(x,29, liqui.cod_compro if liqui.cod_compro else '', bord)
			# 	worksheet.write(x,30, liqui.cod_conces if liqui.cod_conces else '', bord)
			# 	worksheet.write(x,31, liqui.nombre_conces if liqui.nombre_conces else '', bord)
			# 	worksheet.write(x,32, liqui.subsource_zone.ubigeo if liqui.subsource_zone.ubigeo else '', bord)
			# 	worksheet.write(x,33, liqui.acopiador.name if liqui.acopiador.id else '', bord)
			# 	worksheet.write(x,34, 0 , numberdosespecial)
			# 	worksheet.write(x,35, 0 , numberdosespecial)
			# 	worksheet.write(x,36, dic_state[liqui.state], bord)


				# totales[2] += round(liqui.ley_oz_au*34.285,3)
                #
				# totales[4] += liqui.flete
				# totales[5] += liqui.importe_dol
				# totales[6] += liqui.reintegro_dol
				# totales[7] += liqui.nuevo_importe_dol
				# x += 1



			numberdosespecial = workbook.add_format({'num_format':"""_ "$"* #,##0.00_ ;_ "$"* -#,##0.00_ ;_ "$"* "-"??_ ;_ @_ """})
			numberdosespecial.set_border(style=1)
			numberdosespecial.set_font_size(10)
			numberdosespecial.set_font_color('green')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_font_size(10)

			numberdos.set_border(style=1)
			numberdos.set_font_size(10)

			numbertres.set_border(style=1)
			numbertres.set_font_size(10)


			worksheet.write(x,10, totales[0] , numbertres)

			worksheet.write(x,12, totales[1] , numbertres)

			worksheet.write(x,17, totales[2] , numbertres)
			worksheet.write(x,18, totales[3] , numbertres)

			worksheet.write(x,34, totales[4] , numbertres)
			# worksheet.write(x,21, totales[5] , numbertres)
			# worksheet.write(x,22, totales[6] , numbertres)
			# worksheet.write(x,23, totales[7] , numbertres)


		workbook.close()


		f = open( direccion + u'Licitacionesxtg.xlsx', 'rb')


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
