# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

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
class export_file_save(osv.TransientModel):
	_name = 'export.file.save'	
	
	output_name = fields.Char('Output filename', size=128)
	output_file = fields.Binary('Output file', readonly=True, filename="output_name")

class account_move_line_book_wizard(osv.TransientModel):
	_name='account.move.line.book.wizard'
	
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	asientos =  fields.Selection([('posted','Asentados'),('draft','No Asentados'),('both','Ambos')], 'Asientos')
	moneda = fields.Many2one('res.currency','Moneda')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')], 'Mostrar en', required=True)
	libros = fields.Many2many('account.journal','account_book_journal_rel','id_book_origen','id_journal_destino', string='Libros', required=True)


	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)



	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'period_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )], 'period_end':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'period_ini':[], 'period_end':[]}}

	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini
			
		parameters = self.env['main.parameter'].search([])
		if len(parameters) == 0:
			raise osv.except_osv('Alerta!', "No existe el objeto parametros en su sistema. Contacte a su administrador.")
		parameter = parameters[0]
		
		#Coloco la moneda configurada de divisa extranjera
		ids = []
		ids.append(parameter.currency_id.id)
		
		#Coloco la moneda configurada de divisa extranjera
		user = self.env['res.users'].browse(self.env.uid)
		if user.company_id.id == False:
			raise osv.except_osv('Alerta!', "No existe una compañia configurada para el usuario actual.")
		if user.company_id.currency_id.id == False:
			raise osv.except_osv('Alerta!', "No existe una moneda configurada para la compañia del usuario actual.")
		ids.append(user.company_id.currency_id.id)
		#self.moneda = ids
		moneda_domain = [
			('id', 'in', ids)
		]
		result = {
			'domain': {
				'moneda': moneda_domain,
			},
		}
		return result	


	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		has_currency = self.moneda
		
		filtro = []
		
		currency = False
		if has_currency.id != False:
			user = self.env['res.users'].browse(self.env.uid)
			if user.company_id.id == False:
				raise osv.except_osv('Alerta!', "No existe una compañia configurada para el usuario actual.")
			if user.company_id.currency_id.id == False:
				raise osv.except_osv('Alerta!', "No existe una moneda configurada para la compañia del usuario actual.")

			if has_currency.id != user.company_id.currency_id.id:
				currency = True
			
		self.env.cr.execute("""
			CREATE OR REPLACE view account_move_line_book as (
				SELECT * 
				FROM get_libro_diario("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
		)""")

		if self.asientos:
			if self.asientos == 'posted':
				filtro.append( ('statefiltro','=','posted') )
			if self.asientos == 'draft':
				filtro.append( ('statefiltro','=','draft') )
		
		if self.libros:
			libros_list = []
			for i in  self.libros:
				libros_list.append(i.code)
			filtro.append( ('libro','in',tuple(libros_list)) )
		
		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_contable_book_it', 'action_account_moves_all_it')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.move.line.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'res_id': id,
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_librodiario.xlsx')
			worksheet = workbook.add_worksheet("Libro Diario")
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
			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, "Libro Diario:", bold)
			tam_col[0] = tam_letra* len("Libro Diario:") if tam_letra* len("Libro Diario:")> tam_col[0] else tam_col[0]

			worksheet.write(0,1, self.period_ini.name, normal)
			tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

			worksheet.write(0,2, self.period_end.name, normal)
			tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

			worksheet.write(1,0, "Fecha:",bold)
			tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(1,1, str(datetime.datetime.today())[:10], normal)
			tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
			

			worksheet.write(3,0, "Periodo",boldbord)
			tam_col[0] = tam_letra* len("Periodo") if tam_letra* len("Periodo")> tam_col[0] else tam_col[0]
			worksheet.write(3,1, "Libro",boldbord)
			tam_col[1] = tam_letra* len("Libro") if tam_letra* len("Libro")> tam_col[1] else tam_col[1]
			worksheet.write(3,2, "Voucher",boldbord)
			tam_col[2] = tam_letra* len("Voucher") if tam_letra* len("Voucher")> tam_col[2] else tam_col[2]
			worksheet.write(3,3, "Cuenta",boldbord)
			tam_col[3] = tam_letra* len("Cuenta") if tam_letra* len("Cuenta")> tam_col[3] else tam_col[3]
			worksheet.write(3,4, "Debe",boldbord)
			tam_col[4] = tam_letra* len("Debe") if tam_letra* len("Debe")> tam_col[4] else tam_col[4]
			worksheet.write(3,5, "Haber",boldbord)
			tam_col[5] = tam_letra* len("Haber") if tam_letra* len("Haber")> tam_col[5] else tam_col[5]
			worksheet.write(3,6, "Divisa",boldbord)
			tam_col[6] = tam_letra* len("Divisa") if tam_letra* len("Divisa")> tam_col[6] else tam_col[6]
			worksheet.write(3,7, "Tipo Cambio",boldbord)
			tam_col[7] = tam_letra* len("Tipo Cambio") if tam_letra* len("Tipo Cambio")> tam_col[7] else tam_col[7]
			worksheet.write(3,8, "Importe Divisa",boldbord)
			tam_col[8] = tam_letra* len("Importe Divisa") if tam_letra* len("Importe Divisa")> tam_col[8] else tam_col[8]
			worksheet.write(3,9, u"Código",boldbord)
			tam_col[9] = tam_letra* len(u"Código") if tam_letra* len(u"Código")> tam_col[9] else tam_col[9]
			worksheet.write(3,10, "Partner",boldbord)
			tam_col[10] = tam_letra* len("Partner") if tam_letra* len("Partner")> tam_col[10] else tam_col[10]
			worksheet.write(3,11, "Tipo Documento",boldbord)
			tam_col[11] = tam_letra* len("Tipo Documento") if tam_letra* len("Tipo Documento")> tam_col[11] else tam_col[11]
			worksheet.write(3,12, u"Número",boldbord)
			tam_col[12] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[12] else tam_col[12]
			worksheet.write(3,13, u"Fecha Emisión",boldbord)
			tam_col[13] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[13] else tam_col[13]
			worksheet.write(3,14, "Fecha Vencimiento",boldbord)
			tam_col[14] = tam_letra* len("Fecha Vencimiento") if tam_letra* len("Fecha Vencimiento")> tam_col[14] else tam_col[14]
			worksheet.write(3,15, "Glosa",boldbord)
			tam_col[15] = tam_letra* len("Glosa") if tam_letra* len("Glosa")> tam_col[15] else tam_col[15]
			worksheet.write(3,16, u"Cta. Analítica",boldbord)
			tam_col[16] = tam_letra* len(u"Cta. Analítica") if tam_letra* len(u"Cta. Analítica")> tam_col[16] else tam_col[16]
			worksheet.write(3,17, u"Referencia Conciliación",boldbord)
			tam_col[17] = tam_letra* len(u"Referencia Conciliación") if tam_letra* len(u"Referencia Conciliación")> tam_col[17] else tam_col[17]

			worksheet.write(3,18, u"Estado",boldbord)
			tam_col[18] = tam_letra* len(u"Estado") if tam_letra* len(u"Estado")> tam_col[18] else tam_col[18]

			for line in self.env['account.move.line.book'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.cuenta if line.cuenta  else '',bord)
				worksheet.write(x,4,line.debe ,numberdos)
				worksheet.write(x,5,line.haber ,numberdos)
				worksheet.write(x,6,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,7,line.tipodecambio ,numbertres)
				worksheet.write(x,8,line.importedivisa ,numberdos)
				worksheet.write(x,9,line.codigo if line.codigo else '',bord)
				worksheet.write(x,10,line.partner if line.partner else '',bord)
				worksheet.write(x,11,line.tipodocumento if line.tipodocumento else '',bord)
				worksheet.write(x,12,line.numero if line.numero  else '',bord)
				worksheet.write(x,13,line.fechaemision if line.fechaemision else '',bord)
				worksheet.write(x,14,line.fechavencimiento if line.fechavencimiento else '',bord)
				worksheet.write(x,15,line.glosa if line.glosa else '',bord)
				worksheet.write(x,16,line.ctaanalitica if line.ctaanalitica  else '',bord)
				worksheet.write(x,17,line.refconcil if line.refconcil  else '',bord)
				worksheet.write(x,18,line.state if line.state  else '',bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.cuenta if line.cuenta  else '') if tam_letra* len(line.cuenta if line.cuenta  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len("%0.2f"%line.debe ) if tam_letra* len("%0.2f"%line.debe )> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len("%0.2f"%line.haber ) if tam_letra* len("%0.2f"%line.haber )> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len(line.divisa if  line.divisa else '') if tam_letra* len(line.divisa if  line.divisa else '')> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len("%0.3f"%line.tipodecambio ) if tam_letra* len("%0.3f"%line.tipodecambio )> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len("%0.2f"%line.importedivisa ) if tam_letra* len("%0.2f"%line.importedivisa )> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len(line.codigo if line.codigo else '') if tam_letra* len(line.codigo if line.codigo else '')> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len(line.partner if line.partner else '') if tam_letra* len(line.partner if line.partner else '')> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len(line.glosa if line.glosa else '') if tam_letra* len(line.glosa if line.glosa else '')> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '') if tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '')> tam_col[16] else tam_col[16]
				tam_col[17] = tam_letra* len(line.refconcil if line.refconcil  else '') if tam_letra* len(line.refconcil if line.refconcil  else '')> tam_col[17] else tam_col[17]
				tam_col[18] = tam_letra* len(line.state if line.state  else '') if tam_letra* len(line.state if line.state  else '')> tam_col[18] else tam_col[18]
				x = x +1


			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10]

			worksheet.set_row(3, 60)
			
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

			workbook.close()
			
			f = open( direccion + 'tempo_librodiario.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'LibroDiario.xlsx',
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
		c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DIARIO DEL MES DE ENERO ***")
		c.setFont("Times-Bold", 10)
		c.drawString(30,hReal, "IT GRUPO")
		c.setFont("Times-Roman", 8)
		c.drawString(30,hReal-12, "AV. LOS PROCERES N")
		c.setFont("Times-Roman", 8)
		c.drawString(500,hReal-12, "24/07/2015")
		c.setFont("Times-Roman", 8)
		c.drawString(30,hReal-24, "MIRAFLORES")
		c.drawString(30,hReal-36, "204550496587")
		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
		    "<font size=7><b>Nº CORREL. ASNTO COD. UNI. DE OPER</b></font>",
		    style
		)
		paragraph2 = Paragraph(
		    "<font size=7><b>FECHA DE LA OPERACION</b></font>",
		    style
		)
		paragraph3 = Paragraph(
		    "<font size=7><b>GLOSA O DESCRIPCION DE LA OPERACION</b></font>",
		    style
		)
		paragraph4 = Paragraph(
		    "<font size=7><b>CUENTA CONTABLE ASOCIADA A LA OPERACION</b></font>",
		    style
		)
		paragraph5 = Paragraph(
		    "<font size=7><b>MOVIMIENTO</b></font>",
		    style
		)
		paragraph6 = Paragraph(
		    "<font size=7><b>CODIGO</b></font>",
		    style
		)
		paragraph7 = Paragraph(
		    "<font size=7><b>DENOMINACION</b></font>",
		    style
		)
		paragraph8 = Paragraph(
		    "<font size=7><b>DEBE</b></font>",
		    style
		)
		paragraph9 = Paragraph(
		    "<font size=7><b>HABER</b></font>",
		    style
		)
		data= [[ paragraph1 , paragraph2 , paragraph3 , paragraph4,'', paragraph5 ,''],
		['', '', '', paragraph6,paragraph7 ,paragraph8,paragraph9]]
		t=Table(data,colWidths=(75, 70, 95, 90, 90, 60, 60), rowHeights=(20,13))
		t.setStyle(TableStyle([
			('SPAN',(0,0),(0,1)),
			('SPAN',(1,0),(1,1)),
			('SPAN',(2,0),(2,1)),
			('SPAN',(3,0),(4,0)),
			('SPAN',(5,0),(6,0)),
			('GRID',(0,0),(-1,-1), 1, colors.black),
			('ALIGN',(0,0),(-1,-1),'CENTER'),
			('VALIGN',(0,0),(-1,-1),'MIDDLE'),
			('TEXTFONT', (0, 0), (-1, -1), 'Times-Bold'),
			('FONTSIZE',(0,0),(-1,-1),7)
		]))
		t.wrapOn(c,30,500)
		t.drawOn(c,30,hReal-85)


	@api.multi
	def reporteador(self,listobjetos):

		import sys
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		wReal = width- 30
		hReal = height - 40
		c = canvas.Canvas("a.pdf", pagesize=A4)
		inicio = 0
		pos_inicial = hReal-100
		libro = None
		voucher = None
		total = 0
		debeTotal = 0
		haberTotal = 0
		pagina = 1
		textPos = 0
		
		tamanios = {}
		voucherTamanio = None
		contTamanio = 0
		for i in listobjetos:
			if voucherTamanio != i.am_id:
				if voucherTamanio != None:
					tamanios[voucherTamanio] = contTamanio
				voucherTamanio = i.am_id
				contTamanio= 0
			contTamanio+= 1
		tamanios[voucherTamanio] = contTamanio

		for i in listobjetos:
			if inicio == 0:
				self.cabezera(c,wReal,hReal)

				c.setFont("Times-Bold", 8)
				c.drawCentredString(300,25,'Pág. ' + str(pagina))
				inicio +=1

			if voucher != i.am_id:
				if voucher != None:
					textPos = 0
					verpag = pagina
					pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,20,pagina)
					if pagina==verpag:
						c.setFont("Times-Bold", 8)
						c.line(450,pos_inicial+25,570,pos_inicial+25)
						c.drawString(400,pos_inicial+10, "TOTAL:")
						c.drawRightString(510,pos_inicial+10, "%0.2f" %(debeTotal))
						c.drawRightString(570,pos_inicial+10, "%0.2f" %(haberTotal))
						debeTotal=0
						haberTotal= 0
					else:
						c.setFont("Times-Bold", 8)
						c.line(450,pos_inicial,570,pos_inicial)
						c.drawString(400,pos_inicial-10, "TOTAL:")
						c.drawRightString(510,pos_inicial-10, "%0.2f" %(debeTotal))
						c.drawRightString(570,pos_inicial-10, "%0.2f" %(haberTotal))
						debeTotal=0
						haberTotal= 0
						pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)

				have_space = 35
				if libro!= i.aj_id:
					have_space +=10
				have_space += tamanios[i.am_id]*10
				pagina,pos_inicial = self.verify_space(c,wReal,hReal,pos_inicial,have_space,pagina)

				if libro != i.aj_id:
					libro = i.aj_id
					c.setFont("Times-Roman", 8)
					c.drawString(35,pos_inicial, unicode(libro.code))
					c.drawString(60,pos_inicial, unicode(libro.name))
					pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)

				voucher = i.am_id
				c.setFont("Times-Roman", 8)
				c.drawString(30,pos_inicial, str(escape("Nº de Vou.: "+unicode(voucher.name))))
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)

			if textPos % 2 == 1:
				fondo = HexColor('#d1d1d1')
				c.setFillColor(fondo)
				c.rect(30,pos_inicial-2,540,9,fill=True,stroke=False)
				c.setFillColor(black)
			textPos +=1
			c.setFont("Times-Roman", 8)
			c.drawString(30,pos_inicial, unicode(i.am_id.name))
			c.drawString(105,pos_inicial, unicode(i.fechaemision))
			if i.glosa:
				c.drawString(175,pos_inicial, unicode(self.particionar_text(i.glosa)))
			c.drawString(270,pos_inicial, unicode(i.aa_id.code))
			lines = simpleSplit(i.aa_id.name,'Times-Roman',8,90)
			print lines
			c.drawString(360,pos_inicial, unicode(i.aa_id.name).split('-')[0])
			debe = i.debe
			haber = i.haber
			if not debe:
				debe= 0.0
			if not haber:
				haber = 0.0
			c.drawRightString(510,pos_inicial, "%0.2f" %debe)
			c.drawRightString(570,pos_inicial, "%0.2f" %haber)
			pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)
			debeTotal += debe
			haberTotal += haber

		if voucher != None:
			verpag = pagina
			pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,20,pagina)
			if pagina==verpag:
				c.setFont("Times-Bold", 8)
				c.line(450,pos_inicial+25,570,pos_inicial+25)
				c.drawString(400,pos_inicial+10, "TOTAL:")
				c.drawRightString(510,pos_inicial+10, "%0.2f" %(debeTotal))
				c.drawRightString(570,pos_inicial+10, "%0.2f" %(haberTotal))
				debeTotal=0
				haberTotal= 0
			else:
				c.setFont("Times-Bold", 8)
				c.line(450,pos_inicial,570,pos_inicial)
				c.drawString(400,pos_inicial-10, "TOTAL:")
				c.drawRightString(510,pos_inicial-10, "%0.2f" %(debeTotal))
				c.drawRightString(570,pos_inicial-10, "%0.2f" %(haberTotal))
				debeTotal=0
				haberTotal= 0
				pagina,pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)


		c.save()

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
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 8)
			c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-100
		else:
			return pagina,posactual-valor
	@api.multi
	def verify_space(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual-valor <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 8)
			c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-100
		else:
			return pagina,posactual



	@api.multi
	def csv_verif_integer(self,data):
		if data:
			return '"' + str(data) + '"'
		else:
			return '""'

	@api.multi
	def csv_verif(self,data):
		if data:
			return '"' + data.replace('"','\'') + '"'
		else:
			return '""'
	@api.multi
	def csv_convert(self,data,separador):
		tmp = self.csv_verif(data.periodo)
		tmp += separador+ self.csv_verif(data.libro)
		tmp += separador+ self.csv_verif(data.voucher)
		tmp += separador+ self.csv_verif(data.cuenta)
		tmp += separador+ self.csv_verif_integer(data.debe)
		tmp += separador+ self.csv_verif_integer(data.haber)
		tmp += separador+ self.csv_verif(data.divisa)
		tmp += separador+ self.csv_verif_integer(data.tipodecambio)
		tmp += separador+ self.csv_verif_integer(data.importedivisa)
		tmp += separador+ self.csv_verif(data.codigo)
		tmp += separador+ self.csv_verif(data.partner)
		tmp += separador+ self.csv_verif(data.tipodocumento)
		tmp += separador+ self.csv_verif(data.numero)
		tmp += separador+ self.csv_verif(data.fechaemision)
		tmp += separador+ self.csv_verif(data.fechavencimiento)
		tmp += separador+ self.csv_verif(data.glosa)
		tmp += separador+ self.csv_verif(data.ctaanalitica) 
		tmp += separador+ self.csv_verif(data.refconcil )
		tmp += separador
		return unicode(tmp)


	@api.multi
	def cabezera_csv(self,separador):		
		tmp = self.csv_verif("Periodo")
		tmp += separador+ self.csv_verif("Libro")
		tmp += separador+ self.csv_verif("Voucher")
		tmp += separador+ self.csv_verif("Cuenta")
		tmp += separador+ self.csv_verif("Debe")
		tmp += separador+ self.csv_verif("Haber")
		tmp += separador+ self.csv_verif("Divisa")
		tmp += separador+ self.csv_verif("Tipo de Cambio")
		tmp += separador+ self.csv_verif("Importe Divisa")
		tmp += separador+ self.csv_verif("Codigo")
		tmp += separador+ self.csv_verif("Partner")
		tmp += separador+ self.csv_verif("Tipo de Documento")
		tmp += separador+ self.csv_verif("Num. Documento")
		tmp += separador+ self.csv_verif("Fecha Emision")
		tmp += separador+ self.csv_verif("Fecha Vencimiento")
		tmp += separador+ self.csv_verif("Glosa")
		tmp += separador+ self.csv_verif("Analitica")
		tmp += separador+ self.csv_verif("Ref. Conciliacion")
		tmp += separador
		return tmp
