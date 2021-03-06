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
class account_state_efective(models.Model):
	_name='account.state.efective'
	_inherit= 'account.state.efective'

	saldoc = fields.Float('Saldo', digits=(12,2))



class account_state_efective_wizard(osv.TransientModel):
	_name='account.state.efective.wizard'
	_inherit='account.state.efective.wizard'


	check_comparative = fields.Boolean('Mostrar Comparativo')
	periodo_si_c = fields.Many2one('account.period','Periodo Saldo Inicial')
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

		flag = 'false'
		if self.currency_id: 
			if self.currency_id.name == 'PEN':
				pass
			elif self.currency_id.name == 'USD':
				flag = 'true'
			else:
				raise osv.except_osv('Alerta','No se ha configurado ese tipo de moneda.')

		self.env.cr.execute(""" 
			DROP VIEW IF EXISTS account_state_efective;
			create or replace view account_state_efective as(
					select row_number() OVER () AS id,* from ( select *,0 as saldoc from get_flujo_efectivo(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.name+"""') ,periodo_num('""" +self.periodo_fin.name +"""' ),periodo_num('""" +self.periodo_si.name +"""' ) ) ) AS T
			)
			""")		

		self.env.cr.execute(""" 
			select * from account_state_efective;
			""")

		t = self.env.cr.fetchall()
		
		#if len(t)==0:
		#	raise osv.except_osv('Alerta','No contiene datos en esos periodos.')

		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']


			return {
				'context': {'tree_view_ref':'account_state_financial_it.view_account_state_efective_tree'},
				'name': 'Flujo Efectivo',
				'type': 'ir.actions.act_window',
				'res_model': 'account.state.efective',
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
				'output_name': 'Flujos de Efectivo.pdf',
				'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
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

			workbook = Workbook(direccion +'Reporte_state_efective.xlsx')
			worksheet = workbook.add_worksheet(u"Estado Efectivo")
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



			boldbordtitle = workbook.add_format({'bold': True})
			boldbordtitle.set_align('center')
			boldbordtitle.set_align('vcenter')
			boldbordtitle.set_text_wrap()
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


			worksheet.write(1,1, self.env["res.company"].search([])[0].name.upper(), boldbordtitle)
			worksheet.write(2,1, u"ESTADO DE FLUJOS DE EFECTIVO", boldbordtitle)
			worksheet.write(3,1, u"AL "+ str(self.periodo_fin.date_stop), boldbordtitle)
			worksheet.write(4,1, u"(Expresado en Nuevos Soles)", boldbordtitle)
		

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




			#### INICIO

			x=6

			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
				where grupo = 'E1'
				group by concept,grupo,orden
				order by orden,concept   """)
			listobjetosF1 =  self.env.cr.fetchall()

			#worksheet.write(x,2, self.fiscalyear_id.name, bold)

			x+=1
			worksheet.write(x,1, u"ACTIVIDADES DE OPERACIÓN", bold)
			x+=1


			sumgrupo1 = None
			for i in listobjetosF1:

				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				x += 1


			worksheet.write(x,1, "Menos:", bold)
			x+=1


			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
				where grupo = 'E2'
				group by concept,grupo,orden
				order by orden,concept   """)
			listobjetosF2 =  self.env.cr.fetchall()

			sumgrupo2 = None
			for i in listobjetosF2:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
				where grupo = 'E2' or grupo='E1' """)
			listtotalF1F2 =  self.env.cr.fetchall()
			x+= 1

			if len(listtotalF1F2) >0:
				worksheet.write(x,1, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				x += 1

			else:
				worksheet.write(x,1, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación", bold)
				worksheet.write(x,2, 0, numberdosbold)
				x += 1

			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
				where grupo = 'E3'
				group by concept,grupo,orden
				order by orden,concept   """)
			listobjetosF1 =  self.env.cr.fetchall()

			x+=1


			worksheet.write(x,1, u"ACTIVIDADES DE INVERSIÓN", bold)
			x+=1
				
			sumgrupo1 = None
			for i in listobjetosF1:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				x += 1

			worksheet.write(x,1, u"Menos:", bold)
			x+=1
			

			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
				where grupo = 'E4'
				group by concept,grupo,orden
				order by orden,concept   """)
			listobjetosF2 =  self.env.cr.fetchall()

			sumgrupo2 = None
			for i in listobjetosF2:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0)   from account_state_efective
				where grupo = 'E3' or grupo='E4' """)
			listtotalF1F2 =  self.env.cr.fetchall()
			x+=1

			if len(listtotalF1F2) >0:

				worksheet.write(x,1, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				x += 1


			else:

				worksheet.write(x,1, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión", bold)
				worksheet.write(x,2, 0, numberdosbold)
				x += 1


			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
				where grupo = 'E5'
				group by concept,grupo,orden
				order by orden,concept  """)
			listobjetosF1 =  self.env.cr.fetchall()

			x+=1


			worksheet.write(x,1, u"ACTIVIDADES DE FINANCIAMIENTO", bold)
			x+=1

			sumgrupo1 = None
			for i in listobjetosF1:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				x += 1

			
			worksheet.write(x,1, u"Menos:", bold)
			x+=1


			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
				where grupo = 'E6'
				group by concept,grupo,orden
				order by orden,concept  """)
			listobjetosF2 =  self.env.cr.fetchall()

			sumgrupo2 = None
			for i in listobjetosF2:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
				where grupo = 'E5' or grupo='E6' """)
			listtotalF1F2 =  self.env.cr.fetchall()

			x+=1

			if len(listtotalF1F2) >0:

				worksheet.write(x,1, u"Aumento(Dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				x += 1

			else:
				worksheet.write(x,1, u"Aumento(Dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento", bold)
				worksheet.write(x,2, 0, numberdosbold)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
				where grupo = 'E5' or grupo='E6' or grupo='E4' or grupo='E3' or grupo='E2' or grupo='E1' """)
			listtotalF1F2 =  self.env.cr.fetchall()

			x+=1

			if len(listtotalF1F2) >0:
				worksheet.write(x,1, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				x += 1

			else:
				worksheet.write(x,1, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO", bold)
				worksheet.write(x,2, 0, numberdosbold)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0)  from account_state_efective
				where grupo = 'E7'""")
			listtotalF1F2 =  self.env.cr.fetchall()

			if len(listtotalF1F2) >0:
				worksheet.write(x,1, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio", normal)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdos)
				x += 1

			else:
				worksheet.write(x,1, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio", normal)
				worksheet.write(x,2, 0, numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0)  from account_state_efective
				where grupo = 'E8'""")
			listtotalF1F2 =  self.env.cr.fetchall()

			if len(listtotalF1F2) >0:
				worksheet.write(x,1, u"Ajuste por diferencia de Cambio", normal)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdos)
				x += 1

			else:

				worksheet.write(x,1, u"Ajuste por diferencia de Cambio", normal)
				worksheet.write(x,2, 0, numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0)  from account_state_efective
				where grupo = 'E5' or grupo='E6' or grupo='E4' or grupo='E3' or grupo='E2' or grupo='E1' or grupo='E7' or grupo='E8' """)
			listtotalF1F2 =  self.env.cr.fetchall()

			x+=1

			if len(listtotalF1F2) >0:

				worksheet.write(x,1, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				x += 1

			else:
				worksheet.write(x,1, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio", bold)
				worksheet.write(x,2, 0, numberdosbold)
				x += 1
				

			worksheet.set_column('B:B',97)
			worksheet.set_column('C:C',24)

			#### FIN

			workbook.close()
			
			f = open(direccion + 'Reporte_state_efective.xlsx', 'rb')
			
			vals = {
				'output_name': 'EstadoEfectivo.xlsx',
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
	def do_rebuild_C(self):

		flag = 'false'
		if self.currency_id: 
			if self.currency_id.name == 'PEN':
				pass
			elif self.currency_id.name == 'USD':
				flag = 'true'
			else:
				raise osv.except_osv('Alerta','No se ha configurado ese tipo de moneda.')

		self.env.cr.execute(""" 
			DROP VIEW IF EXISTS account_state_efective;
			create or replace view account_state_efective as(
					select row_number() OVER () AS id,* from ( 
			select 
			coalesce(A1.grupo,A2.grupo) as grupo,coalesce(A1.periodo,A2.periodo) as periodo,coalesce(A1.code, A2.code) as code, coalesce(A1.concept,A2.concept) as concept, coalesce(A1.saldo,0) as saldo, coalesce(A1.debe,0) as debe, coalesce(A1.haber,0) as haber , coalesce(A1.orden,A2.orden) as orden , coalesce(A2.saldo,0) as saldoc
			from get_flujo_efectivo(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.name+"""') ,periodo_num('""" +self.periodo_fin.name +"""' ),periodo_num('""" +self.periodo_si.name +"""' )) as A1
			full join  get_flujo_efectivo(""" + flag+ """ ,periodo_num('""" + self.periodo_ini_c.name+"""') ,periodo_num('""" +self.periodo_fin_c.name +"""' ),periodo_num('""" +self.periodo_si_c.name +"""' )) AS A2 on (A1.code= A2.code and A1.concept = A2.concept and A1.periodo = A2.periodo)
					) AS T
			)
			""")		

		self.env.cr.execute(""" 
			select * from account_state_efective;
			""")

		t = self.env.cr.fetchall()
		
		#if len(t)==0:
		#	raise osv.except_osv('Alerta','No contiene datos en esos periodos.')
			

		if self.type_show == 'pantalla':
			return {
				'context': {'tree_view_ref':'account_state_financial_compare_it.view_account_state_efective_c_tree'},
				'name': 'Resultado por Función',
				'type': 'ir.actions.act_window',
				'res_model': 'account.state.efective',
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
				'output_name': 'Flujos de Efectivo.pdf',
				'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
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

			workbook = Workbook(direccion +'Reporte_state_efective.xlsx')
			worksheet = workbook.add_worksheet(u"Estado Efectivo")
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
			worksheet.write(2,2, u"ESTADO EFECTIVO", bold)
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


			#### INICIO

			x=6

			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
				where grupo = 'E1'
				group by concept,grupo,orden
				order by orden,concept   """)
			listobjetosF1 =  self.env.cr.fetchall()

			worksheet.write(x,2, self.fiscalyear_id.name, bold)
			worksheet.write(x,3, self.fiscalyear_c_id.name, bold)

			x+=1
			worksheet.write(x,1, u"ACTIVIDADES DE OPERACIÓN", bold)
			x+=1


			sumgrupo1 = None
			for i in listobjetosF1:

				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				worksheet.write(x,3, i[4], numberdos)
				x += 1


			worksheet.write(x,1, "Menos:", bold)
			x+=1


			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
				where grupo = 'E2'
				group by concept,grupo,orden
				order by orden,concept   """)
			listobjetosF2 =  self.env.cr.fetchall()

			sumgrupo2 = None
			for i in listobjetosF2:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				worksheet.write(x,3, i[4], numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0),coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
				where grupo = 'E2' or grupo='E1' """)
			listtotalF1F2 =  self.env.cr.fetchall()
			x+=1

			if len(listtotalF1F2) >0:
				worksheet.write(x,1, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				worksheet.write(x,3, listtotalF1F2[0][1], numberdosbold)
				x += 1

			else:
				worksheet.write(x,1, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación", bold)
				worksheet.write(x,2, 0, numberdosbold)
				worksheet.write(x,3, 0, numberdosbold)
				x += 1

			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
				where grupo = 'E3'
				group by concept,grupo,orden
				order by orden,concept   """)
			listobjetosF1 =  self.env.cr.fetchall()
			x+=1


			worksheet.write(x,1, u"ACTIVIDADES DE INVERSIÓN", bold)
			x+=1
				
			sumgrupo1 = None
			for i in listobjetosF1:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				worksheet.write(x,3, i[4], numberdos)
				x += 1

			worksheet.write(x,1, u"Menos:", bold)
			x+=1
			

			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
				where grupo = 'E4'
				group by concept,grupo,orden
				order by orden,concept   """)
			listobjetosF2 =  self.env.cr.fetchall()

			sumgrupo2 = None
			for i in listobjetosF2:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				worksheet.write(x,3, i[4], numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) ,coalesce(sum(coalesce(saldoc,0)),0)  from account_state_efective
				where grupo = 'E3' or grupo='E4' """)
			listtotalF1F2 =  self.env.cr.fetchall()
			x+=1

			if len(listtotalF1F2) >0:

				worksheet.write(x,1, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				worksheet.write(x,3, listtotalF1F2[0][1], numberdosbold)
				x += 1


			else:

				worksheet.write(x,1, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión", bold)
				worksheet.write(x,2, 0, numberdosbold)
				worksheet.write(x,3, 0, numberdosbold)
				x += 1


			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
				where grupo = 'E5'
				group by concept,grupo,orden
				order by orden,concept  """)
			listobjetosF1 =  self.env.cr.fetchall()

			x+=1


			worksheet.write(x,1, u"ACTIVIDADES DE FINANCIAMIENTO", bold)
			x+=1

			sumgrupo1 = None
			for i in listobjetosF1:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				worksheet.write(x,3, i[4], numberdos)
				x += 1

			
			worksheet.write(x,1, u"Menos:", normal)
			x+=1


			self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
				where grupo = 'E6'
				group by concept,grupo,orden
				order by orden,concept  """)
			listobjetosF2 =  self.env.cr.fetchall()

			sumgrupo2 = None
			for i in listobjetosF2:
				worksheet.write(x,1, i[0], normal)
				worksheet.write(x,2, i[3], numberdos)
				worksheet.write(x,3, i[4], numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0),  coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
				where grupo = 'E5' or grupo='E6' """)
			listtotalF1F2 =  self.env.cr.fetchall()

			x+=1

			if len(listtotalF1F2) >0:

				worksheet.write(x,1, u"Aumento(Dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				worksheet.write(x,3, listtotalF1F2[0][1], numberdosbold)
				x += 1

			else:
				worksheet.write(x,1, u"Aumento(Dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento", bold)
				worksheet.write(x,2, 0, numberdosbold)
				worksheet.write(x,3, 0, numberdosbold)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0),coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
				where grupo = 'E5' or grupo='E6' or grupo='E4' or grupo='E3' or grupo='E2' or grupo='E1' """)
			listtotalF1F2 =  self.env.cr.fetchall()
			x+=1

			if len(listtotalF1F2) >0:
				worksheet.write(x,1, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				worksheet.write(x,3, listtotalF1F2[0][1], numberdosbold)
				x += 1

			else:
				worksheet.write(x,1, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO", bold)
				worksheet.write(x,2, 0, numberdosbold)
				worksheet.write(x,3, 0, numberdosbold)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) , coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
				where grupo = 'E7'""")
			listtotalF1F2 =  self.env.cr.fetchall()

			if len(listtotalF1F2) >0:
				worksheet.write(x,1, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio", normal)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdos)
				worksheet.write(x,3, listtotalF1F2[0][1], numberdos)
				x += 1

			else:
				worksheet.write(x,1, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio", normal)
				worksheet.write(x,2, 0, numberdos)
				worksheet.write(x,3, 0, numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) , coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
				where grupo = 'E8'""")
			listtotalF1F2 =  self.env.cr.fetchall()

			if len(listtotalF1F2) >0:
				worksheet.write(x,1, u"Ajuste por diferencia de Cambio", normal)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdos)
				worksheet.write(x,3, listtotalF1F2[0][1], numberdos)
				x += 1

			else:

				worksheet.write(x,1, u"Ajuste por diferencia de Cambio", normal)
				worksheet.write(x,2, 0, numberdos)
				worksheet.write(x,3, 0, numberdos)
				x += 1


			self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) , coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
				where grupo = 'E5' or grupo='E6' or grupo='E4' or grupo='E3' or grupo='E2' or grupo='E1' or grupo='E7' or grupo='E8' """)
			listtotalF1F2 =  self.env.cr.fetchall()

			x+=1

			if len(listtotalF1F2) >0:

				worksheet.write(x,1, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio", bold)
				worksheet.write(x,2, listtotalF1F2[0][0], numberdosbold)
				worksheet.write(x,3, listtotalF1F2[0][1], numberdosbold)
				x += 1

			else:
				worksheet.write(x,1, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio", bold)
				worksheet.write(x,2, 0, numberdosbold)
				worksheet.write(x,3, 0, numberdosbold)
				x += 1
				

			worksheet.set_column('B:B',57)
			worksheet.set_column('C:C',24)
			worksheet.set_column('D:D',24)
			#### FIN

			workbook.close()
			
			f = open(direccion + 'Reporte_state_efective.xlsx', 'rb')
			
			vals = {
				'output_name': 'EstadoEfectivo.xlsx',
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
		c.drawCentredString((wReal/2)+20,hReal-12, "ESTADO DE FLUJOS DE EFECTIVO")
		if self.check_comparative:
			c.drawCentredString((wReal/2)+20,hReal-24, "al "+ str(self.periodo_fin_c.date_stop))
		else:	
			c.drawCentredString((wReal/2)+20,hReal-24, "al "+ str(self.periodo_fin.date_stop))
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
		width , height = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas(direccion + "a.pdf", pagesize=A4)
		inicio = 0
		pos_inicial = hReal-60

		pagina = 1
		textPos = 0
		
		tamanios = {}
		voucherTamanio = None
		contTamanio = 0

		self.cabezera(c,wReal,hReal)
		c.setFont("Times-Bold", 8)
		c.drawCentredString(300,25,'Pág. ' + str(pagina))


		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
			where grupo = 'E1'
			group by concept,grupo,orden
			order by orden,concept   """)
		listobjetosF1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)


		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)

		c.drawCentredString( (wReal-60)-75+27 ,pos_inicial, self.fiscalyear_id.name )		
		c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
		
		c.drawCentredString( (wReal-60)-10+27 ,pos_inicial, self.fiscalyear_c_id.name )
		c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
		
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,18,pagina)

		c.drawString( 60 , pos_inicial, u"ACTIVIDADES DE OPERACIÓN")

		sumgrupo1 = None
		for i in listobjetosF1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(63,pos_inicial,i[0] )
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %i[3])

		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		c.setFont("Times-Bold", 8)
		c.drawString( 63 , pos_inicial, "Menos:")


		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
			where grupo = 'E2'
			group by concept,grupo,orden
			order by orden,concept   """)
		listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in listobjetosF2:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(63,pos_inicial,i[0] )
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %i[3])
			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %i[4])



		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0),coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
			where grupo = 'E2' or grupo='E1' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		print "-------------------"
		print listtotalF1F2
		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %listtotalF1F2[0][0])
			c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
			c.line((wReal-60)-75, pos_inicial+9, (wReal-60)-20 ,pos_inicial+9)

			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %listtotalF1F2[0][1])
			c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
			c.line((wReal-60)-10, pos_inicial+9, (wReal-60)+45 ,pos_inicial+9)
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %0.00)
			c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
			c.line((wReal-60)-75, pos_inicial+9, (wReal-60)-20 ,pos_inicial+9)

			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %0.00)
			c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
			c.line((wReal-60)-10, pos_inicial+9, (wReal-60)+45 ,pos_inicial+9)






		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
			where grupo = 'E3'
			group by concept,grupo,orden
			order by orden,concept   """)
		listobjetosF1 =  self.env.cr.fetchall()


		c.setFont("Times-Bold", 8)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 60 , pos_inicial, u"ACTIVIDADES DE INVERSIÓN")

		sumgrupo1 = None
		for i in listobjetosF1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(63,pos_inicial,i[0] )
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %i[3])
			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %i[4])

		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		c.setFont("Times-Bold", 8)
		c.drawString( 63 , pos_inicial, "Menos:")


		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
			where grupo = 'E4'
			group by concept,grupo,orden
			order by orden,concept   """)
		listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in listobjetosF2:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(63,pos_inicial,i[0] )
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %i[3])
			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %i[4])



		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) ,coalesce(sum(coalesce(saldoc,0)),0)  from account_state_efective
			where grupo = 'E3' or grupo='E4' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %listtotalF1F2[0][0])

			c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
			c.line((wReal-60)-75, pos_inicial+9, (wReal-60)-20 ,pos_inicial+9)

			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %listtotalF1F2[0][1])

			c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
			c.line((wReal-60)-10, pos_inicial+9, (wReal-60)+45 ,pos_inicial+9)

		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %0.00)

			c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
			c.line((wReal-60)-75, pos_inicial+9, (wReal-60)-20 ,pos_inicial+9)


			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %0.00)

			c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
			c.line((wReal-60)-10, pos_inicial+9, (wReal-60)+45 ,pos_inicial+9)






		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
			where grupo = 'E5'
			group by concept,grupo,orden
			order by orden,concept  """)
		listobjetosF1 =  self.env.cr.fetchall()


		c.setFont("Times-Bold", 8)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 60 , pos_inicial, u"ACTIVIDADES DE FINANCIAMIENTO")

		sumgrupo1 = None
		for i in listobjetosF1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(63,pos_inicial,i[0] )
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %i[3])
			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %i[4])

		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		c.setFont("Times-Bold", 8)
		c.drawString( 63 , pos_inicial, "Menos:")


		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),sum(saldoc),orden from account_state_efective
			where grupo = 'E6'
			group by concept,grupo,orden
			order by orden,concept  """)
		listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in listobjetosF2:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(63,pos_inicial,i[0] )
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %i[3])
			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %i[4])



		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0),  coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
			where grupo = 'E5' or grupo='E6' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"Aumento(Dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %listtotalF1F2[0][0])

			c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
			c.line((wReal-60)-75, pos_inicial+9, (wReal-60)-20 ,pos_inicial+9)


			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %listtotalF1F2[0][1])

			c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
			c.line((wReal-60)-10, pos_inicial+9, (wReal-60)+45 ,pos_inicial+9)
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"Aumento(Dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %0.00)

			c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
			c.line((wReal-60)-75, pos_inicial+9, (wReal-60)-20 ,pos_inicial+9)

			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %0.00)

			c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
			c.line((wReal-60)-10, pos_inicial+9, (wReal-60)+45 ,pos_inicial+9)






		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0),coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
			where grupo = 'E5' or grupo='E6' or grupo='E4' or grupo='E3' or grupo='E2' or grupo='E1' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" % listtotalF1F2[0][0])

			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" % listtotalF1F2[0][1])

		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %0.00)
			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" %0.00)



		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) , coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
			where grupo = 'E7'""")
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.setFont("Times-Roman", 8)
			c.drawString( 63 , pos_inicial, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" % listtotalF1F2[0][0])

			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" % listtotalF1F2[0][1])
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.setFont("Times-Roman", 8)
			c.drawString( 63 , pos_inicial, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %0.00)

			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" % 0.00)






		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) , coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
			where grupo = 'E8'""")
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.setFont("Times-Roman", 8)
			c.drawString( 63 , pos_inicial, u"Ajuste por diferencia de Cambio")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" % listtotalF1F2[0][0])
			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" % listtotalF1F2[0][1])
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.setFont("Times-Roman", 8)
			c.drawString( 63 , pos_inicial, u"Ajuste por diferencia de Cambio")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %0.00)
			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" % 0.00)





		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) , coalesce(sum(coalesce(saldoc,0)),0) from account_state_efective
			where grupo = 'E5' or grupo='E6' or grupo='E4' or grupo='E3' or grupo='E2' or grupo='E1' or grupo='E7' or grupo='E8' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" % listtotalF1F2[0][0])

			c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
			c.line((wReal-60)-75, pos_inicial-5, (wReal-60)-20 ,pos_inicial-5)
			c.line((wReal-60)-75, pos_inicial+9, (wReal-60)-20 ,pos_inicial+9)


			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" % listtotalF1F2[0][1])

			c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
			c.line((wReal-60)-10, pos_inicial-5, (wReal-60)+45 ,pos_inicial-5)
			c.line((wReal-60)-10, pos_inicial+9, (wReal-60)+45 ,pos_inicial+9)

		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 60 , pos_inicial, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio")
			c.drawRightString( (wReal-60)-20 ,pos_inicial,"%0.2f" %0.00)
			c.line((wReal-60)-75, pos_inicial-2, (wReal-60)-20 ,pos_inicial-2)
			c.line((wReal-60)-75, pos_inicial-5, (wReal-60)-20 ,pos_inicial-5)
			c.line((wReal-60)-75, pos_inicial+9, (wReal-60)-20 ,pos_inicial+9)

			c.drawRightString( (wReal-60)+45 ,pos_inicial,"%0.2f" % 0.00)

			c.line((wReal-60)-10, pos_inicial-2, (wReal-60)+45 ,pos_inicial-2)
			c.line((wReal-60)-10, pos_inicial-5, (wReal-60)+45 ,pos_inicial-5)
			c.line((wReal-60)-10, pos_inicial+9, (wReal-60)+45 ,pos_inicial+9)


		canvas.Canvas.save(c)

		

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

