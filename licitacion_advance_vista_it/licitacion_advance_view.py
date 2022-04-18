# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

import datetime

class licitacion_advance_view(models.Model):
	_name = 'licitacion.advance.view'
	_auto = False
	_order = 'licitacion_id'	

	linea_id = fields.Many2one('licitacion.advance.linea')

	licitacion_id = fields.Many2one('licitacion.advance', u'Nro. Licitación')
	date = fields.Date('Fecha')
	employee_id = fields.Many2one('hr.employee','Solicitante')
	area_id = fields.Many2one('area.table', u'Área')
	analytic_id = fields.Many2one('account.analytic.account',u'Centro de Costo')
	product_id = fields.Many2one('product.product', u'Producto')
	description = fields.Char(u'Descripción')
	uom_id = fields.Many2one('product.uom',u'Unidad de Medida')
	justification = fields.Char(u'Justificación')
	priority = fields.Char(u'Prioridad')
	required_qty = fields.Float(u'Cantidad Solicitada')
	order_qty = fields.Float(u'Cantidad en Pedido', related="linea_id.cantidad_pedido")
	order_stock = fields.Float(u'Saldo por Pedir')
	arrival_date = fields.Date(u'Fecha Llegada Planta')
	partner_id = fields.Many2one('res.partner',u'Proveedor')

	def init(self,cr):
		cr.execute("""
			DROP VIEW if exists licitacion_advance_view;
			CREATE OR REPLACE view licitacion_advance_view as (
				SELECT row_number() OVER () AS id,*
				FROM (
					select
						lal.id as linea_id,
						
						la.id as licitacion_id, 
						la.fecha as date, 
						la.solicitante as employee_id, 
						la.area as area_id, 
						lal.centro_costo as analytic_id, 
						lal.product_id as product_id, 
						lal.descripcion as description, 
						pt.uom_id as uom_id, 
						lal.justificacion as justification,
						lal.prioridad as priority,
						lal.cantidad as required_qty,
						lal.cantidad - coalesce(x.saldo,0) as order_stock,
						lal.fecha_llegada as arrival_date,
						lal.proveedor as partner_id
					from licitacion_advance_linea lal
					inner join product_product pp on pp.id = lal.product_id
					inner join product_template pt on pt.id = pp.product_tmpl_id
					inner join licitacion_advance la on lal.padre = la.id
					left join (
						select ll.id as line_id, coalesce(sum(pol.product_qty),0) as saldo from licitacion_advance_linea ll
						left join purchase_order_line pol on pol.licitacion_advance_linea_id = ll.id
						left join purchase_order po on po.id = pol.order_id
						where po.state !='draft'
						group by ll.id
					) as x on x.line_id = lal.id
				)T
			)
		""")

	@api.multi
	def export_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")
		workbook = Workbook( direccion + u'Licitaciones_con_saldo.xlsx')
		worksheet = workbook.add_worksheet(u"Licitaciones")

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
		boldcentred = workbook.add_format({'bold': True})
		boldcentred.set_align('center')
		boldcentred.set_border(style=1)

		numbersix = workbook.add_format()
		numbersix.set_num_format('#,##0.00')
		numbersix.set_text_wrap()
		numbersix.set_border()
		
		numbersixred = workbook.add_format()
		numbersixred.set_num_format('#,##0.00')
		numbersixred.set_font_color('red')
		numbersixred.set_border()

		x= 6				
		worksheet.write(1,0, u"Licitaciones con Saldo", bold)

		columnas = [u'Nro. Licitación', 
					u'Fecha', 
					u'Solicitante',
					u'Área',
					u'Centro de Costo',
					u'Producto',
					u'Descripción',
					u'Unidad de Medida',
					u'Justificación',
					u'Prioridad',
					u'Cantidad Solicitada',
					u'Cantidad en Pedido',
					u'Saldo por Pedir',
					u'Fecha Llegada Planta',
					u'Proveedor']

		worksheet.set_column('A:D', 23.14)
		worksheet.set_column('E:G', 58.57)
		worksheet.set_column('H:H', 23.14)
		worksheet.set_column('I:I', 58.57)
		worksheet.set_column('J:J', 9.29)
		worksheet.set_column('K:M', 23.14)
		worksheet.set_column('N:N', 23.14)
		worksheet.set_column('O:O', 58.57)

		for i in range(len(columnas)):
			worksheet.write(5,i, columnas[i], boldcentred)

		for licitacion in self.env['licitacion.advance.view'].search([]):

			la = self.env['licitacion.advance'].search([('id','=',licitacion.licitacion_id.id)])
			he = self.env['hr.employee'].search([('id','=',licitacion.employee_id.id)])
			at = self.env['area.table'].search([('id','=',licitacion.area_id.id)])
			aaa = self.env['account.analytic.account'].search([('id','=',licitacion.analytic_id.id)])
			pp = self.env['product.product'].search([('id','=',licitacion.product_id.id)])
			pu = self.env['product.uom'].search([('id','=',licitacion.uom_id.id)])
			rp = self.env['res.partner'].search([('id','=',licitacion.partner_id.id)])

			worksheet.write(x,0, la[0].number if len(la) > 0 and la[0].number else '', bord)
			worksheet.write(x,1, licitacion.date if licitacion.date else '', bord)
			worksheet.write(x,2, he[0].name if len(he) > 0 and he[0].name else '', bord)
			worksheet.write(x,3, at[0].name if len(at) > 0 and at[0].name else '', bord)
			worksheet.write(x,4, aaa[0].name if len(aaa) > 0 and aaa[0].name else '', bord)
			worksheet.write(x,5, pp[0].name_template if len(pp) > 0 and pp[0].name_template else '', bord)
			worksheet.write(x,6, licitacion.description if licitacion.description else '', bord)
			worksheet.write(x,7, pu[0].name if len(pu) > 0 and pu[0].name else '', bord)
			worksheet.write(x,8, licitacion.justification if licitacion.justification else '', bord)
			worksheet.write(x,9, licitacion.priority if licitacion.priority else '', bord)
			worksheet.write(x,10, licitacion.required_qty if licitacion.required_qty else 0, numbersix)
			worksheet.write(x,11, licitacion.order_qty if licitacion.order_qty else 0, numbersix)
			worksheet.write(x,12, licitacion.order_stock if licitacion.order_stock else 0, numbersix)
			worksheet.write(x,13, licitacion.arrival_date if licitacion.arrival_date else '', bord)
			worksheet.write(x,14, rp[0].name if len(rp) > 0 and rp[0].name else '', bord)

			x += 1

		workbook.close()

		
		f = open( direccion + u'Licitaciones_con_saldo.xlsx', 'rb')
		
		
		vals = {
			'output_name': u'Licitaciones_con_saldo.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}


class licitacion_advance_view_reporte(models.Model):
	_name = 'licitacion.advance.view.reporte'

	fecha = fields.Date('Fecha')

	@api.multi
	def do_rebuild(self):
		return {
			"domain": [('order_stock','>',0),('arrival_date','>',self.fecha)],
		    "type": "ir.actions.act_window",
		    "res_model": "licitacion.advance.view",
		    "views": [[False, "tree"]],
		}