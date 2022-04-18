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


class account_state_nature(models.Model):
	_name='account.state.nature'
	_auto= False
	_order = 'orden'

	name = fields.Char('Nombre', size=50)
	grupo = fields.Char('Grupo',size=200)
	saldo = fields.Float('Saldo', digits=(12,2))
	orden = fields.Integer('Orden')




class account_state_nature_wizard(osv.TransientModel):
	_name='account.state.nature.wizard'

	periodo_ini = fields.Many2one('account.period','Periodo Inicio', required="1")
	periodo_fin = fields.Many2one('account.period','Periodo Fin', required="1")
	currency_id = fields.Many2one('res.currency','Moneda')

	type_show =  fields.Selection([('pantalla','Pantalla'),('pdf','Pdf')], 'Mostrar en', required=True)


	save_page_states = []


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
			DROP VIEW IF EXISTS account_state_nature;
			create or replace view account_state_nature as(
					select row_number() OVER () AS id,* from ( select * from get_estado_nature(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.name+"""') ,periodo_num('""" +self.periodo_fin.name +"""' )) ) AS T
			)
			""")		

		self.env.cr.execute(""" 
			select * from account_state_nature;
			""")

		t = self.env.cr.fetchall()
		
		#if len(t)==0:
		#	raise osv.except_osv('Alerta','No contiene datos en esos periodos.')

		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			
			return {
				'name': 'Resultado por Naturaleza',
				'type': 'ir.actions.act_window',
				'res_model': 'account.state.nature',
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
				'output_name': 'Estado de Resultados.pdf',
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

		c.setFont("Times-Bold", 12)
		c.setFillColor(black)
		c.drawCentredString((wReal/2)+20,hReal, self.env["res.company"].search([])[0].name.upper())
		c.drawCentredString((wReal/2)+20,hReal-12, "ESTADO DE RESULTADOS")
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
		c.setFont("Times-Bold", 10)
		c.drawCentredString(300,25,'Pág. ' + str(pagina))


		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_nature
			where grupo = 'N1'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosN1 =  self.env.cr.fetchall()

		sumgrupo1 = None
		for i in listobjetosN1:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		if len(listobjetosN1)>0:
			
			self.env.cr.execute(""" select sum(saldo) from account_state_nature where grupo = 'N1' """)
			totalB1 = self.env.cr.fetchall()[0]
			sumgrupo1 = totalB1[0]
			
		else:
			sumgrupo1 = 0
			
		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_nature
			where grupo = 'N2'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosN2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in listobjetosN2:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		if len(listobjetosN2)>0:
			c.setFont("Times-Bold", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.drawString(85,pos_inicial,"MARGEN COMERCIAL")

			self.env.cr.execute(""" select sum(saldo) from account_state_nature where grupo = 'N2' """)
			totalB1 = self.env.cr.fetchall()[0]
			sumgrupo2 = totalB1[0]
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" % (sumgrupo1 + totalB1[0]) )
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)
		else:
			sumgrupo2 = 0
			c.setFont("Times-Bold", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
			c.drawString(85,pos_inicial,"MARGEN COMERCIAL")
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %(sumgrupo1) )
			c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
			c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)


		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_nature
			where grupo = 'N3'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosN3 =  self.env.cr.fetchall()

		for i in listobjetosN3:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalN3 = 0
		if len(listobjetosN3)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_nature where grupo = 'N3' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalN3 = totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "TOTAL PRODUCCIÓN")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( totalN3 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)


		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_nature
			where grupo = 'N4'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosN4 =  self.env.cr.fetchall()

		for i in listobjetosN4:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalN4 = 0
		if len(listobjetosN4)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_nature where grupo = 'N4' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalN4 = totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "VALOR AGREGADO")
		sumgrupo4 = sumgrupo1 + sumgrupo2 + totalN3 + totalN4
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( sumgrupo1 + sumgrupo2 + totalN3 + totalN4 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)



		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_nature
			where grupo = 'N5'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosN5 =  self.env.cr.fetchall()

		for i in listobjetosN5:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalN5 = sumgrupo1 + sumgrupo2 + totalN3 + totalN4
		if len(listobjetosN5)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_nature where grupo = 'N5' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalN5 += totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "EXCEDENTE (O INSUFICIENCIA) BRUTO DE EXPL.")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( totalN5 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)



		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_nature
			where grupo = 'N6'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosN6 =  self.env.cr.fetchall()

		for i in listobjetosN6:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalN6 = totalN5
		if len(listobjetosN6)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_nature where grupo = 'N6' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalN6 += totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "RESULTADO ANTES DE PARTC. E IMPUESTOS")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( totalN6 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)


		self.env.cr.execute(""" select name as code,'' as concept,grupo,sum(saldo),orden from account_state_nature
			where grupo = 'N7'
			group by name,grupo,orden
			order by orden,name   """)
		listobjetosN7 =  self.env.cr.fetchall()

		for i in listobjetosN7:
			c.setFont("Times-Roman", 10)
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)
			c.drawString(88,pos_inicial,i[0] )
			c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %i[3])

		totalN7 = totalN6
		if len(listobjetosN7)>0:
			self.env.cr.execute(""" select sum(saldo) from account_state_nature where grupo = 'N7' """)
			totalB1 = self.env.cr.fetchall()[0]
			totalN7 += totalB1[0]

		c.setFont("Times-Bold", 10)
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
		c.drawString( 85 , pos_inicial, "RESULTADO DEL EJERCICIO")
		c.drawRightString( (wReal-75)-20 ,pos_inicial,"%0.2f" %( totalN7 ) )
		c.line((wReal-75)-75, pos_inicial-2, (wReal-75)-20 ,pos_inicial-2)
		c.line((wReal-75)-75, pos_inicial-4, (wReal-75)-20 ,pos_inicial-4)
		c.line((wReal-75)-75, pos_inicial+9, (wReal-75)-20 ,pos_inicial+9)

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

			c.setFont("Times-Bold", 10)
			c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-60
		else:
			return pagina,posactual-valor

