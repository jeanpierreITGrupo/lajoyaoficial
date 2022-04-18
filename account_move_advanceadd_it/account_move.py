# -*- coding: utf-8 -*-

from openerp import models, fields, api , exceptions , _
from openerp.osv import fields as fieldsseven
from openerp.osv import osv
import re
import base64



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

class account_move_comprobante(models.Model):
	_name='account.move.comprobante'
	_auto = False

	name = fields.Char('Comprobante')
	aml_id = fields.Integer('aml_id')
	partner_id = fields.Many2one('res.partner','Partner')


	def init(self,cr):
		cr.execute(""" 
			drop view if exists account_move_comprobante;
			create or replace view account_move_comprobante as (


select row_number() OVER() as id,* from
(
select 
aml.nro_comprobante || ' (' || coalesce(itd.code,'') || ' )' as name, 
aa.type,
aml.id as aml_id, 
aml.debit,
aml.credit ,
aml.partner_id

from account_move_line aml
inner join account_account aa on aa.id = aml.account_id
left join it_type_document itd on itd.id = aml.type_document_id
where aa.type in ('payable','receivable')
and aml.nro_comprobante is not null and aml.nro_comprobante !=''
and ( (aa.type = 'payable' and aml.credit >0 ) or (aa.type = 'receivable' and aml.debit >0 ) )
order by aml.nro_comprobante



						) AS T  )

			""")


	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
			if not ids:
				# Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
				# on a database with thousands of matching products, due to the huge merge+unique needed for the
				# OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
				# Performing a quick memory merge of ids in Python will give much better performance
				ids = set()
				ids.update(self.search(cr, user, args + [('name',operator,name)], limit=limit, context=context))
				if not limit or len(ids) < limit:
					# we may underrun the limit because of dupes in the results, that's fine
					ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					# vivek
					# Purpose  : To filter the product by using part_number
					ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					#End
				ids = list(ids)
			if not ids:
				ptrn = re.compile('(\[(.*?)\])')
				res = ptrn.search(name)
				if res:
					ids = self.search(cr, user, [('name','=', res.group(2))] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context=context)
		return result


class account_move_line(models.Model):
	_inherit='account.move.line'

	nro_retencion = fields.Char(u'Nro. Retención')
	importe_retencion = fields.Float('Importe',digits=(12,2))

	@api.multi
	def edit_linea_it(self):
		if self.move_id.state != 'draft':
			raise osv.except_osv('Alerta!', "No se puede modificar una linea de un Asiento Asentado.")
		data = {
			'default_glosa':self.name,
			'default_empresa': self.partner_id.id,
			'default_comprobante_manual': self.nro_comprobante,
			'default_account_id':self.account_id.id,
			'default_date_vencimiento': self.date_maturity,
			'default_debit': self.debit,
			'default_credit':self.credit,
			'default_analytic_id': self.analytic_account_id.id,
			'default_import_divisa': self.amount_currency,
			'default_currency_id': self.currency_id.id,
			'default_impuesto':self.tax_code_id.id,
			'default_importe_impuesto':self.tax_amount,
			'default_type_change':self.currency_rate_it,
			'default_type_doc_id':self.type_document_id.id,
			'default_medio_pago':self.means_payment_id.id,
			'default_flujo_efectivo':self.fefectivo_id.id,
			'default_distrib_analytic_id': self.analytics_id.id,
			'default_nro_retencion': self.nro_retencion,
			'default_importe_retencion': self.importe_retencion,
			'default_quantity': self.quantity,
			'default_product_id': self.product_id.id,
			'default_nro_lote': self.nro_lote.id,
			'default_product_uom_id': self.product_uom_id.id,
			'active_ids_line': self.id,
		}
		return {
            'name': 'Agregar Linea',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.wizard.add.linea',
            'target': 'new',
            'context': data
		}


class account_move(models.Model):
	_inherit= 'account.move'
	_name = "account.move"

	def _get_move_from_lines(self, cr, uid, ids, context=None):
		line_obj = self.pool.get('account.move.line')
		return [line.move_id.id for line in line_obj.browse(cr, uid, ids, context=context)]

	"""
	_columns={
		'partner_id': fieldsseven.many2one('res.partner','Empresa'),
	}


	@api.multi
	def button_validate(self):
		t = super(account_move,self).button_validate()
		print "constrains_move"
		if self.state!= 'draft':
			if self.name != '\\':
				filtro = []
				filtro.append( ('name','=',self.name) )
				filtro.append( ('journal_id','=',self.journal_id.id) )
				filtro.append( ('period_id','=',self.period_id.id) )
				filtro.append( ('id','!=',self.id) )
				print "filtro",filtro
				m = self.env['account.move'].search( filtro )
				if len(m) > 0:
					t = self.name
					raise osv.except_osv('Alerta!', u"Número del Asiento Duplicado ("+t+").")
					
		return t
	"""


	@api.multi
	def button_add_linea(self):
		return {
            'name': 'Agregar Linea',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.wizard.add.linea',
            'target': 'new',
            'context': {'active_ids':[self.id]},
		}


	@api.multi
	def export_excel(self):

		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', "No fue configurado el directorio para los archivos en Configuración.")
		workbook = Workbook( direccion + 'tempo_account_move_line.xlsx')
		worksheet = workbook.add_worksheet("Asiento Contable")
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
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.1
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.write(0,0, "Asiento Contable:", bold)
		tam_col[0] = tam_letra* len("Asiento Contable:") if tam_letra* len("Asiento Contable:")> tam_col[0] else tam_col[0]

		worksheet.write(0,1, self.name, normal)
		tam_col[1] = tam_letra* len(self.name) if tam_letra* len(self.name)> tam_col[1] else tam_col[1]

		worksheet.write(1,0, "Diario:", bold)
		tam_col[0] = tam_letra* len("Diario:") if tam_letra* len("Diario:")> tam_col[0] else tam_col[0]

		worksheet.write(1,1, self.journal_id.name, normal)
		tam_col[1] = tam_letra* len(self.journal_id.name) if tam_letra* len(self.journal_id.name)> tam_col[1] else tam_col[1]


		worksheet.write(2,0, "Periodo:",bold)
		tam_col[0] = tam_letra* len("Periodo:") if tam_letra* len("Periodo:")> tam_col[0] else tam_col[0]

		worksheet.write(2,1, self.period_id.name, normal)
		tam_col[1] = tam_letra* len(self.period_id.name) if tam_letra* len(self.period_id.name)> tam_col[1] else tam_col[1]


		worksheet.write(3,0, "Empresa:",bold)
		tam_col[0] = tam_letra* len("Empresa:") if tam_letra* len("Empresa:")> tam_col[0] else tam_col[0]

		worksheet.write(3,1, self.partner_id.name if self.partner_id.name else '', normal)
		tam_col[1] = tam_letra* len(self.partner_id.name) if self.partner_id.name and tam_letra* len(self.partner_id.name)> tam_col[1] else tam_col[1]


		worksheet.write(1,2, "Referencia:", bold)
		tam_col[2] = tam_letra* len("Referencia:") if tam_letra* len("Referencia:")> tam_col[0] else tam_col[0]

		worksheet.write(1,3, self.ref if self.ref else "", normal)
		tam_col[3] = tam_letra* len(self.ref if self.ref else "") if tam_letra* len(self.ref if self.ref else "")> tam_col[1] else tam_col[1]


		worksheet.write(2,2, "Fecha:", bold)
		tam_col[2] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

		worksheet.write(2,3, self.date if self.date else "", normal)
		tam_col[3] = tam_letra* len(self.date if self.date else "") if tam_letra* len(self.date if self.date else "")> tam_col[1] else tam_col[1]






		worksheet.write(5,0, "Factura",boldbord)
		tam_col[0] = tam_letra* len("Factura") if tam_letra* len("Factura")> tam_col[0] else tam_col[0]
		worksheet.write(5,1, "Nombre",boldbord)
		tam_col[1] = tam_letra* len("Nombre") if tam_letra* len("Nombre")> tam_col[1] else tam_col[1]
		worksheet.write(5,2, "Empresa",boldbord)
		tam_col[2] = tam_letra* len("Empresa") if tam_letra* len("Empresa")> tam_col[2] else tam_col[2]
		worksheet.write(5,3, "Comprobante",boldbord)
		tam_col[3] = tam_letra* len("Comprobante") if tam_letra* len("Comprobante")> tam_col[3] else tam_col[3]
		worksheet.write(5,4, "Cuenta",boldbord)
		tam_col[4] = tam_letra* len("Cuenta") if tam_letra* len("Cuenta")> tam_col[4] else tam_col[4]
		worksheet.write(5,5, "Fecha V.",boldbord)
		tam_col[5] = tam_letra* len("Fecha V.") if tam_letra* len("Fecha V.")> tam_col[5] else tam_col[5]
		worksheet.write(5,6, "Debe",boldbord)
		tam_col[6] = tam_letra* len("Debe") if tam_letra* len("Debe")> tam_col[6] else tam_col[6]
		worksheet.write(5,7, "Haber",boldbord)
		tam_col[7] = tam_letra* len("Haber") if tam_letra* len("Haber")> tam_col[7] else tam_col[7]
		worksheet.write(5,8, u"Cta. Analítica",boldbord)
		tam_col[8] = tam_letra* len(u"Cta. Analítica") if tam_letra* len(u"Cta. Analítica")> tam_col[8] else tam_col[8]
		worksheet.write(5,9, u"Importe Divisa",boldbord)
		tam_col[9] = tam_letra* len(u"Importe Divisa") if tam_letra* len(u"Importe Divisa")> tam_col[9] else tam_col[9]
		worksheet.write(5,10, "Divisa",boldbord)
		tam_col[10] = tam_letra* len("Divisa") if tam_letra* len("Divisa")> tam_col[10] else tam_col[10]
		worksheet.write(5,11, "Cuenta Impuesto",boldbord)
		tam_col[11] = tam_letra* len("Cuenta Impuesto") if tam_letra* len("Cuenta Impuesto")> tam_col[11] else tam_col[11]
		worksheet.write(5,12, u"Importe Impuestos",boldbord)
		tam_col[12] = tam_letra* len(u"Importe Impuestos") if tam_letra* len(u"Importe Impuestos")> tam_col[12] else tam_col[12]
		worksheet.write(5,13, u"Tipo Cambio Sunat",boldbord)
		tam_col[13] = tam_letra* len(u"Tipo Cambio Sunat") if tam_letra* len(u"Tipo Cambio Sunat")> tam_col[13] else tam_col[13]
		worksheet.write(5,14, "Tipo Documento",boldbord)
		tam_col[14] = tam_letra* len("Tipo Documento") if tam_letra* len("Tipo Documento")> tam_col[14] else tam_col[14]
		worksheet.write(5,15, "M. Pago",boldbord)
		tam_col[15] = tam_letra* len("M. Pago") if tam_letra* len("M. Pago")> tam_col[15] else tam_col[15]
		worksheet.write(5,16, u"F. Efectivo",boldbord)
		tam_col[16] = tam_letra* len(u"F. Efectivo") if tam_letra* len(u"F. Efectivo")> tam_col[16] else tam_col[16]
		worksheet.write(5,17, u"Estado",boldbord)
		tam_col[17] = tam_letra* len(u"Estado") if tam_letra* len(u"Estado")> tam_col[17] else tam_col[17]
		worksheet.write(5,18, u"Conciliar",boldbord)
		tam_col[18] = tam_letra* len(u"Conciliar") if tam_letra* len(u"Conciliar")> tam_col[18] else tam_col[18]
		worksheet.write(5,19, u"Conciliación Parcial",boldbord)
		tam_col[19] = tam_letra* len(u"Conciliación Parcial") if tam_letra* len(u"Conciliación Parcial")> tam_col[19] else tam_col[19]

		dict_state = {'draft':'Descuadrado','valid':'Cuadrado'}
		for line in self.line_id:
			worksheet.write(x,0,line.invoice.name if line.invoice.name else '' ,bord )
			worksheet.write(x,1,line.name if line.name  else '',bord )
			worksheet.write(x,2,line.partner_id.name if line.partner_id.name  else '',bord)
			worksheet.write(x,3,line.nro_comprobante if line.nro_comprobante  else '',bord)
			worksheet.write(x,4,line.account_id.code if line.account_id.code  else '',bord)
			worksheet.write(x,5,line.date_maturity if line.date_maturity  else '',bord)
			worksheet.write(x,6,line.debit ,numberdos)
			worksheet.write(x,7,line.credit,numberdos)
			worksheet.write(x,8,line.analytic_account_id.name if line.analytic_account_id.name  else '',bord)
			worksheet.write(x,9,line.amount_currency,bord)
			worksheet.write(x,10,line.currency_id.name if line.currency_id.name  else '',bord)
			worksheet.write(x,11,line.tax_code_id.name if line.tax_code_id.name  else '',bord)
			worksheet.write(x,12,line.tax_amount,numberdos)
			worksheet.write(x,13,line.currency_rate_it,numbertres)
			worksheet.write(x,14,line.type_document_id.code if line.type_document_id.code  else '',bord)
			worksheet.write(x,15,line.means_payment_id.description if line.means_payment_id.description  else '',bord)
			worksheet.write(x,16,line.fefectivo_id.concept if line.fefectivo_id.concept  else '',bord)
			worksheet.write(x,17,dict_state[line.state] if line.state  else '',bord)
			worksheet.write(x,18,str(line.reconcile_id.name) if line.reconcile_id.id  else '',bord)
			worksheet.write(x,19,str(line.reconcile_partial_id.name) if line.reconcile_partial_id.id  else '',bord)

			tam_col[0] = tam_letra* len(line.invoice.name if line.invoice.name else '' ) if tam_letra* len(line.invoice.name if line.invoice.name else '' )> tam_col[0] else tam_col[0]
			tam_col[1] = tam_letra* len(line.name if line.name  else '') if tam_letra* len(line.name if line.name  else '')> tam_col[1] else tam_col[1]
			tam_col[2] = tam_letra* len(line.partner_id.name if line.partner_id.name  else '') if tam_letra* len(line.partner_id.name if line.partner_id.name  else '')> tam_col[2] else tam_col[2]
			tam_col[3] = tam_letra* len(line.nro_comprobante if line.nro_comprobante  else '') if tam_letra* len(line.nro_comprobante if line.nro_comprobante  else '')> tam_col[3] else tam_col[3]
			tam_col[4] = tam_letra* len(line.account_id.code if line.account_id.code  else '') if tam_letra* len(line.account_id.code if line.account_id.code  else '')> tam_col[4] else tam_col[4]
			tam_col[5] = tam_letra* len(line.date_maturity if line.date_maturity  else '') if tam_letra* len(line.date_maturity if line.date_maturity  else '')> tam_col[5] else tam_col[5]
			tam_col[6] = tam_letra* len("%0.2f"%line.debit ) if tam_letra* len("%0.2f"%line.debit )> tam_col[6] else tam_col[6]
			tam_col[7] = tam_letra* len("%0.2f"%line.credit) if tam_letra* len("%0.2f"%line.credit)> tam_col[7] else tam_col[7]
			tam_col[8] = tam_letra* len(line.analytic_account_id.name if line.analytic_account_id.name  else '') if tam_letra* len(line.analytic_account_id.name if line.analytic_account_id.name  else '')> tam_col[8] else tam_col[8]
			tam_col[9] = tam_letra* len("%0.2f"%line.amount_currency) if tam_letra* len("%0.2f"%line.amount_currency)> tam_col[9] else tam_col[9]
			tam_col[10] = tam_letra* len(line.currency_id.name if line.currency_id.name  else '') if tam_letra* len(line.currency_id.name if line.currency_id.name  else '')> tam_col[10] else tam_col[10]
			tam_col[11] = tam_letra* len(line.tax_code_id.name if line.tax_code_id.name  else '') if tam_letra* len(line.tax_code_id.name if line.tax_code_id.name  else '')> tam_col[11] else tam_col[11]
			tam_col[12] = tam_letra* len("%0.2f"%line.tax_amount) if tam_letra* len("%0.2f"%line.tax_amount)> tam_col[12] else tam_col[12]
			tam_col[13] = tam_letra* len("%0.3f"%line.currency_rate_it) if tam_letra* len("%0.3f"%line.currency_rate_it)> tam_col[13] else tam_col[13]
			tam_col[14] = tam_letra* len(line.type_document_id.code if line.type_document_id.code  else '') if tam_letra* len(line.type_document_id.code if line.type_document_id.code  else '')> tam_col[14] else tam_col[14]
			tam_col[15] = tam_letra* len(line.means_payment_id.description if line.means_payment_id.description  else '') if tam_letra* len(line.means_payment_id.description if line.means_payment_id.description  else '')> tam_col[15] else tam_col[15]
			tam_col[16] = tam_letra* len(line.fefectivo_id.concept if line.fefectivo_id.concept  else '') if tam_letra* len(line.fefectivo_id.concept if line.fefectivo_id.concept  else '')> tam_col[16] else tam_col[16]
			tam_col[17] = tam_letra* len(dict_state[line.state] if line.state  else '') if tam_letra* len(dict_state[line.state] if line.state  else '')> tam_col[17] else tam_col[17]
			tam_col[18] = tam_letra* len(str(line.reconcile_id.name) if line.reconcile_id.id  else '') if tam_letra* len(str(line.reconcile_id.name) if line.reconcile_id.id  else '')> tam_col[18] else tam_col[18]
			tam_col[19] = tam_letra* len(str(line.reconcile_partial_id.name) if line.reconcile_partial_id.id  else '') if tam_letra* len(str(line.reconcile_partial_id.name) if line.reconcile_partial_id.id  else '')> tam_col[19] else tam_col[19]


			x = x +1

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
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])
		worksheet.set_column('M:M', tam_col[12])
		worksheet.set_column('N:N', tam_col[13])
		worksheet.set_column('O:O', tam_col[14])
		worksheet.set_column('P:P', tam_col[15])
		worksheet.set_column('Q:Q', tam_col[16])
		worksheet.set_column('R:R', tam_col[17])
		worksheet.set_column('S:S', tam_col[18])
		worksheet.set_column('T:T', tam_col[19])

		x = x+2
		worksheet.write(x,0, "DESTINOS:",bold)
		x = x+2


		worksheet.write(x,0, "Cuenta",boldbord)
		worksheet.write(x,1, u"Descripción",boldbord)
		worksheet.write(x,2, "Debe",boldbord)
		worksheet.write(x,3, "Haber",boldbord)

		x += 1
		for destino in self.analytic_lines_id:
			worksheet.write(x,0, destino.cuenta.code,bord)
			worksheet.write(x,1, destino.cuenta.name,bord)
			worksheet.write(x,2, destino.debe ,numberdos)
			worksheet.write(x,3, destino.haber ,numberdos)
			x += 1


		workbook.close()
		
		f = open( direccion + 'tempo_account_move_line.xlsx', 'rb')
		
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'AsientoContable.xlsx',
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
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}



class account_move_wizard_add_linea(osv.TransientModel):
	_name = 'account.move.wizard.add.linea'


	nro_retencion = fields.Char(u'Nro. Retención')
	importe_retencion = fields.Float('Importe',digits=(12,2))
	product_id = fields.Many2one('product.product','Producto')
	quantity = fields.Float('Cantidad')


	nro_lote = fields.Many2one('purchase.liquidation','Nro Lote')
	product_uom_id = fields.Many2one('product.uom','Unidad')

	currency_id = fields.Many2one('res.currency','Moneda')
	account_id = fields.Many2one('account.account','Cuenta')
	type_change = fields.Float('Tipo Cambio',digits=(12,3))
	import_divisa = fields.Float('Importe Divisa', digits=(12,2))
	glosa = fields.Char('Glosa',size=200)
	debit = fields.Float('Debe', digits=(12,2))
	credit = fields.Float('Haber', digits=(12,2))
	analytic_id = fields.Many2one('account.analytic.account','Cta. Analítica')
	distrib_analytic_id = fields.Many2one('account.analytic.plan.instance','Distribución Analítica')

	is_pago  = fields.Boolean('Se esta registrando un pago')
	comprobante_auto = fields.Many2one('account.move.comprobante','Número Comprobante')
	comprobante_manual = fields.Char('Número Comprobante',size=200)
	empresa = fields.Many2one('res.partner','Empresa')

	type_doc_id = fields.Many2one('it.type.document','Tipo Documento')
	impuesto = fields.Many2one('account.tax.code','Impuesto')
	importe_impuesto = fields.Float('Importe Impuesto/Base', digits=(12,2))
	medio_pago = fields.Many2one('it.means.payment','Medio Pago')
	flujo_efectivo = fields.Many2one('account.config.efective','Flujo Efectivo')
	date_vencimiento = fields.Date('Fecha Vencimiento')

	@api.onchange('debit')
	def onchange_debit(self):
		if self.debit==0:
			return
		self.credit=0
		"""
		if self.currency_id.id:
			if self.type_change!=0:
				self.import_divisa = float("%0.2f"% ( (self.debit - self.credit) / float(self.type_change) ))
			else:
				self.import_divisa = 0
		else:
			self.import_divisa= 0"""

	@api.onchange('credit')
	def onchange_credit(self):
		if self.credit==0:
			return
		self.debit=0	
		"""
		if self.currency_id.id:
			if self.type_change!=0:
				self.import_divisa = float("%0.2f"% ( (self.debit - self.credit) / float(self.type_change) ))
			else:
				self.import_divisa = 0
		else:
			self.import_divisa= 0"""


	@api.onchange('type_change','currency_id','import_divisa')
	def onchange_type_change_currency(self):
		if self.currency_id.id:
			if self.import_divisa >=0:
				self.debit = self.import_divisa * self.type_change
				self.credit = 0
			else:
				self.debit = 0
				self.credit = self.import_divisa * self.type_change * -1

	@api.multi
	def do_rebuild(self):
		if 'active_ids_line' in self._context:
			tt = self._context['active_ids_line']

			comprobante = self.comprobante_manual if self.is_pago == False else self.comprobante_auto.name
			data = {
				'name':self.glosa,
				'partner_id': self.empresa.id,
				'nro_comprobante': comprobante if comprobante else '',
				'account_id':self.account_id.id,
				'date_maturity': self.date_vencimiento,
				'debit': self.debit,
				'credit':self.credit,
				'analytic_account_id': self.analytic_id.id,
				'amount_currency': self.import_divisa,
				'currency_id': self.currency_id.id,
				'tax_code_id':self.impuesto.id,
				'tax_amount':self.importe_impuesto,
				'currency_rate_it':self.type_change,
				'type_document_id':self.type_doc_id.id,
				'means_payment_id':self.medio_pago.id,
				'fefectivo_id':self.flujo_efectivo.id,
				'analytics_id': self.distrib_analytic_id.id,
				'nro_retencion':self.nro_retencion,
				'importe_retencion':self.importe_retencion,
				'quantity':self.quantity,
				'product_id':self.product_id.id,
				'nro_lote': self.nro_lote.id,
				'product_uom_id': self.product_uom_id.id,
			}
			obj_linea = self.env['account.move.line'].search([('id','=',tt)])[0].write(data)
			return True

		t = self._context['active_ids']
		if len(t)>1:
			raise osv.except_osv('Alerta!', "Solo debe seleccionar 1 Asiento Contable.")
		m = self.env['account.move'].search([('id','=',t[0])])[0]
		if m.state != 'draft':
			raise osv.except_osv('Alerta!', "Solo se puede agregar si el Asiento Contable esta en borrador.")


		comprobante = self.comprobante_manual if self.is_pago == False else self.comprobante_auto.name
		data = {
			'name':self.glosa,
			'partner_id': self.empresa.id,
			'nro_comprobante': comprobante if comprobante else '',
			'account_id':self.account_id.id,
			'date_maturity': self.date_vencimiento,
			'debit': self.debit,
			'credit':self.credit,
			'analytic_account_id': self.analytic_id.id,
			'amount_currency': self.import_divisa,
			'currency_id': self.currency_id.id,
			'tax_code_id':self.impuesto.id,
			'tax_amount':self.importe_impuesto,
			'currency_rate_it':self.type_change,
			'type_document_id':self.type_doc_id.id,
			'means_payment_id':self.medio_pago.id,
			'fefectivo_id':self.flujo_efectivo.id,
			'move_id':m.id,
			'analytics_id': self.distrib_analytic_id.id,
			'nro_retencion':self.nro_retencion,
			'importe_retencion':self.importe_retencion,
				'quantity':self.quantity,
				'product_id':self.product_id.id,
				'nro_lote': self.nro_lote.id,
				'product_uom_id': self.product_uom_id.id,
		}
		j = self.env['account.move.line'].create(data)
		m.write({'line_id': [(4,j.id)]})

		return True











class account_move_pdf(osv.TransientModel):
	_name = 'account.move.pdf'


	@api.multi
	def do_rebuild(self):
		
		if 'active_ids' in self.env.context:
			obj_move = self.env['account.move'].search([('id','=',self.env.context['active_ids'][0])])[0]

			self.reporteador(obj_move)
			
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'AsientoContable.pdf',
				'output_file': open(direccion + "AsientoContable.pdf", "rb").read().encode("base64"),	
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
	def cabezera(self,c,wReal,hReal,obj_move,titulo):

		c.setFont("Calibri-Bold", 10)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "ASIENTO CONTABLE: "+ obj_move.name + " - " + obj_move.journal_id.name )

		c.setFont("Calibri-Bold", 8)

		c.drawString( 10,hReal-36, 'Periodo:')
		c.drawString( 10,hReal-48, 'Empresa:')
		c.drawString( 400,hReal-36, 'Referencia:')
		c.drawString( 400,hReal-48, 'Fecha:')


		c.setFont("Calibri", 8)
		c.drawString( 10+90,hReal-36, obj_move.period_id.name)
		c.drawString( 10+90,hReal-48, obj_move.partner_id.name if obj_move.partner_id.name else '')
		c.drawString( 400+60,hReal-36, obj_move.ref if obj_move.ref else '')
		c.drawString( 400+60,hReal-48, obj_move.date if obj_move.date else '')


		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
		    "<font size=8><b>Nombre</b></font>",
		    style
		)
		paragraph2 = Paragraph(
		    "<font size=8><b>Empresa</b></font>",
		    style
		)
		paragraph3 = Paragraph(
		    "<font size=8><b>Comprobante</b></font>",
		    style
		)
		paragraph4 = Paragraph(
		    "<font size=8><b>Cuenta</b></font>",
		    style
		)
		paragraph5 = Paragraph(
		    "<font size=8><b>Fecha V.</b></font>",
		    style
		)
		paragraph6 = Paragraph(
		    "<font size=8><b>Debe</b></font>",
		    style
		)
		paragraph7 = Paragraph(
		    "<font size=8><b>Haber</b></font>",
		    style
		)
		paragraph8 = Paragraph(
		    "<font size=8><b>Cta. Analítica</b></font>",
		    style
		)
		paragraph9 = Paragraph(
		    "<font size=8><b>Importe Divisa</b></font>",
		    style
		)
		paragraph10 = Paragraph(
		    "<font size=8><b>Divisa</b></font>",
		    style
		)
		paragraph11 = Paragraph(
		    "<font size=8><b>TC SUNAT</b></font>",
		    style
		)
		paragraph12 = Paragraph(
		    "<font size=8><b>TD</b></font>",
		    style
		)

		paragraph13 = Paragraph(
		    "<font size=8><b>Cuenta</b></font>",
		    style
		)
		paragraph14 = Paragraph(
		    "<font size=8><b>Descripción</b></font>",
		    style
		)
		paragraph15 = Paragraph(
		    "<font size=8><b>Debe</b></font>",
		    style
		)
		paragraph16 = Paragraph(
		    "<font size=8><b>Haber</b></font>",
		    style
		)

		if titulo == 1:
			data= [[ paragraph1 , paragraph2 , paragraph3 , paragraph4, paragraph5 , paragraph6 , paragraph7 ,paragraph12]]
			t=Table(data,colWidths=( 80,120, 80, 90, 50,60,60,25), rowHeights=(9))
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
				('FONTSIZE',(0,0),(-1,-1),4),
				('BACKGROUND', (0, 0), (-1, -1), colors.gray)
			]))
		elif titulo == 2:
			data= [[ paragraph8 ,paragraph9,paragraph10,paragraph11]]
			t=Table(data,colWidths=(100,100,50,60), rowHeights=(9))
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
				('FONTSIZE',(0,0),(-1,-1),4),
				('BACKGROUND', (0, 0), (-1, -1), colors.gray)
			]))
		else:
			data= [[ paragraph13 ,paragraph14,paragraph15,paragraph16]]
			t=Table(data,colWidths=(70,130,60,60), rowHeights=(9))
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
				('FONTSIZE',(0,0),(-1,-1),4),
				('BACKGROUND', (0, 0), (-1, -1), colors.gray)
			]))


		t.wrapOn(c,20,500)
		t.drawOn(c,20,hReal-85)

	@api.multi
	def x_aument(self,a):
		a[0] = a[0]+1

	@api.multi
	def reporteador(self,obj_move):

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')


		pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
		pdfmetrics.registerFont(TTFont('Calibri-Bold', 'CalibriBold.ttf'))

		width ,height  = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "AsientoContable.pdf", pagesize= A4 )
		inicio = 0
		pos_inicial = hReal-83
		libro = None
		voucher = None
		total = 0
		debeTotal = 0
		haberTotal = 0
		pagina = 1
		textPos = 0
		
		self.cabezera(c,wReal,hReal,obj_move,1)


		posicion_indice = 1

		for i in obj_move.line_id:
			c.setFont("Calibri", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,1,obj_move)
			
			c.drawString( 10 ,pos_inicial, str(posicion_indice) )
			c.drawString( 22 ,pos_inicial, self.particionar_text( i.name,70) )
			c.drawString( 102 ,pos_inicial, self.particionar_text( i.partner_id.name if i.partner_id.id else '',100) )
			c.drawString( 222 ,pos_inicial,self.particionar_text( i.nro_comprobante if i.nro_comprobante else '',70) )
			c.drawString( 302 ,pos_inicial,self.particionar_text( i.account_id.code if i.account_id.id else '',75) )
			c.drawString( 392 ,pos_inicial,self.particionar_text( i.date_maturity if i.date_maturity else '',40) )
			c.drawRightString( 498 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.debit)))
			c.drawRightString( 558 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.credit)))
			c.drawString( 562 ,pos_inicial,self.particionar_text( i.type_document_id.code if i.type_document_id.id else '',20) )

			c.line( 20, pos_inicial-2, 585 ,pos_inicial-2)

			tamanios_x = [80,120, 80, 90, 50,60,60,25]

			acum_tx = 20
			for i in tamanios_x:
				c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)
				acum_tx += i
			c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)

			posicion_indice += 1



		posicion_indice= 1



		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,36,pagina,2,obj_move)



		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
		    "<font size=8><b>Nombre</b></font>",
		    style
		)
		paragraph2 = Paragraph(
		    "<font size=8><b>Empresa</b></font>",
		    style
		)
		paragraph3 = Paragraph(
		    "<font size=8><b>Comprobante</b></font>",
		    style
		)
		paragraph4 = Paragraph(
		    "<font size=8><b>Cuenta</b></font>",
		    style
		)
		paragraph5 = Paragraph(
		    "<font size=8><b>Fecha V.</b></font>",
		    style
		)
		paragraph6 = Paragraph(
		    "<font size=8><b>Debe</b></font>",
		    style
		)
		paragraph7 = Paragraph(
		    "<font size=8><b>Haber</b></font>",
		    style
		)
		paragraph8 = Paragraph(
		    "<font size=8><b>Cta. Analítica</b></font>",
		    style
		)
		paragraph9 = Paragraph(
		    "<font size=8><b>Importe Divisa</b></font>",
		    style
		)
		paragraph10 = Paragraph(
		    "<font size=8><b>Divisa</b></font>",
		    style
		)
		paragraph11 = Paragraph(
		    "<font size=8><b>TC SUNAT</b></font>",
		    style
		)
		paragraph12 = Paragraph(
		    "<font size=8><b>TD</b></font>",
		    style
		)

		data= [[ paragraph8 ,paragraph9,paragraph10,paragraph11]]
		t=Table(data,colWidths=(100,100,50,60), rowHeights=(9))
		t.setStyle(TableStyle([
			('GRID',(0,0),(-1,-1), 1, colors.black),
			('ALIGN',(0,0),(-1,-1),'LEFT'),
			('VALIGN',(0,0),(-1,-1),'MIDDLE'),
			('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
			('FONTSIZE',(0,0),(-1,-1),4),
			('BACKGROUND', (0, 0), (-1, -1), colors.gray)
		]))

		t.wrapOn(c,20,pos_inicial)
		t.drawOn(c,20,pos_inicial)


		for i in obj_move.line_id:
			c.setFont("Calibri", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,2,obj_move)
			
			c.drawString( 10 ,pos_inicial, str(posicion_indice) )
			c.drawString( 22 ,pos_inicial,self.particionar_text( i.analytic_account_id.name if i.analytic_account_id.id else '', 43) )
			c.drawRightString( 218 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.amount_currency)))
			c.drawString( 222 ,pos_inicial,self.particionar_text( i.currency_id.name if i.currency_id.id else '',24) )
			c.drawRightString( 328 ,pos_inicial, "%0.3f" % i.currency_rate_it)
			
			c.line( 20, pos_inicial-2, 330 ,pos_inicial-2)


			tamanios_x = [100,100,50,60]

			acum_tx = 20
			for i in tamanios_x:
				c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)
				acum_tx += i
			c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)

			posicion_indice += 1
		
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina,2,obj_move)





		paragraph13 = Paragraph(
		    "<font size=8><b>Cuenta</b></font>",
		    style
		)
		paragraph14 = Paragraph(
		    "<font size=8><b>Descripción</b></font>",
		    style
		)
		paragraph15 = Paragraph(
		    "<font size=8><b>Debe</b></font>",
		    style
		)
		paragraph16 = Paragraph(
		    "<font size=8><b>Haber</b></font>",
		    style
		)

		data= [[ paragraph13 ,paragraph14,paragraph15,paragraph16]]
		t=Table(data,colWidths=(70,130,60,60), rowHeights=(9))
		t.setStyle(TableStyle([
			('GRID',(0,0),(-1,-1), 1, colors.black),
			('ALIGN',(0,0),(-1,-1),'LEFT'),
			('VALIGN',(0,0),(-1,-1),'MIDDLE'),
			('TEXTFONT', (0, 0), (-1, -1), 'Calibri-Bold'),
			('FONTSIZE',(0,0),(-1,-1),4),
			('BACKGROUND', (0, 0), (-1, -1), colors.gray)
		]))



		posicion_indice= 1
		
		c.setFont("Calibri-Bold", 8)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,3,obj_move)
		c.drawString( 10 ,pos_inicial, str("DESTINOS:") )


		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,3,obj_move)

		t.wrapOn(c,20,pos_inicial)
		t.drawOn(c,20,pos_inicial)




		for i in obj_move.analytic_lines_id:
			c.setFont("Calibri", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina,3,obj_move)
			
			c.drawString( 10 ,pos_inicial, str(posicion_indice	) )
			c.drawString( 22 ,pos_inicial, self.particionar_text(i.cuenta.code,70) )
			c.drawString( 92 ,pos_inicial, self.particionar_text(i.cuenta.name,130) )
			c.drawRightString( 278 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.debe)))
			c.drawRightString( 338 ,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.haber)))
			
			c.line( 20, pos_inicial-2, 340 ,pos_inicial-2)


			tamanios_x = [70,130,60,60]

			acum_tx = 20
			for i in tamanios_x:
				c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)
				acum_tx += i
			c.line( acum_tx, pos_inicial-2, acum_tx ,pos_inicial+12)

			posicion_indice += 1
		
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina,3,obj_move)






		c.drawString( 10 ,pos_inicial, 'HECHO POR:' )
		c.drawString( 60 ,pos_inicial, obj_move.create_uid.name )


		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,50,pagina,3,obj_move)

		c.line( 125-47, pos_inicial+10, 125+47 ,pos_inicial+10)
		c.line( 290-47, pos_inicial+10, 290+47 ,pos_inicial+10)
		c.line( 165+290-47, pos_inicial+10, 165+290+47 ,pos_inicial+10)
		c.drawCentredString( 125 ,pos_inicial, 'HECHO POR:' )
		c.drawCentredString( 165+290 ,pos_inicial, 'REVISADO:' )
		c.drawCentredString( 290 ,pos_inicial, 'APROBADO:' )

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
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,titulo,obj_move):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal,obj_move,titulo)

			c.setFont("Calibri-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-83
		else:
			return pagina,posactual-valor