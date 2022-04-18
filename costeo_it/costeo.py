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

class stock_picking(models.Model):
	_inherit = 'stock.picking'


	@api.cr_uid_ids_context
	def do_transfer(self, cr, uid, picking_ids, context=None):
		t = super(stock_picking,self).do_transfer(cr,uid,picking_ids,context)
		if not context:
			context = {}
		notrack_context = dict(context, mail_notrack=True)
		stock_move_obj = self.pool.get('stock.move')
		for picking in self.browse(cr, uid, picking_ids, context=context):
			for moves in picking.move_lines:
				if  0.00001 >= moves.product_uom_qty :
					cr.execute(""" delete from stock_move where id = """ + str(moves.id))
		return t

class stock_move(models.Model):
	_inherit = 'stock.move'


	@api.one
	def get_product_uom(self):
		self.product_uom_static = self.product_uom.id
		
	product_uom_static = fields.Many2one('product.uom','Unidad de Medida',compute='get_product_uom')
	lote_padre = fields.Many2one('purchase.liquidation','Lote Padre')

	@api.multi
	def abrir_detalle_lote(self):
		search_info = self.env['costeo.line.it'].search([('lote','=',self.lote_padre.id),('padre','!=',False)])
		if len(search_info)>0:
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "costeo.line.it",
			    "views": [[False, "form"]],
			    "res_id": search_info[0].id,
			    "target": "new",
			}		


class ubicacion_param(models.Model):
	_name = 'ubicacion.param'

	ubicacion = fields.Many2one('stock.location','Ubicacion',required=True)
	check = fields.Boolean('Costeo')
	parameter = fields.Many2one('production.parameter','Padre')

class gastos_generales_rel(models.Model):
	_name = 'gastos.generales.rel'

	analitic_id = fields.Many2one('account.analytic.account', 'Cuenta Analitica',required=True)
	monto = fields.Float('Monto',digits=(12,2))
	costeo_id = fields.Many2one('costeo.it','Costeo')

class product_template(models.Model):
	_inherit = 'product.template'

	costo_chancado = fields.Boolean('Tiene costo Chancado')


class destino_picking_type(models.Model):
	_name = 'destino.picking.type'

	destino = fields.Many2one('stock.location','Almacen Lote',required=True)
	picking_type_salidas = fields.Many2one('stock.picking.type','Tipo Picking Produccion',required=True)
	picking_type = fields.Many2one('stock.picking.type','Tipo Picking Entrada',required=True)
	parameter= fields.Many2one('production.parameter','Parametro')


class production_parameter(models.Model):
	_inherit = 'production.parameter'

	account_ag_costeo = fields.Many2one('account.account','Cuenta Plata Para Costeo')
	account_chancado = fields.Many2one('account.analytic.account','Cuenta Analiticia para Chancado')

	entrada_albaran = fields.Many2one('stock.picking.type','Tipo Picking Entrada') 
	salida_albaran = fields.Many2one('stock.picking.type','Tipo Picking Salida')
	ubicaciones_check = fields.One2many('ubicacion.param','parameter','Ubicaciones Costeo')


	destino_picking_t_id = fields.One2many('destino.picking.type','parameter','Almacen Lotes')
	#ubicacione_destino_check = fields.Many2one('stock.location','Almacen Lotes')
	picking_type_trasferencias_costeo = fields.Many2one('stock.picking.type','Tipo Picking Transferencias para Costeo')
	listado_costo_analitico = fields.Many2many('account.analytic.account','parametero_analitico_listos_ids','parameter_id','analitico_id','Cuentas Analiticas Padre para Costeo')
	destino_costeo_lote = fields.Many2many('stock.location','parameter_location_rel_ids','parameter_id','location_id','Destinos de Costeo de Lote')

class zona_resumen(models.Model):
	_name = 'zona.resumen'

	name = fields.Char('Zona')

class account_analytic_account(models.Model):
	_inherit = 'account.analytic.account'

	zona_id = fields.Many2one('zona.resumen','Zona')

class costeo_line_it(models.Model):
	_name = 'costeo.line.it'

	ubicacion_especial = fields.Boolean('Ubicacion Especial',default=False)

	ubicacion_check = fields.Boolean('Ubicacion Check',default=False)
	periodo = fields.Many2one('account.period','Periodo')

	lote_padre = fields.Many2one('purchase.liquidation','Lote Padre')

	lote = fields.Many2one('purchase.liquidation','Lote')
	producto = fields.Many2one('product.product','Producto')
	toneladas_secas = fields.Float('Toneladas Secas')
	zona = fields.Many2one('zona.resumen','Zona')
	costo_oro = fields.Float('Costo Oro')
	costo_plata = fields.Float('Costo Plata',digits=(12,8))
	costo_chancado = fields.Float('Costo Chancado',digits=(12,8))
	factor_chancado = fields.Float('FC',digits=(12,8))

	costo_zona = fields.Float('Costo Zona',digits=(12,8))
	factor_zona = fields.Float('FZ',digits=(12,8))
	costo_expediente = fields.Float('Costo Expediente',digits=(12,8))
	factor_expediente = fields.Float('FZ',digits=(12,8))
	gastos_generales = fields.Float('Gastos generales',digits=(12,8))
	factor_generales = fields.Float('FZ',digits=(12,8))
	total_costo = fields.Float('Total Costo',digits=(12,8))
	p_unit = fields.Float('P. Unit',digits=(12,8))
	separador = fields.Char('Separador')

	picking_t_p_id = fields.Many2one('stock.picking.type','Picking Type')
	picking_t_id = fields.Many2one('stock.picking.type','Picking Type')
	check_chancado = fields.Boolean('Chancado',default=True)
	padre = fields.Many2one('costeo.it','Padre')


	@api.multi
	def abrir_detalle_lote(self):
		search_info = self.env['costeo.line.it'].search([('lote','=',self.lote_padre.id),('padre','!=',False)])
		if len(search_info)>0:
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "costeo.line.it",
			    "views": [[False, "form"]],
			    "res_id": search_info[0].id,
			    "target": "new",
			}		


class costeo_it(models.Model):
	_name = 'costeo.it'

	periodo = fields.Many2one('account.period','Periodo',required=True)
	state = fields.Selection([('draft','Borrador'),('1','Costo Oro y Plata'),('2','Costo de Chancado'),('3','Costo Zona'),('4','Costo Expediente'),('5','Gasto Generales'),('6','Calculado'),('done','Finalizado')],'Estado',default='draft')
	lineas = fields.One2many('costeo.line.it','padre','Detalle',domain=[('ubicacion_check','=',True),('ubicacion_especial','=',False)])
	lineas_editable = fields.One2many('costeo.line.it','padre','Detalle',domain=[('ubicacion_check','=',False),('ubicacion_especial','=',False)])
	lineas_especial = fields.One2many('costeo.line.it','padre','Detalle',domain=[('ubicacion_especial','=',True)])

	#analytics_ids = fields.Many2many('account.analytic.account','analytics_rel_costeo_it','analytic_id','costeo_id','Ctas Analiticas')
	analytics_ids = fields.One2many('gastos.generales.rel','costeo_id','Ctas Analiticas')

	#albaran_entrada = fields.Many2one('stock.picking','Albaran Entrada Produccion')
	albaranes_entrada = fields.Many2many('stock.picking','picking_rel_costeo_it','picking_id','costeo_it','Albaranes')
	albaran_salida = fields.Many2one('stock.picking','Albaran Salida Produccion')

	_rec_name = 'periodo'

	@api.one
	def costo_oro_plata(self):

		parametros = self.env['production.parameter'].search([])[0]
		if not parametros.account_ag_costeo.id:
			raise osv.except_osv('Alerta!','No se configuro el parametro "Cuenta Plata para Costeo"')

		destinos_costeo = [0,0,0,0]
		
		for i in parametros.destino_costeo_lote:
			destinos_costeo.append(i.id)
			
		productos='{'
		almacenes='{'

		lst_products  = self.env['product.product'].search([])

		for producto in lst_products:
			productos=productos+str(producto.id)+','
		productos=productos[:-1]+'}'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
		almacenes=almacenes[:-1]+'}'

		t = """ 
			 select 
			 lotemp,
			 --product_id, 
			 sum( CASE WHEN es_plata = true THEN debit ELSE 0 END ) as plata,
			 sum( CASE WHEN es_plata = true THEN 0 ELSE debit END ) as oro
			 --sum( CASE WHEN account_invoice = '""" + parametros.account_ag_costeo.code + """' or account_invoice = '""" +parametros.account_ag_costeo.code + ' - ' + parametros.account_ag_costeo.name + """' THEN debit ELSE 0 END ) as plata,
			 --sum( CASE WHEN account_invoice = '""" + parametros.account_ag_costeo.code + """' or account_invoice = '""" +parametros.account_ag_costeo.code + ' - ' + parametros.account_ag_costeo.name + """' THEN 0 ELSE debit END ) as oro
			 from get_kardex_v("""+ str(self.periodo.fiscalyear_id.name) + "0101," + str(self.periodo.date_stop).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
			 where fecha >= '""" +str(self.periodo.date_start)+ """' and fecha <= '""" +str(self.periodo.date_stop)+ """' and lotemp is not null and lotemp != '' 
			 and ubicacion_destino in """ +str( tuple(destinos_costeo) )+ """
			 group by lotemp
			 order by lotemp
		"""

		self.env.cr.execute(t)

		rptkardex = self.env.cr.dictfetchall()

		for i in rptkardex:
			lote_a = self.env['purchase.liquidation'].search([('name','=', i['lotemp'] )])[0]

			linea = self.env['costeo.line.it'].search( [('padre','=',self.id),('lote','=',lote_a.id)] )

			for elem in linea:
				elem.costo_plata = i['plata']
				elem.costo_oro   = i['oro']

		self.state = '1'

	@api.one
	def regresar_borrador(self):
		for i in self.lineas:
			i.costo_plata = 0
			i.costo_oro = 0
		self.state = 'draft'


	@api.one
	def costo_chancado(self):

		parametros = self.env['production.parameter'].search([])[0]
		if not parametros.account_chancado.id:
			raise osv.except_osv('Alerta!','No se configuro el parametro "Cuenta Analitica para Chancado"')

		self.env.cr.execute(""" select debit - credit as cantidad from account_move am 
			inner join account_move_line aml on aml.move_id = am.id 
			inner join account_period ap on ap.id = am.period_id 
			inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
			inner join account_analytic_account paa on paa.id = aaa.parent_id
		where ap.id = """ +str(self.periodo.id)+ """ and paa.id = """ +str(parametros.account_chancado.id)+ """ and am.state != 'draft' """)

		cantidad_total = 0
		for i in self.env.cr.dictfetchall():
			cantidad_total += i['cantidad']

		toneladas_total = 0
		for i in self.lineas:
			if i.check_chancado:
				toneladas_total += i.toneladas_secas

		for i in self.lineas:
			if i.check_chancado:
				i.factor_chancado = i.toneladas_secas / toneladas_total if toneladas_total!= 0 else 0
				i.refresh()
				i.costo_chancado = i.factor_chancado * cantidad_total
		self.state = '2'

	@api.multi
	def reporte_chancado(self):

		parametros = self.env['production.parameter'].search([])[0]
		if not parametros.account_chancado.id:
			raise osv.except_osv('Alerta!','No se configuro el parametro "Cuenta Analitica para Chancado"')

		self.env.cr.execute(""" select aaa.name, sum(debit - credit) as cantidad from account_move am 
			inner join account_move_line aml on aml.move_id = am.id 
			inner join account_period ap on ap.id = am.period_id 
			inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
			inner join account_analytic_account paa on paa.id = aaa.parent_id
		where ap.id = """ +str(self.periodo.id)+ """ and paa.id = """ +str(parametros.account_chancado.id)+ """ and am.state != 'draft' 
			group by aaa.name
		""")

		anal_chan = []
		for i in self.env.cr.dictfetchall():
			anal_chan.append([i['name'],i['cantidad']])

		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook( direccion + 'chancado.xlsx')
		worksheet = workbook.add_worksheet("Chancado")
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
		numberocho = workbook.add_format({'num_format':'0.00000000'})
		numberocho.set_border(style=1)
		
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

		worksheet.write(0,0, "Chancado:", bold)

		worksheet.write(0,1, self.periodo.name, normal)

		#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
		

		worksheet.write(3,0, "Lote",boldbord)
		worksheet.write(3,1, "Producto",boldbord)
		worksheet.write(3,2, "Toneladas",boldbord)
		worksheet.write(3,3, "Factor Chancando",boldbord)
		y = 4

		for elt in anal_chan:
			worksheet.write(3,y,elt[0],boldbord)
			y = y+1

		worksheet.write(3,y,'Total',boldbord)


		for i in self.lineas:
			if i.check_chancado:
				worksheet.write(x,0,i.lote.name, bord)
				worksheet.write(x,1,i.producto.name if i.producto.id else '', bord)
				worksheet.write(x,2,i.toneladas_secas,numberdos)
				worksheet.write(x,3,i.factor_chancado,numberocho)
				y = 4
				for elt in anal_chan:
					worksheet.write(x,y,elt[1]*i.factor_chancado,numberocho)
					y=y+1

				worksheet.write(x,y,i.costo_chancado,numberocho)

				x+= 1


		tam_col = [20,20,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]

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
		worksheet.set_column('S:BZ', tam_col[18])

		workbook.close()
		
		f = open( direccion + 'chancado.xlsx', 'rb')
		
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'Chancado.xlsx',
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
	def regresar_plataoro(self):
		for i in self.lineas:
			i.costo_chancado = 0
		self.state = '1'


	@api.one
	def costo_zona(self):

		self.env.cr.execute(""" select sum(debit - credit) as cantidad,aaa.zona_id from account_move am inner join account_move_line aml on aml.move_id = am.id inner join account_period ap on ap.id = am.period_id inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
		where ap.id = """ +str(self.periodo.id)+ """ and am.state != 'draft' and aaa.zona_id is not null group by aaa.zona_id """ )



		zonas = {}
		for i in self.env.cr.dictfetchall():
			zonas[str(i['zona_id'])] = i['cantidad']


		zonas_internas = {}

		for i in self.lineas:
			if i.zona.id:
				if str(i.zona.id) in zonas_internas:
					zonas_internas[str(i.zona.id)] +=  i.toneladas_secas
				else:
					zonas_internas[str(i.zona.id)] =  i.toneladas_secas

		for i in self.lineas:
			if i.zona.id:
				i.factor_zona = i.toneladas_secas / zonas_internas[str(i.zona.id)] if zonas_internas[str(i.zona.id)] != 0 else 0
				i.refresh()
				i.costo_zona = i.factor_zona * zonas[str(i.zona.id)] if str(i.zona.id) in zonas else 0

		self.state = '3'


	@api.multi
	def reporte_zona(self):
		parametros = self.env['production.parameter'].search([])[0]

		self.env.cr.execute(""" select sum(debit - credit) as cantidad,zr.name from account_move am inner join account_move_line aml on aml.move_id = am.id inner join account_period ap on ap.id = am.period_id inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
		inner join zona_resumen zr on zr.id = aaa.zona_id

		where ap.id = """ +str(self.periodo.id)+ """ and am.state != 'draft' and aaa.zona_id is not null group by zr.name """ )
		

		anal_zona = []
		for i in self.env.cr.dictfetchall():
			anal_zona.append([i['name'],i['cantidad']])

		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook( direccion + 'zona.xlsx')
		worksheet = workbook.add_worksheet("Zona")
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
		numberocho = workbook.add_format({'num_format':'0.00000000'})
		numberocho.set_border(style=1)
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

		worksheet.write(0,0, "Zona:", bold)

		worksheet.write(0,1, self.periodo.name, normal)

		#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
		
		worksheet.write(3,0,'Zona',boldbord)
		worksheet.write(3,1,'Monto',boldbord)		

		for elemi in anal_zona:
			worksheet.write(x,0,elemi[0])
			worksheet.write(x,1,elemi[1])
			x+=1

		x+=2
		worksheet.write(x,0, "Lote",boldbord)
		worksheet.write(x,1, "Producto",boldbord)
		worksheet.write(x,2, "Toneladas",boldbord)
		worksheet.write(x,3, "Factor Zona",boldbord)
		y = 4
		for i in self.env['zona.resumen'].search([]):
			worksheet.write(x,y,i.name,boldbord)
			y+=1

		x+= 1
		for i in self.lineas.sorted(lambda r: r.zona.id):
			if i.zona.id:
				worksheet.write(x,0,i.lote.name, bord)
				worksheet.write(x,1,i.producto.name if i.producto.id else '', bord)
				worksheet.write(x,2,i.toneladas_secas,numberdos)
				worksheet.write(x,3,i.factor_zona,numberocho)
				y = 4
				for ww in self.env['zona.resumen'].search([]):
					if ww.id == i.zona.id:
						worksheet.write(x,y,i.costo_zona,numberocho)
					else:
						worksheet.write(x,y,0,numberocho)
					y+=1
				x += 1


		tam_col = [20,20,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]

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
		worksheet.set_column('S:BZ', tam_col[18])

		workbook.close()
		
		f = open( direccion + 'zona.xlsx', 'rb')
		
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'Zona.xlsx',
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
	def regresar_chancado(self):
		for i in self.lineas:
			i.costo_zona = 0
		self.state = '2'



	@api.one
	def costo_expediente(self):
		self.env.cr.execute(""" select sum(debit - credit) as cantidad,aaa.id from account_move am inner join account_move_line aml on aml.move_id = am.id inner join account_period ap on ap.id = am.period_id inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
			inner join purchase_costing pc on pc.cuenta_analytica = aaa.id
		where ap.id = """ +str(self.periodo.id)+ """ and am.state != 'draft'  group by aaa.id """ )

		expedientes = {}
		for i in self.env.cr.dictfetchall():
			expedientes[i['id']] = i['cantidad']

		expediente_internas = {}
		for i in self.lineas:
			expendiente = self.env['purchase.costing.detalles'].search([('nro_lote','=',i.lote.id)])
			if len(expendiente)>0:
				expendiente = expendiente[0]
				if expendiente.padre.cuenta_analytica.id:
					if str(expendiente.padre.cuenta_analytica.id) in expediente_internas:
						expediente_internas[str(expendiente.padre.cuenta_analytica.id)] += i.toneladas_secas
					else:
						expediente_internas[str(expendiente.padre.cuenta_analytica.id)] = i.toneladas_secas

		for i in self.lineas:
			expendiente = self.env['purchase.costing.detalles'].search([('nro_lote','=',i.lote.id)])
			if len(expendiente)>0:
				expendiente = expendiente[0]
				if expendiente.padre.cuenta_analytica.id:
					i.factor_expediente = i.toneladas_secas / expediente_internas[str(expendiente.padre.cuenta_analytica.id)] if expediente_internas[str(expendiente.padre.cuenta_analytica.id)] != 0 else 0
					i.refresh()
					i.costo_expediente = i.factor_expediente * expedientes[str(expendiente.padre.cuenta_analytica.id)] if str(expendiente.padre.cuenta_analytica.id) in expedientes else 0

		self.state = '4'


	@api.one
	def regresar_zona(self):
		for i in self.lineas:
			i.costo_expediente = 0
		self.state = '3'
	



	@api.one
	def costo_generales(self):

		## aumentar aqui el codigo restante donde la nueva logica sera la cambiada a esta
		ids_anali = []
		for i in self.analytics_ids:
			i.monto = 0
			ids_anali.append(i.analitic_id.id)

		total_gene = 0
		self.env.cr.execute(""" select sum(debit - credit) as cantidad,aaa.id from account_move am inner join account_move_line aml on aml.move_id = am.id inner join account_period ap on ap.id = am.period_id inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
		where ap.id = """ +str(self.periodo.id)+ """ and am.state != 'draft' and aaa.id is not null group by aaa.id """ )
		
		for i in self.env.cr.dictfetchall():
			if i['id'] in ids_anali:
				total_gene += i['cantidad']
			for w in self.analytics_ids:
				if w.analitic_id.id == i['id']:
					w.monto = w.monto + i['cantidad']



		total_ton = 0
		for i in self.lineas:
			total_ton += i.toneladas_secas

		for i in self.lineas:
			i.factor_generales = i.toneladas_secas / total_ton if total_ton!= 0 else 0
			i.refresh()
			i.gastos_generales = i.factor_generales * total_gene


		self.state = '5'


	@api.multi
	def reporte_gastosgenerales(self):
		
		ids_anali = []
		for i in self.analytics_ids:
			ids_anali.append(i.analitic_id.name)


		self.env.cr.execute(""" select sum(debit - credit) as cantidad,aaa.name from account_move am inner join account_move_line aml on aml.move_id = am.id inner join account_period ap on ap.id = am.period_id inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
		where ap.id = """ +str(self.periodo.id)+ """ and am.state != 'draft' and aaa.id is not null group by aaa.name """ )
		## aumentar aqui el codigo restante donde la nueva logica sera la cambiada a esta

		anal_chan = []
		for i in self.env.cr.dictfetchall():
			if i['name'] in ids_anali:
				anal_chan.append([i['name'],i['cantidad']])

		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook( direccion + 'generales.xlsx')
		worksheet = workbook.add_worksheet("GastosGenerales")
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
		numberocho = workbook.add_format({'num_format':'0.00000000'})
		numberocho.set_border(style=1)
		
		numberochobold = workbook.add_format({'num_format':'0.00000000','bold':True})
		numberochobold.set_border(style=1)
		
		

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

		worksheet.write(0,0, "Gastos Generales:", bold)

		worksheet.write(0,1, self.periodo.name, normal)

		#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
		

		worksheet.write(3,0, "Lote",boldbord)
		worksheet.write(3,1, "Producto",boldbord)
		worksheet.write(3,2, "Toneladas",boldbord)
		worksheet.write(3,3, "Factor Generales",boldbord)
		y = 4

		for elt in anal_chan:
			worksheet.write(3,y,elt[0],boldbord)
			y = y+1

		worksheet.write(3,y,'Total',boldbord)


		for i in self.lineas:
			worksheet.write(x,0,i.lote.name, bord)
			worksheet.write(x,1,i.producto.name if i.producto.id else '', bord)
			worksheet.write(x,2,i.toneladas_secas,numberdos)
			worksheet.write(x,3,i.factor_generales,numberocho)
			y = 4
			for elt in anal_chan:
				worksheet.write(x,y,elt[1]*i.factor_generales,numberocho)
				y=y+1
			worksheet.write(x,y,i.gastos_generales,numberocho)
			x += 1

		y = 4
		worksheet.write(x,3, "TOTAL", bold)
		for elt in anal_chan:
			worksheet.write(x,y, '=sum(' + xl_rowcol_to_cell(4,y) +':' +xl_rowcol_to_cell(x-1,y) + ')' , numberochobold)
			y=y+1

		worksheet.write(x,y, '=sum(' + xl_rowcol_to_cell(4,y) +':' +xl_rowcol_to_cell(x-1,y) + ')' , numberochobold)


		tam_col = [20,20,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]

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
		worksheet.set_column('S:BZ', tam_col[18])

		workbook.close()
		
		f = open( direccion + 'generales.xlsx', 'rb')
		
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'GastosGenerales.xlsx',
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
	def done(self):
		for i in self.lineas:
			i.total_costo = i.costo_plata + i.costo_oro + i.costo_chancado + i.costo_zona + i.costo_expediente +i.gastos_generales
			i.refresh()
			i.p_unit = i.total_costo / i.toneladas_secas if i.toneladas_secas != 0 else 0

		self.state = '6'


	@api.one
	def finish(self):
		self.generar_movimiento()

		self.state = 'done'

	@api.one
	def generar_movimiento(self):
		gen = self.env['production.parameter'].search( [] )[0]

		if len( gen.destino_picking_t_id) == 0 or not gen.salida_albaran.id:
			raise osv.except_osv('Alerta!','No se configuro el parametro "Tipo de Albaranes"')

		#spts = gen.entrada_albaran
		

		#sptd = gen.salida_albaran
		
		#sppc = self.env['stock.picking'].create({'motivo_guia':'7','picking_type_id':spts.id,'date':self.periodo.date_stop})
		#sppt = self.env['stock.picking'].create({'motivo_guia':'7','picking_type_id':sptd.id,'date':self.periodo.date_stop})

		dic_tipos = {}

		dic_produ = {}

		array_nuevo = []


		lineas_total = []

		for i in self.lineas:
			lineas_total.append(i)

		for i in self.lineas_editable:
			lineas_total.append(i)

		for i in lineas_total:
			if i.picking_t_id.id in dic_tipos:
				pass
			else:
				tmp_p = self.env['stock.picking'].create({'motivo_guia':'8','picking_type_id':i.picking_t_id.id,'date':self.periodo.date_stop})
				dic_tipos[i.picking_t_id.id] = [tmp_p.id,0]
				array_nuevo.append(tmp_p.id)

				tmp_p2 = self.env['stock.picking'].create({'motivo_guia':'7','picking_type_id':i.picking_t_p_id.id,'date':self.periodo.date_stop})
				dic_produ[i.picking_t_p_id.id] = [tmp_p2.id,0]
				array_nuevo.append(tmp_p2.id)

			vals = {
				'product_id': i.producto.id,
				'product_uom_qty': i.toneladas_secas,
				'product_uom': i.producto.uom_id.id,
				'name': i.producto.description if i.producto.description else i.producto.name_template,
				'picking_id': dic_tipos[i.picking_t_id.id][0],
				'location_id': i.picking_t_id.default_location_src_id.id,
				'location_dest_id': i.picking_t_id.default_location_dest_id.id,
				'precio_unitario_manual': i.total_costo,
				'lot_num':i.lote.id,
				'state': 'draft',
			}
			sm = self.env['stock.move'].create(vals)
			dic_tipos[i.picking_t_id.id][1] = dic_tipos[i.picking_t_id.id][1] + 1
			if dic_tipos[i.picking_t_id.id][1] == 10:
				tmp_p = self.env['stock.picking'].create({'motivo_guia':'8','picking_type_id':i.picking_t_id.id,'date':self.periodo.date_stop})
				dic_tipos[i.picking_t_id.id] = [tmp_p.id,0]
				array_nuevo.append(tmp_p.id)

			vals2 = {
				'product_id': i.producto.id,
				'product_uom_qty': i.toneladas_secas,
				'product_uom': i.producto.uom_id.id,
				'name': i.producto.description if i.producto.description else i.producto.name_template,
				'picking_id': dic_produ[i.picking_t_p_id.id][0],
				'location_id': i.picking_t_p_id.default_location_src_id.id,
				'location_dest_id': i.picking_t_p_id.default_location_dest_id.id,
				'lot_num':i.lote.id,
				'state': 'draft',
			}
			dic_produ[i.picking_t_p_id.id][1] = dic_produ[i.picking_t_p_id.id][1] + 1

			if dic_produ[i.picking_t_p_id.id][1] == 10:				
				tmp_p2 = self.env['stock.picking'].create({'motivo_guia':'7','picking_type_id':i.picking_t_p_id.id,'date':self.periodo.date_stop})
				dic_produ[i.picking_t_p_id.id] = [tmp_p2.id,0]
				array_nuevo.append(tmp_p2.id)

			sm2 = self.env['stock.move'].create(vals2)


		#sppc.action_confirm()
		#sppt.action_confirm()


		self.albaranes_entrada = [(6, 0, array_nuevo)]

		self.refresh()

		for i in self.albaranes_entrada:
			i.action_confirm()
			i.force_assign()
			i.do_transfer()

		#self.albaran_entrada = sppc.id
		#self.albaran_salida = sppt.id


	@api.one
	def regresar_generales(self):
		for i in self.lineas:
			i.total_costo = 0
			i.p_unit = 0

		for i in self.albaranes_entrada:
			i.action_revert_done()
			i.unlink()
		#if self.albaran_entrada.id:
		#	self.albaran_entrada.unlink()

		if self.albaran_salida.id:
			self.albaran_salida.unlink()

		self.state = '5'


	@api.one
	def regresar_done(self):

		for i in self.albaranes_entrada:
			i.action_revert_done()
			i.unlink()
		#if self.albaran_entrada.id:
		#	self.albaran_entrada.unlink()

		if self.albaran_salida.id:
			self.albaran_salida.action_revert_done()
			self.albaran_salida.unlink()


		parameters = self.env['production.parameter'].search([])[0]

		for i in self.lineas_especial:
			actualizar = self.env['stock.move'].search([('lot_num','=',i.lote.id),('location_id','=',parameters.picking_type_trasferencias_costeo.default_location_src_id.id),('location_dest_id','=',parameters.picking_type_trasferencias_costeo.default_location_dest_id.id)])
			for j in actualizar:
				j.precio_unitario_manual = 0
		

		self.state = '6'




	@api.one
	def regresar_expediente(self):
		for i in self.lineas:
			i.gastos_generales = 0
		self.state = '4'

					

	@api.one
	def actualizar(self):


		for i in self.lineas:
			i.unlink()

		for i in self.lineas_editable:
			i.unlink()

		for i in self.lineas_especial:
			i.unlink()

		productos='{'
		almacenes='{'

		lst_products  = self.env['product.product'].search([('type','=','product')])

		for producto in lst_products:
			productos=productos+str(producto.id)+','
		productos=productos[:-1]+'}'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
		almacenes=almacenes[:-1]+'}'

		origenes = [-1,-1,-1]
		destinos = [-1,-1,-1]

		checkeo = {0:False}
		tipo_salida = {}

		tipo_producion = {}

		parameters = self.env['production.parameter'].search([])[0]
		if len(parameters.destino_picking_t_id) == 0:
			raise osv.except_osv('Alerta!','No se configuro el parametro "Almacen Lotes"')

		for i in parameters.ubicaciones_check:
			origenes.append(i.ubicacion.id)
			checkeo[i.ubicacion.id] = i.check

		for i in parameters.destino_picking_t_id:
			destinos.append(i.destino.id)
			tipo_salida[i.destino.id] = i.picking_type.id	
			tipo_producion[i.destino.id] = i.picking_type_salidas.id

		t = """ 
			 select lotemp, sum(ingreso) as movimiento,max(ubicacion_origen) as origen, max(ubicacion_destino) as destino,max(location_id) as location, product_id from get_kardex_v("""+ str(self.periodo.fiscalyear_id.name) + "0101," + str(self.periodo.date_stop).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
			 where fecha >= '""" +str(self.periodo.date_start)+ """' and fecha <= '""" +str(self.periodo.date_stop)+ """' and lotemp is not null and lotemp != '' 
			 and ubicacion_origen in """ +str(tuple(origenes))+ """
			 and (ubicacion_destino in """ + str(tuple(destinos)) + """ or ( location_id in """ + str(tuple(destinos)) + """ and ubicacion_destino = 0 ) )
			 group by lotemp, product_id
			 order by lotemp
		"""

		self.env.cr.execute(t)

		rptkardex = self.env.cr.dictfetchall()

		print checkeo
		for i in rptkardex:
			lote_a = self.env['purchase.liquidation'].search([('name','=', i['lotemp'] )])[0]
			print i['destino'], i['location']
			data = {
				'periodo':self.periodo.id,
				'lote': lote_a.id,
				'producto':i['product_id'],
				'toneladas_secas':i['movimiento'],
				'zona': lote_a.source_zone.analytic_id.zona_id.id,
				'picking_t_id': tipo_salida[ i['location'] if i['destino'] == 0 else i['destino']],
				'picking_t_p_id': tipo_producion[ i['location'] if i['destino'] == 0 else i['destino']],
				'ubicacion_check': checkeo[i['origen']],
				'padre': self.id,
			}
			self.env['costeo.line.it'].create(data)

		#nueva logica para los mov especiales

		t = """ 
			 select kardex.lotemp, sum(kardex.ingreso) as movimiento,max(kardex.ubicacion_origen) as origen, max(kardex.ubicacion_destino) as destino,max(kardex.location_id) as location, kardex.product_id , max(sm.lote_padre) as sk from get_kardex_v("""+ str(self.periodo.fiscalyear_id.name) + "0101," + str(self.periodo.date_stop).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])  as kardex
			 left join stock_move sm on sm.id = kardex.stock_moveid
			 where fecha >= '""" +str(self.periodo.date_start)+ """' and fecha <= '""" +str(self.periodo.date_stop)+ """' and lotemp is not null and lotemp != '' 
			 and ubicacion_origen = """ +str( parameters.picking_type_trasferencias_costeo.default_location_src_id.id )+ """
			 and ubicacion_destino = """ + str( parameters.picking_type_trasferencias_costeo.default_location_dest_id.id ) + """
			 group by kardex.lotemp, kardex.product_id
			 order by kardex.lotemp
		"""

		self.env.cr.execute(t)

		rptkardex = self.env.cr.dictfetchall()

		print checkeo
		for i in rptkardex:
			lote_a = self.env['purchase.liquidation'].search([('name','=', i['lotemp'] )])[0]

			data = {
				'periodo':self.periodo.id,
				'lote': i['sk'],
				'lote': lote_a.id,
				'producto':i['product_id'],
				'toneladas_secas':i['movimiento'],
				'zona': False,
				'picking_t_id': parameters.picking_type_trasferencias_costeo.id,
				'ubicacion_check': False,
				'ubicacion_especial':True,
				'padre': self.id,
			}
			self.env['costeo.line.it'].create(data)


	@api.one
	def actualizar_transferencias_listado(self):

		for i in self.lineas_especial:
			i.unlink()


		productos='{'
		almacenes='{'

		lst_products  = self.env['product.product'].search([('type','=','product')])

		for producto in lst_products:
			productos=productos+str(producto.id)+','
		productos=productos[:-1]+'}'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
		almacenes=almacenes[:-1]+'}'

		origenes = [-1,-1,-1]
		destinos = [-1,-1,-1]

		checkeo = {0:False}
		tipo_salida = {}

		tipo_producion = {}

		parameters = self.env['production.parameter'].search([])[0]
		if len(parameters.destino_picking_t_id) == 0:
			raise osv.except_osv('Alerta!','No se configuro el parametro "Almacen Lotes"')


		#nueva logica para los mov especiales

		t = """ 
			 select kardex.lotemp, sum(kardex.ingreso) as movimiento,max(kardex.ubicacion_origen) as origen, max(kardex.ubicacion_destino) as destino,max(kardex.location_id) as location, kardex.product_id , max(sm.lote_padre) as sk from get_kardex_v("""+ str(self.periodo.fiscalyear_id.name) + "0101," + str(self.periodo.date_stop).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])  as kardex
			 left join stock_move sm on sm.id = kardex.stock_moveid
			 where fecha >= '""" +str(self.periodo.date_start)+ """' and fecha <= '""" +str(self.periodo.date_stop)+ """' and lotemp is not null and lotemp != '' 
			 and ubicacion_origen = """ +str( parameters.picking_type_trasferencias_costeo.default_location_src_id.id )+ """
			 and ubicacion_destino = """ + str( parameters.picking_type_trasferencias_costeo.default_location_dest_id.id ) + """
			 group by kardex.lotemp, kardex.product_id
			 order by kardex.lotemp
		"""

		self.env.cr.execute(t)

		rptkardex = self.env.cr.dictfetchall()

		print checkeo
		for i in rptkardex:
			lote_a = self.env['purchase.liquidation'].search([('name','=', i['lotemp'] )])[0]

			data = {
				'periodo':self.periodo.id,
				'lote_padre': i['sk'],
				'lote': lote_a.id,
				'producto':i['product_id'],
				'toneladas_secas':i['movimiento'],
				'zona': False,
				'picking_t_id': parameters.picking_type_trasferencias_costeo.id,
				'ubicacion_check': False,
				'ubicacion_especial':True,
				'padre': self.id,
			}
			self.env['costeo.line.it'].create(data)


	@api.one
	def actualizar_transferencias(self):
		parameters = self.env['production.parameter'].search([])[0]

		for i in self.lineas_especial:
			actualizar = self.env['stock.move'].search([('lot_num','=',i.lote.id),('location_id','=',parameters.picking_type_trasferencias_costeo.default_location_src_id.id),('location_dest_id','=',parameters.picking_type_trasferencias_costeo.default_location_dest_id.id)])
			for j in actualizar:
				j.precio_unitario_manual = i.total_costo
		
	@api.one
	def actualizar_transferencias_montos(self):		
		for i in self.lineas_especial:
			if i.lote_padre.id:
				elem = self.env['costeo.line.it'].search([('lote','=',i.lote_padre.id),('padre','!=',False)])
				if len(elem)>0:
					porcen = (i.toneladas_secas)/(elem[0].toneladas_secas)
					i.costo_oro = porcen*elem[0].costo_oro
					i.costo_plata = porcen*elem[0].costo_plata
					i.costo_chancado = porcen*elem[0].costo_chancado
					i.costo_zona = porcen*elem[0].costo_zona
					i.costo_expediente = porcen*elem[0].costo_expediente
					i.gastos_generales = porcen*elem[0].gastos_generales
					i.total_costo = porcen*elem[0].total_costo

	@api.one
	def jalar_cuentas_analiticas(self):
		param = self.env['production.parameter'].search([])[0]
		elem = []
		for i in param.listado_costo_analitico:
			for j in self.env['account.analytic.account'].search([('parent_id','=',i.id)]):
				elem.append(j)
		for i in self.analytics_ids:
			i.unlink()

		for i in elem:
			dicts = {
				'analitic_id':i.id,
				'monto':0,
				'costeo_id':self.id,
			}
			self.env['gastos.generales.rel'].create(dicts)
