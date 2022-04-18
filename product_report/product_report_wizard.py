# -*- coding: utf-8 -*-
# partner.py



from openerp.osv import osv
from openerp import fields, models, api ,exceptions, _
import base64
from zipfile import ZipFile
from dateutil import parser
from datetime import datetime, date, time, timedelta
import calendar

class product_report_wizard(models.Model):
	#_inherit = 'product.template'
	_name = 'product.report.wizard'
	label = fields.Char(u'Consultar todos los productos.',readonly=True)



	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	@api.multi
	def gen_report(self):
		#####################################
		#			Librerias				#
		#####################################
		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		####################################
		#			Variables	 		   #
		####################################
		docname = "REPORTE_PRODUCTOS_GENERAL"
		temp_docname = docname+'.xls'
		letra = 'Calibri'
		title = 'PRODUCTOS'
		####################################
		#			Temporal Path 		   #
		####################################
		output = io.BytesIO()
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion +temp_docname)
		####################################
		#				FORMAT			   #
		####################################
		format_title= workbook.add_format()
		format_title.set_bold()			
		format_title.set_align('center')	
		format_title.set_font_name(letra)
		format_title.set_size(14)

		format_form = workbook.add_format()		
		format_form.set_bold()			
		format_form.set_font_name(letra)
		format_form.set_size(11)

		format_cabecera= workbook.add_format()
		format_cabecera.set_align('left')
		format_cabecera.set_bold()
		format_cabecera.set_font_name(letra)		
		format_cabecera.set_size(9)
		format_cabecera.set_border()
		format_cabecera.set_bg_color('#DCE6F1')
		format_cabecera.set_text_wrap()

		format_detalle= workbook.add_format()
		format_detalle.set_align('left')		
		format_detalle.set_font_name(letra)		
		format_detalle.set_size(9)	
		format_cabecera.set_border()
		format_detalle.set_text_wrap()	
		
		####################################
		#      Caracteres especiales       #
		####################################
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		####################################
		# 	EXCEL SHEET					   #
		####################################
		worksheet = workbook.add_worksheet( 'PRODUCTOS' )
		worksheet.set_portrait() #Vertical
		worksheet.set_paper(9) #A-4
		worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		worksheet.fit_to_pages(1, 0)  # Ajustar por Columna
	
		#PRINT ARREA
		worksheet.merge_range('A1:G1', u""+title, format_title)
		####################################
		# 				SQL				   #
		####################################
		sql_query = """
		select DISTINCT
			B.id AS TPL_ID,
			default_code AS CODIGO,
			CASE 
				WHEN D.value IS NOT NULL THEN D.value
				WHEN D.value IS NULL THEN C.name
			END AS UNIDAD,
			A.name_template AS DESCRIPCION,
			CASE 
				WHEN B.type = 'product' THEN 'Almacenable'
				WHEN B.type = 'consu' THEN 'Consumible'
				WHEN B.type = 'service' THEN 'Servicio'
			END AS TIPO,	
			E.name AS CATEGORIA ,
			G.code ||' '||G.name AS CUENTA
		FROM product_product A	
		LEFT JOIN product_template B on A.product_tmpl_id = B.id
		LEFT JOIN product_uom C on B.uom_id = C.id
		LEFT JOIN ir_translation D ON D.src LIKE C.name
		LEFT JOIN product_category E ON B.categ_id = E.id
		--PROPERTY FIELDS
		LEFT JOIN (select 	
		A.id,
		CAST ( 
			REPLACE (value_reference,'account.account,','' ) 
		AS INT ) AS property_account_expense
		FROM product_template A
		left join ir_property B on B.res_id = 'product.template,' || A.id
		WHERE B.NAME = 'property_account_expense'
		) F ON F.id = B.id
		LEFT JOIN account_account G ON F.property_account_expense = G.id
		WHERE B.active = 't'
		ORDER BY DESCRIPCION,TIPO
		"""
		self.env.cr.execute(sql_query)
		dicc = self.env.cr.dictfetchall()
		#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
		row = 3
		#Cabecera				
		worksheet.write( row, 0, u"Nro",format_cabecera)
		worksheet.write( row, 1, u"Codigo",format_cabecera)
		worksheet.write( row, 2, u"Unidad de Medida",format_cabecera)
		worksheet.write( row, 3, u"Descripcion",format_cabecera)
		worksheet.write( row, 4, u"Tipo de Producto",format_cabecera)
		worksheet.write( row, 5, u"Categoria Interna",format_cabecera)
		worksheet.write( row, 6, u"Cuenta de Gasto",format_cabecera)

		i = 0
		for fila in dicc:
			row = row + 1			
			i = i + 1			
			worksheet.write( row, 0, i,format_detalle)
			worksheet.write( row, 1, fila['codigo'],format_detalle)
			worksheet.write( row, 2, fila['unidad'],format_detalle)
			worksheet.write( row, 3, fila['descripcion'],format_detalle)
			worksheet.write( row, 4, fila['tipo'],format_detalle)
			worksheet.write( row, 5, fila['categoria'],format_detalle)
			worksheet.write( row, 6, fila['cuenta'],format_detalle)


		####################################
		#				SIZE 			   #
		####################################
		tam_col = [4,15,10,60,15,30,25]
		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])

		####################################
		#			LINK SALIDA			   #
		####################################
		workbook.close()
		f = open(direccion + temp_docname, 'rb')
		####################################
		#			LINK SALIDA			   #
		####################################
		vals = {
			'output_name': docname+'.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}
		sfs_id = self.env['export.file.save'].create(vals)
		####################################
		#			DECARGAR			   #
		####################################
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}




	@api.multi
	def fix_name(self):
		i = 0
		#update 
		for product_template in self.env['product.template'].search([]):
			temp_cuenta = product_template.property_account_expense
			if (temp_cuenta):
				cuenta = self.env['account.account'].search([('id','=', temp_cuenta.id)])								
				temp_name = cuenta.code + " "+product_template.name
				product_template.name = temp_name
				i = i + 1
				print (i)

	@api.multi
	def old_name(self):		
		#Restore
		i = 0
		for product_template in self.env['product.template'].search([]):
			cuenta = product_template.property_account_expense
			if (cuenta):
				name = product_template.name
				temp_name = name.split(" ")
				temp_cuenta = temp_name[0]
				existe = self.env['account.account'].search([('code','=', temp_cuenta)])
				if (existe):								
					old_name = name.replace(temp_cuenta+' ','')
					#print (old_name)					
					product_template.name = old_name
					i = i + 1
					print (i)

		
				
				

			

	

