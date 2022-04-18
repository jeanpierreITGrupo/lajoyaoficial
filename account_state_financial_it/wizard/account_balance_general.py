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


class account_balance_general(models.Model):
	_name='account.balance.general'
	_auto= False
	_order = 'orden'
	
	name = fields.Char('Nombre', size=50)
	grupo = fields.Char('Grupo',size=200)
	saldo = fields.Float('Saldo', digits=(12,2))
	orden = fields.Integer('Orden')
	saldoC = fields.Float('Saldo C', digits=(12,2) )



class account_balance_general_wizard(osv.TransientModel):
	_name='account.balance.general.wizard'

	periodo_ini = fields.Many2one('account.period','Periodo Inicio', required="1")
	periodo_fin = fields.Many2one('account.period','Periodo Fin', required="1")
	currency_id = fields.Many2one('res.currency','Moneda')
	type_show =  fields.Selection([('pantalla','Pantalla'),('pdf','Pdf')], 'Mostrar en', required=True)

	save_page_states= []


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
					select row_number() OVER () AS id,* from ( select * from get_balance_general(""" + flag+ """ ,periodo_num('""" + self.periodo_ini.name+"""') ,periodo_num('""" +self.periodo_fin.name +"""' )) ) AS T
			)
			""")		

		self.env.cr.execute(""" 
			select * from account_balance_general;
			""")

		t = self.env.cr.fetchall()
		
		#if len(t)==0:
		#	raise osv.except_osv('Alerta','No contiene datos en esos periodos.')

		print t

		if self.type_show == "pantalla":

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			
			return {
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
		c.drawCentredString((wReal/2)+20,hReal-12, "ESTADO DE SITUACIÓN FINANCIERA")
		c.drawCentredString((wReal/2)+20,hReal-24, "AL "+ str(self.periodo_fin.date_stop))
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
		height ,width = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize=(width,height) )
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
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
			where grupo = 'B1'
			group by name ,grupo,orden
			order by orden,name

			--select * from account_balance_general where grupo = 'B1' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString( 15 , pos_inicialL, "ACTIVO")
		c.line(15,pos_inicialL-1,52,pos_inicialL-1)
		c.drawString(15,pos_inicialL - 24,"ACTIVO CORRIENTE")

		pos_inicialL = pos_inicialL - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(18,pos_inicialL,i[0] )
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO CORRIENTE")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B1' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %totalB1[0])
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO CORRIENTE")
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %(0.0) )
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)

		self.guardar_state(c)


		nivel_left_page = c._pageNumber
		nivel_left_fila = pos_inicialL
		
		
		self.cargar_pagina(c,1)
		
		###  B3
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
where grupo = 'B3'
group by name,grupo,orden
order by orden,name

--select * from account_balance_general where grupo = 'B3' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString( (wReal/2)+20 , pos_inicialR, "PASIVO Y PATRIMONIO")
		c.line( (wReal/2)+20,pos_inicialR-1,(wReal/2)+120,pos_inicialR-1)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PASIVO CORRIENTE")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO CORRIENTE")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B3' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO CORRIENTE")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

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

		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
			where grupo = 'B2'
			group by name,grupo,orden
			order by orden,name

			--select * from account_balance_general where grupo = 'B2' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString(15,pos_inicialL - 24,"ACTIVO NO CORRIENTE")

		pos_inicialL = pos_inicialL - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(18,pos_inicialL,i[0] )
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO NO CORRIENTE")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B2' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %totalB1[0])
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialL = self.verify_linea(c,wReal,hReal,pos_inicialL,12,pagina)
			c.drawString(15,pos_inicialL,"TOTAL ACTIVO NO CORRIENTE")
			c.drawRightString( (wReal/2)-20 ,pos_inicialL,"%0.2f" %(0.0) )
			c.line((wReal/2)-75, pos_inicialL-2, (wReal/2)-20 ,pos_inicialL-2)
			c.line((wReal/2)-75, pos_inicialL-4, (wReal/2)-20 ,pos_inicialL-4)
			c.line((wReal/2)-75, pos_inicialL+9, (wReal/2)-20 ,pos_inicialL+9)

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
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
where grupo = 'B4'
group by name,grupo,orden
order by orden,name

--select * from account_balance_general where grupo = 'B4' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PASIVO NO CORRIENTE")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO NO CORRIENTE")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B4' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PASIVO NO CORRIENTE")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

		self.guardar_state(c)



		###  B5
		self.env.cr.execute(""" select name as code,'' as concept,sum(saldo) from account_balance_general
where grupo = 'B5'
group by name,grupo,orden
order by orden,name

--select * from account_balance_general where grupo = 'B5' order by orden,id""")
		listobjetosB1 =  self.env.cr.fetchall()

		c.setFont("Times-Bold", 8)
		c.drawString((wReal/2)+20,pos_inicialR - 24,"PATRIMONIO")

		pos_inicialR = pos_inicialR - 24
		for i in listobjetosB1:
			c.setFont("Times-Roman", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+23,pos_inicialR,i[0] )
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %i[2])

		if len(listobjetosB1)>0:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PATRIMONIO")

			self.env.cr.execute(""" select sum(saldo) from account_balance_general where grupo = 'B5' """)
			totalB1 = self.env.cr.fetchall()[0]
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalB1[0])
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)
		else:
			c.setFont("Times-Bold", 8)
			pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,12,pagina)
			c.drawString((wReal/2)+20,pos_inicialR,"TOTAL PATRIMONIO")
			c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(0.0) )
			c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
			c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
			c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)

		c.setFont("Times-Roman", 8)
		pagina, pos_inicialR = self.verify_linea(c,wReal,hReal,pos_inicialR,24,pagina)
		c.drawString((wReal/2)+20,pos_inicialR,"RESULTADO DEL PERIODO")
		self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B1' or grupo = 'B2' """)
		totalA12 = self.env.cr.fetchall()[0][0]
		self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B3' or grupo = 'B4' or grupo = 'B5' """)
		totalA345 = self.env.cr.fetchall()[0][0]
		c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %(totalA12- totalA345) )


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

		self.env.cr.execute(""" select coalesce(sum(saldo),0) from account_balance_general
where grupo = 'B1' or grupo = 'B2' """)
		totalA12 = self.env.cr.fetchall()[0][0]
		c.drawRightString( (wReal)-20 ,pos_inicialR,"%0.2f" %totalA12)
		c.line((wReal)-75, pos_inicialR-2, (wReal)-20 ,pos_inicialR-2)
		c.line((wReal)-75, pos_inicialR-4, (wReal)-20 ,pos_inicialR-4)
		c.line((wReal)-75, pos_inicialR+9, (wReal)-20 ,pos_inicialR+9)


		c.drawRightString( (wReal/2)-20 ,pos_inicialR,"%0.2f" %totalA12)
		c.line((wReal/2)-75, pos_inicialR-2, (wReal/2)-20 ,pos_inicialR-2)
		c.line((wReal/2)-75, pos_inicialR-4, (wReal/2)-20 ,pos_inicialR-4)
		c.line((wReal/2)-75, pos_inicialR+9, (wReal/2)-20 ,pos_inicialR+9)

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


