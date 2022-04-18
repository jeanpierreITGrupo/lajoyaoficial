# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
import decimal
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, white, HexColor
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


class grilla_producto_proceso_it(models.Model):
	_name = 'grilla.producto.proceso.it'

	rubro 		= fields.Char('Rubro')
	monto 		= fields.Float('Monto')
	proceso_id 	= fields.Many2one('producto.proceso.it','Producto Proceso')


class producto_proceso_it(models.Model):
	_name = 'producto.proceso.it'

	lote_proceso 			= fields.Char('Lote Producto en Proceso')
	periodo 				= fields.Many2one('account.period','Periodo')
	fecha 					= fields.Date('Fecha')
	producto 				= fields.Many2one('product.product','Producto')
	nro_campana 			= fields.Char(u'Nro. Campaña')
	nro_barra_tanque 		= fields.Char('Nro Barra o Tanque')
	unidad_medida 			= fields.Many2one('product.uom','Unidad de Medida')
	peso_barra 				= fields.Float('Peso Barra o Solucion',digits=(12,2))
	au 						= fields.Float('% AU',digits=(12,2))
	ag 						= fields.Float('% AG',digits=(12,2))
	au_gramo 				= fields.Float('Au Fino Gramos',digits=(12,2))
	ag_gramo 				= fields.Float('Ag Fino Gramos',digits=(12,2))
	costo_gr 				= fields.Float('Costo Und. Gr.',digits=(12,2))
	costo_total 			= fields.Float('Costo Total',digits=(12,2))
	lote 					= fields.Many2one('purchase.liquidation','Lote')


	costo_oro 				= fields.Float('Costo Oro',digits=(12,2)) 
	costo_plata 			= fields.Float('Costo Plata',digits=(12,2))
	costo_chancado 			= fields.Float('Costo Chancado',digits=(12,2))
	costo_zona				= fields.Float('Costo Zona',digits=(12,2))
	costo_expediente 		= fields.Float('Costo Expediente',digits=(12,2))
	gastos_generales 		= fields.Float('Gastos Generales - Chancado - Recepcion - Comercial',digits=(12,2))
	total_mineral 			= fields.Float('Total Costo Mineral',digits=(12,2))

	grilla_id 				= fields.One2many('grilla.producto.proceso.it','proceso_id','Linas')

	#costo_suministro 			= fields.Float('Costo Suministro',digits=(12,2))
	#gastos_personal_benef 		= fields.Float('Gasto de Personal Mas Beneficios',digits=(12,2))
	#gastos_relacionados 		= fields.Float('Gastos Relacionados a Personal',digits=(12,2))
	#produccion_terceros 		= fields.Float('Produccion encargada a terceros',digits=(12,2))
	#cianuro 					= fields.Float('Cianuro',digits=(12,2))
	#depreciacion 				= fields.Float('Depreciacion',digits=(12,2))
	#energia_electrica 			= fields.Float('Energia Electrica',digits=(12,2))
	#seguridad 					= fields.Float('Seguridad y Seguros',digits=(12,2))
	#medio_ambiente 				= fields.Float('Medio Ambiente',digits=(12,2))
	#agua_industrial 			= fields.Float('Agua Industrial',digits=(12,2))
	#agua_potable 				= fields.Float('Agua Potable',digits=(12,2))
	#alquilers 					= fields.Float('Alquileres',digits=(12,2))
	#costo_ajuste_periodo 		= fields.Float('Costo Ajuste Periodos Anterior es Mineral ICC',digits=(12,2))
	#mantenimiento 				= fields.Float('Mantenimiento',digits=(12,2))
	#consumibles 				= fields.Float('Consumibles',digits=(12,2))
	#servicios_evacuacion 		= fields.Float('Servicio de Evacuacion',digits=(12,2))
	#servicio_limpieza 			= fields.Float('Servicio de Limpieza',digits=(12,2))
	#asesorias 					= fields.Float('Asesorias',digits=(12,2))
	#telecom_unicaciones 		= fields.Float('Telecom Unicaciones e Internet',digits=(12,2))
	#otros 						= fields.Float('Otros',digits=(12,2))
	#total_costo_produccion 		= fields.Float('Total Costo Produccion',digits=(12,2))
	#total_costo 				= fields.Float('Total Costo',digits=(12,2))


	_rec_name = 'lote_proceso'


	_order = 'lote_proceso'

	@api.one
	def actualizar(self):
		rubros = []
		self.env.cr.execute(""" select name from rubro_costo_it """)
		for elem in self.env.cr.fetchall():
			rubros.append(elem[0])
		
		rubros.append('Total Costo Produccion')
		rubros.append('Total Costo')

		for i in self.grilla_id:
			if i.rubro not in rubros:
				i.unlink()


		for i in rubros:
			flag = True
			for l in self.grilla_id:
				if i == l.rubro:
					flag = False
			if flag:
				data = {
					'rubro':i,
					'monto':0,
					'proceso_id':self.id,
				}
				self.env['grilla.producto.proceso.it'].create(data)

	@api.multi
	def excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', "No fue configurado el directorio para los archivos en Configuración.")
		workbook = Workbook( direccion + 'excel_proceso.xlsx')
		
		worksheet = workbook.add_worksheet("Generales")
		worksheet_cm = workbook.add_worksheet("Costo Mineral")
		worksheet_gi = workbook.add_worksheet("Gastos Indirectos")
		
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		numberdos.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 6				
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.1
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.write(2,0, "Productos en Proceso:", boldbord)
		worksheet.write(2,1, self.lote_proceso.name, normal)
		

		worksheet_cm.write(2,0, "Productos en Proceso:", boldbord)
		worksheet_cm.write(2,1, self.lote_proceso.name, normal)
		

		worksheet_gi.write(2,0, "Productos en Proceso:", boldbord)
		worksheet_gi.write(2,1, self.lote_proceso.name, normal)
		





		worksheet.write(5,0, "Periodo",boldbord)
		worksheet.write(5,1, "Fecha",boldbord)
		worksheet.write(5,2, "Producto",boldbord)
		worksheet.write(5,3, u"Nro. Campaña",boldbord)
		worksheet.write(5,4, "Nro. Barra Tanque",boldbord)
		worksheet.write(5,5, "Unidad Medida",boldbord)
		worksheet.write(5,6, "Peso Barra",boldbord)
		worksheet.write(5,7, "% AU",boldbord)
		worksheet.write(5,8, "% AG",boldbord)
		worksheet.write(5,9, "Au Fino Gramos",boldbord)
		worksheet.write(5,10, "Ag Fino Gramos",boldbord)
		worksheet.write(5,11, "Costo Und. Gr.",boldbord)
		worksheet.write(5,12, "Costo Total",boldbord)
		worksheet.write(5,13, "Lote",boldbord)



		worksheet.write(6,0, self.periodo.code ,bord)
		worksheet.write(6,1, self.fecha ,bord)
		worksheet.write(6,2, self.producto.name ,bord)
		worksheet.write(6,3, self.nro_campana ,bord)
		worksheet.write(6,4, self.nro_barra_tanque ,bord)
		worksheet.write(6,5, self.unidad_medida.name ,bord)
		worksheet.write(6,6, self.peso_barra ,numberdos)
		worksheet.write(6,7, self.au ,numberdos)
		worksheet.write(6,8, self.ag ,numberdos)
		worksheet.write(6,9, self.au_gramo ,numberdos)
		worksheet.write(6,10, self.ag_gramo ,numberdos)
		worksheet.write(6,11, self.costo_gr ,numberdos)
		worksheet.write(6,12, self.costo_total ,numberdos)
		worksheet.write(6,13, self.lote.name ,bord)







		worksheet_cm.write(5,0, "Costo Oro",boldbord)
		worksheet_cm.write(5,1, "Costo Plata",boldbord)
		worksheet_cm.write(5,2, "Costo Chancado",boldbord)
		worksheet_cm.write(5,3, u"Costo Zona",boldbord)
		worksheet_cm.write(5,4, "Costo Expediente",boldbord)
		worksheet_cm.write(5,5, "Gastos Generales",boldbord)
		worksheet_cm.write(5,6, "Total Costo Mineral",boldbord)


		worksheet_cm.write(6,0, self.costo_oro ,numberdos)
		worksheet_cm.write(6,1, self.costo_plata ,numberdos)
		worksheet_cm.write(6,2, self.costo_chancado ,numberdos)
		worksheet_cm.write(6,3, self.costo_zona ,numberdos)
		worksheet_cm.write(6,4, self.costo_expediente ,numberdos)
		worksheet_cm.write(6,5, self.gastos_generales ,numberdos)
		worksheet_cm.write(6,6, self.total_mineral ,numberdos)



		y = 0
		for line in self.grilla_id:
			worksheet_gi.write(5,y,line.rubro if line.rubro else '' ,bord )
			worksheet_gi.write(6,y,line.monto ,numberdos )
			
			y = y +1

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

		x = x+2
		worksheet.write(x,0, "DESTINOS:",bold)
		x = x+2


		worksheet.write(x,0, "Cuenta",boldbord)
		worksheet.write(x,1, u"Descripción",boldbord)
		worksheet.write(x,2, "Debe",boldbord)
		worksheet.write(x,3, "Haber",boldbord)

		x += 1
		for destino in self.analytic_lines_id:
			worksheet.write(x,0, destino.cuenta.code,bord)
			worksheet.write(x,1, destino.cuenta.name,bord)
			worksheet.write(x,2, destino.debe ,numberdos)
			worksheet.write(x,3, destino.haber ,numberdos)
			x += 1


		workbook.close()
		
		f = open( direccion + 'tempo_account_move_line.xlsx', 'rb')
		
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'AsientoContable.xlsx',
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


class stock_move(models.Model):
	_inherit = 'stock.move'

	lote_producto_proceso_id = fields.Many2one('producto.proceso.it','Lote Producto Proceso')
