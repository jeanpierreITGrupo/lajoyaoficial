# -*- encoding: utf-8 -*-
import base64
from openerp.osv import osv
from openerp import models, fields, api
from datetime import date,timedelta

from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_RIGHT

from reportlab.pdfgen          import canvas
from reportlab.lib.units       import inch
from reportlab.lib.colors      import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase         import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes   import letter, A4, landscape
from reportlab.platypus        import SimpleDocTemplate, Table, TableStyle,BaseDocTemplate, PageTemplate, Frame
from reportlab.lib             import colors
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus        import Paragraph, Table, PageBreak, Spacer, FrameBreak,Image
from reportlab.lib.units       import cm,mm
from reportlab.lib.utils       import simpleSplit
from cgi                       import escape
from reportlab                 import platypus

class hr_employee(models.Model):
	_inherit = 'hr.employee'


	afiliacion        = fields.Many2one('hr.table.membership','Afiliación AFP')
	type_document_id  = fields.Many2one('it.type.document.partner','Tipo de Documento')
	cusspp            = fields.Char('CUSSPP')
	c_mixta           = fields.Boolean('Comisión Mixta')
	fecha_cese        = fields.Date('Fecha cese')
	basica            = fields.Float('Básico', digits=(12,2))
	direccion_text	  = fields.Char(u'Dirección')
	dist_c            = fields.Many2one('hr.distribucion.gastos','Dist. C.C.')
	banco_cts         = fields.Char('Banco CTS', size=50)
	banco_rem         = fields.Char('Banco Rem', size=50)
	cta_cts           = fields.Char('Nro. de Cta. CTS', size=50)
	cta_rem           = fields.Char('Nro. de Cta. Rem', size=50)
	tipo_trabajador   = fields.Many2one('tipo.trabajador','Tipo de Trabajador')
	codigo_trabajador = fields.Char('Código de Trabajador')
	condicion         = fields.Char('Condición')
	situacion         = fields.Char('Situación')
	no_domiciliado    = fields.Boolean('No domiciliado')
	use_eps           = fields.Boolean('Aport. EPS')
	essalud_vida	  = fields.Boolean('EsSalud Vida')
	fondo_jub		  = fields.Boolean(u'Fondo Jubilación')
	movilidad 		  = fields.Float(u'Movilidad supeditada al centro laboral')
	ubicacion_id 	  = fields.Many2one('hr.location',u'Ubicación')

	cuenta_adelanto = fields.Many2one('account.account','Cuenta de adelanto')
	situacion       = fields.Char('Situación', readonly=1, compute="get_situacion")
	is_practicant   = fields.Boolean('Practicante', default=False)
	afp_2p          = fields.Boolean('AFP 2%', default=False)


	@api.one
	def get_situacion(self):
		if self.fecha_cese:		
			if self.fecha_cese >= str(date.today())[:10]:
				self.situacion = "Activo"
			else:
				self.situacion = "Baja"

		else:
			self.situacion = "Activo"

	@api.multi
	def make_pdf(self):
		import os
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		title = 'Ficha_empleado'
		doc = BaseDocTemplate(direccion+title+".pdf", pagesize=A4,bottomMargin=0.5*cm, topMargin=0.5*cm, rightMargin=0.5*cm, leftMargin=0.5*cm)

		pdfmetrics.registerFont(TTFont('Arimo-Bold', 'Arimo-Bold.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-BoldItalic', 'Arimo-BoldItalic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Italic', 'Arimo-Italic.ttf'))
		pdfmetrics.registerFont(TTFont('Arimo-Regular', 'Arimo-Regular.ttf'))

		elements = []

		for employee in self:
			doc.addPageTemplates(
			[
				PageTemplate(
					frames=[
						Frame(
							doc.leftMargin,
							doc.bottomMargin,
							doc.width,
							doc.height,
							id = None
						),
						]
					),
				]
			)
			
			data   = []
			estilo = []

			elements.append(platypus.flowables.Macro('canvas.saveState()'))
			elements.append(platypus.flowables.Macro('canvas.restoreState()'))

			styles           = getSampleStyleSheet()
			styleN           = styles["Normal"]
			styleN.leading   = 10
			styleN.alignment = TA_JUSTIFY

			dtm = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
			rc  = self.env['res.company'].search([])[0]

			estilo.append(('GRID',(0,3),(-1,-1),0.5,black))
			estilo.append(('VALIGN',(0,0),(-1,-1),'MIDDLE'))
			estilo.append(('ALIGN',(0,0),(-1,-1),'CENTER'))
			estilo.append(('FONTSIZE', (0, 0), (-1, -1), 8))
			estilo.append(('FONT', (0, 0), (-1,-1),'Arimo-Regular'))

			I = ''
			if rc.logo:
				fim = open(direccion+'tmp_logo.png','wb')
				fim.write(rc.logo.decode('base64'))
				fim.close()
				I            = Image(direccion+"tmp_logo.png")
				I.drawHeight = 45
				I.drawWidth  = 120

			IE = ''
			if employee.image_medium:
				fim2 = open(direccion+'tmp_employee'+employee.name_related+'.png','wb')
				fim2.write(employee.image_medium.decode('base64'))
				fim2.close()
				IE            = Image(direccion+"tmp_employee"+employee.name_related+".png")
				IE.drawHeight = 45
				IE.drawWidth  = 50

			row_pos = 1

			data.append([I,'',u'FICHA DE DATOS DEL TRABAJADOR','','','','',IE])
			estilo.append(('ALIGN',(0,0),(0,0),'LEFT'))
			estilo.append(('ALIGN',(-1,0),(-1,0),'RIGHT'))
			estilo.append(('SPAN',(2,0),(5,0)))
			estilo.append(('FONTSIZE', (0, 0), (-1, 0), 14))
			estilo.append(('FONT', (0, 0), (-1,0),'Arimo-Bold'))

			data.append(['I. DATOS PERSONALES','','','','','','',''])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('FONTSIZE', (0, row_pos), (-1, row_pos), 11))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append(['','','','','','','',''])
			row_pos += 1

			data.append([u'Apellido Parterno','','',(employee.last_name_father.capitalize() if employee.last_name_father else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Apellido Materno','','',(employee.last_name_mother.capitalize() if employee.last_name_mother else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Nombres','','',(employee.first_name_complete.capitalize() if employee.first_name_complete else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Tipo de Documento','','',(employee.type_document_id.description if employee.type_document_id.description else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Nº Documento','','',(employee.identification_id if employee.identification_id else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Nº Pasaporte','','',(employee.passport_id if employee.passport_id else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Otro ID','','',(employee.otherid if employee.otherid else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Nacionalidad','','',(employee.country_id.name if employee.country_id.name else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Fecha de Nacimiento','','',(employee.birthday if employee.birthday else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Dirección','','',(employee.direccion_text if employee.direccion_text else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			sexo_dict = {'male':'Hombre', 'female':'Mujer'}
			data.append([u'Sexo','','',(sexo_dict[employee.gender] if employee.gender else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			estado_civ_dict = {'single':'Soltero(a)', 'married':'Casado(a)', 'widower':'Viudo(a)', 'divorced':'Divorciado(a)'}
			data.append([u'Estado Civil','','',(estado_civ_dict[employee.marital] if employee.marital else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Nº de Hijos','','',str(employee.children_number),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Correo Electrónico','','',(employee.work_email if employee.work_email else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Celular','','',(employee.work_phone if employee.work_phone else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Emergencias Llamar a','','','','','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(7,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			rowh     = [10]*row_pos
			rowh[0]  = 50
			t = Table(data, colWidths=[40,100,10,100,40,100,10,100],rowHeights=rowh,style=estilo)		
			elements.append(t)

			""" EMERGENCIA """
			if len(employee.emergency_id) > 0:
				data_em   = []
				estilo_em = []
				row_pos_em = 0

				estilo_em.append(('GRID',(0,0),(-1,-1),0.5,black))
				estilo_em.append(('VALIGN',(0,0),(-1,-1),'MIDDLE'))
				estilo_em.append(('ALIGN',(0,0),(-1,-1),'LEFT'))
				estilo_em.append(('FONTSIZE', (0, 0), (-1, -1), 8))
				estilo_em.append(('FONT', (0, 0), (-1,-1),'Arimo-Regular'))

				data_em.append([u'Nombre',u'Teléfono'])
				estilo_em.append(('ALIGN',(0,row_pos_em),(-1,row_pos_em),'CENTER'))
				estilo_em.append(('FONT',(0,row_pos_em),(-1,row_pos_em),'Arimo-Bold'))
				row_pos_em += 1

				for emergencia in employee.emergency_id:
					data_em.append([(emergencia.name if emergencia.name else ''),(emergencia.phone if emergencia.phone else '')])
					row_pos_em += 1

				rowh_em = [10]*row_pos_em
				t_em = Table(data_em, colWidths=[250,250],rowHeights=rowh_em,style=estilo_em)		
				elements.append(t_em)
			""" EMERGENCIA """

			data   = []
			estilo = []
			row_pos = 0

			# estilo.append(('GRID',(0,0),(-1,-1),0.5,black))
			estilo.append(('VALIGN',(0,0),(-1,-1),'MIDDLE'))
			estilo.append(('ALIGN',(0,0),(-1,-1),'CENTER'))
			estilo.append(('FONTSIZE', (0, 0), (-1, -1), 8))
			estilo.append(('FONT', (0, 0), (-1,-1),'Arimo-Regular'))

			data.append(['','','','','','','',''])
			row_pos += 1

			data.append(['','','','','','','',''])
			row_pos += 1

			data.append([u'IV. DATOS FAMILIARES','','','','','','',''])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('FONTSIZE', (0, row_pos), (-1, row_pos), 11))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append(['','','','','','','',''])
			row_pos += 1

			rowh = [10]*row_pos
			t = Table(data, colWidths=[40,100,10,100,40,100,10,100],rowHeights=rowh,style=estilo)		
			elements.append(t)

			""" DATOS FAMILIARES """
			if len(employee.familiar_id) > 0:
				data_fam    = []
				estilo_fam  = []
				row_pos_fam = 0

				estilo_fam.append(('GRID',(0,0),(-1,-1),0.5,black))
				estilo_fam.append(('VALIGN',(0,0),(-1,-1),'MIDDLE'))
				estilo_fam.append(('ALIGN',(0,0),(-1,-1),'LEFT'))
				estilo_fam.append(('FONTSIZE', (0, 0), (-1, -1), 8))
				estilo_fam.append(('FONT', (0, 0), (-1,-1),'Arimo-Regular'))

				data_fam.append(['Nro',u'Nombre',u'Parentesco',u'Fecha de Nacimiento',u'Edad',u'Documento'])
				estilo_fam.append(('ALIGN',(0,row_pos_fam),(-1,row_pos_fam),'CENTER'))
				estilo_fam.append(('FONT',(0,row_pos_fam),(-1,row_pos_fam),'Arimo-Bold'))
				row_pos_fam += 1

				n_ord = 1
				for familiar in employee.familiar_id:
					data_fam.append([str(n_ord),(familiar.name if familiar.name else ''),(familiar.relative if familiar.relative else ''),(familiar.birth_date if familiar.birth_date else ''),(familiar.age if familiar.age else ''),(familiar.documento if familiar.documento else '')])
					row_pos_fam += 1
					n_ord += 1

				rowh_fam = [10]*row_pos_fam
				t_fam = Table(data_fam, colWidths=[15,185,100,100,40,60],rowHeights=rowh_fam,style=estilo_fam)		
				elements.append(t_fam)
			""" DATOS FAMILIARES """

			data   = []
			estilo = []
			row_pos = 0

			estilo.append(('GRID',(0,3),(-1,21),0.5,black))
			estilo.append(('VALIGN',(0,0),(-1,-1),'MIDDLE'))
			estilo.append(('ALIGN',(0,0),(-1,-1),'CENTER'))
			estilo.append(('FONTSIZE', (0, 0), (-1, -1), 8))
			estilo.append(('FONT', (0, 0), (-1,-1),'Arimo-Regular'))

			data.append(['','','','','','','',''])
			row_pos += 1

			data.append([u'V. DATOS LABORALES','','','','','','',''])
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('FONTSIZE', (0, row_pos), (-1, row_pos), 11))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append(['','','','','','','',''])
			row_pos += 1

			data.append([u'Fecha de Ingreso','','',(employee.fecha_ingreso if employee.fecha_ingreso else ''),'',u'Fecha de Cese',':',(employee.fecha_cese if employee.fecha_cese else '')])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('FONT', (5,row_pos), (6,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('LINEBELOW',(7,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Area','','',(employee.department_id.name if employee.department_id.name else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Ubicación','','',(employee.ubicacion_id.name if employee.ubicacion_id.name else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Cargo / Ocupación','','',(employee.job_id.name if employee.job_id.name else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Tipo de Trabajador','','',(employee.tipo_trabajador.name if employee.tipo_trabajador.name else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Código Trabajador','','',(employee.codigo_trabajador if employee.codigo_trabajador else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Básico','','',(employee.basica if employee.basica else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Afiliación','','',(employee.afiliacion.name if employee.afiliacion.name else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Comisión Mixta','','',('SI' if employee.c_mixta else 'NO'),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'CUSSPP','','',(employee.cusspp if employee.cusspp else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Asignación Familiar','','',('SI' if employee.children_number > 0 else 'NO'),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'EsSalud Vida','','',('SI' if employee.essalud_vida else 'NO'),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Fondo de Jubilación','','',('SI' if employee.fondo_jub else 'NO'),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'AFP 2%','','',('SI' if employee.afp_2p else 'NO'),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Condición','','',(employee.condicion if employee.condicion else ''),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Practicante','','',('SI' if employee.is_practicant else 'NO'),'','','',''])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Nº Cuenta CTS','','',(employee.cta_cts if employee.cta_cts else ''),'','Banco',':',(employee.banco_cts if employee.banco_cts else '')])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('FONT', (5,row_pos), (6,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('LINEBELOW',(7,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			data.append([u'Nº Cuenta Remunerativa','','',(employee.cta_rem if employee.cta_rem else ''),'','Banco',':',(employee.banco_rem if employee.banco_rem else '')])
			estilo.append(('SPAN',(0,row_pos),(2,row_pos)))
			estilo.append(('FONT', (0,row_pos), (2,row_pos),'Arimo-Bold'))
			estilo.append(('FONT', (5,row_pos), (6,row_pos),'Arimo-Bold'))
			estilo.append(('SPAN',(3,row_pos),(4,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEBELOW',(3,row_pos),(4,row_pos),0.5,black))
			estilo.append(('LINEBELOW',(7,row_pos),(7,row_pos),0.5,black))
			estilo.append(('ALIGN',(0,row_pos),(-1,row_pos),'LEFT'))
			row_pos += 1

			comp_txt = u"<b>COMPROMISO:</b> Declaro bajo juramento que la información arriba consignada, es veraz y me comprometo a actualizarla en el momento que ocurra el evento (Mudanza, Gestación, Nacimiento, Fallecimiento, Nuevos Títulos), bajo absoluta responsabilidad para cualquier trámite que comprometa la veracidad de los datos declarados, por lo que autorizo a la empresa corrobore los datos."
			data.append([Paragraph("<font size=8>"+comp_txt+"</font>",styleN),'','','','','','',''])
			estilo.append(('SPAN',(0,row_pos),(7,row_pos)))
			row_pos += 1

			data.append([u'','',u'','','','','',''])			
			row_pos += 1

			data.append(['RR.HH.','',u'','','',u'Firma del Trabajador','',u'Huella Dactilar'])
			estilo.append(('FONT', (0,row_pos), (-1,row_pos),'Arimo-Bold'))
			estilo.append(('ALIGN', (0,row_pos), (-1,row_pos),'CENTER'))
			estilo.append(('SPAN',(0,row_pos),(1,row_pos)))
			estilo.append(('SPAN',(5,row_pos),(6,row_pos)))
			estilo.append(('LINEABOVE',(0,row_pos),(1,row_pos),0.5,black))
			estilo.append(('LINEABOVE',(5,row_pos),(5,row_pos),0.5,black))
			estilo.append(('LINEABOVE',(7,row_pos),(7,row_pos),0.5,black))
			row_pos += 1

			rowh = [10]*row_pos
			rowh[-3] = 40
			rowh[-2] = 60
			t = Table(data, colWidths=[40,100,10,100,40,100,10,100],rowHeights=rowh,style=estilo)
			elements.append(t)
			elements.append(PageBreak())
		doc.build(elements)

		reload(sys)
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		vals = {
			'output_name': title+'.pdf',
			'output_file': open(direccion + title +".pdf", "rb").read().encode("base64"),	
		}
		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type"     : "ir.actions.act_window",
			"res_model": "export.file.save",
			"views"    : [[False, "form"]],
			"res_id"   : sfs_id.id,
			"target"   : "new",
			"title_pdf": direccion+title+".pdf",
		}

class tipo_trabajador(models.Model):
	_name     = 'tipo.trabajador'
	_rec_name = 'name'

	name = fields.Char('nombre')

class hr_location(models.Model):
	_name     = 'hr.location'
	_rec_name = 'name'

	name = fields.Char('nombre')