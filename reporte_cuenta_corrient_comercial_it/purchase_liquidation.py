# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv


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



class comercial_report_cuentas_corrienteit(models.TransientModel):
	_name = 'comercial.report.cuentas.corrienteit'

	partner_id = fields.Many2one('res.partner','Proveedor', required=False)
	

	@api.multi
	def do_rebuild(self):
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
		workbook = Workbook( direccion + u'consulta_comercial_cuentacorriente.xlsx')
		worksheet = workbook.add_worksheet(u"Cuenta Corriente")
		worksheet_2 = workbook.add_worksheet(u"Nota credito")

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
		worksheet.write(1,0, u"Reporte Cuenta Corriente" , bold)
		worksheet_2.write(1,0, u"Reporte Cuenta Corriente" , bold)

		if self.partner_id.id:
			worksheet.write(3,0, u"Proveedor: " + self.partner_id.name , bold)
			worksheet_2.write(3,0, u"Proveedor: " + self.partner_id.name , bold)


		columnas = [u'Periodo',
					u'Libro',
					u'Voucher',
					u'Partner',
					u'Ruc',
					u'Tipo Documento',
					u'Glosa',
					u'Comprobante',
					u'Cuenta',
					u'Fecha',
					u'Entregue Adelanto al Proveedor',
					u'Desconte Adelanto en Factura del Proveedor',
					u'Dolares']

		for i in range(len(columnas)):
			worksheet.write(5,i, columnas[i], boldcentred)
			worksheet_2.write(5,i, columnas[i], boldcentred)

		
		cont_txt = ''

		cont_txt += ' where ' + "saldo_filter != 0 "		
		if self.partner_id.id:
			cont_txt += "  and  partner = '" + self.partner_id.name + "' "
		
		elementos_code = [0,0,0]
		parameter_t = self.env['production.parameter'].search([])[0]
		txt_cuenta = "('0','0','"
		for i in parameter_t.cuentas_analisis:
			txt_cuenta += i.code + "','"

		txt_cuenta = txt_cuenta[:-2] + ')'

		cuenta_txt = " and cuentas.code in " + txt_cuenta + " "
			

		tipo_filtro_def = " cuentas.type='payable' or cuentas.type='receivable' "
		tipo_filtro_def = " cuentas.type is not null "


	
		self.env.cr.execute(""" 

select * from ( 
select 
t0.id ,
t0.ide,
t4.code as periodo,
t5.code as libro,
t2.name as voucher,
t6.name as partner,
t6.type_number as ruc,
t7.code as type_document,
t0.nro_comprobante as comprobante,
t3.code as cuenta,
t2.date as fecha,
t0.debit as debe,
t0.credit as haber,
t0.amount_currency,
t1.saldo as saldo_filter,
t3.type as tipofiltro,
t0.glosa
from 
(
select ab.id,concat(ab.partner_id,ab.account_id,ab.type_document_id,ab.nro_comprobante)as ide,ab.move_id,ab.partner_id,ab.account_id,ab.type_document_id,ab.nro_comprobante,ab.debit,ab.credit,ab.amount_currency , ab.name as glosa
from account_move_line ab
left join account_account cuentas on cuentas.id=ab.account_id
left join account_move am on ab.move_id = am.id
left join account_period ap on ap.id = am.period_id
where ( """ +tipo_filtro_def+ """ )   """ +cuenta_txt+ """
-------------- colocar en estas lineas la condicion de los periodos inicial y final ------------------------------
and (ap.id in (select id from account_period where periodo_num(code)>= periodo_num('00/2016') and periodo_num(code) <= periodo_num('12/2200') ) ) 

----------------------------------------------------------------------------------------------------

) t0


left join (

select concat(xx.partner_id,xx.account_id,xx.type_document_id,xx.nro_comprobante)as ide,sum(debit)-sum(credit) as saldo from account_move_line xx
left join account_account cuentas on cuentas.id=xx.account_id
left join account_move am on am.id = xx.move_id
left join account_period ap on ap.id = am.period_id
where ( """ +tipo_filtro_def+ """ )   """ +cuenta_txt+ """

-------------- colocar en estas lineas la condicion de los periodos  inicial y final ------------------------------
and ( periodo_num(ap.code)>= periodo_num('00/2016') and periodo_num(ap.code) <= periodo_num('12/2200') )

----------------------------------------------------------------------------------------------------

group by concat(xx.partner_id,xx.account_id,xx.type_document_id,xx.nro_comprobante) 

) t1 on t1.ide=t0.ide

left join account_move t2 on t2.id=t0.move_id
left join account_account t3 on t3.id=t0.account_id
left join account_period t4 on t4.id=t2.period_id
left join account_journal t5 on t5.id=t2.journal_id 
left join res_partner t6 on t6.id=t0.partner_id
left join it_type_document t7 on t7.id=t0.type_document_id

order by partner,cuenta,type_document,comprobante,fecha
)TT """ + cont_txt + """
			""")

		datatotal = self.env.cr.fetchall()

		tipos1 = []

		for i in parameter_t.tipo_documentos:
			tipos1.append(i.code)
		x = 6		
		partner = "None"

		for elemento in datatotal:
			if elemento[7] not in tipos1:
				if partner != elemento[5]:
					worksheet.write(x,0, elemento[5] ,bold)
					partner = elemento[5]
					x += 1
				worksheet.write(x,0, elemento[2] if elemento[2] else '', bord)
				worksheet.write(x,1, elemento[3] if elemento[3] else '', bord)
				worksheet.write(x,2, elemento[4] if elemento[4] else '', bord)
				worksheet.write(x,3, elemento[5] if elemento[5] else '', bord)
				worksheet.write(x,4, elemento[6] if elemento[6] else '', bord)
				worksheet.write(x,5, elemento[7] if elemento[7] else '', bord)

				worksheet.write(x,6, elemento[16] if elemento[16] else '', bord)

				worksheet.write(x,7, elemento[8] if elemento[8] else '', bord)
				worksheet.write(x,8, elemento[9] if elemento[9] else '', bord)
				worksheet.write(x,9, elemento[10] if elemento[10] else '', bord)
				worksheet.write(x,10, elemento[11] if elemento[11] else 0, numberdos)
				worksheet.write(x,11, elemento[12] if elemento[12] else 0, numberdos)
				worksheet.write(x,12, elemento[13] if elemento[13] else 0, numberdos)
				x += 1

		x = 6
		partner = "None"

		for elemento in datatotal:
			if elemento[7] in tipos1:
				if partner != elemento[5]:
					worksheet_2.write(x,0, elemento[5] ,bold)
					partner = elemento[5]
					x += 1
				worksheet_2.write(x,0, elemento[2] if elemento[2] else '', bord)
				worksheet_2.write(x,1, elemento[3] if elemento[3] else '', bord)
				worksheet_2.write(x,2, elemento[4] if elemento[4] else '', bord)
				worksheet_2.write(x,3, elemento[5] if elemento[5] else '', bord)
				worksheet_2.write(x,4, elemento[6] if elemento[6] else '', bord)
				worksheet_2.write(x,5, elemento[7] if elemento[7] else '', bord)


				worksheet_2.write(x,6, elemento[16] if elemento[16] else '', bord)

				worksheet_2.write(x,7, elemento[8] if elemento[8] else '', bord)
				worksheet_2.write(x,8, elemento[9] if elemento[9] else '', bord)
				worksheet_2.write(x,9, elemento[10] if elemento[10] else '', bord)
				worksheet_2.write(x,10, elemento[11] if elemento[11] else 0, numberdos)
				worksheet_2.write(x,11, elemento[12] if elemento[12] else 0, numberdos)
				worksheet_2.write(x,12, elemento[13] if elemento[13] else 0, numberdos)
				x += 1


		workbook.close()


		f = open( direccion + u'consulta_comercial_cuentacorriente.xlsx', 'rb')


		vals = {
			'output_name': u'CuentaCorrienteComercial.xlsx',
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



class saldo_comprobante_empresa_comercia_saldo(models.Model):
	_name = 'saldo.comprobante.empresa.comercia.saldo'

	periodo = fields.Char('Periodo')
	ruc = fields.Char('Periodo')
	empresa = fields.Char('Periodo')
	code = fields.Char('Periodo')
	descripcion = fields.Char('Periodo')
	tipo_cuenta = fields.Char('Periodo')
	debe = fields.Float('Periodo')
	haber = fields.Float('Periodo')
	saldo = fields.Float('Saldo')
	montocurrency = fields.Float('Saldo')

	_auto = False


class comercial_report_cuentas_corrienteit_saldo(osv.TransientModel):
	_name='comercial.report.cuentas.corrienteit.saldo'

	empresa = fields.Many2one('res.partner','Empresa')



	@api.multi
	def do_rebuild(self):		

		self.env.cr.execute("""  DROP VIEW IF EXISTS saldo_comprobante_empresa_comercia_saldo;
			create or replace view saldo_comprobante_empresa_comercia_saldo as (

select t1.id as id, 
ap.name as periodo,
t3.type_number as ruc,
t3.name as empresa,
t4.code as code,
t4.name as descripcion,
CASE WHEN t4.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta,
t_debe as debe,
t_haber as haber,
t_debe-t_haber as saldo ,
montocurrency

from ( 
select min(aml.id) as id, concat(aml.partner_id,aml.account_id) as identificador,sum(aml.debit) as t_debe,sum(aml.credit) as t_haber,
sum(aml.amount_currency) as montocurrency

 from account_move_line aml
inner join account_move am on am.id = aml.move_id
inner join account_period api on api.id = am.period_id
inner join account_account aa on aa.id = aml.account_id
where aa.reconcile = true 
and am.state != 'draft'
and aml.name != 'cambio: /'
group by identificador) t1

left join account_move_line t2 on t2.id=t1.id
left join account_move am on am.id = t2.move_id
left join account_period ap on ap.id = am.period_id
left join res_partner t3 on t3.id=t2.partner_id
left join account_account t4 on t4.id=t2.account_id


order by code,empresa

						)""")
		filtro = []

		filtro.append( ('saldo','!=',0) )
		
		if self.empresa.id:
			filtro.append( ('empresa','=', self.empresa.name ) )

		move_obj = self.env['saldo.comprobante.empresa.comercia.saldo']
		lstidsmove= move_obj.search(filtro)		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')		

		
		if True:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'saldoperiodo.xlsx')
			worksheet = workbook.add_worksheet("Saldo")
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
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)	


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			worksheet.set_row(0, 30)

			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,8, u"Saldos x Empresa", title)


			worksheet.write(3,0, "Periodo",boldbord)
			worksheet.write(3,1, "Empresa",boldbord)
			worksheet.write(3,2, "RUC",boldbord)
			worksheet.write(3,3, "Tipo Cuenta",boldbord)
			worksheet.write(3,4, u"Cuenta",boldbord)
			worksheet.write(3,5, u"Comprobante",boldbord)
			worksheet.write(3,6, "Entregue Adelanto al Proveedor",boldbord)
			worksheet.write(3,7, "Desconte Adelanto en Factura del Proveedor",boldbord)
			worksheet.write(3,8, "Saldo",boldbord)
			worksheet.write(3,9, "Dolares",boldbord)




			for line in self.env['saldo.comprobante.empresa.comercia.saldo'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.empresa if line.empresa  else '',bord )
				worksheet.write(x,2,line.ruc if line.ruc  else '',bord)
				worksheet.write(x,3,line.tipo_cuenta if line.tipo_cuenta  else '',bord)
				worksheet.write(x,4,line.code if line.code  else '',bord)
				worksheet.write(x,5,line.descripcion if line.descripcion  else '',bord)
				worksheet.write(x,6,line.debe ,numberdos)
				worksheet.write(x,7,line.haber ,numberdos)
				worksheet.write(x,8,line.saldo ,numberdos)
				worksheet.write(x,8,line.montocurrency ,numberdos)
				x = x +1

			tam_col = [11,6,8.8,7.14,38,11,11,11,10,11,14,10,11,14,14,10,16,16,20,36]


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

			workbook.close()
			
			f = open(direccion + 'saldoperiodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'SaldoEmpresa.xlsx',
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


		