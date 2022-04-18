# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
import base64

class kardex_product_export(models.Model):
	_name = 'kardex.product.export'
	
	fecha_inicio = fields.Date('Fecha Inicio')
	fecha_final = fields.Date('Fecha Inicio') 
	ubicaciones = fields.Many2many('stock.location','location_rel_kardex_product_export','location_id','kardex_product_id','Ubicaciones')


	check_fecha = fields.Boolean('Editar Fecha')
	alllocations = fields.Boolean('Todos los almacenes')

	fecha_ini_mod = fields.Date('Fecha Inicial')
	fecha_fin_mod = fields.Date('Fecha Final')


	_defaults={
		'check_fecha': False,
		'alllocations': True,
	}
	
	@api.onchange('fecha_ini_mod')
	def onchange_fecha_ini_mod(self):
		self.fecha_inicio = self.fecha_ini_mod


	@api.onchange('fecha_fin_mod')
	def onchange_fecha_fin_mod(self):
		self.fecha_final = self.fecha_fin_mod

	def default_get(self, cr, uid, fields, context=None):
		res = super(kardex_product_export, self).default_get(cr, uid, fields, context=context)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01' 
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fecha_inicio':fecha_inicial})
		res.update({'fecha_final':fecha_hoy})

		locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		res.update({'ubicaciones':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			self.ubicaciones = [(6,0,locat_ids.ids)]
		else:
			self.ubicaciones = [(6,0,[])]







	@api.multi
	def update_or_create_table(self):
		if 'saldo' not in  self.env.context:
			productos='{'
			almacenes='{'
			
			lst_products  = self.env['product.product'].search([('product_tmpl_id','=',self.env.context['active_id'] )])

			for producto in lst_products:
				productos=productos+str(producto.id)+','
			productos=productos[:-1]+'}'

			lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

			for location in self.ubicaciones:
				almacenes=almacenes+str(location.id)+','
			almacenes=almacenes[:-1]+'}'

			if True:

				import io
				from xlsxwriter.workbook import Workbook
				output = io.BytesIO()
				########### PRIMERA HOJA DE LA DATA EN TABLA
				#workbook = Workbook(output, {'in_memory': True})

				direccion = self.env['main.parameter'].search([])[0].dir_create_file
				workbook = Workbook(direccion +'kardex_producto.xlsx')
				worksheet = workbook.add_worksheet("Kardex Producto")
				bold = workbook.add_format({'bold': True})
				bold.set_font_size(8)
				normal = workbook.add_format()
				boldbord = workbook.add_format({'bold': True})
				boldbord.set_border(style=2)
				boldbord.set_align('center')
				boldbord.set_align('vcenter')
				boldbord.set_text_wrap()
				boldbord.set_font_size(8)
				boldbord.set_bg_color('#DCE6F1')

				especial1 = workbook.add_format({'bold': True})
				especial1.set_align('center')
				especial1.set_align('vcenter')
				especial1.set_text_wrap()
				especial1.set_font_size(15)
				
				numbertres = workbook.add_format({'num_format':'0.000'})
				numberdos = workbook.add_format({'num_format':'0.00'})
				numberseis = workbook.add_format({'num_format':'0.000000'})
				numberseis.set_font_size(8)
				numberocho = workbook.add_format({'num_format':'0.00000000'})
				numberocho.set_font_size(8)
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_font_size(8)
				numberdos.set_border(style=1)
				numberdos.set_font_size(8)
				numbertres.set_border(style=1)			
				numberseis.set_border(style=1)			
				numberocho.set_border(style=1)		
				numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})	
				numberdosbold.set_font_size(8)
				x= 10				
				tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				tam_letra = 1.2
				import sys
				reload(sys)
				sys.setdefaultencoding('iso-8859-1')

				worksheet.merge_range(1,5,1,10, "KARDEX VALORADO", especial1)
				worksheet.write(2,0,'FECHA INICIO:',bold)
				worksheet.write(3,0,'FECHA FIN:',bold)
				worksheet.write(4,0,'UNIDAD MEDIDA:',bold)
				worksheet.write(5,0,'CODIGO PRODUCTO:',bold)
				worksheet.write(6,0,'CUENTA CONTABLE:',bold)

				worksheet.write(2,1,self.fecha_inicio)
				worksheet.write(3,1,self.fecha_final)			
				worksheet.write(4,1,lst_products[0].uom_id.name)
				worksheet.write(5,1,lst_products[0].default_code)
				worksheet.write(6,1,lst_products[0].categ_id.property_stock_valuation_account_id.code if lst_products[0].categ_id.property_stock_valuation_account_id.code else '' )
				import datetime		

				worksheet.merge_range(8,0,9,0, u"Fecha Alm.",boldbord)
				worksheet.merge_range(8,1,9,1, u"Fecha",boldbord)
				worksheet.merge_range(8,2,9,2, u"Tipo",boldbord)
				worksheet.merge_range(8,3,9,3, u"Serie",boldbord)
				worksheet.merge_range(8,4,9,4, u"Número",boldbord)
				worksheet.merge_range(8,5,9,5, u"T. OP.",boldbord)
				worksheet.merge_range(8,6,9,6, u"Proveedor",boldbord)
				worksheet.merge_range(8,7,8,8, "Ingreso",boldbord)
				worksheet.write(9,7, "Cantidad",boldbord)
				worksheet.write(9,8, "Costo",boldbord)
				worksheet.merge_range(8,9,8,10, "Salida",boldbord)
				worksheet.write(9,9, "Cantidad",boldbord)
				worksheet.write(9,10, "Costo",boldbord)
				worksheet.merge_range(8,11,8,12, "Saldo",boldbord)
				worksheet.write(9,11, "Cantidad",boldbord)
				worksheet.write(9,12, "Costo",boldbord)
				worksheet.merge_range(8,13,9,13, "Costo Adquisicion",boldbord)
				worksheet.merge_range(8,14,9,14, "Costo Promedio",boldbord)
				worksheet.merge_range(8,15,9,15, "Ubicacion Origen",boldbord)
				worksheet.merge_range(8,16,9,16, "Ubicacion Destino",boldbord)
				worksheet.merge_range(8,17,9,17, "Almacen",boldbord)
				worksheet.merge_range(8,18,9,18, "Cuenta Factura",boldbord)
				worksheet.merge_range(8,19,9,19, "Documento Almacen",boldbord)


				self.env.cr.execute(""" 
					 select 
					fecha as "Fecha",
					type_doc as "T. Doc.",
					serial as "Serie",
					nro as "Nro. Documento",
					operation_type as "Tipo de operacion",				 
					ingreso as "Ingreso Fisico",
					round(debit,6) as "Ingreso Valorado.",
					salida as "Salida Fisico",
					round(credit,6) as "Salida Valorada",
					saldof as "Saldo Fisico",
					round(saldov,6) as "Saldo valorado",
					round(cadquiere,6) as "Costo adquisicion",
					round(cprom,6) as "Costo promedio",
						origen as "Origen",
						destino as "Destino",
					almacen AS "Almacen",
					account_invoice as "Cuenta factura",
					stock_doc as "Doc. Almacén",
					fecha_albaran as "Fecha Alb.",
					name as "Proveedor"

					from get_kardex_v("""+ str(self.fecha_inicio).replace('-','') + "," + str(self.fecha_final).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
				""")

				ingreso1= 0
				ingreso2= 0
				salida1= 0
				salida2= 0

				for line in self.env.cr.fetchall():
					worksheet.write(x,0,line[18] if line[18] else '' ,bord )
					worksheet.write(x,1,line[0] if line[0] else '' ,bord )
					worksheet.write(x,2,line[1] if line[1] else '' ,bord )
					worksheet.write(x,3,line[2] if line[2] else '' ,bord )
					worksheet.write(x,4,line[3] if line[3] else '' ,bord )
					worksheet.write(x,5,line[4] if line[4] else '' ,bord )
					
					worksheet.write(x,6,line[18] if line[18] else 0 ,numberdos )
					worksheet.write(x,7,line[5] if line[5] else 0 ,numberdos )
					worksheet.write(x,8,line[6] if line[6] else 0 ,numberdos )
					worksheet.write(x,9,line[7] if line[7] else 0 ,numberdos )
					worksheet.write(x,10,line[8] if line[8] else 0 ,numberdos )
					worksheet.write(x,11,line[9] if line[9] else 0 ,numberdos )
					worksheet.write(x,12,line[10] if line[10] else 0 ,numberdos )
					worksheet.write(x,13,line[11] if line[11] else 0 ,numberseis )
					worksheet.write(x,14,line[12] if line[12] else 0 ,numberocho )

					worksheet.write(x,15,line[13] if line[13] else '' ,bord )
					worksheet.write(x,16,line[14] if line[14] else '' ,bord )
					worksheet.write(x,17,line[15] if line[15] else '' ,bord )
					worksheet.write(x,18,line[16] if line[16] else '' ,bord )
					worksheet.write(x,19,line[17] if line[17] else '' ,bord )

					ingreso1 += line[5] if line[5] else 0
					ingreso2 +=line[6] if line[6] else 0
					salida1 +=line[7] if line[7] else 0
					salida2 += line[8] if line[8] else 0

					x = x +1

				tam_col = [11,11,5,5,7,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]

				worksheet.write(x,6,'TOTALES:' ,bold )
				worksheet.write(x,7,ingreso1 ,numberdosbold )
				worksheet.write(x,8,ingreso2 ,numberdosbold )
				worksheet.write(x,9,salida1 ,numberdosbold )
				worksheet.write(x,10,salida2 ,numberdosbold )

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
				
				f = open(direccion + 'kardex_producto.xlsx', 'rb')
				
				
				sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
				vals = {
					'output_name': 'ProductoKardex.xlsx',
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
		
		else:
			productos='{'
			almacenes='{'
			
			lst_products  = self.env['product.product'].search([('product_tmpl_id','=',self.env.context['active_id'] )])

			for producto in lst_products:
				productos=productos+str(producto.id)+','
			productos=productos[:-1]+'}'

			lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

			for location in self.ubicaciones:
				almacenes=almacenes+str(location.id)+','
			almacenes=almacenes[:-1]+'}'

			if True:

				import io
				from xlsxwriter.workbook import Workbook
				output = io.BytesIO()
				########### PRIMERA HOJA DE LA DATA EN TABLA
				#workbook = Workbook(output, {'in_memory': True})

				direccion = self.env['main.parameter'].search([])[0].dir_create_file
				workbook = Workbook(direccion +'kardex_producto.xlsx')
				worksheet = workbook.add_worksheet("Kardex Producto")
				bold = workbook.add_format({'bold': True})
				bold.set_font_size(8)
				normal = workbook.add_format()
				boldbord = workbook.add_format({'bold': True})
				boldbord.set_border(style=2)
				boldbord.set_align('center')
				boldbord.set_align('vcenter')
				boldbord.set_text_wrap()
				boldbord.set_font_size(8)
				boldbord.set_bg_color('#DCE6F1')

				especial1 = workbook.add_format({'bold': True})
				especial1.set_align('center')
				especial1.set_align('vcenter')
				especial1.set_text_wrap()
				especial1.set_font_size(15)
				
				numbertres = workbook.add_format({'num_format':'0.000'})
				numberdos = workbook.add_format({'num_format':'0.00'})
				numberseis = workbook.add_format({'num_format':'0.000000'})
				numberseis.set_font_size(8)
				numberocho = workbook.add_format({'num_format':'0.00000000'})
				numberocho.set_font_size(8)
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_font_size(8)
				numberdos.set_border(style=1)
				numberdos.set_font_size(8)
				numbertres.set_border(style=1)			
				numberseis.set_border(style=1)			
				numberocho.set_border(style=1)		
				numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})	
				numberdosbold.set_font_size(8)
				x= 10				
				tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				tam_letra = 1.2
				import sys
				reload(sys)
				sys.setdefaultencoding('iso-8859-1')

				worksheet.merge_range(1,5,1,10, "KARDEX VALORADO", especial1)
				worksheet.write(2,0,'FECHA INICIO:',bold)
				worksheet.write(3,0,'FECHA FIN:',bold)
				worksheet.write(4,0,'UNIDAD MEDIDA:',bold)
				worksheet.write(5,0,'CODIGO PRODUCTO:',bold)
				worksheet.write(6,0,'CUENTA CONTABLE:',bold)

				worksheet.write(2,1,self.fecha_inicio)
				worksheet.write(3,1,self.fecha_final)			
				worksheet.write(4,1,lst_products[0].uom_id.name)
				worksheet.write(5,1,lst_products[0].default_code)
				worksheet.write(6,1,lst_products[0].categ_id.property_stock_valuation_account_id.code if lst_products[0].categ_id.property_stock_valuation_account_id.code else '' )
				import datetime		

				worksheet.merge_range(8,1,8,2, "Saldo",boldbord)
				worksheet.write(9,1, "Cantidad",boldbord)
				worksheet.write(9,2, "Costo",boldbord)
				
				saldoneteado = 0
				costoneteado = 0

				self.env.cr.execute(""" 					
					 select 
					sum(ingreso) - sum(salida) as "saldo cantidad",
					sum(round(debit,6) - round(credit,6)) as "saldo costo"
					from get_kardex_v("""+ str(self.fecha_inicio).replace('-','') + "," + str(self.fecha_final).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
					group by product_id
				""")


				ingreso1= 0
				ingreso2= 0
				salida1= 0
				salida2= 0

				for line in self.env.cr.fetchall():
					saldoneteado+=line[0] if line[0] else 0 
					costoneteado+=line[1] if line[1] else 0 
					worksheet.write(x,1,line[0] if line[0] else 0 ,numberdos )
					worksheet.write(x,2,line[1] if line[1] else 0 ,numberdos )
					
					
					x = x +1

				raise osv.except_osv('Total Saldo','Saldo Cantidad: ' + str(saldoneteado) + ' , Saldo Costo: '+ str(costoneteado) )
				tam_col = [11,11,5,5,7,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]

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
				
				f = open(direccion + 'kardex_producto.xlsx', 'rb')
				
				
				sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
				vals = {
					'output_name': 'ProductoKardex.xlsx',
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
