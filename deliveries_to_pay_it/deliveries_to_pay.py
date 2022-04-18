# -*- coding: utf-8 -*-
import base64
import codecs

from openerp.osv import osv
from openerp import models, fields, api

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
from cgi import escape
import decimal

class rendicion_view(models.Model):
	_name = 'rendicion.view'

	_auto = False


	@api.multi
	def get_saldo_entregar(self):
		ini = 0
		for i in self.sorted(key=lambda r: r.id):
			ini += i.ingreso - i.gasto
			i.saldo_entregar = ini


	rendicion_id = fields.Many2one('deliveries.to.pay',u'Rendición')
	periodo = fields.Char('Periodo')
	diario = fields.Char('Diario')
	asiento = fields.Char('Asiento')
	fecha = fields.Date('Fecha')
	td = fields.Char('TD')
	nro_comprobante = fields.Char('Nro. Comprobante')
	ruc_dni = fields.Char('RUC/DNI')
	partner = fields.Char('Partner')
	cuenta = fields.Char('Cuenta')
	ingreso = fields.Float('Ingreso',digits=(12,2))
	gasto = fields.Float('Gasto',digits=(12,2))
	saldo_entregar = fields.Float('Saldo',digits=(12,2),compute="get_saldo_entregar")
	importe_me = fields.Float('Importe ME',digits=(12,2))
	tipo_camb = fields.Float('Tipo de Cambio',digits=(12,3))
	descripcion = fields.Char(u'Descripción')


	def init(self,cr):
		cr.execute("""DROP VIEW IF EXISTS rendicion_view;
			create or replace view rendicion_view as (
				select row_number() over() as id,* from (
select A1.rendicion_id,
A6.code AS periodo,
A5.name as diario,
A2.name as asiento,
A2.date as fecha,
A7.code as td,
A1.nro_comprobante,
A4.type_number as ruc_dni,
A4.NAME AS partner,
A3.code as cuenta,
A1.credit as ingreso,
A1.debit as gasto, 
A1.amount_currency as importe_me, 
A1.currency_rate_it as tipo_camb,
A1.name as descripcion 
FROM  account_move_line A1

left join account_move A2 on A2.id=A1.move_id
left join account_account A3 on A3.id=A1.account_id
left join res_partner A4 on A4.id=A1.partner_id
left join account_journal A5 on A5.id=A2.journal_id
left join account_period A6 on A6.id=A2.period_id
left join it_type_document A7 on A7.id=A1.type_document_id




where

A1.account_id <> (select deliver_account_mn from main_parameter) and
A1.account_id<> (select deliver_account_me from main_parameter) and
A1.account_id<> (select account_journal.internal_account_id as cta_tran_mn from main_parameter left join account_journal on account_journal.id=main_parameter.loan_journal_mn) and
A1.account_id<> (select account_journal.internal_account_id as cta_tran_me from main_parameter left join account_journal on account_journal.id=main_parameter.loan_journal_me) and
(debit + credit ) <> 0 AND
A2.state='posted' 

order by a2.date) tt
			);

 """)

class account_move(models.Model):
	_inherit = "account.move"

	rendicion_id = fields.Many2one('deliveries.to.pay', 'Rendición')
	hide2 = fields.Boolean('Oculto',related="journal_id.is_fixer")


	@api.model
	def create(self, vals):
		x = super(account_move, self).create(vals)
		if 'rendicion_id' in vals:
			if x.journal_id.is_fixer:
				for line in x.line_id:
					line.write({'rendicion_id': x.rendicion_id.id})

				x.rendicion_id.write({'done_move': [(4, x.id)]})
		return x
	
	@api.one
	def write(self, vals):
		if 'rendicion_id' in vals:
			if vals['rendicion_id'] == False:
				self.rendicion_id.write({'done_move': [(3, self.id)]})

		x = super(account_move, self).write(vals)
		self.refresh()
		if 'rendicion_id' in vals:
			if self.journal_id.is_fixer:
				for line in self.line_id:
					line.write({'rendicion_id': self.rendicion_id.id})

				self.rendicion_id.write({'done_move': [(4, self.id)]})
			else:
				for line in self.line_id:
					line.write({'rendicion_id': False})

				self.rendicion_id.write({'done_move': [(3, self.id)]})

		return x


class account_move_line(models.Model):
	_inherit = 'account.move.line'

	@api.multi
	def get_saldo_entregar(self):
		ini = 0
		for i in self.sorted(key=lambda r: r.date):
			ini += i.debit - i.credit
			i.saldo_entregar = ini

	saldo_entregar = fields.Float('Saldo',digits=(12,2),compute="get_saldo_entregar")

class deliveries_to_pay(models.Model):
	_name = 'deliveries.to.pay'

	STATE_SELECTION = [
		('draft', 'Borrador'),
		('aproved', 'Aprobado'),
		('delivered', 'Entregado'),
		('done', 'Rendido'),
		('cancel', 'Cancelado')
	]
	'''
	@api.depends('name')
	def _compute_upper(self):
		for rec in self:
			rec.upper = rec.name.upper() if rec.name else False
	'''

	@api.multi
	def export_pdf(self):
		return {
				'context': {'active_ids':[self.id]},
				'type': 'ir.actions.act_window',
				'res_model': 'print.entregas.rendir.pdf',
				'view_mode': 'form',
				'view_type': 'form',
				'views': [(False, 'form')],
				'target': 'new',
			}


	@api.multi
	def export_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})

		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		workbook = Workbook(direccion +'tempo_entregarendir.xlsx')
		worksheet = workbook.add_worksheet("Apuntes Entrega")
		worksheet1 = workbook.add_worksheet("Apuntes Rendicion")
		worksheet2 = workbook.add_worksheet("Control Saldo")
		
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		numberdos_nb = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 8			
		y= 8			
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		
		#Cabecera de la primera hoja
		#Left Group
		worksheet.write(0,0, self.name, bold)
		worksheet.write(1,0, "Fecha Entrega:", bold)
		worksheet.write(1,1, self.deliver_date, normal)
		worksheet.write(2,0, "Empleado:", bold)
		worksheet.write(2,1, self.partner_id.name, normal)
		worksheet.write(3,0, "Monto Entregado:",bold)
		worksheet.write(3,1, self.deliver_amount,numberdos_nb)
		worksheet.write(4,0, "Caja Entrega:", bold)
		worksheet.write(4,1, self.deliver_journal_id.name, normal)
		worksheet.write(5,0, "Medio Pago:", bold)
		worksheet.write(5,1, self.means_payment_id.description if self.means_payment_id.id != False else '', normal)
		
		#Right Group
		worksheet.write(1,3, "Nro. Comprobante:", bold)
		worksheet.write(1,4, self.invoice_number, normal)
		worksheet.write(2,3, "Memoria:", bold)
		worksheet.write(2,4, self.memory, normal)
		worksheet.write(3,3, u"Fecha Rendición:",bold)
		worksheet.write(3,4, self.done_date if self.done_date else '',normal)
		worksheet.write(4,3, "Monto Rendido:", bold)
		worksheet.write(4,4, self.done_amount, numberdos_nb)
		
		#Cabecera de la segunda hoja
		#Left Group
		worksheet1.write(0,0, self.name, bold)
		worksheet1.write(1,0, "Fecha Entrega:", bold)
		worksheet1.write(1,1, self.deliver_date, normal)
		worksheet1.write(2,0, "Empleado:", bold)
		worksheet1.write(2,1, self.partner_id.name, normal)
		worksheet1.write(3,0, "Monto Entregado:",bold)
		worksheet1.write(3,1, self.deliver_amount,numberdos_nb)
		worksheet1.write(4,0, "Caja Entrega:", bold)
		worksheet1.write(4,1, self.deliver_journal_id.name, normal)
		worksheet1.write(5,0, "Medio Pago:", bold)
		worksheet1.write(5,1, self.means_payment_id.description if self.means_payment_id.id != False else '', normal)
		
		#Right Group
		worksheet1.write(1,3, "Nro. Comprobante:", bold)
		worksheet1.write(1,4, self.invoice_number, normal)
		worksheet1.write(2,3, "Memoria:", bold)
		worksheet1.write(2,4, self.memory, normal)
		worksheet1.write(3,3, u"Fecha Rendición:",bold)
		worksheet1.write(3,4, self.done_date if self.done_date else '',normal)
		worksheet1.write(4,3, "Monto Rendido:", bold)
		worksheet1.write(4,4, self.done_amount, numberdos_nb)
		
		#Cabecera de la tercera hoja
		#Left Group
		worksheet2.write(0,0, self.name, bold)
		worksheet2.write(1,0, "Fecha Entrega:", bold)
		worksheet2.write(1,1, self.deliver_date, normal)
		worksheet2.write(2,0, "Empleado:", bold)
		worksheet2.write(2,1, self.partner_id.name, normal)
		worksheet2.write(3,0, "Monto Entregado:",bold)
		worksheet2.write(3,1, self.deliver_amount,numberdos_nb)
		worksheet2.write(4,0, "Caja Entrega:", bold)
		worksheet2.write(4,1, self.deliver_journal_id.name, normal)
		worksheet2.write(5,0, "Medio Pago:", bold)
		worksheet2.write(5,1, self.means_payment_id.description if self.means_payment_id.id != False else '', normal)
		
		#Right Group
		worksheet2.write(1,3, "Nro. Comprobante:", bold)
		worksheet2.write(1,4, self.invoice_number, normal)
		worksheet2.write(2,3, "Memoria:", bold)
		worksheet2.write(2,4, self.memory, normal)
		worksheet2.write(3,3, u"Fecha Rendición:",bold)
		worksheet2.write(3,4, self.done_date if self.done_date else '',normal)
		worksheet2.write(4,3, "Monto Rendido:", bold)
		worksheet2.write(4,4, self.done_amount, numberdos_nb)
		
		
		#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
		import datetime
		#worksheet.write(1,1, str(datetime.datetime.today())[:10], normal)
		
		worksheet.write(7,0, u"Número",boldbord)
		worksheet.write(7,1, "Comprobante",boldbord)
		worksheet.write(7,2, "Fecha",boldbord)
		worksheet.write(7,3, "Periodo",boldbord)
		worksheet.write(7,4, "Diario",boldbord)
		worksheet.write(7,5, "Empresa",boldbord)
		worksheet.write(7,6, "Importe",boldbord)
		worksheet.write(7,7, "Importe Divisa",boldbord)
		worksheet.write(7,8, "Estado",boldbord)
		
		worksheet1.write(7,0, u"Número",boldbord)
		worksheet1.write(7,1, "Comprobante",boldbord)
		worksheet1.write(7,2, "Fecha",boldbord)
		worksheet1.write(7,3, "Periodo",boldbord)
		worksheet1.write(7,4, "Diario",boldbord)
		worksheet1.write(7,5, "Empresa",boldbord)
		worksheet1.write(7,6, "Importe",boldbord)
		worksheet1.write(7,7, "Importe Divisa",boldbord)
		worksheet1.write(7,8, "Glosa",boldbord)
		worksheet1.write(7,9, "Estado",boldbord)
		
		#Primer detalle
		for line in self.deliver_move:
			worksheet.write(x,0,line.name if line.name else '' ,bord )
			worksheet.write(x,1,line.invoice_number if line.invoice_number  else '',bord )
			worksheet.write(x,2,line.date if line.date  else '',bord)
			worksheet.write(x,3,line.period_id.name if line.period_id  else '',bord)
			worksheet.write(x,4,line.journal_id.name if line.journal_id  else '',bord)
			worksheet.write(x,5,line.partner_id.name if line.partner_id  else '',bord)
			worksheet.write(x,6,line.amount ,numberdos)
			worksheet.write(x,7,line.amount_currency_deliver ,numberdos)
			#worksheet.write(x,7,line.state if  line.state else '',bord)
			x+=1
		
		#Segundo detalle
		for line in self.done_move:
			worksheet1.write(y,0,line.name if line.name else '' ,bord )
			worksheet1.write(y,1,line.invoice_number if line.invoice_number  else '',bord )
			worksheet1.write(y,2,line.date if line.date  else '',bord)
			worksheet1.write(y,3,line.period_id.name if line.period_id  else '',bord)
			worksheet1.write(y,4,line.journal_id.name if line.journal_id  else '',bord)
			worksheet1.write(y,5,line.partner_id.name if line.partner_id  else '',bord)
			worksheet1.write(y,6,line.amount ,numberdos)
			worksheet1.write(x,7,line.amount_currency_deliver ,numberdos)
			worksheet1.write(y,8,line.glosa_deliver if line.glosa_deliver else '',bord)
			#worksheet1.write(y,8,line.state if  line.state else '',bord)
			y+=1
		
		#Tercer detalle
		worksheet2.write(7,0, "Diario:", bold)
		worksheet2.write(7,1, self.journal_id.name if self.journal_id else '', normal)
		worksheet2.write(8,0, "Cta. Desajuste:", bold)
		worksheet2.write(8,1, self.account_refund_id.name if self.account_refund_id else '', normal)
		worksheet2.write(9,0, u"Cta. Analítica:",bold)
		worksheet2.write(9,1, self.account_analytic_refund_id.name if self.account_analytic_refund_id else '',normal)
		worksheet2.write(10,0, "Monto Devolver:", bold)
		worksheet2.write(10,1, self.refund_amount, numberdos_nb)
		
		
		tam_col = [22,30,22,22,30,22,22,22,22,22]

		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		
		worksheet1.set_column('A:A', tam_col[0])
		worksheet1.set_column('B:B', tam_col[1])
		worksheet1.set_column('C:C', tam_col[2])
		worksheet1.set_column('D:D', tam_col[3])
		worksheet1.set_column('E:E', tam_col[4])
		worksheet1.set_column('F:F', tam_col[5])
		worksheet1.set_column('G:G', tam_col[6])
		worksheet1.set_column('H:H', tam_col[7])
		worksheet1.set_column('I:I', tam_col[8])
		worksheet1.set_column('J:J', tam_col[9])
		
		worksheet2.set_column('A:A', tam_col[0])
		worksheet2.set_column('B:B', tam_col[1])
		worksheet2.set_column('C:C', tam_col[2])
		worksheet2.set_column('D:D', tam_col[3])
		worksheet2.set_column('E:E', tam_col[4])
		worksheet2.set_column('F:F', tam_col[5])
		worksheet2.set_column('G:G', tam_col[6])
		worksheet2.set_column('H:H', tam_col[7])
		worksheet2.set_column('I:I', tam_col[8])
		worksheet2.set_column('J:J', tam_col[9])
		
		
		
		workbook.close()
			
		f = open(direccion + 'tempo_entregarendir.xlsx', 'rb')


		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'EntregaRendir.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id

		#import os
		#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
			}
	


	
	def write(self, cr, uid, ids, vals, context=None):
		for deliver in self.browse(cr, uid, ids, context):
			if 'journal_id' in vals:
				journal = self.pool.get('account.journal').browse(cr, uid, vals['journal_id'], context)
				if journal and deliver.state != 'done' and deliver.refund_amount > 0:
					if journal.default_debit_account_id.id == False:
						raise osv.except_osv('Error!', 'Debe configurar una cuenta de debito por defecto en el diario de devoluciones.')
					vals.update({'account_refund_id': journal.default_debit_account_id.id})
				if journal and deliver.state != 'done' and deliver.refund_amount < 0:
					if not 'account_refund_id' in vals:
						parameters = self.pool.get('main.parameter').search(cr, uid, [])
						if len(parameters)==0:
							raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
						parameter = self.pool.get('main.parameter').browse(cr, uid, parameters[0], context)
						if parameter.loan_account_mn.id == False:
							raise osv.except_osv('Error!', 'Debe configurar una cuenta de prestamos en moneda nacional en los Parametros de la configuracion contable.')
						if parameter.loan_account_me.id == False:
							raise osv.except_osv('Error!', 'Debe configurar una cuenta de prestamos en moneda extranjera en los Parametros de la configuracion contable.')
						vals.update({'account_refund_id': parameter.loan_account_mn.id if deliver.deliver_journal_id.currency.id == False else parameter.loan_account_me.id})
		return super(deliveries_to_pay, self).write(cr, uid, ids, vals, context)

	def unlink(self, cr, uid, ids, context=None):
		for rendicion in self.pool.get('deliveries.to.pay').browse(cr,uid,ids,context):
			raise osv.except_osv('Acción Inválida!', 'Las rendiciones no pueden borrarse')
			if rendicion.state != 'draft':
				raise osv.except_osv('Acción Inválida!', 'Solo se puede borrar una rendicion en estado Borrador')
			if len(rendicion.done_move) > 0:
				raise osv.except_osv('Acción Inválida!', 'no se puede eliminar una rendicion que tiene pagos a facturas')
				
			return super (deliveries_to_pay, self).unlink(cr,uid,ids,context)
		return super (deliveries_to_pay, self).unlink(cr,uid,ids,context)
		
	def copy(self, cr, uid, id, default=None, context=None):
		default = default or {}
		default.update({
			'name': 'Rendicion Borrador',
			'deliver_move': False,
			'done_move': False,
			'refund_journal_id': False,
			'means_payment_refund_id': False,
			'state': 'draft',
		})
		return super(deliveries_to_pay, self).copy(cr, uid, id, default, context)
	
	@api.depends('deliver_amount')
	def _refund_amount(self):
		for deliver in self:
			deliver.refund_amount = deliver.deliver_amount - deliver.done_amount
			'''
			if deliver.refund_amount < 0:
				print 'GOGOGOG'
				parameters = self.env['main.parameter'].search([])
				if len(parameters)==0:
					raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
				parameter = parameters[0]
				if parameter.loan_account_mn.id == False:
					raise osv.except_osv('Error!', 'Debe configurar una cuenta de prestamos en moneda nacional en los Parametros de la configuracion contable.')
				if parameter.loan_account_me.id == False:
					raise osv.except_osv('Error!', 'Debe configurar una cuenta de prestamos en moneda extranjera en los Parametros de la configuracion contable.')
				deliver.account_refund_id = parameter.loan_account_mn.id if deliver.deliver_journal_id.currency.id == False else parameter.loan_account_me.id
			'''
			
	@api.onchange('journal_id')
	def onchange_journal_id(self):
		if self.journal_id and self.state != 'done' and self.refund_amount > 0:
			if self.journal_id.default_debit_account_id.id == False:
				raise osv.except_osv('Error!', 'Debe configurar una cuenta de debito por defecto en el diario de devoluciones.')
			self.account_refund_id = self.journal_id.default_debit_account_id.id
		if self.journal_id and self.state != 'done' and self.refund_amount < 0:
			parameters = self.env['main.parameter'].search([])
			if len(parameters)==0:
				raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
			parameter = parameters[0]
			if parameter.loan_account_mn.id == False:
				raise osv.except_osv('Error!', 'Debe configurar una cuenta de prestamos en moneda nacional en los Parametros de la configuracion contable.')
			if parameter.loan_account_me.id == False:
				raise osv.except_osv('Error!', 'Debe configurar una cuenta de prestamos en moneda extranjera en los Parametros de la configuracion contable.')
			self.account_refund_id = parameter.loan_account_mn.id if self.deliver_journal_id.currency.id == False else parameter.loan_account_me.id
	
	'''
	@api.depends('deliver_amount')
	def _done_amount(self):
		parameters = self.env['main.parameter'].search([])
		if len(parameters)==0:
			raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
		parameter = parameters[0]
		for deliver in self:
			done_moves = deliver.done_move
			val = 0.00
			print '------------------------------------'
			print 'BEGIN', val
			if deliver.state != 'done':
				for done_move in done_moves:
					for line in done_move.line_id:
						if deliver.deliver_journal_id.currency.id != False:
							if line.amount_currency<0:
								val += float(abs(line.amount_currency))
								print 'E1', val
						else:
							if line.debit>0:
								val += float(line.debit)
								print 'E2', val
			else:
				for done_move in done_moves:
					for line in done_move.line_id:
						if deliver.deliver_journal_id.currency.id != False:
							if line.amount_currency<0:
								val += float(abs(line.amount_currency))
								print 'E3', val
							if line.account_id.id == parameter.loan_account.id or line.account_id.id == deliver.deliver_journal_id.id:
								val -= float(abs(line.amount_currency))
								print 'E4', val
						else:
							if line.debit>0:
								val += float(line.debit)
								print 'E5', val
							if line.account_id.id == parameter.deliver_account_mn.id or line.account_id.id == parameter.deliver_account_me.id: 
								val -= float(abs(line.debit))	
								print 'E6', val	
			print 'END', val
			deliver.done_amount = val
	'''
	
	@api.depends('deliver_amount')
	def _done_amount(self):
		parameters = self.env['main.parameter'].search([])
		if len(parameters)==0:
			raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
		parameter = parameters[0]
		for deliver in self:
			done_moves = deliver.done_move
			val = 0.00
			print '------------------------------------'
			print 'BEGIN', val
			if deliver.state != 'done':
				for done_move in done_moves:
					for line in done_move.line_id:
						if deliver.deliver_journal_id.currency.id != False:
							if line.amount_currency<0:
								val += float(abs(line.amount_currency))
								print 'E1', val
						else:
							if line.debit>0:
								val += float(line.debit)
								print 'E2', val
			else:
				for done_move in done_moves:
					for line in done_move.line_id:
						if deliver.deliver_journal_id.currency.id != False:
							if line.amount_currency<0:
								val += float(abs(line.amount_currency))
								print 'E3', val
							if line.account_id.id == parameter.loan_account_me.id or line.account_id.id == deliver.deliver_journal_id.id:
								val -= float(abs(line.amount_currency))
								print 'E4', val
						else:
							#if line.debit>0:
							#	val += float(line.debit)
							#	print 'E5', val
							if line.account_id.id == parameter.deliver_account_mn.id or line.account_id.id == parameter.deliver_account_me.id: 
								val += float((line.credit - line.debit))	
								print 'E6', val
			print 'END', val
			deliver.done_amount = val
	
	@api.depends('refund_amount')
	def _saldo_amount(self):
		for deliver in self:
			deliver.saldo_amount = deliver.deliver_amount - deliver.done_amount
	
	@api.one
	def get_move_lines_deliveries(self):
		contenedor = []
		parametro = self.env['main.parameter'].search([])[0]
		for i in self.deliver_move:
			for j in i.line_id:
				if i.journal_id.currency:
					if j.account_id.id == parametro.deliver_account_me.id:
						contenedor.append( j.id )
				else:
					if j.account_id.id == parametro.deliver_account_mn.id:
						contenedor.append( j.id )

		for i in self.done_move:
			for j in i.line_id:
				if i.journal_id.currency:
					if j.account_id.id == parametro.deliver_account_me.id:
						contenedor.append( j.id )
				else:
					if j.account_id.id == parametro.deliver_account_mn.id:
						contenedor.append( j.id )
		self.move_lines_deliveries = contenedor
			
	
	name = fields.Char('Nombre',size=50, default='Rendicion Borrador')
	deliver_date = fields.Date('Fecha de Entrega')
	partner_id = fields.Many2one('res.partner','Empleado')
	deliver_amount = fields.Float('Monto Entregado', digits=(12,2))
	deliver_journal_id = fields.Many2one('account.journal','Metodo Pago')
	means_payment_id = fields.Many2one('it.means.payment', 'Medio de Pago',ondelete='restrict')
	invoice_number = fields.Char('Numero Comprobante', size=50)
	memory = fields.Char('Memoria', size=50)
	ref_int = fields.Char('Referencia', size=30)
	done_date = fields.Date('Fecha de Rendicion')
	done_amount = fields.Float('Monto Rendido', digits=(12,2), compute='_done_amount')
	saldo_amount = fields.Float('Saldo', digits=(12,2), compute='_saldo_amount')

	move_lines_deliveries = fields.One2many('rendicion.view','rendicion_id','Lineas de Rendición')

	deliver_move = fields.Many2many('account.move', 'deliver_account_move_rel', 'balance_fixer_id', 'account_move_id', string="Asiento de Entrega", readonly=True)
	deliver_move_hidden = fields.Many2many('account.move', 'deliver_account_move_rel_hidden', 'balance_fixer_id', 'account_move_id', string="Asiento de Entrega", readonly=True)
	done_move = fields.Many2many('account.move', 'done_account_move_rel', 'balance_fixer_id', 'account_move_id', string="Asiento de Rendicion", readonly=True)
	done_move_hidden = fields.Many2many('account.move', 'done_account_move_rel_hidden', 'balance_fixer_id', 'account_move_id', string="Asiento de Rendicion", readonly=True)
	refund_journal_id = fields.Many2one('account.journal', string="Metodo de Pago")
	journal_id = fields.Many2one('account.journal','Diario')
	account_refund_id = fields.Many2one('account.account','Diario')
	account_analytic_refund_id = fields.Many2one('account.analytic.account','Diario')
	#means_payment_refund_id = fields.Many2one('it.means.payment', 'Medio de Pago')
	#refund_amount = fields.function(_refund_amount,string='Monto a devolver',digits=(12,2))
	refund_amount = fields.Float('Monto Devolver', digits=(12,2), compute='_refund_amount')
	state = fields.Selection(STATE_SELECTION, 'Status', readonly=True, select=True, default='draft')

	deliver_a = fields.Char('Deliver A', size=50,copy=False)
	asiento_d_a = fields.Many2one('account.move','Asiento D A',copy=False)
	deliver_b = fields.Char('Deliver B', size=50,copy=False)
	asiento_d_b = fields.Many2one('account.move','Asiento D B',copy=False)
	done_a = fields.Char('Done A', size=50,copy=False)
	asiento_done_a = fields.Many2one('account.move','Asiento DONE A',copy=False)
	done_b = fields.Char('Done B', size=50,copy=False)
	asiento_done_b = fields.Many2one('account.move','Asiento DONE B',copy=False)
	done_loan = fields.Char('Done Loan', size=50,copy=False)
	asiento_d_loan = fields.Many2one('account.move','Asiento D LOAN',copy=False)
	period_id = fields.Many2one('account.period','Periodo',copy=False)
	

	partner_reporte = fields.Many2one('res.partner','Partner',copy=False)	

	@api.multi
	def balance_aprove(self):
		vals = {}
		if vals.get('name','Rendicion Borrador')=='Rendicion Borrador':
			vals['name'] = self.pool.get('ir.sequence').get(self.env.cr, self.env.uid, 'deliveries.to.pay') or '/'
		vals.update({'state': 'aproved'})
		self.write(vals)
		return True
	
	@api.multi
	def action_cancel(self):
		parameters = self.env['main.parameter'].search([])
		if len(parameters)==0:
			raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
		parameter = parameters[0]
		for deliver in self:
			if deliver.state == 'aproved':
				self.write({'state': 'draft', 'name': 'Rendicion Borrador'})
				return True
			elif deliver.state == 'delivered':
				#if len(deliver.done_move) > 0:
				#	raise osv.except_osv('Acción Inválida!', 'No se puede cancelar una rendicion que tiene pagos a facturas')
				if len(deliver.deliver_move_hidden) > 0:
					"""
					for move in deliver.deliver_move_hidden:
						self.pool.get('account.move').write(self.env.cr,self.env.uid,[move.id],{'state': 'draft'},self.env.context)
						lines_ids = self.pool.get('account.move.line').search(self.env.cr, self.env.uid, [('move_id', '=', move.id)])
						self.pool.get('account.move.line').unlink(self.env.cr,self.env.uid,lines_ids,self.env.context)
						print 'TO_DELETE_ID', move.id
						vals = {
							'tax_amount': 0.0, 
							'name': 'ANULADO', 
							'ref': False,
							'nro_comprobante': False,
							'currency_id': move.journal_id.currency.id, 
							'debit': 0,
							'credit': 0, 
							'date_maturity': False, 
							'date': move.date,
							'amount_currency': 0, 
							'account_id': move.journal_id.internal_account_id.id,
							'partner_id': False,
							'move_id': move.id,
						}
						new_line = self.pool.get('account.move.line').create(self.env.cr, self.env.uid, vals, self.env.context)
						print 'New Line', new_line
						self.pool.get('account.move').post(self.env.cr, self.env.uid, [move.id], context=None)
					self.env.cr.execute(""delete from deliver_account_move_rel where balance_fixer_id ='"" + str(deliver.id) + ""'"")
					self.env.cr.execute(""delete from deliver_account_move_rel_hidden where balance_fixer_id ='"" + str(deliver.id) + ""'"")
					"""
					self.pool.get('account.move').write(self.env.cr,self.env.uid,deliver.deliver_move_hidden.mapped('id'),{'state': 'draft'},self.env.context)
					self.pool.get('account.move').unlink(self.env.cr,self.env.uid,deliver.deliver_move_hidden.mapped('id'),self.env.context)
				self.write({'state': 'draft'})
				return True
			elif deliver.state == 'done':
				currency_id = deliver.deliver_journal_id.currency.id
				account_search_id = parameter.deliver_account_mn.id if currency_id == False else parameter.deliver_account_me.id
				reconcile_ids = self.env['account.move.line'].search([('rendicion_id','=',deliver.id),('account_id','=',account_search_id)]).mapped('id')
				print 'reconcile', reconcile_ids
				self.pool.get('account.move.line')._remove_move_reconcile(self.env.cr, self.env.uid, reconcile_ids)
				for move in deliver.done_move_hidden:
					#if move.journal_id.id in [deliver.refund_journal_id.id, parameter.loan_journal_mn.id, parameter.loan_journal_me.id]:
					self.pool.get('account.move').write(self.env.cr,self.env.uid,[move.id],{'state': 'draft'},self.env.context)
					lines_ids = self.pool.get('account.move.line').search(self.env.cr, self.env.uid, [('move_id', '=', move.id)])
					self.pool.get('account.move.line').unlink(self.env.cr,self.env.uid,lines_ids,self.env.context)
					print 'TO_DELETE_ID', move.id
					vals = {
						'tax_amount': 0.0, 
						'name': 'ANULADO', 
						'ref': False,
						'nro_comprobante': False,
						'currency_id': move.journal_id.currency.id, 
						'debit': 0,
						'credit': 0, 
						'date_maturity': False, 
						'date': move.date,
						'amount_currency': 0, 
						'account_id': move.journal_id.internal_account_id.id,
						'partner_id': False,
						'move_id': move.id,
					}
					new_line = self.pool.get('account.move.line').create(self.env.cr, self.env.uid, vals, self.env.context)
					print 'New Line', new_line
					self.pool.get('account.move').post(self.env.cr, self.env.uid, [move.id], context=None)

					self.env.cr.execute("""delete from done_account_move_rel where account_move_id ='""" + str(move.id) + """'""")
					self.env.cr.execute("""delete from done_account_move_rel_hidden where account_move_id ='""" + str(move.id) + """'""")
					#self.pool.get('account.move').write(self.env.cr,self.env.uid,[move.id],{'state': 'draft'},self.env.context)
					#self.pool.get('account.move').unlink(self.env.cr,self.env.uid,[move.id],self.env.context)
				self.write({'state': 'delivered'})
				return True
	@api.multi
	def balance_deliver(self):
		if not self.asiento_d_b.id:
			ids_move = []
			ids_move_hidden = []
			#Reviso si existe el objeto parametros
			parameters = self.env['main.parameter'].search([])
			if len(parameters)==0:
				raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
			parameter = parameters[0]
			
			name_deliver = None
			if self.name == 'Rendicion Borrador' or self.name is None or self.name == False:
				name_deliver = self.pool.get('ir.sequence').get(self.env.cr, self.env.uid, 'deliveries.to.pay') or '/'
				self.write({'name': name_deliver})
			else:
				name_deliver = self.name
				
			for deliver in self:
				journal = None
				#Reviso si estan configuradas las cuentas de rendiciones
				if deliver.deliver_journal_id.currency.id != False:
					if parameter.deliver_account_me.id == False:
						raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de rendiciones en Moneda Extranjera.')
					if parameter.loan_journal_me.id == False:
						raise osv.except_osv('Acción Inválida!', 'Debe configurar un diario de rendiciones en Moneda Extranjera.')
					journal = parameter.loan_journal_me
				else:
					if parameter.deliver_account_mn.id == False:
						raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de rendiciones en Moneda Nacional.')
					if parameter.loan_journal_mn.id == False:
						raise osv.except_osv('Acción Inválida!', 'Debe configurar un diario de rendiciones en Moneda Nacional.')
					journal = parameter.loan_journal_mn
				
				currency_id = deliver.deliver_journal_id.currency.id
				monto = deliver.deliver_amount
				monto_currency = 0
				
				if currency_id != False:
					currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',deliver.deliver_date), ('currency_id','=', currency_id)])
					if len(currency_rate) == 0:
						raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
					monto_currency = monto
					monto = monto * currency_rate[0].type_sale
				
				obj_sequence = self.pool.get('ir.sequence')
				
				
				if deliver.deliver_journal_id.internal_account_id.id == False:
					raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de transferencias internas para el Metodo de Pago seleccionado.')
				if journal.internal_account_id.id == False:
					raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de transferencias internas para el diario de Entregas a Rendir.')
				
				lst = self.env['account.period'].search([('date_start','<=',deliver.deliver_date),('date_stop','>=',deliver.deliver_date)])
				if len(lst) == 0:
					raise osv.except_osv('Alerta!', 'No existe un periodo para la fecha ' + deliver.deliver_date + '.')
				period_id=lst[0]
				
				#Asiento que saca el dinero de la caja
				id_seq = deliver.deliver_journal_id.sequence_id.id
				#name = None
				"""
				context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
				name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
				self.write({'deliver_a': name, 'period_id':period_id.id})
				"""
				name = None
				if deliver.period_id.id != period_id.id:
					#self.env.context.update({'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}) 
					context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
					name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
					self.write({'deliver_a': name, 'period_id':period_id.id})
				else:
					if deliver.deliver_a == False:
						context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
						name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
						self.write({'deliver_a': name})
					else:
						name = deliver.deliver_a
				
				cc = [(0,0,{
						'tax_amount': 0.0, 
						'name': deliver.memory, 
						'ref': False,
						'nro_comprobante':deliver.invoice_number,
						'currency_id': False, 
						'debit': monto,
						'credit': 0, 
						'date_maturity': False, 
						'date': deliver.deliver_date,
						'amount_currency': 0, 
						'account_id': deliver.deliver_journal_id.internal_account_id.id,
						'partner_id': deliver.partner_id.id,
						'rendicion_id': deliver.id,
						}),
					(0,0,{
						'tax_amount': 0.0, 
						'name': deliver.memory, 
						'ref': False, 
						'nro_comprobante':deliver.invoice_number,
						'currency_id': currency_id if currency_id != False else None, 
						'debit': 0,
						'credit': monto,
						'date_maturity': False, 
						'date': deliver.deliver_date,
						'amount_currency': -1 * monto_currency,
						'account_id': deliver.deliver_journal_id.default_debit_account_id.id,
						'partner_id': False,
						'rendicion_id': deliver.id,
					})]
				
				# raise osv.except_osv('Alerta', cc)					
									
				move = {
						'name':name,
						'ref': deliver.name,
						'line_id': cc,
						'date': deliver.deliver_date,
						'journal_id': deliver.deliver_journal_id.id,
						'period_id':period_id.id,
						'company_id': deliver.partner_id.company_id.id,
					}
				move_obj = self.pool.get('account.move')
				move_id1 = move_obj.create(self.env.cr, self.env.uid, move, context=None)


				self.write({'asiento_d_a':move_id1})

				move_id_act=move_id1
				move_obj.post(self.env.cr, self.env.uid, [move_id1], context=None)
				#ids_move.append(move_id_act)
				ids_move_hidden.append(move_id_act)

				
				#Asiento que mete el dinero al diario de rendicion
				id_seq2 = journal.sequence_id.id
				#name2 = None
				"""
				context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
				name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
				self.write({'deliver_b': name2, 'period_id':period_id.id})
				"""

				name2 = None
				if deliver.period_id.id != period_id.id:
					#self.env.context.update({'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}) 
					context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
					name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
					self.write({'deliver_b': name2, 'period_id':period_id.id})
				else:
					if deliver.deliver_b == False:
						context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
						name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
						self.write({'deliver_b': name2})
					else:
						name2 = deliver.deliver_b
				
				cc2 = [(0,0,{
						'tax_amount': 0.0, 
						'name': deliver.memory, 
						'ref': False,
						'nro_comprobante':deliver.name,
						'currency_id': currency_id if currency_id != False else None, 
						'debit': monto,
						'credit': 0, 
						'date_maturity': False, 
						'date': deliver.deliver_date,
						'amount_currency': monto_currency, 
						'account_id': parameter.deliver_account_mn.id if currency_id == False else parameter.deliver_account_me.id,
						'partner_id': deliver.partner_id.id,
						'rendicion_id': deliver.id,
						}),
					(0,0,{
						'tax_amount': 0.0, 
						'name': deliver.memory, 
						'ref': False, 
						'nro_comprobante':deliver.name,
						'currency_id': False, 
						'debit': 0,
						'credit': monto,
						'date_maturity': False, 
						'date': deliver.deliver_date,
						'amount_currency': 0.00,
						'account_id': journal.internal_account_id.id,
						'partner_id': False,
						'rendicion_id': deliver.id,
					})]
					
									
				move2 = {
						'name':name2,
						'ref': deliver.name,
						'line_id': cc2,
						'date': deliver.deliver_date,
						'journal_id': journal.id,
						'period_id':period_id.id,
						'company_id': deliver.partner_id.company_id.id,
					}
				move_obj2 = self.pool.get('account.move')
				move_id12 = move_obj.create(self.env.cr, self.env.uid, move2, context=None)

				self.write({'asiento_d_b':move_id12})

				move_id_act2=move_id12
				move_obj2.post(self.env.cr, self.env.uid, [move_id12], context=None)
				ids_move.append(move_id_act2)
				ids_move_hidden.append(move_id_act2)
		
			self.write({'state': 'delivered', 'name': name_deliver, 'deliver_move': [(6, 0, ids_move)], 'deliver_move_hidden': [(6, 0, ids_move_hidden)]})
			return True
	
	@api.multi
	def balance_done(self):
		if not self.asiento_done_a.id:
			ids_move = []
			ids_move_hidden = []
			new_move = None
			
			#Reviso si existe el objeto parametros
			parameters = self.env['main.parameter'].search([])
			if len(parameters)==0:
				raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
			parameter = parameters[0]
			
			for deliver in self:
				refund_amount = deliver.deliver_amount - deliver.done_amount
				currency_amount = 0
				currency_id = None
			
				if deliver.deliver_journal_id.currency.id != False:
					currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',deliver.done_date), ('currency_id','=', deliver.deliver_journal_id.currency.id)])
					if len(currency_rate) == 0:
						raise osv.except_osv('Acción Inválida!', 'no existe un tipo de cambio para la fecha.')
					currency_amount = abs(refund_amount)
					currency_id = deliver.deliver_journal_id.currency.id
					refund_amount = refund_amount * currency_rate[0].type_sale
					
				if abs(refund_amount) > 0.001:
					#invoices = fixer.invoices
					if refund_amount > 0 :
						if deliver.journal_id.id is None or deliver.journal_id.id == False:
							raise osv.except_osv('Acción Inválida!', 'Debe seleccionar un Metodo de Pago para las devoluciones/prestamos en la pestaña Control Saldo.')
						if deliver.journal_id.default_debit_account_id.id is None or deliver.journal_id.default_debit_account_id.id == False:
							raise osv.except_osv('Acción Inválida!', 'Debe seleccionar una cuenta de debito en el metodo de pago seleccionado en la pestaña Control Saldo.')
						
						if deliver.journal_id.internal_account_id.id is None or deliver.journal_id.internal_account_id.id == False:
							raise osv.except_osv('Acción Inválida!', 'Debe seleccionar una cuenta para las transferencias internas en el Metodo de pago.')
						
						
						
						lst = self.env['account.period'].search([('date_start','<=',deliver.done_date),('date_stop','>=',deliver.done_date)])
						if len(lst) == 0:
							raise osv.except_osv('Alerta!', 'No existe un periodo para la fecha ' + deliver.done_date + '.')
						period_id=lst[0]
						
						#Asiento saca dinero en el diario entregas a rendir
						cc = []
						#Ingreso la devolucion
						refund_cc1 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'MONTO DEVUELTO POR ENCARGADO', 
								'ref': False, 
								'currency_id': currency_id,
								'nro_comprobante': deliver.name,
								'debit': refund_amount,
								'credit': 0, 
								'date_maturity': False, 
								'date': deliver.done_date,
								'amount_currency':currency_amount, 
								#'account_id': deliver.account_refund_id.id,
								'account_id': deliver.journal_id.default_debit_account_id.id,
								#'analytic_account_id': deliver.account_analytic_refund_id.id if deliver.account_analytic_refund_id.id != False else False,
								'partner_id': False,
								'rendicion_id': deliver.id,
								})
						cc.append(refund_cc1)

						#parcho al empleado
						employee_fix_cc1 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'MONTO DEVUELTO POR ENCARGADO', 
								'ref': False, 
								'currency_id': False, 
								'nro_comprobante':deliver.name,
								'debit': 0,
								'credit': refund_amount, 
								'date_maturity': False, 
								'date': deliver.done_date,
								'amount_currency': 0.00, 
								'account_id': deliver.journal_id.internal_account_id.id,
								#'analytic_account_id': deliver.account_analytic_refund_id.id if deliver.account_analytic_refund_id.id != False else False,		
								'partner_id': deliver.partner_id.id,
								'rendicion_id': deliver.id,
								})
						cc.append(employee_fix_cc1)
						
						# raise osv.except_osv('Alerta', cc)					
						obj_sequence = self.pool.get('ir.sequence')
						id_seq = deliver.journal_id.sequence_id.id

						"""
						#name = None
						context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
						name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
						self.write({'done_a': name, 'period_id':period_id.id})
						"""
						name = None
						if deliver.period_id.id != period_id.id:
							#if deliver.done_a == False:
							context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
							name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
							self.write({'done_a': name, 'period_id':period_id.id})
						else:
												
							if deliver.done_a == False:
								context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
								name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
								self.write({'done_a': name})
							else:
								name = deliver.done_a



						move = {
								'name':name,
								'ref': deliver.name,
								'line_id': cc,
								'date': deliver.done_date,
								'journal_id': deliver.journal_id.id,
								'period_id':period_id.id,
								'company_id': deliver.partner_id.company_id.id,
							}
						move_obj = self.pool.get('account.move')
						move_id1 = move_obj.create(self.env.cr, self.env.uid, move, context=None)


						self.write({'asiento_done_a':move_id1})

						move_id_act=move_id1
						move_obj.post(self.env.cr, self.env.uid, [move_id1], context=None)
						#ids_move.append(move_id_act)
						ids_move_hidden.append(move_id_act)
						self.write({'done_move_hidden': [(4, move_id_act)]})
						
						journal = parameter.loan_journal_mn if currency_id is None else parameter.loan_journal_me
						if journal.internal_account_id.id == False:
							raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de transferecia en el diario de Entregas a Rendir.')
						
						#Asiento mete dinero en el diario devolucion
						cc2 = []
						#Ingreso la devolucion
						refund_cc2 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'MONTO DEVUELTO POR ENCARGADO', 
								'ref': False, 
								'currency_id': False, 
								'nro_comprobante': deliver.name,
								'debit': refund_amount,
								'credit': 0, 
								'date_maturity': False, 
								'date': deliver.done_date,
								'amount_currency':0.00, 
								'account_id': journal.internal_account_id.id,
								#'analytic_account_id': deliver.account_analytic_refund_id.id if deliver.account_analytic_refund_id.id != False else False,
								'partner_id': False,
								'rendicion_id': deliver.id,
								})
						cc2.append(refund_cc2)

						#parcho al empleado
						employee_fix_cc2 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'MONTO DEVUELTO POR ENCARGADO', 
								'ref': False, 
								'currency_id': currency_id,
								'nro_comprobante': deliver.name,
								'debit': 0,
								'credit': refund_amount, 
								'date_maturity': False, 
								'date': deliver.done_date,
								'amount_currency':currency_amount * -1, 
								'account_id': parameter.deliver_account_mn.id if currency_id is None else parameter.deliver_account_me.id,
								#'analytic_account_id': deliver.account_analytic_refund_id.id if deliver.account_analytic_refund_id.id != False else False,
								'partner_id': deliver.partner_id.id,
								'rendicion_id': deliver.id,
								})
						cc2.append(employee_fix_cc2)

						# raise osv.except_osv('Alerta', cc)					
						id_seq2 = journal.sequence_id.id
						#name2 = None
						name2= None
						"""
						context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
						name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
						self.write({'done_b': name2, 'period_id':period_id.id})
						"""
						
						'''
						if deliver.period_id.id != period_id.id:
							#if deliver.done_b == False:
							self.env.context.update({'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}) 
							name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, self.env.context)
							self.write({'done_b': name2, 'period_id':period_id.id})
						else:
							name2 = deliver.done_b
						'''



						if deliver.period_id.id != period_id.id:
							#if deliver.done_a == False:
							context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
							name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
							self.write({'done_b': name2, 'period_id':period_id.id})
						else:
												
							if deliver.done_b == False:
								context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
								name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
								self.write({'done_b': name2})
							else:
								name2 = deliver.done_b



						move2 = {
								'name':name2,
								'ref': deliver.name,
								'line_id': cc2,
								'date': deliver.done_date,
								'journal_id': journal.id,
								'period_id':period_id.id,
								'company_id': deliver.partner_id.company_id.id,
							}
						move_obj2 = self.pool.get('account.move')
						move_id12 = move_obj.create(self.env.cr, self.env.uid, move2, context=None)


						self.write({'asiento_done_b':move_id12})

						move_id_act2=move_id12
						move_obj2.post(self.env.cr, self.env.uid, [move_id12], context=None)
						ids_move.append(move_id_act2)
						#ids_move_hidden.append(move_id_act2)
						self.write({'done_move_hidden': [(4, move_id_act2)]})
					else:
						
						if deliver.journal_id.id is None or deliver.journal_id.id == False:
							raise osv.except_osv('Acción Inválida!', 'Debe seleccionar un Metodo de Pago para las devoluciones en la pestaña Control Saldo.')
							
						if deliver.account_refund_id.id is None or deliver.account_refund_id.id == False:
							raise osv.except_osv('Acción Inválida!', 'Debe seleccionar una cuenta para las devoluciones/prestamos en la pestaña Control Saldo.')
						'''
						if deliver.journal_id.internal_account_id.id is None or deliver.journal_id.internal_account_id.id == False:
							raise osv.except_osv('Acción Inválida!', 'Debe seleccionar una cuenta para las transferencias internas en el Metodo de pago.')
						'''
						
							
						lst = self.env['account.period'].search([('date_start','<=',deliver.done_date),('date_stop','>=',deliver.done_date)])
						if len(lst) == 0:
							raise osv.except_osv('Alerta!', 'No existe un periodo para la fecha ' + deliver.done_date + '.')
						period_id=lst[0]
						
						journal = parameter.loan_journal_mn if currency_id is None else parameter.loan_journal_me
						if journal.internal_account_id.id == False:
							raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de transferecia en el diario de Entregas a Rendir.')
						
						
						cc1 = []
						#Ingreso la devolucion
						refund_cc1 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'MONTO PAGADO EN EXCESO', 
								'ref': False, 
								'currency_id': currency_id,
								'nro_comprobante': deliver.name,
								'debit': 0,
								'credit': abs(refund_amount), 
								'date_maturity': False, 
								'date': deliver.done_date,
								'amount_currency':currency_amount * -1, 
								'account_id': deliver.account_refund_id.id,
								'analytic_account_id': deliver.account_analytic_refund_id.id if deliver.account_analytic_refund_id.id != False else False,
								'partner_id': deliver.partner_id.id,
								'rendicion_id': deliver.id,
								})
						cc1.append(refund_cc1)

						#parcho al empleado
						employee_fix_cc1 = (0,0,{
								'tax_amount': 0.0, 
								'name': 'MONTO PAGADO EN EXCESO', 
								'ref': False, 
								'currency_id': currency_id,
								'nro_comprobante': deliver.name,
								'debit': abs(refund_amount),
								'credit': 0, 
								'date_maturity': False, 
								'date': deliver.done_date,
								'amount_currency':currency_amount, 
								'account_id': parameter.deliver_account_mn.id if currency_id is None else parameter.deliver_account_me.id,
								'analytic_account_id': deliver.account_analytic_refund_id.id if deliver.account_analytic_refund_id.id != False else False,
								'partner_id': deliver.partner_id.id,
								'rendicion_id': deliver.id,
								})
						cc1.append(employee_fix_cc1)

						# raise osv.except_osv('Alerta', cc)					
						obj_sequence = self.pool.get('ir.sequence')
						id_seq = journal.sequence_id.id
						
						"""
						context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
						name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
						self.write({'done_loan': name, 'period_id':period_id.id})
						"""
						#name = None
						name = None
						'''
						if deliver.period_id.id != period_id.id:
							#if deliver.done_loan == False:
							self.env.context.update({'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}) 
							name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, self.env.context)
							self.write({'done_loan': name, 'period_id':period_id.id})
						else:
							name = deliver.done_loan
						'''


						if deliver.period_id.id != period_id.id:
							#if deliver.done_a == False:
							context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
							name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
							self.write({'done_loan': name, 'period_id':period_id.id})
						else:
												
							if deliver.done_loan == False:
								context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
								name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
								self.write({'done_loan': name})
							else:
								name = deliver.done_loan


						move = {
								'name':name,
								'ref': deliver.name,
								'line_id': cc1,
								'date': deliver.done_date,
								'journal_id': journal.id,
								'period_id':period_id.id,
								'company_id': deliver.partner_id.company_id.id,
								'rendicion_id': deliver.id
							}
						move_obj = self.pool.get('account.move')
						move_id1 = move_obj.create(self.env.cr, self.env.uid, move, context=None)


						self.write({'asiento_d_loan':move_id1})


						move_id_act=move_id1
						move_obj.post(self.env.cr, self.env.uid, [move_id1], context=None)
						#ids_move.append(move_id_act)
						ids_move_hidden.append(move_id_act)
						ids_move.append(move_id_act)
						self.write({'done_move_hidden': [(4, move_id_act)]})
							
					self.write({'state': 'done', 'done_move': [(4, ids_move[0])]})
					
					account_search_id = parameter.deliver_account_mn.id if currency_id is None else parameter.deliver_account_me.id
					
					reconcile_ids = self.env['account.move.line'].search([('rendicion_id','=',deliver.id),('account_id','=',account_search_id)]).mapped('id')
					print 'reconcile', reconcile_ids
					'''
					for recon in reconcile_ids:
						print recon.id, recon.debit, recon.credit 
					'''
					#raise osv.except_osv('Acción Inválida!', reconcile_ids)

					move_rendicion_obj = self.env['account.move.line'].search([('rendicion_id','=',deliver.id),('account_id','=',account_search_id)])
					totalamount = 0
					for elem_r_o in move_rendicion_obj:
						totalamount += elem_r_o.debit
						totalamount -= elem_r_o.credit

					print "ids rendicon", reconcile_ids

					if totalamount == 0:
						self.pool.get('account.move.line').reconcile(self.env.cr, self.env.uid, reconcile_ids)
					else:
						vals_data = {}
						concile_move = self.with_context({'active_ids':reconcile_ids}).env['account.move.line.reconcile'].create(vals_data)
						concile_move.trans_rec_reconcile_partial_reconcile()
						
					#self.pool.get('account.move.line').reconcile(self.env.cr, self.env.uid, reconcile_ids)	
		
				else:
					print "ENTRE AKI RENDICION"
					self.write({'state': 'done'})
					account_search_id = parameter.deliver_account_mn.id if currency_id is None else parameter.deliver_account_me.id
					reconcile_ids = self.env['account.move.line'].search([('rendicion_id','=',deliver.id),('account_id','=',account_search_id)]).mapped('id')
					
					move_rendicion_obj = self.env['account.move.line'].search([('rendicion_id','=',deliver.id),('account_id','=',account_search_id)])
					totalamount = 0
					for elem_r_o in move_rendicion_obj:
						totalamount += elem_r_o.debit
						totalamount -= elem_r_o.credit

					print "ids rendicon", reconcile_ids

					if totalamount == 0:
						self.pool.get('account.move.line').reconcile(self.env.cr, self.env.uid, reconcile_ids)
					else:
						vals_data = {}
						concile_move = self.with_context({'active_ids':reconcile_ids}).env['account.move.line.reconcile'].create(vals_data)
						concile_move.trans_rec_reconcile_partial_reconcile()
			return True




class print_entregas_rendir_pdf(models.Model):
	_name = 'print.entregas.rendir.pdf'

	seleccionar = fields.Selection([('1','Apuntes de Entrega'),('2','Apuntes de Rendición')], string='Exportar',required=True)

	@api.multi
	def do_rebuild(self):
		
		self.reporteador()
		
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		import os

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		vals = {
			'output_name': 'EntregaRendir.pdf',
			'output_file': open(direccion + "entregarendir.pdf", "rb").read().encode("base64"),	
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
	def cabezera(self,c,wReal,hReal):

		obj_entrega = self.env['deliveries.to.pay'].search([('id','=',self.env.context['active_ids'][0])])[0]

		c.setFont("Calibri-Bold", 10)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "ENTREGAS A RENDIR: "+ obj_entrega.name )

		c.setFont("Calibri-Bold", 8)

		c.drawString( 10,hReal-36, 'Fecha Entrega:')
		c.drawString( 10,hReal-48, 'Empleado:')
		c.drawString( 10,hReal-60, 'Monto Entregado:')
		c.drawString( 10,hReal-72, 'Caja Entrega:')
		c.drawString( 10,hReal-84, 'Medio Pago:')

		c.drawString( 400,hReal-36, u'Número Comprobante:')
		c.drawString( 400,hReal-48, 'Memoria:')
		c.drawString( 400,hReal-60, u'Fecha Rendición:')
		c.drawString( 400,hReal-72, 'Monto Rendido:')


		c.setFont("Calibri", 8)
		c.drawString( 10+90,hReal-36, obj_entrega.deliver_date)
		c.drawString( 10+90,hReal-48, obj_entrega.partner_id.name)
		c.drawString( 10+90,hReal-60, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%obj_entrega.deliver_amount)))
		c.drawString( 10+90,hReal-72, obj_entrega.deliver_journal_id.name)
		c.drawString( 10+90,hReal-84, obj_entrega.means_payment_id.description if obj_entrega.means_payment_id.id else '')

		c.drawString( 400+90,hReal-36, obj_entrega.invoice_number)
		c.drawString( 400+90,hReal-48, obj_entrega.memory)
		c.drawString( 400+90,hReal-60, obj_entrega.done_date if obj_entrega.done_date else '')
		c.drawString( 400+90,hReal-72, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%obj_entrega.done_amount)))



		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
		    "<font size=8><b>Número</b></font>",
		    style
		)
		paragraph2 = Paragraph(
		    "<font size=8><b>Comprobante</b></font>",
		    style
		)
		paragraph3 = Paragraph(
		    "<font size=8><b>Fecha</b></font>",
		    style
		)
		paragraph4 = Paragraph(
		    "<font size=8><b>Periodo</b></font>",
		    style
		)
		paragraph5 = Paragraph(
		    "<font size=8><b>Diario</b></font>",
		    style
		)
		paragraph6 = Paragraph(
		    "<font size=8><b>Empresa</b></font>",
		    style
		)
		paragraph7 = Paragraph(
		    "<font size=8><b>Importe</b></font>",
		    style
		)
		paragraph8 = Paragraph(
		    "<font size=8><b>Importe Divisa</b></font>",
		    style
		)
		paragraph9 = Paragraph(
		    "<font size=8><b>Glosa</b></font>",
		    style
		)


		if self.seleccionar== '1':
			tam = [50,70,50,50,90,100,75,75]

			data= [[ paragraph1 ,paragraph2,paragraph3,paragraph4,paragraph5,paragraph6,paragraph7,paragraph8]]

			t=Table(data,colWidths=(50,70,50,50,90,100,75,75), rowHeights=(15))

			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
				('FONTSIZE',(0,0),(-1,-1),4),
				('BACKGROUND', (0, 0), (-1, -1), colors.gray)
			]))

			t.wrapOn(c,10,hReal-116)
			t.drawOn(c,10,hReal-116)

		if self.seleccionar== '2':
			tam = [30,65,45,45,70,90,60,60,100]

			
			data= [[ paragraph1 ,paragraph2,paragraph3,paragraph4,paragraph5,paragraph6,paragraph7 ,paragraph8,paragraph9]]

			t=Table(data,colWidths=(50,66,46,46,71,91,61,61,91), rowHeights=(15))

			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
				('FONTSIZE',(0,0),(-1,-1),4),
				('BACKGROUND', (0, 0), (-1, -1), colors.gray)
			]))

			t.wrapOn(c,10,hReal-116)
			t.drawOn(c,10,hReal-116)
		

	@api.multi
	def x_aument(self,a):
		a[0] = a[0]+1

	@api.multi
	def reporteador(self):

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')


		pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
		pdfmetrics.registerFont(TTFont('Calibri-Bold', 'CalibriBold.ttf'))

		width ,height  = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "entregarendir.pdf", pagesize= A4 )
		inicio = 0
		pos_inicial = hReal-128
		libro = None
		voucher = None
		total = 0
		debeTotal = 0
		haberTotal = 0
		pagina = 1
		textPos = 0
		
		self.cabezera(c,wReal,hReal)
		
		obj_entrega = self.env['deliveries.to.pay'].search([('id','=',self.env.context['active_ids'][0])])[0]


		if self.seleccionar== '1':

			for line in obj_entrega.deliver_move:
				
				#tam = [50,70,50,50,90,100,75,75]
				c.setFont("Calibri", 8)

				c.drawString( 10 ,pos_inicial, line.name if line.name else '' )
				c.drawString( 60 ,pos_inicial, line.invoice_number if line.invoice_number  else '' )
				c.drawString( 130 ,pos_inicial, line.date if line.date  else '' )

				c.drawString( 180 ,pos_inicial, line.period_id.name if line.period_id  else '' )
				c.drawString( 230 ,pos_inicial, line.journal_id.name if line.journal_id  else '' )
				add = 0
				name = line.partner_id.name if line.partner_id  else ''
				while len(name) > 25:
					c.drawString( 320 ,pos_inicial - add, name[0:25])
					add +=12
					name = name[25:]
				c.drawString( 320 ,pos_inicial - add, name)
				#c.drawString( 390 ,pos_inicial, line.partner_id.name if line.partner_id  else '' )
				c.drawRightString( 492 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%line.amount )))
				c.drawRightString( 567 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%line.amount_currency_deliver )))
				pos_inicial -= add
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)

			
		
		if self.seleccionar== '2':
			tam = [30,70,55,55,90,100,60,110]

			for line in obj_entrega.done_move:

				#50,66,46,46,71,91,61,61,91
				c.drawString( 10 ,pos_inicial, line.name if line.name else '' )
				c.drawString( 60 ,pos_inicial, line.invoice_number if line.invoice_number  else '' )
				c.drawString( 126 ,pos_inicial, line.date if line.date  else '' )
				c.drawString( 172 ,pos_inicial, line.period_id.name if line.period_id  else '' )
				c.drawString( 218 ,pos_inicial, line.journal_id.name if line.journal_id  else '' )
				add = 0
				name = line.partner_id.name if line.partner_id  else ''
				while len(name) > 25:
					c.drawString( 289 ,pos_inicial - add, name[0:25])
					add +=12
					name = name[25:]
				c.drawString( 289 ,pos_inicial - add, name)
				#c.drawString( 270 ,pos_inicial, line.partner_id.name if line.partner_id  else '' )
				c.drawRightString( 438 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%line.amount )))
				c.drawRightString( 499 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%line.amount_currency_deliver )))
				c.drawString( 502 ,pos_inicial, line.glosa_deliver if line.glosa_deliver else '' )
				pos_inicial -= add
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)

		c.save()


	@api.multi
	def particionar_text(self,c,tam):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Calibri',8,tam)
			if len(lines)>1:
				return tet[:-1]
		return tet

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Calibri-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-128
		else:
			return pagina,posactual-valor



class deliveries_to_pay_view(models.Model):
	_name = 'deliveries.to.pay.view'
	_auto = False

	entrega = fields.Char('Entrega')
	encargado = fields.Char('Encargado')	
	periodo = fields.Char('Periodo')
	libro = fields.Char('Libro')
	voucher = fields.Char('Voucher')
	cuenta = fields.Char('Cuenta')
	proveedor = fields.Char('Proveedor')
	fecha = fields.Char('Fecha')
	tipo_doc = fields.Char('Tipo Doc.')
	nro_comprobante = fields.Char('Nro. Comprobante')
	monto = fields.Float('Monto',digits=(12,2))

	_order = 'entrega,periodo,libro,voucher'


	def init(self,cr):

		cr.execute(""" DROP VIEW IF EXISTS deliveries_to_pay_view;
			create or replace view deliveries_to_pay_view as (
			

select b1.move_id as id ,b6.name as entrega,b7.name as encargado,b8.name as periodo, b3.name as libro, b2.name as voucher,b5.code as cuenta,b4.name as proveedor,b2.date as fecha,b9.code as tipo_doc,b1.nro_comprobante,b1.credit as monto from (

select distinct provisiones.identifica,provisiones.id,pagos.rendicion_id,provisiones.move_id,provisiones.type_document_id,provisiones.partner_id,
provisiones.account_id,provisiones.nro_comprobante,provisiones.credit


from (
select concat(a1.partner_id,a1.account_id,a1.type_document_id,nro_comprobante) as identifica,rendicion_id,a1.id,move_id,partner_id,type_document_id,account_id,nro_comprobante,debit,credit from account_move_line as a1
left join account_account a2 on a2.id=a1.account_id 
where rendicion_id is null and
a2.type='payable' and debit =0 and credit > 0) as provisiones

inner join (select concat(a1.partner_id,a1.account_id,a1.type_document_id,nro_comprobante) as identifica,rendicion_id,a1.id,move_id,partner_id,type_document_id,account_id,nro_comprobante,debit,credit from account_move_line as a1
left join account_account a2 on a2.id=a1.account_id 
where rendicion_id is not null and
a2.type='payable'
order by rendicion_id) pagos on pagos.identifica=provisiones.identifica ) as b1

left join account_move b2 on b2.id=b1.move_id
left join account_journal b3 on b3.id=b2.journal_id
left join res_partner b4 on b4.id=b1.partner_id
left join account_account b5 on b5.id=b1.account_id
left join deliveries_to_pay b6 on b6.id=b1.rendicion_id
left join res_partner b7 on b7.id=b6.partner_id 
left join account_period  b8 on b8.id=b2.period_id
left join it_type_document b9 on b9.id=b1.type_document_id

order by entrega,periodo,libro,voucher )""")
