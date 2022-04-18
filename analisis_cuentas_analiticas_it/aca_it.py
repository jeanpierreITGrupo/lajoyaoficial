# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
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
import decimal


class periodo_aanalitica_it(osv.osv):
	_name = 'periodo.aanalitica.it'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_fin = fields.Many2one('account.period','Periodo Final',required=True)
	mostrar = fields.Selection([('PDF','PDF'),('EXCEL','EXCEL')],'Mostrar en',required=True,default= 'EXCEL')
	tipo = fields.Selection([('1','Contabilidad'),('2','Suministros')],'Tipo',required=True)



	@api.multi
	def do_rebuild(self):
		if self.tipo == '1':
			return self.do_contabilidad()
		else:
			return self.do_suministros()


	@api.multi
	def do_suministros(self):
		if True:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'analitica_periodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Analitica x Periodo")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			#boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			#boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
			bord = workbook.add_format()
			bord.set_border(style=1)
			#numberdos.set_border(style=1)
			#numbertres.set_border(style=1)			
			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, u"Reporte Analítico de Periodo " + self.period_ini.code + ' a ' + self.period_fin.code, bold)

			productos='{'
			almacenes='{'

			lst_products  = self.env['product.product'].search([])

			for producto in lst_products:
				productos=productos+str(producto.id)+','
			productos=productos[:-1]+'}'

			lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

			for location in lst_locations:
				almacenes=almacenes+str(location.id)+','
			almacenes=almacenes[:-1]+'}'

			t = """ 
			"""
			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			self.env.cr.execute(""" 

				 select 
				 fecha as date, kardex.numdoc_cuadre , aaa.name as ref,
				 ''::varchar as name , ''::varchar as ajname,  kardex.credit as credit,
				 kardex.salida as unit_amount, aaa_padre.name , aaa.name, kardex.account_invoice, '' as rcname,linea.amount, 
	padre.amount, aaa.code, aaa_padre.code,
	aaa.type, aaa_padre.type,
	0 as beneficiario,
	''::varchar as departamento,
	false as is_employee,
	pp.name_template,
	pp.default_code

				 from get_kardex_v("""+ str(self.period_ini.fiscalyear_id.name) + "0101," + str(self.period_fin.date_stop).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) as kardex
				 inner join stock_move sm on sm.id = kardex.stock_moveid
				 inner join account_analytic_account aaa on aaa.id= sm.analitic_id				 
				 left join product_product pp on pp.id = kardex.product_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
		left join (

		--

		select aaa.id as id,sum(kardex.credit) as amount


		from get_kardex_v("""+ str(self.period_ini.fiscalyear_id.name) + "0101," + str(self.period_fin.date_stop).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) as kardex
				 inner join stock_move sm on sm.id = kardex.stock_moveid
				 inner join account_analytic_account aaa on aaa.id= sm.analitic_id				 
				 left join product_product pp on pp.id = kardex.product_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join (

		select aaa.id as id,sum(aal.amount) as amount
		from account_analytic_line aal
		left join account_analytic_account aaa on aaa.id = aal.account_id
		left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
		left join account_account aa on aa.id = aal.general_account_id
		left join res_users ru on ru.id = aal.user_id
		left join res_partner rp on rp.id = ru.partner_id
		left join account_move_line aml on aml.id = aal.move_id
		left join account_move am on am.id = aml.move_id
		left join account_period ap on ap.id = am.period_origin_id
		left join res_currency rc on rc.id = am.com_det_currency

		where periodo_num(ap.code) >= periodo_num('""" +self.period_ini.code+ """')  and  periodo_num(ap.code) <= periodo_num('""" +self.period_fin.code+ """') 
		group by aaa.id

	) linea on linea.id = aaa.id

 where kardex.fecha >= '""" +str(self.period_ini.date_start)+ """' and kardex.fecha <= '""" +str(self.period_fin.date_stop)+ """' 
		
	group by aaa.id

		--

	) linea on linea.id = aaa.id

	left join (

		select aaa_padre.id as id,sum(kardex.credit) as amount


		from get_kardex_v("""+ str(self.period_ini.fiscalyear_id.name) + "0101," + str(self.period_fin.date_stop).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) as kardex
				 inner join stock_move sm on sm.id = kardex.stock_moveid
				 inner join account_analytic_account aaa on aaa.id= sm.analitic_id				 
				 left join product_product pp on pp.id = kardex.product_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join (

		select aaa.id as id,sum(aal.amount) as amount
		from account_analytic_line aal
		left join account_analytic_account aaa on aaa.id = aal.account_id
		left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
		left join account_account aa on aa.id = aal.general_account_id
		left join res_users ru on ru.id = aal.user_id
		left join res_partner rp on rp.id = ru.partner_id
		left join account_move_line aml on aml.id = aal.move_id
		left join account_move am on am.id = aml.move_id
		left join account_period ap on ap.id = am.period_origin_id
		left join res_currency rc on rc.id = am.com_det_currency
		where periodo_num(ap.code) >= periodo_num('""" +self.period_ini.code+ """')  and  periodo_num(ap.code) <= periodo_num('""" +self.period_fin.code+ """') 
		group by aaa.id

	) linea on linea.id = aaa.id
 where kardex.fecha >= '""" +str(self.period_ini.date_start)+ """' and kardex.fecha <= '""" +str(self.period_fin.date_stop)+ """' 
		

	group by aaa_padre.id

	) padre on padre.id = aaa_padre.id
				 where kardex.fecha >= '""" +str(self.period_ini.date_start)+ """' and kardex.fecha <= '""" +str(self.period_fin.date_stop)+ """' 

	order by aaa_padre.name, aaa.name,fecha
	 """)

			c_anal = None
			c_padre_anal = None
			dic_type = {
				'':'',
				'view':u'Vista Analítica',
				'normal':u'Cuenta Analítica',
				'contract':u'Contrato o Proyecto',
				'template':u'Plantilla de Contrato',
			}
			elementos = self.env.cr.fetchall()
			for i in elementos:
				if c_padre_anal != i[7]:
					c_padre_anal = i[7]
					c_anal = None
					worksheet.write(x,1, "Referencia",boldbord)
					worksheet.write(x,5, "Codigo",boldbord)
					worksheet.write(x,6, "Importe Soles",boldbord)
					worksheet.write(x,8, "Moneda",boldbord)
					worksheet.write(x,9, "Tipo",boldbord)
					worksheet.write(x,10, u"Estado Análitico",boldbord)
					x += 1
					
					worksheet.write(x,1, i[7] if i[7] else '',bold)
					worksheet.write(x,5, i[14] if i[14] else '',bold)
					worksheet.write(x,6, i[12] if i[12] else 0.00,numberdosbold)
					worksheet.write(x,8, i[12] if i[12] else 0.00,numberdosbold)
					worksheet.write(x,9, i[10] if i[10] and i[10]!= '' else 'PEN',bold)
					worksheet.write(x,10, dic_type[i[16] if i[16] else ''],bold)
					x += 1


				if c_anal != i[8]:
					c_anal = i[8]

					worksheet.write(x,1, i[8] if i[8] else '',bold)
					worksheet.write(x,5, i[13] if i[13] else '',bold)
					worksheet.write(x,6, i[11] if i[11] else 0.00,numberdosbold)
					worksheet.write(x,8, i[11] if i[11] else 0.00,numberdosbold)
					worksheet.write(x,9, i[10] if i[10] and i[10]!= '' else 'PEN',bold)
					worksheet.write(x,10, dic_type[i[15] if i[15] else ''],bold)
					x += 1


					worksheet.write(x,0, u"Fecha",boldbord)
					worksheet.write(x,1, u"Ref.",boldbord)
					worksheet.write(x,2, u"Descripción",boldbord)
					worksheet.write(x,3, u"Usuario",boldbord)
					worksheet.write(x,4, u"Diario Analítico",boldbord)
					worksheet.write(x,5, u"Beneficiario",boldbord)
					worksheet.write(x,6, u"Departamento",boldbord)
					worksheet.write(x,8, u"Importe Soles",boldbord)
					worksheet.write(x,9, u"Cantidad",boldbord)
					worksheet.write(x,11, u"Tipo",boldbord)
					worksheet.write(x,12, u"Estado Analítico",boldbord)
					worksheet.write(x,13, u"Cuenta General",boldbord)
					worksheet.write(x,14, u"Producto",boldbord)
					worksheet.write(x,15, u"Codigo",boldbord)
					x += 1

				ben = False
				if i[19] == True:
					he = self.env['hr.employee'].search([('id','=',i[17])])
					if len(he) > 0:
						ben = he[0].name_related
				else:
					rp = self.env['res.partner'].search([('id','=',i[17])])
					if len(rp) > 0:
						ben = rp[0].display_name

				worksheet.write(x,0, i[0] if i[0] else '',normal)
				worksheet.write(x,1, i[1] if i[1] else '',normal)
				worksheet.write(x,2, i[2] if i[2] else '',normal)
				worksheet.write(x,3, i[3] if i[3] else '',normal)
				worksheet.write(x,4, i[4] if i[4] else '',normal)
				worksheet.write(x,5, ben if ben else '',normal)
				worksheet.write(x,6, i[18] if i[18] else '',normal)
				worksheet.write(x,8, i[5] if i[5] else 00,numberdos)
				worksheet.write(x,9, i[6] if i[6] else 00,numberdos)
				worksheet.write(x,11, i[10] if i[10] else 'PEN',normal)
				worksheet.write(x,12, i[8] if i[8] else '',normal)
				worksheet.write(x,13, i[9] if i[9] else '',normal)

				worksheet.write(x,14, i[20] if i[20] else '',normal)
				worksheet.write(x,15, i[21] if i[21] else '',normal)
				x += 1


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
			
			f = open(direccion + 'analitica_periodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'PeriodoAnalisisAnalitica.xlsx',
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


	@api.multi
	def do_contabilidad(self):
		if self.mostrar == 'PDF':
			self.reporteador()
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'PeriodoAnalisisAnalitica.pdf',
				'output_file': open(direccion + "PeriodoAnalisisAnalitica.pdf", "rb").read().encode("base64"),	
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
		else:

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'analitica_periodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Analitica x Periodo")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			#boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			#boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
			bord = workbook.add_format()
			bord.set_border(style=1)
			#numberdos.set_border(style=1)
			#numbertres.set_border(style=1)			
			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, u"Reporte Analítico de Periodo " + self.period_ini.code + ' a ' + self.period_fin.code, bold)

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			self.env.cr.execute(""" 

	select 
	aal.date, aal.ref, aal.name, 
	rp.name , aj.name, aal.amount, 
	aal.unit_amount, aaa_padre.name , aaa.name, 
	aa.code || ' - ' || aa.name, rc.name, linea.amount, 
	padre.amount, aaa.code, aaa_padre.code,
	aaa.type, aaa_padre.type,
	(case when ai.is_employee = true then ai.b_employee_id else ai.b_partner_id end) as beneficiario,
	(case when ai.is_employee = true then ai.department_he else ai.department_rp end) as departamento,
	ai.is_employee,
	ad.code || ' - ' || ad.name,
	ah.code || ' - ' || ah.name,
	pplx.name_template,
	pplx.default_code

	from account_analytic_line aal
	left join account_journal aj on aj.id = aal.journal_id
	left join account_analytic_account aaa on aaa.id = aal.account_id

	left join account_account ad on ad.id = aaa.account_account_moorage_id
	left join account_account ah on ah.id = aaa.account_account_moorage_credit_id

	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join account_account aa on aa.id = aal.general_account_id
	left join res_users ru on ru.id = aal.user_id
	left join res_partner rp on rp.id = ru.partner_id
	inner join account_move_line aml on aml.id = aal.move_id
	left join product_product pplx on pplx.id = aml.product_id
	inner join account_move am on am.id = aml.move_id
	inner join account_period ap on ap.id = am.period_id
	left join res_currency rc on rc.id = am.com_det_currency
	left join account_invoice ai on ai.move_id = am.id	
	inner join (

		select aaa.id as id,sum(aal.amount) as amount
		from account_analytic_line aal
		left join account_analytic_account aaa on aaa.id = aal.account_id
		left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
		left join account_account aa on aa.id = aal.general_account_id
		left join res_users ru on ru.id = aal.user_id
		left join res_partner rp on rp.id = ru.partner_id
		inner join account_move_line aml on aml.id = aal.move_id
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_id
		left join res_currency rc on rc.id = am.com_det_currency
		where periodo_num(ap.code) >= periodo_num('""" +self.period_ini.code+ """')  and  periodo_num(ap.code) <= periodo_num('""" +self.period_fin.code+ """') 
		and am.state != 'draft'
		group by aaa.id

	) linea on linea.id = aaa.id

	inner join (

		select aaa_padre.id as id,sum(aal.amount) as amount
		from account_analytic_line aal
		left join account_analytic_account aaa on aaa.id = aal.account_id
		left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
		left join account_account aa on aa.id = aal.general_account_id
		left join res_users ru on ru.id = aal.user_id
		left join res_partner rp on rp.id = ru.partner_id
		inner join account_move_line aml on aml.id = aal.move_id
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_id
		left join res_currency rc on rc.id = am.com_det_currency
		where periodo_num(ap.code) >= periodo_num('""" +self.period_ini.code+ """')  and  periodo_num(ap.code) <= periodo_num('""" +self.period_fin.code+ """') 
		and am.state != 'draft'
		group by aaa_padre.id

	) padre on padre.id = aaa_padre.id
	where periodo_num(ap.code) >= periodo_num('""" +self.period_ini.code+ """')  and  periodo_num(ap.code) <= periodo_num('""" +self.period_fin.code+ """')
	and am.state != 'draft' 
	order by aaa_padre.name, aaa.name,aal.date
	 """)

			c_anal = None
			c_padre_anal = None
			dic_type = {
				'':'',
				'view':u'Vista Analítica',
				'normal':u'Cuenta Analítica',
				'contract':u'Contrato o Proyecto',
				'template':u'Plantilla de Contrato',
			}
			elementos = self.env.cr.fetchall()
			for i in elementos:
				if c_padre_anal != i[7]:
					c_padre_anal = i[7]
					c_anal = None
					worksheet.write(x,1, "Referencia",boldbord)
					worksheet.write(x,5, "Codigo",boldbord)
					worksheet.write(x,6, "Importe Soles",boldbord)
					worksheet.write(x,8, "Moneda",boldbord)
					worksheet.write(x,9, "Tipo",boldbord)
					worksheet.write(x,10, u"Estado Análitico",boldbord)
					x += 1
					
					worksheet.write(x,1, i[7] if i[7] else '',bold)
					worksheet.write(x,5, i[14] if i[14] else '',bold)
					worksheet.write(x,6, i[12] if i[12] else 0.00,numberdosbold)
					worksheet.write(x,8, i[12] if i[12] else 0.00,numberdosbold)
					worksheet.write(x,9, i[10] if i[10] and i[10]!= '' else 'PEN',bold)
					worksheet.write(x,10, dic_type[i[16] if i[16] else ''],bold)
					x += 1


				if c_anal != i[8]:
					c_anal = i[8]

					worksheet.write(x,1, i[8] if i[8] else '',bold)
					worksheet.write(x,5, i[13] if i[13] else '',bold)
					worksheet.write(x,6, i[11] if i[11] else 0.00,numberdosbold)
					worksheet.write(x,8, i[11] if i[11] else 0.00,numberdosbold)
					worksheet.write(x,9, i[10] if i[10] and i[10]!= '' else 'PEN',bold)
					worksheet.write(x,10, dic_type[i[15] if i[15] else ''],bold)
					x += 1


					worksheet.write(x,0, u"Fecha",boldbord)
					worksheet.write(x,1, u"Ref.",boldbord)
					worksheet.write(x,2, u"Descripción",boldbord)
					worksheet.write(x,3, u"Usuario",boldbord)
					worksheet.write(x,4, u"Diario Analítico",boldbord)
					worksheet.write(x,5, u"Beneficiario",boldbord)
					worksheet.write(x,6, u"Departamento",boldbord)
					worksheet.write(x,8, u"Importe Soles",boldbord)
					worksheet.write(x,9, u"Cantidad",boldbord)
					worksheet.write(x,11, u"Tipo",boldbord)
					worksheet.write(x,12, u"Estado Analítico",boldbord)
					worksheet.write(x,13, u"Cuenta General",boldbord)

					worksheet.write(x,14, u"Amarre al Debe",boldbord)
					worksheet.write(x,15, u"Amarre al Haber",boldbord)
					worksheet.write(x,16, u"Producto",boldbord)
					worksheet.write(x,17, u"Codigo",boldbord)
					x += 1

				ben = False
				if i[19] == True:
					he = self.env['hr.employee'].search([('id','=',i[17])])
					if len(he) > 0:
						ben = he[0].name_related
				else:
					rp = self.env['res.partner'].search([('id','=',i[17])])
					if len(rp) > 0:
						ben = rp[0].display_name

				worksheet.write(x,0, i[0] if i[0] else '',normal)
				worksheet.write(x,1, i[1] if i[1] else '',normal)
				worksheet.write(x,2, i[2] if i[2] else '',normal)
				worksheet.write(x,3, i[3] if i[3] else '',normal)
				worksheet.write(x,4, i[4] if i[4] else '',normal)
				worksheet.write(x,5, ben if ben else '',normal)
				worksheet.write(x,6, i[18] if i[18] else '',normal)
				worksheet.write(x,8, i[5] if i[5] else 00,numberdos)
				worksheet.write(x,9, i[6] if i[6] else 00,numberdos)
				worksheet.write(x,11, i[10] if i[10] else 'PEN',normal)
				worksheet.write(x,12, i[8] if i[8] else '',normal)
				worksheet.write(x,13, i[9] if i[9] else '',normal)

				worksheet.write(x,14, i[20] if i[20] else '',normal)
				worksheet.write(x,15, i[21] if i[21] else '',normal)

				worksheet.write(x,16, i[22] if i[22] else '',normal)
				worksheet.write(x,17, i[23] if i[23] else '',normal)
				x += 1


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
			
			f = open(direccion + 'analitica_periodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'PeriodoAnalisisAnalitica.xlsx',
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



	@api.multi
	def cabezera(self,c,wReal,hReal):

		c.setFont("Times-Bold", 15)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, u"Reporte Analítico de Periodo " + self.period_ini.code + ' a ' + self.period_fin.code )
		
	@api.multi
	def reporteador(self):
		import sys
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = height - 30
		hReal = width - 40
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas(direccion + "PeriodoAnalisisAnalitica.pdf", pagesize=(height,width))
		
		inicio = 0
		pagina = 1
		pos_inicial = hReal-20
		c_anal = None
		c_padre_anal = None
		self.cabezera(c,wReal,hReal)

		self.env.cr.execute(""" 

select 
aal.date, aal.ref, aal.name, 
rp.name , aj.name, aal.amount, 
aal.unit_amount, aaa_padre.name , aaa.name, 
aa.code || ' - ' || aa.name, rc.name, linea.amount, 
padre.amount, aaa.code, aaa_padre.code,
aaa.type, aaa_padre.type,
(case when ai.is_employee = true then ai.b_employee_id else ai.b_partner_id end) as beneficiario,
(case when ai.is_employee = true then ai.department_he else ai.department_rp end) as departamento,
ai.is_employee
from account_analytic_line aal
left join account_journal aj on aj.id = aal.journal_id
left join account_analytic_account aaa on aaa.id = aal.account_id
left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
left join account_account aa on aa.id = aal.general_account_id
left join res_users ru on ru.id = aal.user_id
left join res_partner rp on rp.id = ru.partner_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
inner join account_period ap on ap.id = am.period_origin_id
left join res_currency rc on rc.id = am.com_det_currency
left join account_invoice ai on ai.move_id = am.id
inner join (

	select aaa.id as id,sum(aal.amount) as amount
	from account_analytic_line aal
	left join account_analytic_account aaa on aaa.id = aal.account_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join account_account aa on aa.id = aal.general_account_id
	left join res_users ru on ru.id = aal.user_id
	left join res_partner rp on rp.id = ru.partner_id
		inner join account_move_line aml on aml.id = aal.move_id
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_origin_id
	left join res_currency rc on rc.id = am.com_det_currency
	where periodo_num(ap.code) >= periodo_num('""" +self.period_ini.code+ """')  and  periodo_num(ap.code) <= periodo_num('""" +self.period_fin.code+ """') 
	group by aaa.id

) linea on linea.id = aaa.id

inner join (

	select aaa_padre.id as id,sum(aal.amount) as amount
	from account_analytic_line aal
	left join account_analytic_account aaa on aaa.id = aal.account_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join account_account aa on aa.id = aal.general_account_id
	left join res_users ru on ru.id = aal.user_id
	left join res_partner rp on rp.id = ru.partner_id
		inner join account_move_line aml on aml.id = aal.move_id
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_origin_id
	left join res_currency rc on rc.id = am.com_det_currency
	where periodo_num(ap.code) >= periodo_num('""" +self.period_ini.code+ """')  and  periodo_num(ap.code) <= periodo_num('""" +self.period_fin.code+ """') 
	group by aaa_padre.id

) padre on padre.id = aaa_padre.id
where periodo_num(ap.code) >= periodo_num('""" +self.period_ini.code+ """')  and  periodo_num(ap.code) <= periodo_num('""" +self.period_fin.code+ """') 
order by aaa_padre.name, aaa.name,aal.date
 """)

		c_anal = None
		c_padre_anal = None
		valores = 		[40, 50, 85,  85, 55, 50, 50, 45, 50, 35,155,115]
		pos_ini_val = 	[20, 60, 110,195,280,335,385,435,480,530,565,720]
		dic_type = {
			'':'',
			'view':u'Vista Analítica',
			'normal':u'Cuenta Analítica',
			'contract':u'Contrato o Proyecto',
			'template':u'Plantilla de Contrato',
		}
		elementos = self.env.cr.fetchall()
		for i in elementos:
			if c_padre_anal != i[7]:
				c_padre_anal = i[7]
				c_anal = None

				c.setFont("Times-Bold", 12)
				c.drawString(pos_ini_val[1], pos_inicial, 'Referencia')
				c.drawString(pos_ini_val[5], pos_inicial, 'Codigo')
				c.drawString(pos_ini_val[6], pos_inicial, 'Importe Soles')
				c.drawString(pos_ini_val[8], pos_inicial, 'Moneda')
				c.drawString(pos_ini_val[9], pos_inicial, 'Tipo')
				c.drawString(pos_ini_val[10], pos_inicial, u'Estado Análitico')
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,20,pagina)
				
				c.setFont("Times-Bold", 8)
				c.drawString(pos_ini_val[1], pos_inicial, i[7] if i[7] else '')
				c.drawString(pos_ini_val[5], pos_inicial, i[14] if i[14] else '')
				c.drawRightString(pos_ini_val[7]-2, pos_inicial,  "%0.2f" %(abs(i[12] if i[12] else 0.00)) )
				c.drawRightString(pos_ini_val[9]-2, pos_inicial, "%0.2f" %(i[12] if i[12] else 0.00))
				c.drawString(pos_ini_val[9], pos_inicial, i[10] if i[10] and i[10]!= '' else 'PEN')
				c.drawString(pos_ini_val[10], pos_inicial, dic_type[i[16] if i[16] else ''])
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			
			if c_anal != i[8]:
				c_anal = i[8]

				c.setFont("Times-Bold", 8)				
				c.drawString(pos_ini_val[1], pos_inicial, i[8] if i[8] else '')
				c.drawString(pos_ini_val[5], pos_inicial, i[13] if i[13] else '')
				c.drawRightString(pos_ini_val[7]-2, pos_inicial,  "%0.2f" %(abs(i[11] if i[11] else 0.00)) )
				c.drawRightString(pos_ini_val[9]-2, pos_inicial, "%0.2f" %(i[11] if i[11] else 0.00))
				c.drawString(pos_ini_val[9], pos_inicial, i[10] if i[10] and i[10]!= '' else 'PEN')
				c.drawString(pos_ini_val[10], pos_inicial, dic_type[i[15] if i[15] else ''])
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,20,pagina)


				c.setFont("Times-Bold", 10)				
				c.drawString(pos_ini_val[0], pos_inicial, u'Fecha')
				c.drawString(pos_ini_val[1], pos_inicial, u'Ref.')
				c.drawString(pos_ini_val[2], pos_inicial, u'Descripción')
				c.drawString(pos_ini_val[3], pos_inicial, u'Usuario')
				c.drawString(pos_ini_val[4], pos_inicial, u'Diario Analítico')
				c.drawString(pos_ini_val[6], pos_inicial, u'Importe Soles')
				c.drawString(pos_ini_val[7], pos_inicial, u'     Cantidad')
				c.drawString(pos_ini_val[9], pos_inicial, u'Tipo')
				c.drawString(pos_ini_val[10], pos_inicial, u'Estado Analítico')
				c.drawString(pos_ini_val[11], pos_inicial, u'Cuenta General')
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)

			c.setFont("Times-Roman", 8)				
			c.drawString(pos_ini_val[0], pos_inicial, self.particionar_text( i[0] if i[0] else '' , valores[0]-5) )
			c.drawString(pos_ini_val[1], pos_inicial, self.particionar_text( i[1][:10] if i[1] else '' , 20) )
			c.drawString(pos_ini_val[2], pos_inicial, self.particionar_text( i[2] if i[2] else '' , valores[2]-5) )
			c.drawString(pos_ini_val[3], pos_inicial, self.particionar_text( i[3] if i[3] else '' , valores[3]-5) )
			c.drawString(pos_ini_val[4], pos_inicial, self.particionar_text( i[4] if i[4] else '' , 50 ))
			c.drawRightString(pos_ini_val[7]-2, pos_inicial, "%0.2f" %(i[5] if i[5] else 0) )
			c.drawRightString(pos_ini_val[8]-2, pos_inicial, str( i[6] if i[6] else 0) )
			c.drawString(pos_ini_val[9], pos_inicial, self.particionar_text( i[10] if i[10] else 'PEN' , valores[9]-5) )
			c.drawString(pos_ini_val[10], pos_inicial, self.particionar_text( i[8] if i[8] else '' , valores[10]-5) )
			c.drawString(pos_ini_val[11], pos_inicial, self.particionar_text( i[9] if i[9] else '' , valores[11]-5) )

			pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		c.save()

	@api.multi
	def particionar_text(self,c,f):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Times-Roman',8,f)
			if len(lines)>1:
				return tet[:-1]
		return tet

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-25
		else:
			return pagina,posactual-valor
	@api.multi
	def verify_space(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual-valor <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-25
		else:
			return pagina,posactual





class fecha_aanalitica_it(osv.osv):
	_name = 'fecha.aanalitica.it'

	date_ini = fields.Date('Fecha Inicial',required=True)
	date_fin = fields.Date('Fecha Final',required=True)
	mostrar = fields.Selection([('PDF','PDF'),('EXCEL','EXCEL')],'Mostrar en',required=True)

	@api.multi
	def do_rebuild(self):
		if self.mostrar == 'PDF':
			self.reporteador()
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'FechaAnalisisAnalitica.pdf',
				'output_file': open(direccion + "PeriodoAnalisisAnalitica.pdf", "rb").read().encode("base64"),	
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

		else:

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'analitica_periodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Analitica x Periodo")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			#boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			#boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
			bord = workbook.add_format()
			bord.set_border(style=1)
			#numberdos.set_border(style=1)
			#numbertres.set_border(style=1)			
			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, u"Reporte Analítico de Periodo " + str(self.date_ini) + ' a ' + str(self.date_fin) , bold)

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			
			self.env.cr.execute(""" 

select 
aal.date, aal.ref, aal.name, 
rp.name , aj.name, aal.amount, 
aal.unit_amount, aaa_padre.name , aaa.name, 
aa.code || ' - ' || aa.name, rc.name, linea.amount, 
padre.amount, aaa.code, aaa_padre.code,
aaa.type, aaa_padre.type,
(case when ai.is_employee = true then ai.b_employee_id else ai.b_partner_id end) as beneficiario,
(case when ai.is_employee = true then ai.department_he else ai.department_rp end) as departamento,
ai.is_employee
from account_analytic_line aal
left join account_journal aj on aj.id = aal.journal_id
left join account_analytic_account aaa on aaa.id = aal.account_id
left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
left join account_account aa on aa.id = aal.general_account_id
left join res_users ru on ru.id = aal.user_id
left join res_partner rp on rp.id = ru.partner_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
inner join account_period ap on ap.id = am.period_id
left join res_currency rc on rc.id = am.com_det_currency
left join account_invoice ai on ai.move_id = am.id
inner join (

	select aaa.id as id,sum(aal.amount) as amount
	from account_analytic_line aal
	left join account_analytic_account aaa on aaa.id = aal.account_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join account_account aa on aa.id = aal.general_account_id
	left join res_users ru on ru.id = aal.user_id
	left join res_partner rp on rp.id = ru.partner_id
		inner join account_move_line aml on aml.id = aal.move_id
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_id
	left join res_currency rc on rc.id = am.com_det_currency
	where aal.date >=  '""" +self.date_ini+ """'  and  aal.date <= '""" +self.date_fin+ """' 
	group by aaa.id

) linea on linea.id = aaa.id

inner join (

	select aaa_padre.id as id,sum(aal.amount) as amount
	from account_analytic_line aal
	left join account_analytic_account aaa on aaa.id = aal.account_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join account_account aa on aa.id = aal.general_account_id
	left join res_users ru on ru.id = aal.user_id
	left join res_partner rp on rp.id = ru.partner_id
		inner join account_move_line aml on aml.id = aal.move_id
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_id
	left join res_currency rc on rc.id = am.com_det_currency
	where aal.date >=  '""" +self.date_ini+ """'  and  aal.date <= '""" +self.date_fin+ """' 
	group by aaa_padre.id

) padre on padre.id = aaa_padre.id
where aal.date >=  '""" +self.date_ini+ """'  and  aal.date <= '""" +self.date_fin+ """' 
order by aaa_padre.name, aaa.name
 """)


			c_anal = None
			c_padre_anal = None
			dic_type = {
				'':'',
				'view':u'Vista Analítica',
				'normal':u'Cuenta Analítica',
				'contract':u'Contrato o Proyecto',
				'template':u'Plantilla de Contrato',
			}
			elementos = self.env.cr.fetchall()
			for i in elementos:
				if c_padre_anal != i[7]:
					c_padre_anal = i[7]
					c_anal = None
					worksheet.write(x,1, "Referencia",boldbord)
					worksheet.write(x,5, "Codigo",boldbord)
					worksheet.write(x,6, "Importe Soles",boldbord)
					worksheet.write(x,8, "Moneda",boldbord)
					worksheet.write(x,9, "Tipo",boldbord)
					worksheet.write(x,10, u"Estado Análitico",boldbord)
					x += 1
					
					worksheet.write(x,1, i[7] if i[7] else '',bold)
					worksheet.write(x,5, i[14] if i[14] else '',bold)
					worksheet.write(x,6, i[12] if i[12] else 0.00,numberdosbold)
					worksheet.write(x,8, i[12] if i[12] else 0.00,numberdosbold)
					worksheet.write(x,9, i[10] if i[10] and i[10]!= '' else 'PEN',bold)
					worksheet.write(x,10, dic_type[i[16] if i[16] else ''],bold)
					x += 1


				if c_anal != i[8]:
					c_anal = i[8]

					worksheet.write(x,1, i[8] if i[8] else '',bold)
					worksheet.write(x,5, i[13] if i[13] else '',bold)
					worksheet.write(x,6, i[11] if i[11] else 0.00,numberdosbold)
					worksheet.write(x,8, i[11] if i[11] else 0.00,numberdosbold)
					worksheet.write(x,9, i[10] if i[10] and i[10]!= '' else 'PEN',bold)
					worksheet.write(x,10, dic_type[i[15] if i[15] else ''],bold)
					x += 1


					worksheet.write(x,0, u"Fecha",boldbord)
					worksheet.write(x,1, u"Ref.",boldbord)
					worksheet.write(x,2, u"Descripción",boldbord)
					worksheet.write(x,3, u"Usuario",boldbord)
					worksheet.write(x,4, u"Diario Analítico",boldbord)
					worksheet.write(x,5, u"Beneficiario",boldbord)
					worksheet.write(x,6, u"Departamento",boldbord)
					worksheet.write(x,8, u"Importe Soles",boldbord)
					worksheet.write(x,9, u"Cantidad",boldbord)
					worksheet.write(x,11, u"Tipo",boldbord)
					worksheet.write(x,12, u"Estado Analítico",boldbord)
					worksheet.write(x,13, u"Cuenta General",boldbord)
					x += 1

				ben = False
				if i[19] == True:
					he = self.env['hr.employee'].search([('id','=',i[17])])
					if len(he) > 0:
						ben = he[0].name_related
				else:
					rp = self.env['res.partner'].search([('id','=',i[17])])
					if len(rp) > 0:
						ben = rp[0].display_name

				worksheet.write(x,0, i[0] if i[0] else '',normal)
				worksheet.write(x,1, i[1] if i[1] else '',normal)
				worksheet.write(x,2, i[2] if i[2] else '',normal)
				worksheet.write(x,3, i[3] if i[3] else '',normal)
				worksheet.write(x,4, i[4] if i[4] else '',normal)
				worksheet.write(x,5, ben if ben else '',normal)
				worksheet.write(x,6, i[18] if i[18] else '',normal)
				worksheet.write(x,8, i[5] if i[5] else 00,numberdos)
				worksheet.write(x,9, i[6] if i[6] else 00,numberdos)
				worksheet.write(x,11, i[10] if i[10] else 'PEN',normal)
				worksheet.write(x,12, i[8] if i[8] else '',normal)
				worksheet.write(x,13, i[9] if i[9] else '',normal)
				x += 1


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
			
			f = open(direccion + 'analitica_periodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'PeriodoAnalisisAnalitica.xlsx',
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


	@api.multi
	def cabezera(self,c,wReal,hReal):

		c.setFont("Times-Bold", 15)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, u"Reporte Analítico de Fecha " + str(self.date_ini) + ' a ' + str(self.date_fin) )
		
	@api.multi
	def reporteador(self):
		import sys
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = height - 30
		hReal = width - 40
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas(direccion + "PeriodoAnalisisAnalitica.pdf", pagesize=(height,width))
		
		inicio = 0
		pagina = 1
		pos_inicial = hReal-25
		c_anal = None
		c_padre_anal = None
		self.cabezera(c,wReal,hReal)

		self.env.cr.execute(""" 

select 
aal.date, aal.ref, aal.name, 
rp.name , aj.name, aal.amount, 
aal.unit_amount, aaa_padre.name , aaa.name, 
aa.code || ' - ' || aa.name, rc.name, linea.amount, 
padre.amount, aaa.code, aaa_padre.code,
aaa.type, aaa_padre.type,
(case when ai.is_employee = true then ai.b_employee_id else ai.b_partner_id end) as beneficiario,
(case when ai.is_employee = true then ai.department_he else ai.department_rp end) as departamento,
ai.is_employee
from account_analytic_line aal
left join account_journal aj on aj.id = aal.journal_id
left join account_analytic_account aaa on aaa.id = aal.account_id
left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
left join account_account aa on aa.id = aal.general_account_id
left join res_users ru on ru.id = aal.user_id
left join res_partner rp on rp.id = ru.partner_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
inner join account_period ap on ap.id = am.period_id
left join res_currency rc on rc.id = am.com_det_currency
left join account_invoice ai on ai.move_id = am.id
inner join (

	select aaa.id as id,sum(aal.amount) as amount
	from account_analytic_line aal
	left join account_analytic_account aaa on aaa.id = aal.account_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join account_account aa on aa.id = aal.general_account_id
	left join res_users ru on ru.id = aal.user_id
	left join res_partner rp on rp.id = ru.partner_id
		inner join account_move_line aml on aml.id = aal.move_id
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_id
	left join res_currency rc on rc.id = am.com_det_currency
	where aal.date >=  '""" +self.date_ini+ """'  and  aal.date <= '""" +self.date_fin+ """' 
	group by aaa.id

) linea on linea.id = aaa.id

inner join (

	select aaa_padre.id as id,sum(aal.amount) as amount
	from account_analytic_line aal
	left join account_analytic_account aaa on aaa.id = aal.account_id
	left join account_analytic_account aaa_padre on aaa_padre.id = aaa.parent_id
	left join account_account aa on aa.id = aal.general_account_id
	left join res_users ru on ru.id = aal.user_id
	left join res_partner rp on rp.id = ru.partner_id
		inner join account_move_line aml on aml.id = aal.move_id
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_id
	left join res_currency rc on rc.id = am.com_det_currency
	where aal.date >=  '""" +self.date_ini+ """'  and  aal.date <= '""" +self.date_fin+ """' 
	group by aaa_padre.id

) padre on padre.id = aaa_padre.id
where aal.date >=  '""" +self.date_ini+ """'  and  aal.date <= '""" +self.date_fin+ """' 
order by aaa_padre.name, aaa.name
 """)

		c_anal = None
		c_padre_anal = None
		valores = 		[40, 50, 85,  85, 55, 50, 50, 45, 50, 35,155,115]
		pos_ini_val = 	[20, 60, 110,195,280,335,385,435,480,530,565,720]
		dic_type = {
			'':'',
			'view':u'Vista Analítica',
			'normal':u'Cuenta Analítica',
			'contract':u'Contrato o Proyecto',
			'template':u'Plantilla de Contrato',
		}
		elementos = self.env.cr.fetchall()
		for i in elementos:
			if c_padre_anal != i[7]:
				c_padre_anal = i[7]
				c_anal = None

				c.setFont("Times-Bold", 12)
				c.drawString(pos_ini_val[1], pos_inicial, 'Referencia')
				c.drawString(pos_ini_val[5], pos_inicial, 'Codigo')
				c.drawString(pos_ini_val[6], pos_inicial, 'Importe Soles')
				c.drawString(pos_ini_val[8], pos_inicial, 'Moneda')
				c.drawString(pos_ini_val[9], pos_inicial, 'Tipo')
				c.drawString(pos_ini_val[10], pos_inicial, u'Estado Análitico')
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,20,pagina)
				
				c.setFont("Times-Bold", 8)
				c.drawString(pos_ini_val[1], pos_inicial, i[7] if i[7] else '')
				c.drawString(pos_ini_val[5], pos_inicial, i[14] if i[14] else '')
				c.drawRightString(pos_ini_val[7]-2, pos_inicial,  "%0.2f" %(abs(i[12] if i[12] else 0.00)) )
				c.drawRightString(pos_ini_val[9]-2, pos_inicial, "%0.2f" %(i[12] if i[12] else 0.00))
				c.drawString(pos_ini_val[9], pos_inicial, i[10] if i[10] else 'PEN')
				c.drawString(pos_ini_val[10], pos_inicial, dic_type[i[16] if i[16] else ''])
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			
			if c_anal != i[8]:
				c_anal = i[8]

				c.setFont("Times-Bold", 8)				
				c.drawString(pos_ini_val[1], pos_inicial, i[8] if i[8] else '')
				c.drawString(pos_ini_val[5], pos_inicial, i[13] if i[13] else '')
				c.drawRightString(pos_ini_val[7]-2, pos_inicial,  "%0.2f" %(abs(i[11] if i[11] else 0.00)) )
				c.drawRightString(pos_ini_val[9]-2, pos_inicial, "%0.2f" %(i[11] if i[11] else 0.00))
				c.drawString(pos_ini_val[9], pos_inicial, i[10] if i[10] else 'PEN')
				c.drawString(pos_ini_val[10], pos_inicial, dic_type[i[15] if i[15] else ''])
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,20,pagina)


				c.setFont("Times-Bold", 10)				
				c.drawString(pos_ini_val[0], pos_inicial, u'Fecha')
				c.drawString(pos_ini_val[1], pos_inicial, u'Ref.')
				c.drawString(pos_ini_val[2], pos_inicial, u'Descripción')
				c.drawString(pos_ini_val[3], pos_inicial, u'Usuario')
				c.drawString(pos_ini_val[4], pos_inicial, u'Diario Analítico')
				c.drawString(pos_ini_val[6], pos_inicial, u'Importe Soles')
				c.drawString(pos_ini_val[7], pos_inicial, u'     Cantidad')
				c.drawString(pos_ini_val[9], pos_inicial, u'Tipo')
				c.drawString(pos_ini_val[10], pos_inicial, u'Estado Analítico')
				c.drawString(pos_ini_val[11], pos_inicial, u'Cuenta General')
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)

			c.setFont("Times-Roman", 8)				
			c.drawString(pos_ini_val[0], pos_inicial, self.particionar_text( i[0] if i[0] else '' , valores[0]-5) )
			c.drawString(pos_ini_val[1], pos_inicial, self.particionar_text( i[1][:10] if i[1] else '' , 20) )
			c.drawString(pos_ini_val[2], pos_inicial, self.particionar_text( i[2] if i[2] else '' , valores[2]-5) )
			c.drawString(pos_ini_val[3], pos_inicial, self.particionar_text( i[3] if i[3] else '' , valores[3]-5) )
			c.drawString(pos_ini_val[4], pos_inicial, self.particionar_text( i[4] if i[4] else '' , valores[4]-5) )
			c.drawRightString(pos_ini_val[7]-2, pos_inicial, "%0.2f" %(i[5] if i[5] else 0) )
			c.drawRightString(pos_ini_val[8]-2, pos_inicial, str( i[6] if i[6] else 0) )
			c.drawString(pos_ini_val[9], pos_inicial, self.particionar_text( i[10] if i[10] else 'PEN' , valores[9]-5) )
			c.drawString(pos_ini_val[10], pos_inicial, self.particionar_text( i[8] if i[8] else '' , valores[10]-5) )
			c.drawString(pos_ini_val[11], pos_inicial, self.particionar_text( i[9] if i[9] else '' , valores[11]-5) )

			pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		c.save()

	@api.multi
	def particionar_text(self,c,f):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Times-Roman',8,f)
			if len(lines)>1:
				return tet[:-1]
		return tet
	
	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-25
		else:
			return pagina,posactual-valor
	@api.multi
	def verify_space(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual-valor <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 8)
			#c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-25
		else:
			return pagina,posactual



