# -*- encoding: utf-8 -*-
import base64
from openerp.osv import osv
from openerp import models, fields, api
import csv
from tempfile import TemporaryFile

class stock_import_rest(models.Model):
	_name='stock.import.rest'

	date_rest = fields.Datetime('Fecha Inventario')
	picking_type_id = fields.Many2one('stock.picking.type','Tipo de Picking')
	stock_location_origin=fields.Many2one('stock.location','Ubic. origen')
	stock_location_dest = fields.Many2one('stock.location','Ubic. Destino')
	commet_sing = fields.Char('Valor para las notas')
	lines = fields.One2many('stock.import.rest.lines','main_import','Lineas')
	file_inv = fields.Binary('Archivo a Importar')

	@api.one
	def loadlines(self):
		for line in self.lines:
			line.unlink()
		if self.file_inv:
			self.env.cr.execute("set client_encoding ='UTF8';")
			line_obj = self.env['stock.import.rest.lines']
			data = self.read()[0]
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(data['file_inv']))
			fileobj.seek(0)
			c=base64.decodestring(data['file_inv'])
			fic = csv.reader(fileobj,delimiter='|',quotechar='"')
			#Creación de líneas en pantalla.
			for data in fic:
		
				try:
					pro = self.env['product.product'].browse(int(data[0]))
					tmpl = self.env['product.template'].browse(pro.product_tmpl_id.id)
					# print data[0],pro
					if pro:
						vals = {
							'product_id':data[0],
							'codprod':data[1],
							'product_name':data[2],
							'lot_num':data[3],
							'saldof':float(data[4]),
							'saldov':float(data[5]),
							'cprom':float(data[5])/float(data[4]),
							'main_import':self.id,
							'imported':False,
							'problem':None,
						}
						line_obj.create(vals)
				except Exception as e:
					vals = {
							'product_id':False,
							'codprod':data[1],
							'product_name':data[2],
							'lot_num':data[3],
							'saldof':float(data[4]),
							'saldov':float(data[5]),
							'cprom':float(data[5])/float(data[4]),
							'main_import':self.id,
							'imported':False,
							'problem':e,
						}
					line_obj.create(vals)


	@api.one
	def create_inv(self):
		npicking = 0 
		vals_picking = {
			'location_id':self.stock_location_origin.id,
			'location_dest_id':self.stock_location_dest.id,
			'fecha_kardex':self.date_rest,
			'origin':'Inventario Inicial',
			'date_done':self.date_rest,
			'picking_type_id':self.picking_type_id.id,
			'min_date':self.date_rest,
			'date':self.date_rest,
			'max_date':self.date_rest,
			'name':'Inventario '+' - '+self.stock_location_dest.location_id.name,
			'motivo_guia':'15',
		}
		apickings = []
		picking_id = self.env['stock.picking'].create(vals_picking)
		print 1
		apickings.append(picking_id)
		count=0
		for line in self.lines:
			lote = self.env['purchase.liquidation'].search([('name','=',line.lot_num)])
			lote_id=None
			if lote:
				lote_id = lote.id
			print lote_id
			valores = self._get_move_values(line.product_id,
				line.cprom,
				line.saldof,
				self.stock_location_origin.id,
				self.stock_location_dest.id,
				picking_id,lote_id)


			self.env['stock.move'].create(valores)
			count=count+1
			if count>79:
				npicking=npicking+1
				print picking_id
				# picking_id.do_transfer()
				print '---------------->',picking_id.name
				vals_picking.update({'name':'Inventario - '+str(npicking)+' - '+self.stock_location_dest.location_id.name})
				picking_id = self.env['stock.picking'].create(vals_picking)

				print 2
				count =0
				# apickings.append(picking_id)
		# self.env['stock.picking'].do_transfer(apickings)
		# picking_id.do_transfer()
		print 3
		
		print 4
		return True

	def _get_move_values(self, product,price_unit,qty, location_id, location_dest_id,idmain,lote_id):
		self.ensure_one()
		cadname = 'importado - '+ str(self.id) +str(product.id)
		return {
			'product_id': product.id,
			'product_uom': product.uom_id.id,
			'product_uom_qty': qty,
			# 'product_qty': qty,
			'precio_unitario_manual':price_unit,
			'date': self.date_rest,
			'location_id': location_id,
			'location_dest_id': location_dest_id,
			'picking_id':idmain.id,
			'origin':'Inventario Inicial',
			'picking_type_id':self.picking_type_id.id,
			'ordered_qty':qty,
			'date_expected':self.date_rest,
			'name': 'INV:' + (idmain.name or ''),
			'lot_num':lote_id,
		}







class stock_import_rest_lines(models.Model):
	_name='stock.import.rest.lines'

	product_id = fields.Many2one('product.product','Producto')
	codprod = fields.Char(u'Código producto')
	product_name = fields.Char('Producto')
	lot_num = fields.Char('Lote')
	saldof = fields.Float(u'Saldo Físico')
	saldov = fields.Float(u'Saldo Valorado')
	cprom =  fields.Float(u'Costo Promedio')
	main_import = fields.Many2one('stock.import.rest','main')

	imported = fields.Boolean('Importado')
	problem = fields.Text('Problema')
