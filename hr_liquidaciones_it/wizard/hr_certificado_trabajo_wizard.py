# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp     import models, fields, api
import base64

from datetime import datetime

import codecs
import sys
import os
import decimal
from reportlab.lib.enums       import TA_JUSTIFY,TA_CENTER,TA_RIGHT
from reportlab.pdfgen          import canvas
from reportlab.lib.units       import inch
from reportlab.lib.colors      import magenta, red , black , blue, gray, white, Color, HexColor
from reportlab.pdfbase         import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes   import letter, A4
from reportlab.platypus        import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib             import colors
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus        import Paragraph, Table, PageBreak, Spacer
from reportlab.lib.units       import  cm,mm
from reportlab.lib.utils       import simpleSplit
from cgi                       import escape
from reportlab                 import platypus


class hr_certificado_trabajo_wizard(models.TransientModel):
	_name = 'hr.certificado.trabajo.wizard'

	date         = fields.Date("Fecha", required=True)
	employee_ids = fields.Many2many('hr.employee', 'certificado_employee_rel','certificado_id','employee_id','empleados')

	@api.one
	def date_to_text(self, date):
		d = date.split('-')
		months = {
			'01': 'enero',
			'02': 'febrero',
			'03': 'marzo',
			'04': 'abril',
			'05': 'mayo',
			'06': 'junio',
			'07': 'julio',
			'08': 'agosto',
			'09': 'septiembre',
			'10': 'octubre',
			'11': 'noviembre',
			'12': 'diciembre',
		}
		res = d[2] + " de " + months[d[1]] + " del " + d[0]
		return res

	@api.model
	def default_get(self, fields):
		res = super(hr_certificado_trabajo_wizard,self).default_get(fields)
		res['employee_ids'] = [(6, 0, self.env.context['employees'])]
		return res

	@api.multi
	def do_rebuild(self):
		self.reporteador()
		
		import os
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj   = self.env['ir.model.data']
		act_obj   = self.env['ir.actions.act_window']
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		title     = 'Certificado_Trabajo.pdf'
		vals = {
			'output_name': title,
			'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
		}
		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type"     : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"    : [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
		}

	@api.multi
	def cabecera(self,c,wReal,hReal):
		import os
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		c.setFont("Arimo-Bold", 8)
		c.setFillColor(black)
		endl = 12
		pos_inicial = hReal-10
		pagina = 1
		pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*6,pagina)
		c.drawImage(direccion + 'calquipalright.png',20, hReal-20, width=120, height=50)
		c.drawImage(direccion + 'calquipalleft.png',430, hReal-35, width=140, height=70)

	@api.multi
	def reporteador(self):
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize=A4)
		inicio = 0
		pos_inicial = hReal-100
		endl = 12
		font_size = 10

		pagina = 1
		textPos = 0

		pdfmetrics.registerFont(TTFont('Arimo-Bold', 'Arimo-Bold.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-BoldItalic', 'Arimo-BoldItalic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Italic', 'Arimo-Italic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Regular', 'Arimo-Regular.ttf'))

		for employee in self.employee_ids:
			for cont in range(2):
				self.cabecera(c,wReal,hReal)

				c.setFont("Arimo-Bold", 14)
				c.drawCentredString((wReal/2)+20,pos_inicial, u"CERTIFICADO DE TRABAJO")
				c.line(205, pos_inicial-2, 400 , pos_inicial-2)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*6,pagina)
				if cont == 1:
					pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*-9,pagina)
					c.setFont("Arimo-Regular", 14)
					c.setFillColor(white)
					c.setStrokeColor(black)
					c.rect(400, pos_inicial-4, 80, endl*2, stroke=1, fill=1)
					c.setFillColor(black)
					c.drawString( 410 , pos_inicial+3, u"CARGO")
					pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*9,pagina)

				c.setFont("Arimo-Regular", font_size)
				c.drawString( 30 , pos_inicial, u"A QUIEN CORRESPONDA:")
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*8,pagina)
				style = getSampleStyleSheet()["Normal"]
				style.leading   = 12
				style.alignment = 4
				sust = " "
				if employee.gender == 'male':
					sust = " el Sr. "
				if employee.gender == 'female':
					sust = " la Sra. "
				data= [
					[Paragraph("<font size="+str(font_size)+">" + u"Dejamos constancia que" + sust + "<b>" + employee.name_related.upper() + u"</b>, identificado con <b>DNI Nº " + (employee.identification_id if employee.identification_id else '') + u"</b> prestó servicios en nuestra empresa desde el " + (self.date_to_text(employee.fecha_ingreso)[0] if len(self.date_to_text(employee.fecha_ingreso)) > 0 else '') + ", hasta el " + (self.date_to_text(employee.fecha_cese)[0] if len(self.date_to_text(employee.fecha_cese)) > 0 else '') + u", desempeñandose como <b>" + (employee.job_id.name if  employee.job_id.name else '') + u"</b>, demostrando durante su permanencia responsabilidad, honestidad y dedicación en las labores que le fueron encomendadas. <br/><br/> Extendemos el presente a solicitud del interesado(a) para los fines que estime pertinentes." + "</font>",style)]
				]
				t=Table(data,colWidths=(560-30), rowHeights=(40))
				t.setStyle(TableStyle([
				('TEXTFONT', (0, 0), (-1, -1), 'Arimo-Regular'),
				('FONTSIZE',(0,0),(-1,-1),font_size)
				]))
				t.wrapOn(c,25,pos_inicial)
				t.drawOn(c,25,pos_inicial)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*3,pagina)

				c.drawString( 30 , pos_inicial, u"Arequipa, " + self.date_to_text(self.date)[0] if len(self.date_to_text(self.date)) else "_"*13)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*10,pagina)

				c.setFont("Arimo-Bold", font_size)
				c.drawString( 30 , pos_inicial, u"p. CALQUIPA")
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
				rc = self.env['res.company'].search([])[0]
				c.drawString( 30 , pos_inicial, rc.vat[3:])
				c.setFont("Arimo-Regular", font_size)
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl*25,pagina)

				c.setFont("Arimo-Bold", font_size)
				c.drawCentredString(width/2.00, pos_inicial, rc.name.upper() if rc.name else '')
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
				c.drawCentredString(width/2.00, pos_inicial, rc.street.capitalize() if rc.street else '')
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
				c.drawCentredString(width/2.00, pos_inicial,("Tel " + rc.phone) if rc.phone else '')
				pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,endl,pagina)
				c.setFillColor(HexColor("#175CBB"))
				c.drawCentredString(width/2.00, pos_inicial, rc.website + " / www.calquipa.com" if rc.website else '')


				c.showPage()
				inicio = 0
				pos_inicial = hReal-100
				pagina = 1
				textPos = 0
		c.save()

	@api.multi
	def particionar_text(self,c,f,d):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Arimo-Regular',f,d)
			if len(tet)>d:
				return tet[:-1]
		return tet

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabecera(c,wReal,hReal)

			#c.setFont("Arimo-Bold", 8)
			#c.drawCentredString(300,25,'Pag. ' + str(pagina+1))
			return pagina+1,hReal-100
		else:
			return pagina,posactual-valor