# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
from datetime import datetime
from datetime import timedelta
from tempfile import TemporaryFile
import csv
import base64
import sys
reload(sys)  
sys.setdefaultencoding('utf8')


class import_out_picking(models.Model):
	_name = 'import.out.picking'
	_rec_name = 'import_date'

	state = fields.Selection([('draft','Borrador'),('process_exception','Excepciones'),('ready','Listo para importar'),('done','Hecho')],"Estado", default="draft", compute='_get_state')
	binary_file = fields.Binary("File")
	file_name = fields.Char("Nombre")
	import_date = fields.Date("Fecha importación", readonly=1)
	reason = fields.Char("Motivo", default="Salida", readonly=1)
	picking_type = fields.Many2one('stock.picking.type', 'Tipo Picking')
	lines = fields.One2many('import.out.picking.line', 'parent', 'Detalle', domain=[('state','=','invalid')])
	lines2 = fields.One2many('import.out.picking.line', 'parent', 'Detalle', domain=[('state','=','valid')])
	lines3 = fields.One2many('import.out.picking.line', 'parent', 'Detalle', domain=[('state','=','done')])
	done = fields.Boolean("Hecho", default=False)

	@api.model
	def create(self,vals):
		vals['reason'] = 'Salida'
		return super(import_out_picking,self).create(vals)

	@api.one
	def _get_state(self):
		if self.done:
			self.state = 'done'
		else:
			self.state = 'draft'
			lines = self.env['import.out.picking.line'].search([('parent','=',self.id)])
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
			line_obj = self.env['import.out.picking.line']
			data = self.read()[0]
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(data['binary_file']))
			fileobj.seek(0)
			c=base64.decodestring(data['binary_file'])
			fic = csv.reader(fileobj,delimiter=';',quotechar='"')	
			#Procesamiento
			for data in fic:
				product_id = self.env['product.product'].search([('default_code','=',data[0].strip())])
				account_id = self.env['account.analytic.account'].search([('code','=',data[4].strip())])
				vals = {
					'parent'			: self.id,
					'code'				: data[0].strip(),
					'account'			: data[4].strip(),
					'qty'				: float(data[1].strip()) if data[1] else 0,
					'date'				: data[3].strip(),
					'order'				: data[5].strip(),
					'state'				: 'valid',
				}
				#Validaciones
				vals['observations'] = ''
				if not product_id:
					vals['observations'] += 'Producto no encontrado,'
					vals['state'] = 'invalid'
				else:
					if len(product_id) > 1:
						vals['observations'] += u'Código duplicado,'
						vals['state'] = 'invalid'
				if not account_id:
					vals['observations'] += u'Cuenta inválida.'
					vals['state'] = 'invalid'
				
				line_obj.create(vals)
		else:
			raise osv.except_osv('Alerta!',"No hay un archivo ingresado.")


	@api.one
	def import_data(self):
		self.import_date = fields.Date.today()
		lines = self.env['import.out.picking.line'].search([('parent','=',self.id),('state','=','valid')])
		picking = self.env['stock.picking']
		move = self.env['stock.move']
		prev_order = ''
		picking_id = None
		for line in lines:
			if prev_order != line.order:
				if picking_id:
					picking_id.do_transfer()
				#Creación de Picking
				vals = {
					'motivo_guia'		: '7',
					'date'				: datetime.strptime(line.date + ' 05:00:00', '%Y-%m-%d %H:%M:%S'),
					'min_date'			: datetime.strptime(line.date + ' 05:00:00', '%Y-%m-%d %H:%M:%S'),
					'move_type'			: 'direct',
					'picking_type_id'	: self.picking_type.id,
					'priority'			: '1',
					'origin'			: line.order,
				}
				picking_id = picking.create(vals)
				prev_order = line.order
			#Lineas de Picking
			product_id = self.env['product.product'].search([('default_code','=',line.code)])
			account_id = self.env['account.analytic.account'].search([('code','=',line.account)])
			vals = {
				'picking_id'		: picking_id.id,
				'product_id'		: product_id[0].id,
				'product_uom_qty'	: line.qty,
				'product_uom'		: product_id[0].uom_id.id,
				'date'				: picking_id.date,
				'date_expected'		: picking_id.date,
				'analitic_id'		: account_id.id,
				'name'				: product_id[0].name,
				'invoice_state'		: 'none',
				'location_id'		: self.picking_type.default_location_src_id.id,
				'location_dest_id'	: self.picking_type.default_location_dest_id.id,
			}
			move.create(vals)
		picking_id.do_transfer()
		self.done = True


class import_out_picking_line(models.Model):
	_name = 'import.out.picking.line'

	parent = fields.Many2one('import.out_picking','Import')
	code = fields.Char("Código")
	qty = fields.Float("Cantidad")
	date = fields.Date("Fecha Kardex")
	account = fields.Char("Centro Costo")
	order = fields.Char("Orden Salida")
	observations = fields.Char("Observaciones", readonly=1)
	state = fields.Selection([('invalid', 'Inválido'),('valid','Válido'),('done','Procesado')], readonly=1)