# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

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
import decimal

class costeo_it(models.Model):
	_inherit = 'costeo.it'


	@api.multi
	def do_rebuild(self):

		if True:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			
			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'costeolote.xlsx')
			worksheet = workbook.add_worksheet("Costeo Lote")
			worksheet_manual = workbook.add_worksheet("Costeo Manual")
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

			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			worksheet.set_row(0, 30)
			worksheet_manual.set_row(0, 30)

			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,10, u"Costeo Lote", title)

			worksheet.write(2,0, u"Periodo", bold)
			worksheet.write(2,1, self.periodo.code, normal)


			worksheet.write(4,0, "Lote",boldbord)
			worksheet.write(4,1, "Producto",boldbord)
			worksheet.write(4,2, "Tn.S",boldbord)
			worksheet.write(4,3, u"Zona",boldbord)
			worksheet.write(4,4, u"Costo Oro",boldbord)
			worksheet.write(4,5, u"Costo Plata",boldbord)
			worksheet.write(4,6, "Costo Chancado",boldbord)
			worksheet.write(4,7, "Costo Zona",boldbord)
			worksheet.write(4,8, "Costo Expediente",boldbord)
			worksheet.write(4,9, "Gastos generales",boldbord)
			worksheet.write(4,10, "Total Costo",boldbord)
			worksheet.write(4,11, "P. Unit",boldbord)



			worksheet_manual.merge_range(0,0,0,10, u"Costeo Lote Manual", title)

			worksheet_manual.write(2,0, u"Periodo", bold)
			worksheet_manual.write(2,1, self.periodo.code, normal)


			worksheet_manual.write(4,0, "Lote",boldbord)
			worksheet_manual.write(4,1, "Producto",boldbord)
			worksheet_manual.write(4,2, "Tn.S",boldbord)
			worksheet_manual.write(4,3, u"Zona",boldbord)
			worksheet_manual.write(4,4, u"Costo Oro",boldbord)
			worksheet_manual.write(4,5, u"Costo Plata",boldbord)
			worksheet_manual.write(4,6, "Costo Chancado",boldbord)
			worksheet_manual.write(4,7, "Costo Zona",boldbord)
			worksheet_manual.write(4,8, "Costo Expediente",boldbord)
			worksheet_manual.write(4,9, "Gastos generales",boldbord)
			worksheet_manual.write(4,10, "Total Costo",boldbord)
			worksheet_manual.write(4,11, "P. Unit",boldbord)



			for line in self.lineas:
				worksheet.write(x,0,line.lote.name if line.lote.id else '',bord )
				worksheet.write(x,1,line.producto.name if line.producto.id else '' ,bord)
				worksheet.write(x,2,line.toneladas_secas ,numberdos)
				worksheet.write(x,3,line.zona.name if line.zona.id else '',numberdos)
				worksheet.write(x,4,line.costo_oro,numberdos)
				worksheet.write(x,5,line.costo_plata,numberdos)
				worksheet.write(x,6,line.costo_chancado,numberdos)
				worksheet.write(x,7,line.costo_zona,numberdos)
				worksheet.write(x,8,line.costo_expediente,numberdos)
				worksheet.write(x,9,line.gastos_generales,numberdos)
				worksheet.write(x,10,line.total_costo,numberdos)
				worksheet.write(x,11,line.p_unit,numberdos)
				x = x +1



			x= 5
			for line in self.lineas_editable:
				worksheet_manual.write(x,0,line.lote.name if line.lote.id else '',bord )
				worksheet_manual.write(x,1,line.producto.name if line.producto.id else '' ,bord)
				worksheet_manual.write(x,2,line.toneladas_secas ,numberdos)
				worksheet_manual.write(x,3,line.zona.name if line.zona.id else '',numberdos)
				worksheet_manual.write(x,4,line.costo_oro,numberdos)
				worksheet_manual.write(x,5,line.costo_plata,numberdos)
				worksheet_manual.write(x,6,line.costo_chancado,numberdos)
				worksheet_manual.write(x,7,line.costo_zona,numberdos)
				worksheet_manual.write(x,8,line.costo_expediente,numberdos)
				worksheet_manual.write(x,9,line.gastos_generales,numberdos)
				worksheet_manual.write(x,10,line.total_costo,numberdos)
				worksheet_manual.write(x,11,line.p_unit,numberdos)
				x = x +1

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
			
			f = open(direccion + 'costeolote.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'CosteoLote.xlsx',
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




class armado_ruma_line(models.Model):
	_inherit = 'armado.ruma.line'

	@api.one
	def get_f_costo_oro(self):
		t = self.env['costeo.line.it'].search([('lote','=',self.nro_lote.id),('padre','!=',False)])
		if len(t)>0:
			t = t[0]
		self.f_costo_oro = t.costo_oro


	@api.one
	def get_f_costo_plata(self):
		t = self.env['costeo.line.it'].search([('lote','=',self.nro_lote.id),('padre','!=',False)])
		if len(t)>0:
			t = t[0]
		self.f_costo_plata = t.costo_plata

	@api.one
	def get_f_costo_chancado(self):
		t = self.env['costeo.line.it'].search([('lote','=',self.nro_lote.id),('padre','!=',False)])
		if len(t)>0:
			t = t[0]
		self.f_costo_chancado = t.costo_chancado

	@api.one
	def get_f_costo_zona(self):
		t = self.env['costeo.line.it'].search([('lote','=',self.nro_lote.id),('padre','!=',False)])
		if len(t)>0:
			t = t[0]
		self.f_costo_zona = t.costo_zona

	@api.one
	def get_f_costo_expediente(self):
		t = self.env['costeo.line.it'].search([('lote','=',self.nro_lote.id),('padre','!=',False)])
		if len(t)>0:
			t = t[0]
		self.f_costo_expediente = t.costo_expediente

	@api.one
	def get_f_gastos_generales(self):
		t = self.env['costeo.line.it'].search([('lote','=',self.nro_lote.id),('padre','!=',False)])
		if len(t)>0:
			t = t[0]
		self.f_gastos_generales = t.gastos_generales

	@api.one
	def get_f_total_costo(self):
		t = self.env['costeo.line.it'].search([('lote','=',self.nro_lote.id),('padre','!=',False)])
		if len(t)>0:
			t = t[0]
		self.f_total_costo = t.total_costo

	f_costo_oro = fields.Float('Costo Oro',compute="get_f_costo_oro")
	f_costo_plata = fields.Float('Costo Plata',digits=(12,8),compute="get_f_costo_plata")
	f_costo_chancado = fields.Float('Costo Chancado',digits=(12,8),compute="get_f_costo_chancado")	
	f_costo_zona = fields.Float('Costo Zona',digits=(12,8),compute="get_f_costo_zona")
	f_costo_expediente = fields.Float('Costo Expediente',digits=(12,8),compute="get_f_costo_expediente")
	f_gastos_generales = fields.Float('Gastos generales',digits=(12,8),compute="get_f_gastos_generales")
	f_total_costo = fields.Float('Total Costo',digits=(12,8),compute="get_f_total_costo")

	
class armado_ruma(models.Model):
	_inherit = 'armado.ruma'	

	@api.multi
	def do_rebuild(self):

		if True:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			
			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'armadoruma.xlsx')
			worksheet = workbook.add_worksheet("Armado Ruma")
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

			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			worksheet.set_row(0, 30)

			x= 8				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,10, u"Armado Ruma", title)


			worksheet.write(2,0, u"Números de Ruma", bold)
			worksheet.write(2,1, self.name, normal)

			worksheet.write(3,0, u"Categoría", bold)
			worksheet.write(3,1, self.categoria_id.name if self.categoria_id.id else '', normal)

			worksheet.write(4,0, u"Toneladas", bold)
			worksheet.write(4,1, self.toneladas, normal)

			worksheet.write(5,0, u"Expectativa Oro", bold)
			worksheet.write(5,1, self.oro_expectativa, normal)

			worksheet.write(2,5, u"Fecha Creación", bold)
			worksheet.write(2,6, self.fecha_creacion, normal)

			worksheet.write(3,5, u"Total Costo Armado", bold)
			worksheet.write(3,6, self.total_costo_armado, normal)

			worksheet.write(4,5, u"Periodo", bold)
			worksheet.write(4,6, self.period_id.code, normal)


			worksheet.write(7,0, "Nro de Lote",boldbord)
			worksheet.write(7,1, "Producto",boldbord)
			worksheet.write(7,2, "Tn.",boldbord)
			worksheet.write(7,3, u"Valor",boldbord)
			worksheet.write(7,4, "Costo Oro",boldbord)
			worksheet.write(7,5, "Costo Plata",boldbord)
			worksheet.write(7,6, "Costo Chancado",boldbord)
			worksheet.write(7,7, "Costo Zona",boldbord)
			worksheet.write(7,8, "Costo Expediente",boldbord)
			worksheet.write(7,9, "Gastos Generales",boldbord)
			worksheet.write(7,10, u"Total Costo",boldbord)


			for line in self.lines:
				worksheet.write(x,0,line.nro_lote.name if line.nro_lote.id else '',bord )
				worksheet.write(x,1,line.product_id.name if line.product_id.id  else '',bord)
				worksheet.write(x,2,line.tn ,numberdos)
				worksheet.write(x,3,line.valor,numberdos)

				worksheet.write(x,4,line.f_costo_oro,numberdos)
				worksheet.write(x,5,line.f_costo_plata,numberdos)
				worksheet.write(x,6,line.f_costo_chancado,numberdos)
				worksheet.write(x,7,line.f_costo_zona,numberdos)
				worksheet.write(x,8,line.f_costo_expediente,numberdos)
				worksheet.write(x,9,line.f_gastos_generales,numberdos)
				worksheet.write(x,10,line.f_total_costo,numberdos)

				x = x +1

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
			
			f = open(direccion + 'armadoruma.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'ArmadoRuma.xlsx',
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





class costeo_ruma_linea(models.Model):
	_inherit = 'costeo.ruma.linea'


	@api.one
	def get_f_costo_oro(self):
		t = self.env['armado.ruma'].search([('id','=',self.ruma_id.id)])
		tmp = 0
		if len(t)>0:
			t = t[0]
			for i in t.lines:
				tmp+= i.f_costo_oro
		self.f_costo_oro = tmp


	@api.one
	def get_f_costo_plata(self):
		t = self.env['armado.ruma'].search([('id','=',self.ruma_id.id)])
		tmp = 0
		if len(t)>0:
			t = t[0]
			for i in t.lines:
				tmp+= i.f_costo_plata
		self.f_costo_plata = tmp

	@api.one
	def get_f_costo_chancado(self):
		t = self.env['armado.ruma'].search([('id','=',self.ruma_id.id)])
		tmp = 0
		if len(t)>0:
			t = t[0]
			for i in t.lines:
				tmp+= i.f_costo_chancado
		self.f_costo_chancado = tmp

	@api.one
	def get_f_costo_zona(self):
		t = self.env['armado.ruma'].search([('id','=',self.ruma_id.id)])
		tmp = 0
		if len(t)>0:
			t = t[0]
			for i in t.lines:
				tmp+= i.f_costo_zona
		self.f_costo_zona = tmp

	@api.one
	def get_f_costo_expediente(self):
		t = self.env['armado.ruma'].search([('id','=',self.ruma_id.id)])
		tmp = 0
		if len(t)>0:
			t = t[0]
			for i in t.lines:
				tmp+= i.f_costo_expediente
		self.f_costo_expediente = tmp

	@api.one
	def get_f_gastos_generales(self):
		t = self.env['armado.ruma'].search([('id','=',self.ruma_id.id)])
		tmp = 0
		if len(t)>0:
			t = t[0]
			for i in t.lines:
				tmp+= i.f_gastos_generales
		self.f_gastos_generales = tmp

	@api.one
	def get_f_total_costo(self):
		t = self.env['armado.ruma'].search([('id','=',self.ruma_id.id)])
		tmp = 0
		if len(t)>0:
			t = t[0]
			for i in t.lines:
				tmp+= i.f_total_costo

		tmp += self.gastos_armados
		self.f_total_costo = tmp

	f_costo_oro = fields.Float('Costo Oro',compute="get_f_costo_oro")
	f_costo_plata = fields.Float('Costo Plata',digits=(12,8),compute="get_f_costo_plata")
	f_costo_chancado = fields.Float('Costo Chancado',digits=(12,8),compute="get_f_costo_chancado")	
	f_costo_zona = fields.Float('Costo Zona',digits=(12,8),compute="get_f_costo_zona")
	f_costo_expediente = fields.Float('Costo Expediente',digits=(12,8),compute="get_f_costo_expediente")
	f_gastos_generales = fields.Float('Gastos generales',digits=(12,8),compute="get_f_gastos_generales")
	f_total_costo = fields.Float('Total Costo',digits=(12,8),compute="get_f_total_costo")



class costeo_ruma(models.Model):
	_inherit= 'costeo.ruma'
	
	@api.one
	def calcular(self):
		total_tone = 0
		total_gasto = 0
		for i in self.lineas:
			total_tone += i.toneladas

		cuentas = [0,0,0,0,0]
		for i in self.cuentas:
			cuentas.append(i.id)

		self.env.cr.execute("""
			select debit - credit as monto from account_move am 
			inner join account_move_line aml on aml.move_id = am.id
			inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
			where aaa.id in """ + str(tuple(cuentas)) + """ and am.period_id = """ + str(self.periodo.id) + """ and am.state != 'done'
		 """)

		for i in self.env.cr.fetchall():
			total_gasto += i[0]

		for i in self.lineas:
			i.factor = i.toneladas / total_tone if total_tone != 0 else 0
			i.refresh()
			i.gastos_armados = i.factor * total_gasto
			i.refresh()
			i.total = i.valor_materia_prima + i.gastos_armados
			i.refresh()
			i.p_unit = i.total / i.toneladas if i.toneladas != 0 else 0
			i.refresh()

			for w in i.ruma_id.picking_2.move_lines:
				print i.f_total_costo, 'revision', w.id
				w.precio_unitario_manual = i.f_total_costo

				
	@api.multi
	def do_rebuild(self):

		if True:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			
			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'costeoruma.xlsx')
			worksheet = workbook.add_worksheet("Costeo Ruma")
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

			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			worksheet.set_row(0, 30)

			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,10, u"Costeo Ruma", title)

			worksheet.write(2,0, u"Periodo", bold)
			worksheet.write(2,1, self.periodo.code, normal)


			worksheet.write(4,0, "Ruma",boldbord)
			worksheet.write(4,1, "Toneladas",boldbord)
			worksheet.write(4,2, "VMP",boldbord)
			worksheet.write(4,3, u"Factor",boldbord)
			worksheet.write(4,4, u"Gastos Armado",boldbord)
			worksheet.write(4,5, u"Total",boldbord)
			worksheet.write(4,6, "Costo Oro",boldbord)
			worksheet.write(4,7, "Costo Plata",boldbord)
			worksheet.write(4,8, "Costo Chancado",boldbord)
			worksheet.write(4,9, "Costo Zona",boldbord)
			worksheet.write(4,10, "Costo Expediente",boldbord)
			worksheet.write(4,11, "Gastos Generales",boldbord)
			worksheet.write(4,12, u"Total Costo",boldbord)


			for line in self.lineas:
				worksheet.write(x,0,line.ruma_id.name if line.ruma_id.id else '',bord )
				worksheet.write(x,1,line.toneladas ,numberdos)
				worksheet.write(x,2,line.valor_materia_prima ,numberdos)
				worksheet.write(x,3,line.factor,numberdos)
				worksheet.write(x,4,line.gastos_armados,numberdos)
				worksheet.write(x,5,line.total,numberdos)
				worksheet.write(x,6,line.f_costo_oro,numberdos)
				worksheet.write(x,7,line.f_costo_plata,numberdos)
				worksheet.write(x,8,line.f_costo_chancado,numberdos)
				worksheet.write(x,9,line.f_costo_zona,numberdos)
				worksheet.write(x,10,line.f_costo_expediente,numberdos)
				worksheet.write(x,11,line.f_gastos_generales,numberdos)
				worksheet.write(x,12,line.f_total_costo,numberdos)
				x = x +1

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
			
			f = open(direccion + 'costeoruma.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'CosteoRuma.xlsx',
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



