# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import sys
from datetime import datetime
import os
import decimal
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_RIGHT
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, PageBreak, Spacer
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
from reportlab import platypus


class hr_liquidations_wizard(models.TransientModel):
	_name = 'hr.liquidations.wizard'

	date = fields.Date("Fecha")
	lines = fields.One2many('hr.liquidations.lines.wizard', 'liquidation')

	def default_get(self, cr, uid, fields, context=None):
		res = super(hr_liquidations_wizard, self).default_get(cr, uid, fields, context=context)
		lines = self.pool.get('hr.liquidaciones.lines.cts').search(cr, uid, [('liquidacion_id','=',context['active_id'])])
		lines = self.pool.get('hr.liquidaciones.lines.cts').browse(cr, uid, lines, context=context)
		values = []
		if lines:
			for line in lines:
				values.append((0,0,{'select':False,'employee_id':line.employee_id.id}))
			res.update({'lines':values})
		return res

	@api.multi
	def liquidation_cts(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		doc = SimpleDocTemplate(direccion+"Liquidacion.pdf", pagesize=A4)

		colorfondo = colors.lightblue
		e_cabecera = []
		elements=[]
		#Definiendo los estilos de la cabecera.
		font_size = 10
		styles = getSampleStyleSheet()
		styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
		styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
		styles.add(ParagraphStyle(name='LeftBold', 
			fontSize=font_size,
			fontName='Helvetica-Bold',

			))
		styles.add(ParagraphStyle(name='Left', 
			fontSize=font_size,
			fontName='Helvetica',			
			))
		styles.add(ParagraphStyle(name='RightBold', 
			fontSize= 25,
			fontName='Helvetica-Bold',
			alignment=TA_CENTER,
			))
		styles.add(ParagraphStyle(name='Right', 
			fontSize=font_size,
			alignment=TA_RIGHT,
			fontName='Helvetica',			
			))
		estilo_c = [
					('SPAN',(0,0),(1,0)),
					('SPAN',(2,0),(3,0)),
					('ALIGN',(2,0),(3,0),'RIGHT'),
					('VALIGN',(0,0),(-1,-1),'TOP'),
				]
		#------------------------------------------------------Insertando Data-----------------------------------------
		#--------------------------------------------------Cabecera
		a = Image(direccion+"calquipalleft.png")  
		a.drawHeight = 70
		a.drawWidth = 105
		b = Image(direccion+"calquipalright.png")  
		b.drawHeight = 70
		b.drawWidth = 95
		cabecera = [[a,'',b,''],]
		table_c = Table(cabecera, colWidths=[120]*2, rowHeights=50, style=estilo_c)
		e_cabecera.append(table_c)
		e_cabecera.append(Spacer(0,20))

		#----------------------------------------------------Datos

		for liquidation in self.lines:
			if liquidation.select:
				cts_line = self.env['hr.liquidaciones.lines.cts'].search([('employee_id','=',liquidation.employee_id.id)])
				employee = cts_line.employee_id
				print employee.gender
				elements = elements + e_cabecera
				text = "Arequipa, " + datetime.strptime(str(self.date), '%Y-%m-%d').strftime("%d de %B del %Y")
				elements.append(Paragraph(text, styles['Right']))
				elements.append(Spacer(0,30))
				text = u"""Señores<br/>
							<b>BANCO BBVA CONTINENTAL</b><br/>
							Presente.-"""
				elements.append(Paragraph(text, styles['Left']))
				elements.append(Spacer(0,50))
				text = u"<b>REF.: DEPÓSITO DE COMPENSACIÓN POR TIEMPO DE SERVICIOS</b>"
				elements.append(Paragraph(text, styles['Left']))
				elements.append(Spacer(0,40))
				text = u"""De nuestra consideración:<br/><br/>
							Por medio de la presente nos dirigimos a ustedes para 
							informarles que """+("""el Sr. <b>""" if employee.gender == 'male' else """la Sra. <b>""") + employee.name_related + u"""</b>
							 identificado con documento de identidad <b>Nº """+employee.identification_id+"""</b> ha laborado
							 en nuestra empresa hasta el <b>"""+datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').strftime("%d/%m/%Y")+"""</b>."""
				elements.append(Paragraph(text, styles['Justify']))
				elements.append(Spacer(0,20))
				text = u"""Motivo por el cual el ex trabajador personalmente podrá efectuar 
							el retiro de su depósito de Compensación por Tiempo de Servicios, 
							depositada en su institución."""
				elements.append(Paragraph(text, styles['Justify']))
				elements.append(Spacer(0,20))
				text = """Extendemos el presente a solicitud del interesado para los fines que estime pertinentes."""
				elements.append(Paragraph(text, styles['Justify']))
				elements.append(Spacer(0,40))
				text = """<b>p. CALQUIPA<br/>
							RUC 20455959943</b>"""
				elements.append(Paragraph(text, styles['Left']))
				elements.append(Spacer(0,100))
				text = """____________________________________"""
				elements.append(Paragraph(text, styles['Left']))
				elements.append(Spacer(0,60))
				text = u"""<b>Calquipa S.A.C.</b><br/>
							Urbanización San José D-11, Yanahuara, Arequipa - Perú.<br/>
							Tel +51 54 - 270702/271906<br/>
							ventascalquipa@calidra.com.mx; recepcion_calquipa@calidra.com.mx<br/>
							www.calidra.com / www.calquipa.com
							"""
				elements.append(Paragraph(text, styles['Center']))
				elements.append(PageBreak())
				elements = elements + e_cabecera 
				text = 'CARGO'
				datat=[['','','',Paragraph(text, styles['RightBold'])]]
				table=Table(datat,colWidths=[120]*4, rowHeights=40)
				table.setStyle(TableStyle(
					[
					('BOX',(3,0),(3,0),1, colors.black),
					('ALIGN',(0,0),(-1,-1),'LEFT'),
					('VALIGN',(0,0),(-1,-1),'TOP'),
					]
					))
				elements.append(Spacer(0,10))
				elements.append(table)
				elements.append(Spacer(0,10))
				text = "Arequipa, " + datetime.strptime(str(self.date), '%Y-%m-%d').strftime("%d de %B del %Y")
				elements.append(Paragraph(text, styles['Right']))
				elements.append(Spacer(0,30))
				text = u"""Señores<br/>
							<b>BANCO BBVA CONTINENTAL</b><br/>
							Presente.-"""
				elements.append(Paragraph(text, styles['Left']))
				elements.append(Spacer(0,30))
				text = u"<b>REF.: DEPÓSITO DE COMPENSACIÓN POR TIEMPO DE SERVICIOS</b>"
				elements.append(Paragraph(text, styles['Left']))
				elements.append(Spacer(0,40))
				text = u"""De nuestra consideración:<br/><br/>
							Por medio de la presente nos dirigimos a ustedes para 
							informarles que """+ ("""el Sr. <b>""" if employee.gender == 'male' else """la Sra. <b>""") + employee.name_related + u"""</b>
							 """ +("""identificado""" if employee.gender == 'male' else """identificada""")+""" con documento de identidad <b>Nº """+employee.identification_id+"""</b> ha laborado
							 en nuestra empresa hasta el <b>"""+datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').strftime("%d/%m/%Y")+"""</b>."""
				elements.append(Paragraph(text, styles['Justify']))
				elements.append(Spacer(0,20))
				text = u"""Motivo por el cual el ex trabajador personalmente podrá efectuar 
							el retiro de su depósito de Compensación por Tiempo de Servicios, 
							depositada en su institución."""
				elements.append(Paragraph(text, styles['Justify']))
				elements.append(Spacer(0,20))
				text = """Extendemos el presente a solicitud del interesado para los fines que estime pertinentes."""
				elements.append(Paragraph(text, styles['Justify']))
				elements.append(Spacer(0,40))
				text = """<b>p. CALQUIPA<br/>
							RUC 20455959943</b>"""
				elements.append(Paragraph(text, styles['Left']))
				elements.append(Spacer(0,80))
				text = """____________________________________"""
				elements.append(Paragraph(text, styles['Left']))
				elements.append(Spacer(0,40))
				text = u"""<b>Calquipa S.A.C.</b><br/>
							Urbanización San José D-11, Yanahuara, Arequipa - Perú.<br/>
							Tel +51 54 - 270702/271906<br/>
							ventascalquipa@calidra.com.mx; recepcion_calquipa@calidra.com.mx<br/>
							www.calidra.com / www.calquipa.com
							"""
				elements.append(Paragraph(text, styles['Center']))
				elements.append(PageBreak())
		doc.build(elements)
		f = open(direccion + 'Liquidacion.pdf', 'rb')

		vals = {
			'output_name': 'Liquidacion.pdf',
			'output_file': f.read().encode("base64"),		
		}
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}

class hr_liquidations_lines_wizard(models.TransientModel):
	_name = 'hr.liquidations.lines.wizard'

	liquidation = fields.Many2one('hr.liquidations.wizard', 'Liquidation')
	select = fields.Boolean('Liquidar')
	employee_id = fields.Many2one('hr.employee',"Empleado")
