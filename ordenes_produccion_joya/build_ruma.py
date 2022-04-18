# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

#Orden de Compra
 
class production_parameter(models.Model):
	_inherit = 'production.parameter'

	picking_type_consumo_cr = fields.Many2one('stock.picking.type','Albaran Consumo Ruma')
	picking_type_ingreso_producto_cr = fields.Many2one('stock.picking.type','Albaran Ingreso Producto Terminado Ruma')
	picking_type_ingreso_lote_cr = fields.Many2one('stock.picking.type','Albaran Ingreso Producto Proceso Ruma')

	producto_bullon = fields.Many2one('product.product','Producto Bullon')

class stock_move(models.Model):
	_inherit = 'stock.move'

	lote_armado_id = fields.Many2one('armado.ruma','Lote Armado R.')

class stock_picking(models.Model):
	_inherit='stock.picking'

	origen_type_picking_id = fields.Many2one('stock.location','Origen TP', related='picking_type_id.default_location_src_id')
	destino_type_picking_id = fields.Many2one('stock.location','Destino TP', related='picking_type_id.default_location_dest_id')
	date = fields.Date('Fecha Creación', help="Fecha creación, Usualmente la fecha de la orden", select=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, track_visibility='onchange')


class analiticas_consumo_ruma(models.Model):
	_name = 'analiticas.consumo.ruma'

	analitica = fields.Many2one('account.analytic.account','Cuenta Analitica',required=True)
	monto = fields.Float('Monto',readonly=True)
	padre = fields.Many2one('consumo.ruma','Padre')


	@api.one
	def write(self,vals):
		t = super(analiticas_consumo_ruma,self).write(vals)
		self.refresh()
		if 'lleno' in vals:
			pass
		else:
			self.env.cr.execute(""" select debit-credit from account_move_line aml 
			inner join account_move am on am.id = aml.move_id
			inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
			inner join account_period ap on ap.id = am.period_id
					inner join account_account aa on aa.id = aml.account_id
					inner join rubro_costo_it rci on rci.id = aa.rubro_costo_id
			where am.state != 'draft' and aaa.id = """ + str(self.analitica.id) + """
			and ap.id = """ + str(self.padre.period_id.id)+ """
			""")
			tmp = 0
			for i in self.env.cr.fetchall():
				tmp+= i[0]

			self.write({'monto':tmp,'lleno':1})

		return t

	@api.model
	def create(self,vals):
		t = super(analiticas_consumo_ruma,self).create(vals)

		self.env.cr.execute(""" select debit-credit from account_move_line aml 
		inner join account_move am on am.id = aml.move_id
		inner join account_period ap on ap.id = am.period_id
		inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
					inner join account_account aa on aa.id = aml.account_id
					inner join rubro_costo_it rci on rci.id = aa.rubro_costo_id
		where am.state != 'draft' and aaa.id = """ + str(t.analitica.id)+ """
			and ap.id = """ + str(t.padre.period_id.id)+ """
			""")
		tmp = 0
		for i in self.env.cr.fetchall():
			tmp+= i[0]

		t.write({'monto':tmp,'lleno':1})
		return t

class consumo_productos_finalizados_ruma(models.Model):
	_name = 'consumo.productos.finalizados.ruma'

	lote_id  = fields.Many2one('lote.terminado.tabla','Lote Fabricado')
	producto = fields.Many2one('product.product','Productos')
	unidad   = fields.Many2one('product.uom','Unidad')
	cantidad = fields.Float('Cantidad',digits=(12,2), default=1)
	barra = fields.Char(string='Nro. Barra', related='lote_id.barra')
	campania = fields.Char(string=u'Campaña', related='lote_id.campana')


	padre = fields.Many2one('consumo.ruma','Padre')

	@api.onchange('producto')
	def onchange_producto(self):
		if self.producto.id:
			self.unidad   = self.producto.uom_id.id
			self.cantidad = self.lote_id.peso_barra

class consumo_ruma_line(models.Model):
	_name = 'consumo.ruma.line'


	stock_move = fields.Many2one('stock.move','Asiento Contable')
	nro_ruma = fields.Many2one('armado.ruma','Nro Ruma')
	exp_oro = fields.Float('Expect. de Oro',digits=(12,2),readonly=True)
	tn = fields.Float('Tn.',digits=(12,2),readonly=True)
	valor = fields.Float('Valor',digits=(12,2),readonly=True)

	padre = fields.Many2one('consumo.ruma','Padre')


	@api.one
	def recalcular(self):
		params = self.env['production.parameter'].search([])

		if self.nro_ruma:
			ar_id = self.env['armado.ruma'].search([('id','=',self.nro_ruma.id)])
			if ar_id.picking_2.id:
				if len(ar_id.picking_2.move_lines) >0:
					move_id = ar_id.picking_2.move_lines[0]
					self.stock_move	= move_id.id
					self.nro_expediente = False
					self.exp_oro = move_id.gold_expected
					self.product_id = move_id.product_id.id
					self.tn = move_id.product_uom_qty
					self.valor = move_id.p_et2
			
			ar_id = self.env['costeo.ruma.linea'].search([('ruma_id','=',self.nro_ruma.id),('costeo_id','!=',False)])
			if len(ar_id)>0:
				ar_id = ar_id[0]
				self.tn = ar_id.toneladas
				self.valor = ar_id.f_total_costo



	@api.one
	def write(self,vals):
		params = self.env['production.parameter'].search([])


		if 'nro_ruma' in vals.keys():
			ar_id = self.env['armado.ruma'].search([('id','=',vals['nro_ruma'])])
			if ar_id.picking_2.id:
				if len(ar_id.picking_2.move_lines) >0:
					move_id = ar_id.picking_2.move_lines[0]
					vals['stock_move']	= move_id.id
					vals['nro_expediente'] = False
					vals['exp_oro'] = move_id.gold_expected
					vals['product_id'] = move_id.product_id.id
			ar_id = self.env['costeo.ruma.linea'].search([('ruma_id','=',vals['nro_ruma']),('costeo_id','!=',False)])
			if len(ar_id)>0:
				ar_id = ar_id[0]
				vals['tn'] = ar_id.toneladas
				vals['valor'] = ar_id.f_total_costo

		return super(consumo_ruma_line, self).write(vals)


	@api.model
	def create(self,vals):
		params = self.env['production.parameter'].search([])


		if 'nro_ruma' in vals.keys():
			ar_id = self.env['armado.ruma'].search([('id','=',vals['nro_ruma'])])
			if ar_id.picking_2.id:
				if len(ar_id.picking_2.move_lines) >0:
					move_id = ar_id.picking_2.move_lines[0]
					vals['stock_move']	= move_id.id
					vals['nro_expediente'] = False
					vals['exp_oro'] = move_id.gold_expected
					vals['product_id'] = move_id.product_id.id
		ar_id = self.env['costeo.ruma.linea'].search([('ruma_id','=',vals['nro_ruma']),('costeo_id','!=',False)])
		if len(ar_id)>0:
			ar_id = ar_id[0]
			vals['tn'] = ar_id.toneladas
			vals['valor'] = ar_id.f_total_costo
		return super(consumo_ruma_line, self).create(vals)

	@api.one
	@api.onchange('nro_ruma')
	def onchange_nro_ruma(self):
		params = self.env['production.parameter'].search([])

		if self.nro_ruma:
			ar_id = self.env['armado.ruma'].search([('id','=',self.nro_ruma.id)])
			if ar_id.picking_2.id:
				if len(ar_id.picking_2.move_lines) >0:
					move_id = ar_id.picking_2.move_lines[0]
					self.stock_move	= move_id.id
					self.nro_expediente = False
					self.exp_oro = move_id.gold_expected
					self.product_id = move_id.product_id.id
					self.tn = move_id.product_uom_qty
					self.valor = move_id.p_et2
			
			ar_id = self.env['costeo.ruma.linea'].search([('ruma_id','=',self.nro_ruma.id),('costeo_id','!=',False)])
			if len(ar_id)>0:
				ar_id = ar_id[0]
				self.tn = ar_id.toneladas
				self.valor = ar_id.f_total_costo

class consumo_ruma(models.Model):
	_name = 'consumo.ruma'
	_inherit = 'mail.thread'

	state = fields.Selection([('draft','Borrador'),('iniciada','Producción Iniciada'),('done','Finalizada')], default='draft')
	name = fields.Char(u'Número de C. Ruma',readonly=True)
	fecha_inicio = fields.Date('Fecha Inicio')
	fecha_fin = fields.Date('Fecha Fin')

	lines = fields.One2many('consumo.ruma.line','padre','Lineas')
	prod_fina_lines = fields.One2many('consumo.productos.finalizados.ruma','padre','Lineas')
	albaranes = fields.Many2many('stock.picking','consumo_ruma_rel_spit','consumo_ruma_id','picking_id','albaranes')

	albaran_id = fields.Many2one('stock.picking','albaran')
	analiticas = fields.One2many('analiticas.consumo.ruma','padre','Analitica')

	period_id = fields.Many2one('account.period','Periodo',required=True)

	@api.one
	def recalcular(self):
		for i in self.lines:
			i.recalcular()

	@api.one
	def crear_albaranes(self):

		if len(self.albaranes)==0:

			param = self.env['production.parameter'].search( [] )[0]
			if not param.picking_type_consumo_cr.id :
				raise osv.except_osv('Alerta!','No se configuro el parametro "Tipo de Albaranes Consumo"')

			if not param.picking_type_ingreso_lote_cr.id :
				raise osv.except_osv('Alerta!','No se configuro el parametro "Tipo de Albaranes Ingreso Producto Proceso"')

			if not param.picking_type_ingreso_producto_cr.id :
				raise osv.except_osv('Alerta!','No se configuro el parametro "Tipo de Albaranes Ingreso Producto Terminado"')

			picking_consumo_cr = self.env['stock.picking'].create({'motivo_guia':'7','picking_type_id':param.picking_type_consumo_cr.id,'date':self.period_id.date_stop})

			picking_ingreso_pro_pro_cr = self.env['stock.picking'].create({'motivo_guia':'8','picking_type_id':param.picking_type_ingreso_lote_cr.id,'date':self.period_id.date_stop})
			picking_ingreso_pro_ter_cr = self.env['stock.picking'].create({'motivo_guia':'8','picking_type_id':param.picking_type_ingreso_producto_cr.id,'date':self.period_id.date_stop})

			for i in self.lines:
				stock_move_d = {
					'product_id': param.ruma_product.id,
					'product_uom_qty': i.tn,
					'product_uom': param.ruma_product.uom_id.id,
					'name': param.ruma_product.description if param.ruma_product.description else param.ruma_product.name_template,
					'picking_id': picking_consumo_cr.id,
					'location_id': param.picking_type_consumo_cr.default_location_src_id.id,
					'location_dest_id': param.picking_type_consumo_cr.default_location_dest_id.id,
					'precio_unitario_manual': 0,
					'lot_num':0,
					'lote_armado_id':i.nro_ruma.id,
					'state': 'draft',
				}
				sm = self.env['stock.move'].create(stock_move_d)


			self.env.cr.execute("""
				select costo_total,id,au_fino from lote_terminado_tabla where period_id = """ +str(self.period_id.id)+ """
			 """)

			for j in self.env.cr.fetchall():
				stock_move_d = {
					'product_id': param.producto_bullon.id,
					'product_uom_qty': j[2] if j[2] else 0,
					'product_uom': param.producto_bullon.uom_id.id,
					'name': param.producto_bullon.description if param.producto_bullon.description else param.producto_bullon.name_template,
					'picking_id': picking_ingreso_pro_ter_cr.id,
					'location_id': param.picking_type_ingreso_producto_cr.default_location_src_id.id,
					'location_dest_id': param.picking_type_ingreso_producto_cr.default_location_dest_id.id,
					'precio_unitario_manual': j[0] if j[0] else 0,
					'lot_num':0,
					'lote_armado_id':0,
					'state': 'draft',
					'lote_terminado_tabla_id': j[1] if j[1] else 0,
				}
				sm = self.env['stock.move'].create(stock_move_d)


			self.env.cr.execute("""
				select  producto, costo_total, id from producto_proceso_it where periodo = """ +str(self.period_id.id)+ """
			 """)

			for j in self.env.cr.fetchall():
				producto_tt =  self.env['product.product'].browse(j[0])

				stock_move_d = {
					'product_id': producto_tt.id,
					#'product_uom_qty': j[3],
					'product_uom': producto_tt.uom_id.id,
					'name': producto_tt.description if producto_tt.description else producto_tt.name_template,
					'picking_id': picking_ingreso_pro_pro_cr.id,
					'location_id': param.picking_type_ingreso_lote_cr.default_location_src_id.id,
					'location_dest_id': param.picking_type_ingreso_lote_cr.default_location_dest_id.id,
					'precio_unitario_manual': j[1],
					'lot_num':0,
					'lote_armado_id':0,
					'lote_producto_proceso_id': j[2],
					'state': 'draft',
				}
				sm = self.env['stock.move'].create(stock_move_d)

			array_nuevo =[picking_consumo_cr.id,picking_ingreso_pro_pro_cr.id,picking_ingreso_pro_ter_cr.id]

			self.albaranes = [(6, 0, array_nuevo)]

			self.refresh()
			for i in self.albaranes:			
				i.action_confirm()
				i.force_assign()
				i.do_transfer()



	@api.onchange('period_id')
	def onchange_periodid(self):
		if self.period_id.id:
			self.fecha_inicio = self.period_id.date_start
			self.fecha_fin = self.period_id.date_stop

	@api.one
	def get_oro_total(self):
		lineas_d = []
		for i in self.lines:
			lineas_d.append( i.nro_ruma.id )
		total = 0
		for line in self.env['costeo.ruma.linea'].search( [('ruma_id','in',lineas_d )] ):
			total += line.f_costo_oro

		self.oro_total = total


	@api.one
	def get_plata_total(self):
		lineas_d = []
		for i in self.lines:
			lineas_d.append( i.nro_ruma.id )
		total = 0
		for line in self.env['costeo.ruma.linea'].search( [('ruma_id','in',lineas_d )] ):
			total += line.f_costo_plata

		self.plata_total = total

	@api.one
	def get_chancado_total(self):
		lineas_d = []
		for i in self.lines:
			lineas_d.append( i.nro_ruma.id )
		total = 0
		for line in self.env['costeo.ruma.linea'].search( [('ruma_id','in',lineas_d )] ):
			total += line.f_costo_chancado

		self.chancado_total = total


	@api.one
	def get_zona_total(self):
		lineas_d = []
		for i in self.lines:
			lineas_d.append( i.nro_ruma.id )
		total = 0
		for line in self.env['costeo.ruma.linea'].search( [('ruma_id','in',lineas_d )] ):
			total += line.f_costo_zona

		self.zona_total = total

	@api.one
	def get_expediente_total(self):
		lineas_d = []
		for i in self.lines:
			lineas_d.append( i.nro_ruma.id )
		total = 0
		for line in self.env['costeo.ruma.linea'].search( [('ruma_id','in',lineas_d )] ):
			total += line.f_costo_expediente

		self.expediente_total = total

	@api.one
	def get_gastos_total(self):
		lineas_d = []
		for i in self.lines:
			lineas_d.append( i.nro_ruma.id )
		total = 0
		for line in self.env['costeo.ruma.linea'].search( [('ruma_id','in',lineas_d )] ):
			total += line.f_gastos_generales

		self.gastos_total = total


	oro_total = fields.Float('Oro',compute='get_oro_total')
	plata_total = fields.Float('Plata',compute='get_plata_total')
	chancado_total = fields.Float('Chancado',compute='get_chancado_total')
	zona_total = fields.Float('Zona',compute='get_zona_total')
	expediente_total = fields.Float('Expediente',compute='get_expediente_total')
	gastos_total = fields.Float('Gastos Generales',compute='get_gastos_total')


	@api.multi
	def detalle_costo_rumas(self):
		if True:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_librodiario.xlsx')
			worksheet = workbook.add_worksheet("Detalle Costo Rumas")
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

			worksheet.write(0,0, "Detalle Costo Rumas", bold)
			
			worksheet.write(0,1, self.name, normal)
			

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			

			worksheet.write(3,0, "Ruma",boldbord)
			worksheet.write(3,1, "Toneladas",boldbord)
			worksheet.write(3,2, "VMP",boldbord)
			worksheet.write(3,3, "Factor",boldbord)
			worksheet.write(3,4, "Gastos Armado",boldbord)
			worksheet.write(3,5, "Total",boldbord)
			worksheet.write(3,6, "Precio Unitario",boldbord)
			worksheet.write(3,7, "Costo Oro",boldbord)
			worksheet.write(3,8, "Costo Plata",boldbord)
			worksheet.write(3,9, u"Costo Chancado",boldbord)
			worksheet.write(3,10, "Costo Zona",boldbord)
			worksheet.write(3,11, "Costo Expediente",boldbord)
			worksheet.write(3,12, u"Gastos Generales",boldbord)
			worksheet.write(3,13, u"Total Costo",boldbord)
			
			lineas_d = []
			for i in self.lines:
				lineas_d.append( i.nro_ruma.id )

			for line in self.env['costeo.ruma.linea'].search( [('ruma_id','in',lineas_d )] ):
				worksheet.write(x,0,line.ruma_id.name if line.ruma_id.id else '' ,bord )
				worksheet.write(x,1,line.toneladas ,numberdos )
				worksheet.write(x,2,line.valor_materia_prima ,numberdos )
				worksheet.write(x,3,line.factor ,numberdos )
				worksheet.write(x,4,line.gastos_armados ,numberdos )
				worksheet.write(x,5,line.total ,numberdos )
				worksheet.write(x,6,line.p_unit ,numberdos )
				worksheet.write(x,7,line.f_costo_oro ,numberdos )
				worksheet.write(x,8,line.f_costo_plata ,numberdos )
				worksheet.write(x,9,line.f_costo_chancado ,numberdos )
				worksheet.write(x,10,line.f_costo_zona ,numberdos )
				worksheet.write(x,11,line.f_costo_expediente ,numberdos )
				worksheet.write(x,12,line.f_gastos_generales ,numberdos )
				worksheet.write(x,13,line.f_total_costo ,numberdos )

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
				'output_name': 'Detalle Costo Rumas.xlsx',
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
	def detalle_costo_produccion(self):
		if True:
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_librodiario.xlsx')
			worksheet = workbook.add_worksheet("Detalle Costo Produccion")
			worksheet2 = workbook.add_worksheet("Resumen Costo Produccion")
			worksheet3 = workbook.add_worksheet("Prorrateo del Costo")
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

			worksheet.write(0,0, "Detalle Costo Rumas", bold)
			
			worksheet.write(0,1, self.name, normal)
			
			worksheet2.write(0,0, "Detalle Costo Rumas", bold)
			
			worksheet2.write(0,1, self.name, normal)
			

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			
			worksheet2.write(3,0, "Rubro",boldbord)
			worksheet2.write(3,1, "Monto",boldbord)

			worksheet.write(3,0, "Periodo",boldbord)
			worksheet.write(3,1, "Cuenta Contable",boldbord)
			worksheet.write(3,2, "Cuenta Analitica",boldbord)
			worksheet.write(3,3, "Rubro",boldbord)
			worksheet.write(3,4, "Monto",boldbord)
			
			lineas_d = [-1,-1,-1,-1,-1]
			for i in self.analiticas:
				lineas_d.append( i.analitica.id )

			self.env.cr.execute("""
					select ap.code, aa.code, aaa.name, rci.name, sum(debit-credit) from 
					account_move am
					inner join account_move_line aml on aml.move_id = am.id
					inner join account_period ap on ap.id = am.period_id
					inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
					inner join account_account aa on aa.id = aml.account_id
					inner join rubro_costo_it rci on rci.id = aa.rubro_costo_id
					where am.state != 'draft' and ap.id = """ +str(self.period_id.id)+ """
					and aaa.id in """ +str(tuple(lineas_d))+ """
					group by ap.code, aa.code, aaa.name, rci.name
			 """)

			for line in self.env.cr.fetchall():
				worksheet.write(x,0,line[0] if line[0] else '' ,bord )
				worksheet.write(x,1,line[1] if line[1] else '' ,bord )
				worksheet.write(x,2,line[2] if line[2] else '' ,bord )
				worksheet.write(x,3,line[3] if line[3] else '' ,bord )
				worksheet.write(x,4,line[4] ,numberdos )

				x = x +1

		
			x= 4				
			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10]


			self.env.cr.execute("""
					select rci.name, sum(debit-credit) from 
					account_move am
					inner join account_move_line aml on aml.move_id = am.id
					inner join account_period ap on ap.id = am.period_id
					inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
					inner join account_account aa on aa.id = aml.account_id
					inner join rubro_costo_it rci on rci.id = aa.rubro_costo_id
					where am.state != 'draft' and ap.id = """ +str(self.period_id.id)+ """
					and aaa.id in """ +str(tuple(lineas_d))+ """
					group by  rci.name
			 """)

			totalax = 0

			for line in self.env.cr.fetchall():
				worksheet2.write(x,0,line[0] if line[0] else '' ,bord )
				worksheet2.write(x,1,line[1] ,numberdos )
				totalax += line[1]
				x = x +1

			worksheet2.write(x+1,0, 'Total Gastos Indirectos',bord)
			worksheet2.write(x+1,1, totalax,numberdos)



			worksheet2.write(x+4,0, 'Resumen Oro',bord)
			worksheet2.write(x+4,1, self.oro_total,bord)

			worksheet2.write(x+5,0, 'Resumen Plata',bord)
			worksheet2.write(x+5,1, self.plata_total ,bord)

			worksheet2.write(x+6,0, 'Resumen Chancado',bord)
			worksheet2.write(x+6,1, self.chancado_total,bord)

			worksheet2.write(x+7,0, 'Resumen Zona',bord)
			worksheet2.write(x+7,1, self.zona_total,bord)

			worksheet2.write(x+8,0, 'Resumen Expediente',bord)
			worksheet2.write(x+8,1, self.expediente_total,bord)

			worksheet2.write(x+9,0, 'Resumen Gastos Generales',bord)
			worksheet2.write(x+9,1, self.gastos_total,bord)

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





			#jajajajajaja



			worksheet3.write(4,0,'COMPONENTE',boldbord)

			worksheet3.write(4,1,'GRAMOS ORO INVENTARIO INICIAL',boldbord)
			worksheet3.write(4,2,'GRAMOS ENVIADOS A PROCESO EN EL PERIODO',boldbord)
			worksheet3.write(4,3,'TOTAL GRAMOS PROCESADOS',boldbord)
			worksheet3.write(4,4,'GRAMOS PRODUCTO TERMINADO PERIODO',boldbord)
			worksheet3.write(4,5,'GRAMOS PRODUCTOS EN PROCESO PERIODO',boldbord)
			worksheet3.write(4,6,'VALOR INVENTARIO INICIAL',boldbord)
			worksheet3.write(4,7,'VALOR GRAMOS ENVIADOS A PROCESO',boldbord)
			worksheet3.write(4,8,'VALOR PRODUCTO TERMINADO PERIODO',boldbord)
			worksheet3.write(4,9,'VALOR PRODUCTO EN PROCESO PERIODO',boldbord)
			worksheet3.write(4,10,'TOTAL COSTO',boldbord)
		
			x= 5				
			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10]


			#self.env.cr.execute("""
			#		select rci.name, coalesce( sum(coalesce(debit,0)-coalesce(credit,0)) ,0) from 
			#		rubro_costo_it rci
			#		left join account_account aa on aa.rubro_costo_id = rci.id
			#		left join account_move_line aml on aml.account_id = aa.id
			#		left join account_move am on am.id = aml.move_id and am.state != 'draft'
			#		left join account_period ap on ap.id = am.period_id and ap.id = """ +str(self.period_id.id)+ """
			#		left join account_analytic_account aaa on aaa.id = aml.analytic_account_id and aaa.id in """ +str(tuple(lineas_d))+ """				
			#		group by  rci.name

			#""")


			#tlinex = self.env.cr.fetchall()



			self.env.cr.execute("""
					select rci.name, sum(debit-credit) from 
					account_move am
					inner join account_move_line aml on aml.move_id = am.id
					inner join account_period ap on ap.id = am.period_id
					inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
					inner join account_account aa on aa.id = aml.account_id
					inner join rubro_costo_it rci on rci.id = aa.rubro_costo_id
					where am.state != 'draft' and ap.id = """ +str(self.period_id.id)+ """
					and aaa.id in """ +str(tuple(lineas_d))+ """
					group by  rci.name
			 """)


			tlinex = self.env.cr.fetchall()


			dic_lineas_variables = {}
			for i in tlinex:
				dic_lineas_variables[i[0]] = i[1]



			self.env.cr.execute("""
				select name from rubro_costo_it
			 """)

			rubrostotales = []
			for iele in self.env.cr.fetchall():
				rubrostotales.append(iele[0])



			for line in rubrostotales:
				worksheet3.write(x,0,line if line else '' ,bord )
				x = x +1


			worksheet3.write(x,0, 'Resumen Oro',bord)
			worksheet3.write(x+1,0, 'Resumen Chancado',bord)
			worksheet3.write(x+2,0, 'Resumen Zona',bord)
			worksheet3.write(x+3,0, 'Resumen Expediente',bord)
			worksheet3.write(x+4,0, 'Resumen Gastos Generales',bord)


			period_ant = {
				'13':'12',
				'12':'11',
				'11':'10',
				'10':'09',
				'09':'08',
				'08':'07',
				'07':'06',
				'06':'05',
				'05':'04',
				'04':'03',
				'03':'02',
				'02':'01',
				'01':'12',
			}

			periodo_obj_a = self.env['account.period'].search([('code','=', period_ant[self.period_id.code.split('/')[0]] + '/' + (self.period_id.code.split('/')[1] if period_ant[self.period_id.code.split('/')[0]] != '12' else str( int(self.period_id.code.split('/')[1])-1  )  ) )])[0]

			g1 = 0
			g2 = 0
			g3 = 0
			g4 = 0
			g5 = 0
			g6 = 0
			g7 = 0
			g8 = 0
			g9 = 0			
			g10 = 0

			self.env.cr.execute("""
			select au_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g1 += wt[0]

			tmpeluo = 0
			for elu in self.lines:
				for ojl in elu.nro_ruma.lines:
					tmpeluo += ojl.nro_lote.gr_gold* ojl.nro_lote.percentage_recovery/100.00
			g2 = tmpeluo

			g3 = g1+g2


			self.env.cr.execute("""
			select au_fino from 
			lote_terminado_tabla ppi
			where period_id = """ +str(self.period_id.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g4 += wt[0]


			self.env.cr.execute("""
			select au_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(self.period_id.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g5 += wt[0]



			x = 5

			for line in rubrostotales:
				worksheet3.write(x,1,g1 ,numberdos )
				worksheet3.write(x,2,g2 ,numberdos )
				worksheet3.write(x,3,g3 ,numberdos )
				worksheet3.write(x,4,g4 ,numberdos )
				worksheet3.write(x,5,g5 ,numberdos )



				g6 = 0

				self.env.cr.execute("""
				select gppi.monto from 
				producto_proceso_it ppi
				inner join grilla_producto_proceso_it gppi on gppi.proceso_id = ppi.id
				where periodo = """ +str(periodo_obj_a.id)+ """  and gppi.rubro = '""" + line + """'
				""")

				for wt in self.env.cr.fetchall():
					g6 += wt[0]

				g7 = dic_lineas_variables[line] if line in dic_lineas_variables else 0

				g8 = ( g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
				g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
				g10 = g8+ g9

				worksheet3.write(x,6,g6 ,numberdos )
				worksheet3.write(x,7,g7 ,numberdos )
				worksheet3.write(x,8,g8 ,numberdos )
				worksheet3.write(x,9,g9 ,numberdos )
				worksheet3.write(x,10,g10 ,numberdos )
				x = x +1



			g6 = 0
			self.env.cr.execute("""
			select costo_oro from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.oro_total

			g8 = (g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g10 = g8+ g9


			worksheet3.write(x,1,g1 ,numberdos )
			worksheet3.write(x,2,g2 ,numberdos )
			worksheet3.write(x,3,g3 ,numberdos )
			worksheet3.write(x,4,g4 ,numberdos )
			worksheet3.write(x,5,g5 ,numberdos )

			worksheet3.write(x,6,g6 ,numberdos )
			worksheet3.write(x,7,g7 ,numberdos )
			worksheet3.write(x,8,g8 ,numberdos )
			worksheet3.write(x,9,g9 ,numberdos )
			worksheet3.write(x,10,g10 ,numberdos )
			x += 1



			g6=0
			self.env.cr.execute("""
			select costo_chancado from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.chancado_total

			g8 = ( g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g10 = g8+ g9

			worksheet3.write(x,1,g1 ,numberdos )
			worksheet3.write(x,2,g2 ,numberdos )
			worksheet3.write(x,3,g3 ,numberdos )
			worksheet3.write(x,4,g4 ,numberdos )
			worksheet3.write(x,5,g5 ,numberdos )


			worksheet3.write(x,6,g6 ,numberdos )
			worksheet3.write(x,7,g7 ,numberdos )
			worksheet3.write(x,8,g8 ,numberdos )
			worksheet3.write(x,9,g9 ,numberdos )
			worksheet3.write(x,10,g10 ,numberdos )
			x += 1



			g6=0
			self.env.cr.execute("""
			select costo_zona from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.zona_total

			g8 = ( g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g10 = g8+ g9

			worksheet3.write(x,1,g1 ,numberdos )
			worksheet3.write(x,2,g2 ,numberdos )
			worksheet3.write(x,3,g3 ,numberdos )
			worksheet3.write(x,4,g4 ,numberdos )
			worksheet3.write(x,5,g5 ,numberdos )
			worksheet3.write(x,6,g6 ,numberdos )
			worksheet3.write(x,7,g7 ,numberdos )
			worksheet3.write(x,8,g8 ,numberdos )
			worksheet3.write(x,9,g9 ,numberdos )
			worksheet3.write(x,10,g10 ,numberdos )
			x += 1


			g6=0

			self.env.cr.execute("""
			select costo_expediente from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.expediente_total

			g8 = ( g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g10 = g8+ g9

			worksheet3.write(x,1,g1 ,numberdos )
			worksheet3.write(x,2,g2 ,numberdos )
			worksheet3.write(x,3,g3 ,numberdos )
			worksheet3.write(x,4,g4 ,numberdos )
			worksheet3.write(x,5,g5 ,numberdos )
			worksheet3.write(x,6,g6 ,numberdos )
			worksheet3.write(x,7,g7 ,numberdos )
			worksheet3.write(x,8,g8 ,numberdos )
			worksheet3.write(x,9,g9 ,numberdos )
			worksheet3.write(x,10,g10 ,numberdos )
			x += 1



			g6=0
			self.env.cr.execute("""
			select gastos_generales from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.gastos_total

			g8 = ( g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g10 = g8+ g9

			worksheet3.write(x,1,g1 ,numberdos )
			worksheet3.write(x,2,g2 ,numberdos )
			worksheet3.write(x,3,g3 ,numberdos )
			worksheet3.write(x,4,g4 ,numberdos )
			worksheet3.write(x,5,g5 ,numberdos )
			worksheet3.write(x,6,g6 ,numberdos )
			worksheet3.write(x,7,g7 ,numberdos )
			worksheet3.write(x,8,g8 ,numberdos )
			worksheet3.write(x,9,g9 ,numberdos )
			worksheet3.write(x,10,g10 ,numberdos )
			x += 1


			### plata


			g1 = 0
			g2 = 0
			g3 = 0
			g4 = 0
			g5 = 0
			g6 = 0
			g7 = 0
			g8 = 0
			g9 = 0			
			g10 = 0

			g6=0
			self.env.cr.execute("""
			select ag_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g1 += wt[0]


			tmpeluo = 0
			for elu in self.lines:
				for ojl in elu.nro_ruma.lines:
					tmpeluo += ojl.nro_lote.gr_silver
			g2 = tmpeluo

			g3 = g1+g2


			self.env.cr.execute("""
			select ag_fino from 
			lote_terminado_tabla ppi
			where period_id = """ +str(self.period_id.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g4 += wt[0]


			self.env.cr.execute("""
			select ag_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(self.period_id.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g5 += wt[0]


			g6=0
			self.env.cr.execute("""
			select costo_plata from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]



			g7 = self.plata_total

			g8 = ( g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g10 = g8+ g9


			x = 6


			for line in rubrostotales:
				x = x +1

			x+= 4

			worksheet3.write(x,0,'Resumen Plata' ,bord )
			worksheet3.write(x,1,g1 ,numberdos )
			worksheet3.write(x,2,g2 ,numberdos )
			worksheet3.write(x,3,g3 ,numberdos )
			worksheet3.write(x,4,g4 ,numberdos )
			worksheet3.write(x,5,g5 ,numberdos )

			worksheet3.write(x,6,g6 ,numberdos )
			worksheet3.write(x,7,g7 ,numberdos )
			worksheet3.write(x,8,g8 ,numberdos )
			worksheet3.write(x,9,g9 ,numberdos )
			worksheet3.write(x,10,g10 ,numberdos )
			x += 1


			workbook.close()
			
			f = open( direccion + 'tempo_librodiario.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'Detalle Costo Produccion.xlsx',
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






	@api.one
	def actualizar_costos(self):
		if True:
			lineas_d = [-1,-1,-1,-1,-1]
			for i in self.analiticas:
				lineas_d.append( i.analitica.id )

			totalax = 0
			
			#jajajajajaja

			self.env.cr.execute("""
					select rci.name, sum(debit-credit) from 
					account_move am
					inner join account_move_line aml on aml.move_id = am.id
					inner join account_period ap on ap.id = am.period_id
					inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
					inner join account_account aa on aa.id = aml.account_id
					inner join rubro_costo_it rci on rci.id = aa.rubro_costo_id
					where am.state != 'draft' and ap.id = """ +str(self.period_id.id)+ """
					and aaa.id in """ +str(tuple(lineas_d))+ """
					group by  rci.name
			 """)


			tlinex = self.env.cr.fetchall()


			dic_lineas_variables = {}
			for i in tlinex:
				dic_lineas_variables[i[0]] = i[1]
				totalax += i[1]


			self.env.cr.execute("""
				select name from rubro_costo_it
			 """)

			rubrostotales = []
			for iele in self.env.cr.fetchall():
				rubrostotales.append(iele[0])




			period_ant = {
				'13':'12',
				'12':'11',
				'11':'10',
				'10':'09',
				'09':'08',
				'08':'07',
				'07':'06',
				'06':'05',
				'05':'04',
				'04':'03',
				'03':'02',
				'02':'01',
				'01':'00',
			}

			total_oro_prorrateo = 0

			self.env.cr.execute("""
			select ppi.id, au_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(self.period_id.id)+ """ 
			""")

			obj_prorateo_proceso = []

			for wt in self.env.cr.fetchall():
				total_oro_prorrateo += wt[1]
				obj_prorateo_proceso.append( [wt[0],wt[1]] )



			total_oro_prorrateo_lote = 0

			self.env.cr.execute("""
			select id, au_fino from 
			lote_terminado_tabla ppi
			where period_id = """ +str(self.period_id.id)+ """ 
			""")

			obj_prorateo_lote = []

			for wt in self.env.cr.fetchall():
				total_oro_prorrateo_lote += wt[1]
				obj_prorateo_lote.append( [wt[0],wt[1]] )

	
			periodo_obj_a = self.env['account.period'].search([('code','=', period_ant[self.period_id.code.split('/')[0]] + '/' + self.period_id.code.split('/')[1] )])[0]

			g1 = 0
			g2 = 0
			g3 = 0
			g4 = 0
			g5 = 0
			g6 = 0
			g7 = 0
			g8 = 0
			g9 = 0			
			g10 = 0

			self.env.cr.execute("""
			select au_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g1 += wt[0]

			g3 = g1+g2


			self.env.cr.execute("""
			select au_fino from 
			lote_terminado_tabla ppi
			where period_id = """ +str(self.period_id.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g4 += wt[0]


			self.env.cr.execute("""
			select au_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(self.period_id.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g5 += wt[0]



			x = 5

			for line in rubrostotales:

				g6=0
				self.env.cr.execute("""
				select gppi.monto from 
				producto_proceso_it ppi
				inner join grilla_producto_proceso_it gppi on gppi.proceso_id = ppi.id
				where periodo = """ +str(periodo_obj_a.id)+ """  and gppi.rubro = '""" + line + """'
				""")

				for wt in self.env.cr.fetchall():
					g6 += wt[0]

				g7 = dic_lineas_variables[line] if line in dic_lineas_variables else 0

				g8 = ( g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
				g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
				g10 = g8+ g9

				for elementos in obj_prorateo_lote:

					self.env.cr.execute("""
						update grilla_lote_terminado set
						monto = """ +str( g8 *( elementos[1]/total_oro_prorrateo_lote ) )+ """ 
						where lote_id = """ +str(elementos[0])+ """ and rubro = '""" + line+ """'
					 """)

				for elementos in obj_prorateo_proceso:

					self.env.cr.execute("""
						update grilla_producto_proceso_it set
						monto = """ +str( g9 *( elementos[1]/total_oro_prorrateo ) )+ """ 
						where proceso_id = """ +str(elementos[0])+ """ and rubro = '""" + line+ """'
					 """)




			g6=0
			self.env.cr.execute("""
			select costo_oro from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.oro_total

			g8 = (g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g9 = ( g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g10 = g8+ g9


			for elementos in obj_prorateo_lote:

				self.env.cr.execute("""
					update lote_terminado_tabla set
					costo_oro = """ +str( g8 *( elementos[1]/total_oro_prorrateo_lote ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)

			for elementos in obj_prorateo_proceso:

				self.env.cr.execute("""
					update producto_proceso_it set
					costo_oro = """ +str( g9 *( elementos[1]/total_oro_prorrateo ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)








			g6=0
			self.env.cr.execute("""
			select costo_chancado from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.chancado_total

			g8 = (g4* ((g6+g7)/(g4+g5))) if g4+g5!= 0 else 0
			g9 = (g5* ((g6+g7)/(g4+g5))) if g4+g5!= 0 else 0
			g10 = g8+ g9


			for elementos in obj_prorateo_lote:

				self.env.cr.execute("""
					update lote_terminado_tabla set
					costo_chancado = """ +str( g8 *( elementos[1]/total_oro_prorrateo_lote ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)

			for elementos in obj_prorateo_proceso:

				self.env.cr.execute("""
					update producto_proceso_it set
					costo_chancado = """ +str( g9 *( elementos[1]/total_oro_prorrateo ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)


			g6=0
			self.env.cr.execute("""
			select costo_zona from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.zona_total

			g8 = (g4* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g9 = (g5* ((g6+g7)/(g4+g5)) ) if g4+g5!= 0 else 0
			g10 = g8+ g9


			for elementos in obj_prorateo_lote:

				self.env.cr.execute("""
					update lote_terminado_tabla set
					costo_zona = """ +str( g8 *( elementos[1]/total_oro_prorrateo_lote ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)

			for elementos in obj_prorateo_proceso:

				self.env.cr.execute("""
					update producto_proceso_it set
					costo_zona = """ +str( g9 *( elementos[1]/total_oro_prorrateo ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)



			g6=0
			self.env.cr.execute("""
			select costo_expediente from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.expediente_total

			g8 = (g4* ((g6+g7)/(g4+g5))) if g4+g5!= 0 else 0
			g9 = (g5* ((g6+g7)/(g4+g5))) if g4+g5!= 0 else 0
			g10 = g8+ g9


			for elementos in obj_prorateo_lote:

				self.env.cr.execute("""
					update lote_terminado_tabla set
					costo_expediente = """ +str( g8 *( elementos[1]/total_oro_prorrateo_lote ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)

			for elementos in obj_prorateo_proceso:

				self.env.cr.execute("""
					update producto_proceso_it set
					costo_expediente = """ +str( g9 *( elementos[1]/total_oro_prorrateo ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)



			g6=0
			self.env.cr.execute("""
			select gastos_generales from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.gastos_total

			g8 = (g4* ((g6+g7)/(g4+g5))) if g4+g5!= 0 else 0
			g9 = (g5* ((g6+g7)/(g4+g5))) if g4+g5!= 0 else 0
			g10 = g8+ g9


			for elementos in obj_prorateo_lote:

				self.env.cr.execute("""
					update lote_terminado_tabla set
					gastos_generales = """ +str( g8 *( elementos[1]/total_oro_prorrateo_lote ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)

			for elementos in obj_prorateo_proceso:

				self.env.cr.execute("""
					update producto_proceso_it set
					gastos_generales = """ +str( g9 *( elementos[1]/total_oro_prorrateo ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)


			### plata


			g1 = 0
			g2 = 0
			g3 = 0
			g4 = 0
			g5 = 0
			g6 = 0
			g7 = 0
			g8 = 0
			g9 = 0			
			g10 = 0

			self.env.cr.execute("""
			select ag_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g1 += wt[0]

			g3 = g1+g2


			self.env.cr.execute("""
			select ag_fino from 
			lote_terminado_tabla ppi
			where period_id = """ +str(self.period_id.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g4 += wt[0]


			self.env.cr.execute("""
			select ag_gramo from 
			producto_proceso_it ppi
			where periodo = """ +str(self.period_id.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g5 += wt[0]

			g6=0

			self.env.cr.execute("""
			select costo_plata from 
			producto_proceso_it ppi
			where periodo = """ +str(periodo_obj_a.id)+ """ 
			""")

			for wt in self.env.cr.fetchall():
				g6 += wt[0]

			g7 = self.plata_total

			g8 = (g4* ((g6+g7)/(g4+g5))) if g4+g5!= 0 else 0
			g9 = (g5* ((g6+g7)/(g4+g5))) if g4+g5!= 0 else 0
			g10 = g8+ g9



			for elementos in obj_prorateo_lote:

				self.env.cr.execute("""
					update lote_terminado_tabla set
					costo_plata = """ +str( g8 *( elementos[1]/total_oro_prorrateo_lote ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)

			for elementos in obj_prorateo_proceso:

				self.env.cr.execute("""
					update producto_proceso_it set
					costo_plata = """ +str( g9 *( elementos[1]/total_oro_prorrateo ) )+ """ 
					where id = """ +str(elementos[0])+ """ 
				 """)




			for elementos in obj_prorateo_lote:

				self.env.cr.execute("""
					update lote_terminado_tabla set
					total_mineral = costo_oro + costo_plata + costo_chancado + costo_zona + costo_expediente + gastos_generales
					where id = """ +str(elementos[0])+ """ 
				 """)

			for elementos in obj_prorateo_proceso:

				self.env.cr.execute("""
					update producto_proceso_it set
					total_mineral = costo_oro + costo_plata + costo_chancado + costo_zona + costo_expediente + gastos_generales
					where id = """ +str(elementos[0])+ """ 
				 """)



			for elementos in obj_prorateo_lote:
				tuipo = 0

				self.env.cr.execute("""
					select monto from
					grilla_lote_terminado glt 
					where lote_id = """ +str(elementos[0])+ """
					""")
				for uiuiu in self.env.cr.fetchall():
					tuipo += uiuiu[0]

				self.env.cr.execute("""
					update lote_terminado_tabla set
					costo_total =  total_mineral + """ +str(tuipo)+ """
					where id = """ +str(elementos[0])+ """ 
				 """)

			for elementos in obj_prorateo_proceso:

				tuipo = 0

				self.env.cr.execute("""
					select monto from
					grilla_producto_proceso_it glt 
					where proceso_id = """ +str(elementos[0])+ """
					""")
				for uiuiu in self.env.cr.fetchall():
					tuipo += uiuiu[0]

				self.env.cr.execute("""
					update producto_proceso_it set
					costo_total =  total_mineral + """ +str(tuipo)+ """
					where id = """ +str(elementos[0])+ """ 
				 """)



	@api.one
	def cancel_last(self):
		if self.state == 'iniciada':
			if self.albaran_id.id:
				if self.albaran_id.state != 'draft':
					self.albaran_id.action_revert_done()
					self.albaran_id.unlink()
				else:
					self.albaran_id.unlink()

			for i in self.albaranes:
				i.action_revert_done()
				i.unlink()

			self.state = 'draft'
		else:
			print "Nada"



	@api.one
	def eliminar_lotes(self):
		if self.albaran_id.id:
			if self.albaran_id.state != 'draft':
				self.albaran_id.action_revert_done()
				self.albaran_id.unlink()
			else:
				self.albaran_id.unlink()

		for i in self.albaranes:
			i.action_revert_done()
			i.unlink()


	@api.model
	def create(self,vals):
		t = super(consumo_ruma,self).create(vals)
		parameter = self.env['production.parameter'].search([])[0]


		sequence_id = self.env['ir.sequence'].search([('name','=','Build Consumo Ruma')])
		if len(sequence_id)== 0:
			dic_new_seq = {
					'name': 'Build Consumo Ruma',
					'padding': 7,
					'number_next_actual': 1,
					'number_increment': 1,
					'implementation': 'no_gap',
					'prefix': 'OP-',
					}
			sequence_id = self.env['ir.sequence'].create(dic_new_seq)
		else:
			sequence_id =sequence_id[0]

		t.write({'name': self.env['ir.sequence'].next_by_id(sequence_id.id) })
		import datetime
		#t.write({'fecha_creacion': str(datetime.datetime.now())[:10] })
		return t

	@api.one
	def iniciar_produccion(self):
		if len(self.lines)==0:
			raise osv.except_osv('Alerta!',"No existe rumas seleccionados.")
		from datetime import datetime
		if self.albaran_id.id:
			pass

		self.state = 'iniciada'

		if False:
			picking = self.env['stock.picking']
			move = self.env['stock.move']


			params = self.env['production.parameter'].search([])

			picking_type = params.top_consumo_ruma
			#Traslado de productos a ubicación de producción.
			picking_vals = {
				'motivo_guia'		: '7',
				'move_type'			: 'direct',
				'picking_type_id'	: picking_type.id,
				'priority'			: '1',
				'date'				:  self.fecha_inicio,
			}

			picking_obj = picking.create(picking_vals)

			self.write({'albaran_id':picking_obj.id})

			self.write({ 'albaranes':[(4,picking_obj.id)] })

			for line in self.lines:
				move_vals = {
					'picking_id'		: picking_obj.id,
					'lot_num'			: line.stock_move.lot_num,
					'product_id'		: line.stock_move.product_id.id,
					'gold_expected'		: line.stock_move.gold_expected,
					'ponderation'		: line.stock_move.ponderation,
					'product_uom_qty'	: line.stock_move.product_uom_qty,
					'product_uom'		: line.stock_move.product_uom.id,
					'p_et2'				: line.stock_move.p_et2,
					'location_id'		: picking_type.default_location_src_id.id,
					'location_dest_id'	: picking_type.default_location_dest_id.id,
					'name'				: line.stock_move.name,
					'invoice_state'		: line.stock_move.invoice_state,
					'date'				: datetime.now(),
					'date_expected'		: datetime.now(),
					'state'				: 'done',
				}
				move_obj = move.create(move_vals)
