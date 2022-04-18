# -*- coding: utf-8 -*-
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
from cgi import escape
import base64

class account_balance_general(models.Model):
	_name='account.balance.general'
	_inherit = 'account.balance.general'
	
	saldoc = fields.Float('Saldo C', digits=(12,2) )



class account_balance_general_wizard(osv.TransientModel):
	_name='account.balance.general.wizard'
	_inherit = 'account.balance.general.wizard'

	check_comparative = fields.Boolean('Mostrar Comparativo')
	periodo_ini_c = fields.Many2one('account.period','Periodo Inicio')
	periodo_fin_c = fields.Many2one('account.period','Periodo Fin')
	fiscalyear_c_id = fields.Many2one('account.fiscalyear','Año Fiscal')

	type_show =  fields.Selection([('pantalla','Pantalla'),('pdf','Pdf'),('excel','Excel')], 'Mostrar en', required=True)
	save_page_states= []


	@api.onchange('fiscalyear_c_id')
	def onchange_fiscalyear_c(self):
		if self.fiscalyear_c_id:
			return {'domain':{'periodo_ini_c':[('fiscalyear_id','=',self.fiscalyear_c_id.id )], 'periodo_fin_c':[('fiscalyear_id','=',self.fiscalyear_c_id.id )]}}
		else:
			return {'domain':{'periodo_ini_c':[], 'periodo_fin_c':[]}}


	@api.onchange('periodo_ini_c')
	def _change_periodo_ini_c(self):
		if self.periodo_ini_c:
			self.periodo_fin_c= self.periodo_ini_c


	@api.multi
	def do_rebuild(self):
		self.save_page_states= []
		flag = 'false'
		if self.currency_id: 
			if self.currency_id.name == 'PEN':
				pass
			elif self.currency_id.name == 'USD':
				flag = 'true'
			else:
				raise osv.except_osv('Alerta','No se ha configurado ese tipo de moneda.')

		self.env.cr.execute(""" 
			DROP VIEW IF EXISTS account_balance_general;
			create or replace view account_balance_general as(
					select row_number() OVER () AS id,* from ( select *,0 as saldoc from get_balance_general(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.name+"""') ,periodo_num('""" +self.periodo_fin.name +"""' )) ) AS T
			)
			""")		

		self.env.cr.execute(""" 
			select * from account_balance_general;
			""")

		t = self.env.cr.fetchall()
		
		#if len(t)==0:
		#	raise osv.except_osv('Alerta','No contiene datos en esos periodos.')

		if self.type_show == "pantalla":

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			
			return {
				'context': {'tree_view_ref':'account_state_financial_it.view_account_balance_general_tree'},
				'name': 'Situación Financiera',
				'type': 'ir.actions.act_window',
				'res_model': 'account.balance.general',
				'view_mode': 'tree',
				'view_type': 'form',
			}

		if self.type_show == 'pdf':
			self.reporteador()
			
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'Balance General.pdf',
				'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
			}
			sfs_id = self.env['export.file.save'].create(vals)
			result = {}
			view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}


		if self.type_show == 'excel':

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

			workbook = Workbook(direccion +'Reporte_Balance_general.xlsx')
			worksheet = workbook.add_worksheet(u"Balance General")
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
			numberdos = workbook.add_format({'num_format':'#,##0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)


			numbertresbold = workbook.add_format({'num_format':'0.000','bold':True})
			numberdosbold = workbook.add_format({'num_format':'#,##0.00','bold':True})
			numberdosbold.set_border(style=1)
			numbertresbold.set_border(style=1)	

			numberdoscon = workbook.add_format({'num_format':'#,##0.00'})

			boldtotal = workbook.add_format({'bold': True})
			boldtotal.set_align('right')
			boldtotal.set_align('vright')

			merge_format = workbook.add_format({
												'bold': 1,
												'border': 1,
												'align': 'center',
												'valign': 'vcenter',
												})	
			merge_format.set_bg_color('#DCE6F1')
			merge_format.set_text_wrap()
			merge_format.set_font_size(9)


			worksheet.write(1,2, self.env["res.company"].search([])[0].name.upper(), bold)
			worksheet.write(2,2, u"ESTADO DE SITUACIÓN FINANCIERA", bold)
			worksheet.write(3,2, u"AL "+ str(self.periodo_fin.date_stop), bold)
			worksheet.write(4,2, u"(Expresado en Nuevos Soles)", bold)
		

			colum = {
				1: "Enero",
				2: "Febrero",
				3: "Marzo",
				4: "Abril",
				5: "Mayo",
				6: "Junio",
				7: "Julio",
				8: "Agosto",
				9: "Septiembre",
				10: "Octubre",
				11: "Noviembre",
				12: "Diciembre",
			}


			###  B1
			self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
				where grupo = 'B1'
				group by name ,grupo,orden
				order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			
			worksheet.write(6,1, 'ACTIVO' , bold)
			#worksheet.write(6,2, self.fiscalyear_id.name , bold)

			worksheet.write(7,1, 'ACTIVO CORRIENTE' , bold)

			x=9
			for i in listobjetosB1:

				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[2], numberdos)
				x += 1

			x += 1

			if len(listobjetosB1)>0:
				worksheet.write(x,1, 'TOTAL ACTIVO CORRIENTE' , bold)

				self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B1' """)
				totalB1 = self.env.cr.fetchall()[0]
				
				worksheet.write(x,2, totalB1[0], numberdosbold)
				x+=1

			else:
				worksheet.write(x,1, 'TOTAL ACTIVO CORRIENTE' , bold)

				worksheet.write(x,2, 0, numberdosbold)
				x+=1


			# segunda parte B2
			x += 1

			self.env.cr.execute(""" select name as code,'' as concept, sum(saldo) from account_balance_general
				where grupo = 'B2'
				group by name,grupo,orden
				order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,1, 'ACTIVO NO CORRIENTE' , bold)

			for i in listobjetosB1:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[2], numberdos)
				x += 1

			data_inicial2 = 0

			if len(listobjetosB1)>0:
				worksheet.write(x,1, 'TOTAL ACTIVO NO CORRIENTE' , bold)

				self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B2' """)
				totalB1 = self.env.cr.fetchall()[0]

				worksheet.write(x,2, totalB1[0], numberdosbold)	
				data_inicial2 = totalB1[0]
				x+=1

			else:

				worksheet.write(x,1, 'TOTAL ACTIVO NO CORRIENTE' , bold)
				
				worksheet.write(x,2, 0, numberdosbold)			
				x+=1

			pos_inicial2 = x+1

			###  B3 AQUI ES EL LADO DERECHO

			x=6
			self.env.cr.execute(""" select name as code,'' as concept, sum(saldo) from account_balance_general
	where grupo = 'B3'
	group by name,grupo,orden
	order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,5, 'PASIVO Y PATRIMONIO' , bold)
			#worksheet.write(x,6, self.fiscalyear_id.name + '(' + self.periodo_ini.code[:2] +' - ' + self.periodo_fin.code[:2] + ')' , bold)
			
			x+=2


			worksheet.write(x,5, 'PASIVO CORRIENTE' , bold)
			x+=1

			for i in listobjetosB1:

				worksheet.write(x,5, i[0], normal)
				worksheet.write(x,6, i[2], numberdos)
				x+=1


			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PASIVO CORRIENTE' , bold)
								
				self.env.cr.execute(""" select  sum(saldo) from account_balance_general where grupo = 'B3' """)
				totalB1 = self.env.cr.fetchall()[0]
				worksheet.write(x,6, totalB1[0], numberdosbold)
				x+=1

			else:

				worksheet.write(x,5, 'TOTAL PASIVO CORRIENTE' , bold)
								
				worksheet.write(x,6, 0, numberdosbold)
				x+=1

			x+= 1

			
			###  B4
			self.env.cr.execute(""" select name as code,'' as concept, sum(saldo) from account_balance_general
	where grupo = 'B4'
	group by name,grupo,orden
	order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()
			
			worksheet.write(x,5, 'PASIVO NO CORRIENTE' , bold)
			x+=1

			for i in listobjetosB1:
				worksheet.write(x,5, i[0], normal)
				worksheet.write(x,6, i[2], numberdos)
				x+=1

		
			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PASIVO NO CORRIENTE' , bold)
			
				self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B4' """)
				totalB1 = self.env.cr.fetchall()[0]

				worksheet.write(x,6, totalB1[0], numberdosbold)
				x+=1

			else:
				
				worksheet.write(x,5, 'TOTAL PASIVO NO CORRIENTE' , bold)
				worksheet.write(x,6, 0, numberdosbold)
				x+=1


			x+= 1




			###  B5
			self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
	where grupo = 'B5'
	group by name,grupo,orden
	order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,5, 'PATRIMONIO' , bold)
			
			for i in listobjetosB1:
				worksheet.write(x,5, i[0] , bold)
				worksheet.write(x,6, i[2], numberdos)
				x+=1


			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PATRIMONIO' , bold)
				
				self.env.cr.execute(""" select  sum(saldo) from account_balance_general where grupo = 'B5' """)
				totalB1 = self.env.cr.fetchall()[0]
				
				worksheet.write(x,6, totalB1[0], numberdosbold)
				x+=1

			else:

				worksheet.write(x,5, 'TOTAL PATRIMONIO' , bold)
								
				worksheet.write(x,6, 0, numberdosbold)
				x+=1

			x+= 1


			worksheet.write(x,5, 'RESULTADO DEL PERIODO' , bold)

			self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
	where grupo = 'B1' or grupo = 'B2' """)
			tmp_consultaB1B2 = self.env.cr.fetchall()
			totalA12 = tmp_consultaB1B2[0][0]
			self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
	where grupo = 'B3' or grupo = 'B4' or grupo = 'B5' """)
			tmp_consultaB345 = self.env.cr.fetchall()
			totalA345 = tmp_consultaB345[0][0]

			worksheet.write(x,6, totalA12- totalA345, numberdos)
		
			x+=2
			#### AQUI VAN LOS FINALES FINALES
			if x > pos_inicial2:
				pass
			else:
				x = pos_inicial2

			worksheet.write(x,5, 'TOTAL PASIVO Y PATRIMONIO' , bold)
			
			worksheet.write(x,1, 'TOTAL ACTIVO' , bold)


			self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
	where grupo = 'B1' or grupo = 'B2' """)
			tmp_totalA12 = self.env.cr.fetchall()
			
			totalA12 = tmp_totalA12[0][0]

			worksheet.write(x,2, totalA12 , numberdosbold)


			worksheet.write(x,6, totalA12 , numberdosbold)

			worksheet.set_column('B:B',57)
			worksheet.set_column('C:C',24)
			worksheet.set_column('F:F',57)
			worksheet.set_column('G:G',24)

			workbook.close()
			
			f = open(direccion + 'Reporte_Balance_general.xlsx', 'rb')
			
			vals = {
				'output_name': 'BalanceGeneral.xlsx',
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
	def do_rebuild_c(self):
		self.save_page_states= []
		flag = 'false'
		if self.currency_id: 
			if self.currency_id.name == 'PEN':
				pass
			elif self.currency_id.name == 'USD':
				flag = 'true'
			else:
				raise osv.except_osv('Alerta','No se ha configurado ese tipo de moneda.')

		self.env.cr.execute(""" 
			DROP VIEW IF EXISTS account_balance_general;
			create or replace view account_balance_general as(
					select row_number() OVER () AS id,* from ( 
						select 
coalesce(A1.name, A2.name) as name, coalesce(A1.grupo,A2.grupo) as grupo, coalesce(A1.saldo,0) as saldo, coalesce(A1.orden,A2.orden)as orden , coalesce(A2.saldo,0) as saldoc
from get_balance_general(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.name+"""') ,periodo_num('""" +self.periodo_fin.name +"""' )) as A1
full join  get_balance_general(""" + flag+ """ ,periodo_num('""" + self.periodo_ini_c.name+"""') ,periodo_num('""" +self.periodo_fin_c.name +"""' )) AS A2 on (A1.name= A2.name and A1.grupo = A2.grupo)
					) AS T
			)
			""")

		self.env.cr.execute(""" 
			select * from account_balance_general;
			""")

		t = self.env.cr.fetchall()
		
		#if len(t)==0:
		#	raise osv.except_osv('Alerta','No contiene datos en esos periodos.')


		if self.type_show == "pantalla":

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			
			return {
				'context': {'tree_view_ref':'view_account_balance_general_c_tree'},
				'name': 'Situación Financiera',
				'type': 'ir.actions.act_window',
				'res_model': 'account.balance.general',
				'view_mode': 'tree',
				'view_type': 'form',
			}
		if self.type_show == 'pdf':
			self.reporteador_C()
			
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'Balance General.pdf',
				'output_file': open(direccion +"a.pdf", "rb").read().encode("base64"),	
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

		if self.type_show == 'excel':

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

			workbook = Workbook(direccion +'Reporte_Balance_general.xlsx')
			worksheet = workbook.add_worksheet(u"Balance General")
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
			numberdos = workbook.add_format({'num_format':'#,##0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)

			numbertresbold = workbook.add_format({'num_format':'0.000','bold': True})
			numberdosbold = workbook.add_format({'num_format':'#,##0.00','bold': True})
			numberdosbold.set_border(style=1)
			numbertresbold.set_border(style=1)

			numberdoscon = workbook.add_format({'num_format':'#,##0.00'})

			boldtotal = workbook.add_format({'bold': True})
			boldtotal.set_align('right')
			boldtotal.set_align('vright')

			merge_format = workbook.add_format({
												'bold': 1,
												'border': 1,
												'align': 'center',
												'valign': 'vcenter',
												})	
			merge_format.set_bg_color('#DCE6F1')
			merge_format.set_text_wrap()
			merge_format.set_font_size(9)


			worksheet.write(1,2, self.env["res.company"].search([])[0].name.upper(), bold)
			worksheet.write(2,2, u"ESTADO DE SITUACIÓN FINANCIERA", bold)
			worksheet.write(3,2, u"AL "+ str(self.periodo_fin.date_stop), bold)
			worksheet.write(4,2, u"(Expresado en Nuevos Soles)", bold)
		

			colum = {
				1: "Enero",
				2: "Febrero",
				3: "Marzo",
				4: "Abril",
				5: "Mayo",
				6: "Junio",
				7: "Julio",
				8: "Agosto",
				9: "Septiembre",
				10: "Octubre",
				11: "Noviembre",
				12: "Diciembre",
			}


			###  B1
			self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc) ,sum(saldo) from account_balance_general
				where grupo = 'B1'
				group by name ,grupo,orden
				order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			
			worksheet.write(6,1, 'ACTIVO' , bold)
			worksheet.write(6,2, self.fiscalyear_c_id.name , bold)
			worksheet.write(6,3, self.fiscalyear_id.name , bold)

			worksheet.write(7,1, 'ACTIVO CORRIENTE' , bold)

			x=9
			for i in listobjetosB1:

				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[2], numberdos)
				worksheet.write(x,3, i[3], numberdos)
				x += 1

			if len(listobjetosB1)>0:
				worksheet.write(x,1, 'TOTAL ACTIVO CORRIENTE' , bold)

				self.env.cr.execute(""" select sum(saldoc),sum(saldo) from account_balance_general where grupo = 'B1' """)
				totalB1 = self.env.cr.fetchall()[0]
				
				worksheet.write(x,2, totalB1[0], numberdosbold)				
				worksheet.write(x,3, totalB1[1], numberdosbold)
				x+=1

			else:
				worksheet.write(x,1, 'TOTAL ACTIVO CORRIENTE' , bold)

				worksheet.write(x,2, 0, numberdosbold)				
				worksheet.write(x,3, 0, numberdosbold)
				x+=1

			x += 1


			# segunda parte B2

			self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc), sum(saldo) from account_balance_general
				where grupo = 'B2'
				group by name,grupo,orden
				order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,1, 'ACTIVO NO CORRIENTE' , bold)

			for i in listobjetosB1:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[2], numberdos)
				worksheet.write(x,3, i[3], numberdos)
				x += 1

			if len(listobjetosB1)>0:
				worksheet.write(x,1, 'TOTAL ACTIVO NO CORRIENTE' , bold)

				self.env.cr.execute(""" select sum(saldoc),sum(saldo) from account_balance_general where grupo = 'B2' """)
				totalB1 = self.env.cr.fetchall()[0]

				worksheet.write(x,2, totalB1[0], numberdosbold)				
				worksheet.write(x,3, totalB1[1], numberdosbold)
				x+=1

			else:

				worksheet.write(x,1, 'TOTAL ACTIVO NO CORRIENTE' , bold)
				
				worksheet.write(x,2, 0, numberdosbold)				
				worksheet.write(x,3, 0, numberdosbold)
				x+=1

			x += 1

			pos_inicial2 = x + 1

			###  B3 AQUI ES EL LADO DERECHO

			x=6
			self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc), sum(saldo) from account_balance_general
	where grupo = 'B3'
	group by name,grupo,orden
	order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,5, 'PASIVO Y PATRIMONIO' , bold)
			worksheet.write(x,7, self.fiscalyear_id.name  , bold)
			worksheet.write(x,6, self.fiscalyear_c_id.name  , bold)

			x+=2

			worksheet.write(x,5, 'PASIVO CORRIENTE' , bold)
			x+=1

			for i in listobjetosB1:

				worksheet.write(x,5, i[0], normal)
				worksheet.write(x,6, i[2], numberdos)
				worksheet.write(x,7, i[3], numberdos)
				x+=1


			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PASIVO CORRIENTE' , bold)
								
				self.env.cr.execute(""" select sum(saldoc), sum(saldo) from account_balance_general where grupo = 'B3' """)
				totalB1 = self.env.cr.fetchall()[0]
				worksheet.write(x,6, totalB1[0], numberdosbold)
				worksheet.write(x,7, totalB1[1], numberdosbold)
				x+=1

			else:

				worksheet.write(x,5, 'TOTAL PASIVO CORRIENTE' , bold)
								
				worksheet.write(x,6, 0, numberdosbold)
				worksheet.write(x,7, 0, numberdosbold)
				x+=1

			x+= 1

			
			###  B4
			self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc), sum(saldo) from account_balance_general
	where grupo = 'B4'
	group by name,grupo,orden
	order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()
			
			worksheet.write(x,5, 'PASIVO NO CORRIENTE' , bold)
			x+=1

			for i in listobjetosB1:
				worksheet.write(x,5, i[0], normal)
				worksheet.write(x,6, i[2], numberdos)
				worksheet.write(x,7, i[3], numberdos)
				x+=1

		
			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PASIVO NO CORRIENTE' , bold)
			
				self.env.cr.execute(""" select sum(saldoc),sum(saldo) from account_balance_general where grupo = 'B4' """)
				totalB1 = self.env.cr.fetchall()[0]

				worksheet.write(x,6, totalB1[0], numberdosbold)
				worksheet.write(x,7, totalB1[1], numberdosbold)
				x+=1

			else:
				
				worksheet.write(x,5, 'TOTAL PASIVO NO CORRIENTE' , bold)
				worksheet.write(x,6, 0, numberdosbold)
				worksheet.write(x,7, 0, numberdosbold)
				x+=1

			x += 1



			###  B5
			self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc),sum(saldo) from account_balance_general
	where grupo = 'B5'
	group by name,grupo,orden
	order by orden,name """)
			listobjetosB1 =  self.env.cr.fetchall()

			worksheet.write(x,5, 'PATRIMONIO' , bold)
			
			for i in listobjetosB1:
				worksheet.write(x,5, i[0] , bold)
				worksheet.write(x,6, i[2], numberdos)
				worksheet.write(x,7, i[3], numberdos)
				x+=1


			if len(listobjetosB1)>0:
				worksheet.write(x,5, 'TOTAL PATRIMONIO' , bold)
				
				self.env.cr.execute(""" select sum(saldoc), sum(saldo) from account_balance_general where grupo = 'B5' """)
				totalB1 = self.env.cr.fetchall()[0]
				
				worksheet.write(x,6, totalB1[0], numberdosbold)
				worksheet.write(x,7, totalB1[1], numberdosbold)
				x+=1

			else:

				worksheet.write(x,5, 'TOTAL PATRIMONIO' , bold)
								
				worksheet.write(x,6, 0, numberdosbold)
				worksheet.write(x,7, 0, numberdosbold)
				x+=1

			x+= 1

			worksheet.write(x,5, 'RESULTADO DEL PERIODO' , bold)

			self.env.cr.execute(""" select coalesce(sum(saldoc),0),coalesce(sum(saldo),0) from account_balance_general
	where grupo = 'B1' or grupo = 'B2' """)
			tmp_consultaB1B2 = self.env.cr.fetchall()
			totalA12 = tmp_consultaB1B2[0][0]
			totalA12N = tmp_consultaB1B2[0][1]
			self.env.cr.execute(""" select coalesce(sum(saldoc),0),coalesce(sum(saldo),0) from account_balance_general
	where grupo = 'B3' or grupo = 'B4' or grupo = 'B5' """)
			tmp_consultaB345 = self.env.cr.fetchall()
			totalA345 = tmp_consultaB345[0][0]
			totalA345N = tmp_consultaB345[0][1]

			worksheet.write(x,6, totalA12- totalA345, numberdosbold)
			worksheet.write(x,7, totalA12N- totalA345N, numberdosbold)
		
			x+=2
			#### AQUI VAN LOS FINALES FINALES

			if x > pos_inicial2:
				pass
			else:
				x = pos_inicial2

			worksheet.write(x,5, 'TOTAL PASIVO Y PATRIMONIO' , bold)
			
			worksheet.write(x,1, 'TOTAL ACTIVO' , bold)


			self.env.cr.execute(""" select coalesce(sum(saldoc),0),coalesce(sum(saldo),0) from account_balance_general
	where grupo = 'B1' or grupo = 'B2' """)
			tmp_totalA12 = self.env.cr.fetchall()
			
			totalA12 = tmp_totalA12[0][0]
			totalA12N = tmp_totalA12[0][1]

			worksheet.write(x,2, totalA12 , numberdosbold)
			worksheet.write(x,3, totalA12N , numberdosbold)


			worksheet.write(x,6, totalA12 , numberdosbold)
			worksheet.write(x,7, totalA12N , numberdosbold)


			worksheet.set_column('B:B',57)
			worksheet.set_column('C:C',24)
			worksheet.set_column('D:D',24)
			worksheet.set_column('F:F',57)
			worksheet.set_column('G:G',24)
			worksheet.set_column('H:H',24)

			workbook.close()
			
			f = open(direccion + 'Reporte_Balance_general.xlsx', 'rb')
			
			vals = {
				'output_name': 'BalanceGeneral.xlsx',
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
	def cabezera(self,c,wReal,hReal):

		c.setFont("Times-Bold", 10)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "ESTADO DE SITUACIÓN FINANCIERA")

		if  self.check_comparative:
			c.drawCentredString((wReal/2)+20,hReal-24, "AL "+ str(self.periodo_fin_c.date_stop))
		else:
			c.drawCentredString((wReal/2)+20,hReal-24, "AL "+ str(self.periodo_fin.date_stop))
		c.drawCentredString((wReal/2)+20,hReal-36, "(Expresado en Nuevos Soles)")

		

	@api.multi
	def reporteador_C(self):

		import sys
		nivel_left_page = 1
		nivel_left_fila = 0
		
		nivel_right_page = 1
		nivel_right_fila = 0
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		height ,width = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas(direccion + "a.pdf", pagesize=(width,height))
		self.save_page_states.append(dict(c.__dict__))
		inicio = 0
		pos_inicialL = hReal-60
		pos_inicialR = hReal-60

		pagina = 1
		textPos = 0
		
		tamanios = {}
		voucherTamanio = None
		contTamanio = 0

		self.cabezera(c,wReal,hReal)
		c.setFont("Times-Bold", 8)
		c.drawCentredString(300,25,'Pág. ' + str(pagina))

		###  B1
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc) ,sum(saldo) from account_balance_general
			where grupo = 'B1'
			group by name ,grupo,orden
			order by orden,name """)
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString( 15 , pos_inicialL, "ACTIVO")
		c.drawString( (wReal/2)-140 , pos_inicialL, self.fiscalyear_id.name )
		c.drawString( (wReal/2)-75 , pos_inicialL, self.fiscalyear_c_id.name )

		c.line(15,pos_inicialL-1,52,pos_inicialL-1)
		c.drawString(15,pos_inicialL - 24,"ACTIVO CORRIENTE")

		pos_inicialL = pos_inicialL - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(18,pos_inicialL,i[0] )
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %i[2])
			c.drawRightString( (wReal/2)-85 ,pos_inicialL,"%0.2f" %i[3])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO CORRIENTE")

			self.env.cr.execute(""" select sum(saldoc),sum(saldo) from account_balance_general where grupo = 'B1' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %totalB1[0])
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)

			c.drawRightString( (wReal/2)-85 ,pos_inicialL,"%0.2f" %totalB1[1])
			c.line((wReal/2)-140, pos_inicialL-2, (wReal/2)-85 ,pos_inicialL-2)
			c.line((wReal/2)-140, pos_inicialL-4, (wReal/2)-85 ,pos_inicialL-4)
			c.line((wReal/2)-140, pos_inicialL+9, (wReal/2)-85 ,pos_inicialL+9)

		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO CORRIENTE")
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %(0.0) )
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)

			c.drawRightString( (wReal/2)-85 ,pos_inicialL,"%0.2f" %(0.0) )
			c.line((wReal/2)-140, pos_inicialL-2, (wReal/2)-85 ,pos_inicialL-2)
			c.line((wReal/2)-140, pos_inicialL-4, (wReal/2)-85 ,pos_inicialL-4)
			c.line((wReal/2)-140, pos_inicialL+9, (wReal/2)-85 ,pos_inicialL+9)


		self.guardar_state(c)


		nivel_left_page = c._pageNumber
		nivel_left_fila = pos_inicialL
		
		
		self.cargar_pagina(c,1)
		
		###  B3
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc), sum(saldo) from account_balance_general
where grupo = 'B3'
group by name,grupo,orden
order by orden,name """)
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString( (wReal/2)+20 , pos_inicialR, "PASIVO Y PATRIMONIO")

		c.drawString( (wReal)-140 , pos_inicialR, self.fiscalyear_id.name  )
		c.drawString( (wReal)-75 , pos_inicialR, self.fiscalyear_c_id.name  )


		c.line( (wReal/2)+20,pos_inicialR-1,(wReal/2)+120,pos_inicialR-1)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PASIVO CORRIENTE")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])
			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %i[3])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO CORRIENTE")

			self.env.cr.execute(""" select sum(saldoc), sum(saldo) from account_balance_general where grupo = 'B3' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)


			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %totalB1[1])
			c.line((wReal)-140, pos_inicialR-2, (wReal)-85 ,pos_inicialR-2)
			c.line((wReal)-140, pos_inicialR-4, (wReal)-85 ,pos_inicialR-4)
			c.line((wReal)-140, pos_inicialR+9, (wReal)-85 ,pos_inicialR+9)

		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO CORRIENTE")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)


			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-140, pos_inicialR-2, (wReal)-85 ,pos_inicialR-2)
			c.line((wReal)-140, pos_inicialR-4, (wReal)-85 ,pos_inicialR-4)
			c.line((wReal)-140, pos_inicialR+9, (wReal)-85 ,pos_inicialR+9)


		self.guardar_state(c)


		nivel_right_page = c._pageNumber
		nivel_right_fila = pos_inicialR


		if nivel_left_page > nivel_right_page:
			pos_inicialL = nivel_left_fila
			pos_inicialR = nivel_left_fila
			c.__dict__.update(self.save_page_states[nivel_left_page-1])
		elif nivel_left_page < nivel_right_page:

			pos_inicialL = nivel_right_fila
			pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		else:
			if nivel_left_fila < nivel_right_fila:
				pos_inicialL = nivel_left_fila
				pos_inicialR = nivel_left_fila
			else:
				pos_inicialL = nivel_right_fila
				pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		# segunda parte B2

		self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc), sum(saldo) from account_balance_general
			where grupo = 'B2'
			group by name,grupo,orden
			order by orden,name """)
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString(15,pos_inicialL - 24,"ACTIVO NO CORRIENTE")

		pos_inicialL = pos_inicialL - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(18,pos_inicialL,i[0] )
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %i[2])
			c.drawRightString( (wReal/2)-85 ,pos_inicialL,"%0.2f" %i[3])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO NO CORRIENTE")

			self.env.cr.execute(""" select sum(saldoc),sum(saldo) from account_balance_general where grupo = 'B2' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %totalB1[0])
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)


			c.drawRightString( (wReal/2)-85 ,pos_inicialL,"%0.2f" %totalB1[1])
			c.line((wReal/2)-140, pos_inicialL-2, (wReal/2)-85 ,pos_inicialL-2)
			c.line((wReal/2)-140, pos_inicialL-4, (wReal/2)-85 ,pos_inicialL-4)
			c.line((wReal/2)-140, pos_inicialL+9, (wReal/2)-85 ,pos_inicialL+9)


		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO NO CORRIENTE")
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %(0.0) )
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)

			c.drawRightString( (wReal/2)-85 ,pos_inicialL,"%0.2f" %(0.0) )
			c.line((wReal/2)-140, pos_inicialL-2, (wReal/2)-85 ,pos_inicialL-2)
			c.line((wReal/2)-140, pos_inicialL-4, (wReal/2)-85 ,pos_inicialL-4)
			c.line((wReal/2)-140, pos_inicialL+9, (wReal/2)-85 ,pos_inicialL+9)

		self.guardar_state(c)

		if nivel_left_page > nivel_right_page:
			pos_inicialL = nivel_left_fila
			pos_inicialR = nivel_left_fila
			c.__dict__.update(self.save_page_states[nivel_left_page-1])
		elif nivel_left_page < nivel_right_page:

			pos_inicialL = nivel_right_fila
			pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		else:
			if nivel_left_fila < nivel_right_fila:
				pos_inicialL = nivel_left_fila
				pos_inicialR = nivel_left_fila
			else:
				pos_inicialL = nivel_right_fila
				pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		nivel_left_page = c._pageNumber
		nivel_left_fila = pos_inicialL
		###  B4
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc), sum(saldo) from account_balance_general
where grupo = 'B4'
group by name,grupo,orden
order by orden,name """)
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PASIVO NO CORRIENTE")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])
			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %i[3])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO NO CORRIENTE")

			self.env.cr.execute(""" select sum(saldoc),sum(saldo) from account_balance_general where grupo = 'B4' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %totalB1[1])
			c.line((wReal)-140, pos_inicialR-2, (wReal)-85 ,pos_inicialR-2)
			c.line((wReal)-140, pos_inicialR-4, (wReal)-85 ,pos_inicialR-4)
			c.line((wReal)-140, pos_inicialR+9, (wReal)-85 ,pos_inicialR+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO NO CORRIENTE")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-140, pos_inicialR-2, (wReal)-85 ,pos_inicialR-2)
			c.line((wReal)-140, pos_inicialR-4, (wReal)-85 ,pos_inicialR-4)
			c.line((wReal)-140, pos_inicialR+9, (wReal)-85 ,pos_inicialR+9)

		self.guardar_state(c)



		###  B5
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldoc),sum(saldo) from account_balance_general
where grupo = 'B5'
group by name,grupo,orden
order by orden,name """)
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PATRIMONIO")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])
			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %i[3])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PATRIMONIO")

			self.env.cr.execute(""" select sum(saldoc), sum(saldo) from account_balance_general where grupo = 'B5' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %totalB1[1])
			c.line((wReal)-140, pos_inicialR-2, (wReal)-85 ,pos_inicialR-2)
			c.line((wReal)-140, pos_inicialR-4, (wReal)-85 ,pos_inicialR-4)
			c.line((wReal)-140, pos_inicialR+9, (wReal)-85 ,pos_inicialR+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PATRIMONIO")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)


			c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-140, pos_inicialR-2, (wReal)-85 ,pos_inicialR-2)
			c.line((wReal)-140, pos_inicialR-4, (wReal)-85 ,pos_inicialR-4)
			c.line((wReal)-140, pos_inicialR+9, (wReal)-85 ,pos_inicialR+9)

		c.setFont("Times-Roman", 8)
		pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,24,pagina)
		c.drawString((wReal/2)+20,pos_inicialR,"RESULTADO DEL PERIODO")
		self.env.cr.execute(""" select coalesce(sum(saldoc),0),coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B1' or grupo = 'B2' """)
		tmp_consultaB1B2 = self.env.cr.fetchall()
		totalA12 = tmp_consultaB1B2[0][0]
		totalA12N = tmp_consultaB1B2[0][1]
		self.env.cr.execute(""" select coalesce(sum(saldoc),0),coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B3' or grupo = 'B4' or grupo = 'B5' """)
		tmp_consultaB345 = self.env.cr.fetchall()
		totalA345 = tmp_consultaB345[0][0]
		totalA345N = tmp_consultaB345[0][1]

		c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(totalA12- totalA345) )
		c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %(totalA12N- totalA345N) )


		self.guardar_state(c)


		nivel_right_page = c._pageNumber
		nivel_right_fila = pos_inicialR


		if nivel_left_page > nivel_right_page:
			pos_inicialL = nivel_left_fila
			pos_inicialR = nivel_left_fila
			c.__dict__.update(self.save_page_states[nivel_left_page-1])
		elif nivel_left_page < nivel_right_page:

			pos_inicialL = nivel_right_fila
			pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])

		else:
			if nivel_left_fila < nivel_right_fila:
				pos_inicialL = nivel_left_fila
				pos_inicialR = nivel_left_fila
			else:
				pos_inicialL = nivel_right_fila
				pos_inicialR = nivel_right_fila
			c.__dict__.update(self.save_page_states[nivel_right_page-1])


		c.setFont("Times-Bold", 8)
		pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
		c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO Y PATRIMONIO")
		c.line((wReal/2)+20,pos_inicialR-1,(wReal/2)+145,pos_inicialR-1)

		c.drawString(15,pos_inicialR,"TOTAL ACTIVO")
		c.line(15,pos_inicialR-1,80,pos_inicialR-1)

		self.env.cr.execute(""" select coalesce(sum(saldoc),0),coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B1' or grupo = 'B2' """)
		tmp_totalA12 = self.env.cr.fetchall()
		totalA12 = tmp_totalA12[0][0]
		totalA12N = tmp_totalA12[0][1]

		c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalA12)
		c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
		c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
		c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

		c.drawRightString( (wReal)-85 ,pos_inicialR,"%0.2f" %totalA12N)
		c.line((wReal)-140, pos_inicialR-2, (wReal)-85 ,pos_inicialR-2)
		c.line((wReal)-140, pos_inicialR-4, (wReal)-85 ,pos_inicialR-4)
		c.line((wReal)-140, pos_inicialR+9, (wReal)-85 ,pos_inicialR+9)


		c.drawRightString( (wReal/2)-20 ,pos_inicialR,"%0.2f" %totalA12)
		c.line((wReal/2)-75, pos_inicialR-2, (wReal/2)-20 ,pos_inicialR-2)
		c.line((wReal/2)-75, pos_inicialR-4, (wReal/2)-20 ,pos_inicialR-4)
		c.line((wReal/2)-75, pos_inicialR+9, (wReal/2)-20 ,pos_inicialR+9)

		c.drawRightString( (wReal/2)-85 ,pos_inicialR,"%0.2f" %totalA12N)
		c.line((wReal/2)-140, pos_inicialR-2, (wReal/2)-85 ,pos_inicialR-2)
		c.line((wReal/2)-140, pos_inicialR-4, (wReal/2)-85 ,pos_inicialR-4)
		c.line((wReal/2)-140, pos_inicialR+9, (wReal/2)-85 ,pos_inicialR+9)

		self.finalizar(c)

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
	def cargar_pagina(self,c,pagina):
		c.__dict__.update(self.save_page_states[pagina-1])

	@api.multi
	def finalizar(self,c):
		for state in self.save_page_states:
			c.__dict__.update(state)
			canvas.Canvas.showPage(c)
		canvas.Canvas.save(c)

	@api.multi
	def guardar_state(self,c):
		if c._pageNumber > len(self.save_page_states):
			self.save_page_states.append(dict(c.__dict__))
		else:
			self.save_page_states[c._pageNumber-1] = dict(c.__dict__)
		return True

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			if c._pageNumber > len(self.save_page_states):
				self.save_page_states.append(dict(c.__dict__))
			else:
				self.save_page_states[c._pageNumber-1] = dict(c.__dict__)
			c._startPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 8)
			c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-60
		else:
			return pagina,posactual-valor


