# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
from datetime import datetime
from datetime import timedelta
from tempfile import TemporaryFile
import csv
import base64

class import_inventory(models.Model):
	_name = 'import.inventory'
	_rec_name = 'import_date'

	state = fields.Selection([('draft','Borrador'),('process_exception','Excepciones'),('ready','Listo para importar'),('done','Hecho')],"Estado", default="draft", compute='_get_state')
	binary_file = fields.Binary("File")
	file_name = fields.Char("Nombre")
	import_date = fields.Date("Fecha importación", readonly=1)
	reason = fields.Char("Motivo", default="Saldo inicial", readonly=1)
	picking_type = fields.Many2one('stock.picking.type', 'Tipo Picking')
	lines = fields.One2many('import.inventory.line', 'parent', 'Detalle', domain=[('state','=','invalid')])
	lines2 = fields.One2many('import.inventory.line', 'parent', 'Detalle', domain=[('state','=','valid')])
	lines3 = fields.One2many('import.inventory.line', 'parent', 'Detalle', domain=[('state','=','done')])
	done = fields.Boolean("Hecho")

	@api.model
	def create(self,vals):
		vals['reason'] = 'Saldo inicial'
		vals['import_date'] = fields.Date.today()
		return super(import_inventory,self).create(vals)

	@api.one
	def _get_state(self):
		if self.done:
			self.state = 'done'
		else:
			self.state = 'draft'
			lines = self.env['import.inventory.line'].search([('parent','=',self.id)])
			if lines:
				self.state = 'ready'
				for line in self.lines:
					if line.state == 'invalid':
						self.state = 'process_exception'
						break

	@api.one
	def pre_process_data(self):
		for line in self.lines:
			line.unlink()
		if self.binary_file:
			self.env.cr.execute("set client_encoding ='UTF8';")
			line_obj = self.env['import.inventory.line']
			data = self.read()[0]
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(data['binary_file']))
			fileobj.seek(0)
			c=base64.decodestring(data['binary_file'])
			fic = csv.reader(fileobj,delimiter=';',quotechar='"')
			#Procesamiento
			for data in fic:
				product_id = self.env['product.product'].search([('default_code','=',data[0].strip())])
				vals = {
					'parent'			: self.id,
					'code'				: data[0].strip(),
					'qty'				: float(data[1].strip()) if data[1] else 0,
					'price_unit'		: float(data[2].strip()) if data[2] else 0,
					'state'				: 'valid',
				}
				#Verifica existencia de producto
				vals['observations'] = ''
				if not product_id:
					vals['observations'] = 'Producto no encontrado.'
					vals['state'] = 'invalid'
				
				#Las lineas inválidas son mostradas para corrección
				line_obj.create(vals)
		else:
			raise osv.except_osv('Alerta!',"No hay un archivo ingresado.")


	@api.one
	def import_data(self):
		self.import_date = fields.Date.today()
		lines = self.env['import.inventory.line'].search([('parent','=',self.id),('state','=','valid')])
		picking = self.env['stock.picking']
		move = self.env['stock.move']
		count = 0
		size_picking = 10 #Cantidad de líneas para el picking
		picking_id = None
		for line in lines:
			product_id = self.env['product.product'].search([('default_code','=',line.code)])
			if count%size_picking == 0:
				if picking_id:
					picking_id.do_transfer()
				#Creación de Picking
				vals = {
					'motivo_guia'		: '15',
					'date'				: datetime.strptime("2019-02-01 05:00:00", '%Y-%m-%d %H:%M:%S'),
					'min_date'			: datetime.strptime("2019-02-01 05:00:00", '%Y-%m-%d %H:%M:%S'),
					'move_type'			: 'direct',
					'picking_type_id'	: self.picking_type.id,
					'priority'			: '1',
				}
				picking_id = picking.create(vals)
			#Lineas de Picking
			vals = {
				'picking_id'		: picking_id.id,
				'product_id'		: product_id.id,
				'product_uom_qty'	: line.qty,
				'price_unit'		: line.price_unit,
				'precio_unitario_manual'		: line.price_unit,
				'product_uom'		: product_id.uom_id.id,
				'date'				: picking_id.date,
				'date_expected'		: picking_id.date,
				'name'				: product_id.name,
				'invoice_state'		: 'none',
				'location_id'		: self.picking_type.default_location_src_id.id,
				'location_dest_id'	: self.picking_type.default_location_dest_id.id,
			}
			move.create(vals)
			count += 1
		picking_id.do_transfer()
		self.done = True


class import_inventory_line(models.Model):
	_name = 'import.inventory.line'

	parent = fields.Many2one('import.inventory','Import')
	code = fields.Char("Código")
	qty = fields.Float("Cantidad")
	price_unit = fields.Float("Costo Un.", digits=(10,4))
	observations = fields.Char("Observaciones", readonly=1)
	state = fields.Selection([('invalid', 'Inválido'),('valid','Válido'),('done','Procesado')], readonly=1)
