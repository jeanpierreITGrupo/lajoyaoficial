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

class account_state_efective(models.Model):
	_name='account.state.efective'
	_auto= False
	_order = 'code'
	periodo = fields.Char('Periodo', size=50)
	code = fields.Char('Codigo', size=50)
	concept = fields.Char('Descripción',size=200)
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	saldo = fields.Float('Saldo', digits=(12,2))
	orden = fields.Integer('Orden')
	grupo = fields.Char('grupo')



class account_state_efective_wizard(osv.TransientModel):
	_name='account.state.efective.wizard'

	periodo_si = fields.Many2one('account.period','Periodo Saldo Inicial', required="1")
	periodo_ini = fields.Many2one('account.period','Periodo Inicio', required="1")
	periodo_fin = fields.Many2one('account.period','Periodo Fin', required="1")
	currency_id = fields.Many2one('res.currency','Moneda')


	type_show =  fields.Selection([('pantalla','Pantalla'),('pdf','Pdf')], 'Mostrar en', required=True)
	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)



	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'periodo_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )], 'periodo_fin':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'periodo_ini':[], 'periodo_fin':[]}}



	@api.onchange('periodo_ini')
	def _change_periodo_ini(self):
		if self.periodo_ini:
			self.periodo_fin= self.periodo_ini

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
					select row_number() OVER () AS id,* from ( select * from get_flujo_efectivo(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.code+"""') ,periodo_num('""" +self.periodo_fin.code +"""' ), periodo_num('""" +self.periodo_si.code +"""' )  ) ) AS T
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







	@api.multi
	def cabezera(self,c,wReal,hReal):

		c.setFont("Times-Bold", 10)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "ESTADO DE FLUJOS DE EFECTIVO")
		c.drawCentredString((wReal/2)+20,hReal-24, "al "+ str(self.periodo_fin.date_stop))
		c.drawCentredString((wReal/2)+20,hReal-36, "(Expresado en Nuevos Soles)")

		


	@api.multi
	def reporteador(self):

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
		c = canvas.Canvas( direccion + "a.pdf", pagesize=A4)
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
		c.drawString( 85 , pos_inicial, "ACTIVIDADES DE OPERACIÓN")

		sumgrupo1 = None
		for i in listobjetosF1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		c.setFont("Times-Bold", 8)
		c.drawString( 88 , pos_inicial, "Menos:")


		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
			where grupo = 'E2'
			group by concept,grupo,orden
			order by orden,concept   """)
		listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in listobjetosF2:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])



		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
			where grupo = 'E2' or grupo='E1' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		print "-------------------"
		print listtotalF1F2
		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %listtotalF1F2[0][0])
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %0.00)
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)






		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
			where grupo = 'E3'
			group by concept,grupo,orden
			order by orden,concept   """)
		listobjetosF1 =  self.env.cr.fetchall()


		c.setFont("Times-Bold", 8)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, u"ACTIVIDADES DE INVERSIÓN")

		sumgrupo1 = None
		for i in listobjetosF1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		c.setFont("Times-Bold", 8)
		c.drawString( 88 , pos_inicial, "Menos:")


		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
			where grupo = 'E4'
			group by concept,grupo,orden
			order by orden,concept   """)
		listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in listobjetosF2:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])



		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
			where grupo = 'E3' or grupo='E4' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %listtotalF1F2[0][0])

			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %0.00)

			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)








		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
			where grupo = 'E5'
			group by concept,grupo,orden
			order by orden,concept  """)
		listobjetosF1 =  self.env.cr.fetchall()


		c.setFont("Times-Bold", 8)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, u"ACTIVIDADES DE FINANCIAMIENTO")

		sumgrupo1 = None
		for i in listobjetosF1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
		c.setFont("Times-Bold", 8)
		c.drawString( 88 , pos_inicial, "Menos:")


		self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
			where grupo = 'E6'
			group by concept,grupo,orden
			order by orden,concept  """)
		listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in listobjetosF2:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])



		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
			where grupo = 'E5' or grupo='E6' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"Aumento(dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %listtotalF1F2[0][0])

			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"Aumento(dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %0.00)

			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)







		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
			where grupo = 'E5' or grupo='E6' or grupo='E4' or grupo='E3' or grupo='E2' or grupo='E1' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" % listtotalF1F2[0][0])
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %0.00)



		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
			where grupo = 'E7'""")
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.setFont("Times-Roman", 8)
			c.drawString( 88 , pos_inicial, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" % listtotalF1F2[0][0])
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.setFont("Times-Roman", 8)
			c.drawString( 88 , pos_inicial, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %0.00)






		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
			where grupo = 'E8'""")
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.setFont("Times-Roman", 8)
			c.drawString( 88 , pos_inicial, u"Ajuste por diferencia de Cambio")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" % listtotalF1F2[0][0])
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			c.setFont("Times-Roman", 8)
			c.drawString( 88 , pos_inicial, u"Ajuste por diferencia de Cambio")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %0.00)





		self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
			where grupo = 'E5' or grupo='E6' or grupo='E4' or grupo='E3' or grupo='E2' or grupo='E1' or grupo='E7' or grupo='E8' """)
		listtotalF1F2 =  self.env.cr.fetchall()

		if len(listtotalF1F2) >0:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" % listtotalF1F2[0][0])

			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial-5, (wReal-75)-20 ,pos_inicial-5)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)
		else:
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.setFont("Times-Bold", 8)
			c.drawString( 85 , pos_inicial, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %0.00)
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial-5, (wReal-75)-20 ,pos_inicial-5)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)


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


class account_account(models.Model):
	_inherit = 'account.account'
	fefectivo_id = fields.Many2one('account.config.efective',string='F. Efectivo')