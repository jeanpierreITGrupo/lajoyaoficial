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


class purchase_parameter(models.Model):
	_name = 'purchase.parameter'

	def init(self, cr):
		cr.execute('select id from res_users')
		uid = cr.dictfetchall()
		print 'uid', uid
		print 'uid0', uid[0]['id']
		cr.execute('select id from purchase_parameter')
		ids = cr.fetchall()
		
		print 'ids', ids
		
		if len(ids) == 0:
			cr.execute("""INSERT INTO purchase_parameter (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Parametros Generales');""")
	
	name = fields.Char('Nombre',size=50, default='Parametros Generales')

	picking_type_default = fields.Many2one('stock.picking.type','Almacen Defecto Compras')
	


class area_table(models.Model):
	_name = 'area.table'

	name = fields.Char('Area')


class purchase_order(models.Model):
	_inherit = 'purchase.order'

	licitacion_advance_id = fields.Many2one('licitacion.advance','Referencia')
	name_descdetalle = fields.Text(u'Descripción',related='order_line.name')



class purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'

	licitacion_advance_linea_id = fields.Many2one('licitacion.advance.linea','Referencia')

class licitacion_advance_linea(models.Model):
	_name  = 'licitacion.advance.linea'
	_order = 'nro_item'


	@api.one
	def get_cantidad_pedido(self):
		ini = 0
		for i in self.lineas_pol:
			if i.state != 'draft':
				ini += i.product_qty
		self.cantidad_pedido = ini


	@api.one
	def get_saldo_pedido(self):
		self.saldo_pedido = self.cantidad - self.cantidad_pedido

	nro_item = fields.Integer('Nro. Item',default=0)
	oculto = fields.Boolean('Seleccionado',default=True)
	centro_costo = fields.Many2one('account.analytic.account','Centro de Costo')
	product_id = fields.Many2one('product.product','Producto')
	descripcion = fields.Char('Descripción')
	unidad = fields.Many2one('product.uom','Unidad de Producto',related='product_id.uom_id',readonly=True)
	cantidad = fields.Float('Cantidad',digits=(12,2))
	justificacion = fields.Char('Justificación')
	prioridad = fields.Char('Prioridad')
	cantidad_pedido = fields.Float('Cantidad en Pedido',compute="get_cantidad_pedido")
	saldo_pedido = fields.Float('Saldo por Pedir',compute="get_saldo_pedido",store=False)
	fecha_llegada = fields.Date('Fecha Llegada Planta')
	proveedor = fields.Many2one('res.partner','Proveedor',domain=[('supplier','=',True)])

	lineas_pol = fields.One2many('purchase.order.line','licitacion_advance_linea_id','Lineas POL')

	padre = fields.Many2one('licitacion.advance','Padre')

	@api.onchange('product_id')
	def onchange_product_id(self):
		if self.product_id.id:
			self.unidad = self.product_id.uom_id.id
			self.descripcion = self.product_id.name
		else:
			self.unidad = False
			self.descripcion = ''


	@api.one
	def write(self,vals):
		if self.padre.state == 'aprobado':
			if (len(vals)== 1 and 'oculto' in vals) or 'nro_item' in vals:
				pass
			else:
				raise osv.except_osv('Alerta!','No se puede editar una linea en una licitacion ya Aprobada')
		return super(licitacion_advance_linea,self).write(vals)

	@api.model
	def create(self,vals):
		t = super(licitacion_advance_linea,self).create(vals)
		if t.padre.state == 'aprobado':
			raise osv.except_osv('Alerta!','No se puede crear una linea en una licitacion ya Aprobada')
		return t

	@api.one
	def unlink(self):
		if self.padre.state == 'aprobado':
			raise osv.except_osv('Alerta!','No se puede eliminar una linea en una licitacion ya Aprobada')

		if len(self.lineas_pol)>0:
			raise osv.except_osv('Alerta!','No se puede eliminar una linea con Solicitudes o Pedidos creados')
		return super(licitacion_advance_linea,self).unlink()

	@api.one
	def ocultar(self):
		self.oculto = False
		"""
	@api.one
	def write(self,vals):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		g1_ids = all_groups.search([('name','=',u'Modificar Licitacion Mensual')])
				
		if not g1_ids: 
			raise osv.except_osv('Alerta!', "No existe el grupo 'Modificar Licitacion Mensual' creada.") 

		if self.env.uid != self.create_uid:
			if not g1_ids in all_users.search([('id','=',self.env.uid)])[0].groups_id:	
				raise osv.except_osv('Alerta','Esta licitación fue creado por otro usuario.')

		t = super(licitacion_advance_linea,self).write(vals)
		return t """

class licitacion_advance(models.Model):
	_name = 'licitacion.advance'
	_rec_name  = 'number'

	state = fields.Selection([('draft','Borrador'),('aprobado','Aprobado')],'Estado', default='draft' )
	number = fields.Char('Número')
	fecha = fields.Date('Fecha Requerimiento Pedido')
	solicitante = fields.Many2one('hr.employee','Solicitante')
	area = fields.Many2one('area.table','Area')
	lineas = fields.One2many('licitacion.advance.linea','padre','Detalle',domain=[('oculto','!=',0)])
	lineas_pedidos = fields.One2many('purchase.order','licitacion_advance_id','Pedidos')


	f_cantidad = fields.Float('Cantidad')
	c_cantidad = fields.Boolean('Check')
	f_producto = fields.Many2one('product.product','Producto')
	c_producto = fields.Boolean('Check')
	f_proveedor = fields.Many2one('res.partner','Proveedor',domain=[('supplier','=',True)])
	c_proveedor = fields.Boolean('Check')
	f_prioridad = fields.Char('Prioridad')
	c_prioridad = fields.Boolean('Check')
	f_fecha = fields.Date('Fecha Llegada')
	c_fecha = fields.Boolean('Check')

	@api.one
	def verificar_validador(self):	
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		g1_ids = all_groups.search([('name','=',u'Aprobar Licitacion Mensual')])
				
		if not g1_ids: 
			raise osv.except_osv('Alerta!', "No existe el grupo 'Aprobar Licitacion Mensual' creada.") 

		if not g1_ids in all_users.search([('id','=',self.env.uid)])[0].groups_id:	
			raise osv.except_osv('Alerta!', u"No tiene permisos para aprobar")
		self.state = 'aprobado'
	
	
	@api.one
	def get_totallinea(self):
		self.totallinea= len(self.env['licitacion.advance.linea'].search([('padre','=',self.id)]))


	@api.one
	def get_lineaconsumida(self):
		intotal = 0
		for i in self.env['licitacion.advance.linea'].search([('padre','=',self.id)]):			
			if i.saldo_pedido != i.cantidad or i.saldo_pedido <=0:
				intotal += 1

		self.lineaconsumida = intotal


	@api.one
	def filtrar(self):

		for i in self.env['licitacion.advance.linea'].search([('padre','=',self.id)]):
			i.oculto = False

		filtro = [('padre','=',self.id)]
		if self.c_cantidad:
			filtro.append( ('cantidad','=',self.f_cantidad) )

		if self.c_producto:
			filtro.append(('product_id','=',self.f_producto.id))

		if self.c_proveedor:
			filtro.append(('proveedor','=',self.f_proveedor.id))

		if self.c_prioridad:
			filtro.append(('prioridad','=',self.f_prioridad))

		if self.c_fecha:
			filtro.append(('fecha_llegada','=',self.f_fecha))

		for i in self.env['licitacion.advance.linea'].search(filtro):
			i.oculto = True

	@api.one
	def get_lineaporconsumir(self):
		intotal = 0
		for i in self.env['licitacion.advance.linea'].search([('padre','=',self.id)]):			
			if i.saldo_pedido != 0:
				intotal += 1

		self.lineaporconsumir = intotal



	@api.one
	def get_solicitudnro(self):
		cont = 0
		for i in self.lineas_pedidos:
			if i.state== 'draft':
				cont+=1
		self.solicitudnro = cont



	@api.one
	def get_pedidosnro(self):

		cont = 0
		for i in self.lineas_pedidos:
			if i.state!= 'draft':
				cont+=1
		self.pedidosnro = cont


	totallinea = fields.Integer('Total Lineas',compute='get_totallinea')
	lineaconsumida = fields.Integer('Total Lineas',compute='get_lineaconsumida')
	lineaporconsumir = fields.Integer('Total Lineas',compute='get_lineaporconsumir')
	pedidosnro = fields.Integer('Total Pedidos', compute='get_pedidosnro')
	solicitudnro = fields.Integer('Total Pedidos', compute='get_solicitudnro')
	@api.one
	def actualizar(self):
		return True


	@api.model
	def create(self,vals):
		t = super(licitacion_advance,self).create(vals)
		nro = 1
		for i in self.env['licitacion.advance.linea'].search([('padre','=',t.id)]).sorted(key=lambda r: r.id):
			i.nro_item = nro
			nro+=1

		sequence_obj = self.env['ir.sequence']
		sequence_id = sequence_obj.search([('name','=','Licitacion Mensual')])
		if sequence_id and sequence_id.id:
			t.number = sequence_id.next_by_id(sequence_id.id)
		else:
			dic_new_seq = {
				'name': 'Licitacion Mensual',
				'padding': 6,
				'number_next_actual': 1,
				'number_increment': 1,
				'implementation': 'no_gap',
				'prefix': 'LM-',
			}
			new_sequence= self.env['ir.sequence'].create(dic_new_seq)
			t.number = new_sequence.next_by_id(new_sequence.id)
		return t


	@api.multi
	def ver_pedidos(self):
		ids_r = []
		for i in self.lineas_pedidos:
			if i.state !='draft':
				ids_r.append(i.id)
		return {
            'name': 'Pedidos',
            'view_mode': 'tree,form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': unicode([('id', 'in', ids_r )]),
        }


	@api.multi
	def ver_solicitudes(self):
		ids_r = []
		for i in self.lineas_pedidos:
			if i.state =='draft':
				ids_r.append(i.id)
		return {
            'name': 'Solicitudes',
            'view_mode': 'tree,form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': unicode([('id', 'in', ids_r )]),
        }



	@api.one
	def write(self,vals):
		"""

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		g1_ids = all_groups.search([('name','=',u'Modificar Licitacion Mensual')])
				
		if not g1_ids: 
			raise osv.except_osv('Alerta!', "No existe el grupo 'Modificar Licitacion Mensual' creada.") 

		if self.env.uid != self.create_uid:
			if not g1_ids in all_users.search([('id','=',self.env.uid)])[0].groups_id:	
				raise osv.except_osv('Alerta','Esta licitación fue creado por otro usuario.') """

		t = super(licitacion_advance,self).write(vals)
		self.refresh()
		nro=1
		for i in self.env['licitacion.advance.linea'].search([('padre','=',self.id)]).sorted(key=lambda r: r.id):
			i.nro_item = nro
			nro+=1
		return t


	@api.one
	def ver_todo(self):
		for i in self.env['licitacion.advance.linea'].search([('padre','=',self.id)]):
			i.oculto= True
	@api.one
	def ver_restantes(self):
		for i in self.env['licitacion.advance.linea'].search([('padre','=',self.id)]):
			if i.saldo_pedido != 0:
				i.oculto = True
			else:
				i.oculto = False
	@api.one
	def ver_consumidos(self):
		for i in self.env['licitacion.advance.linea'].search([('padre','=',self.id)]):
			if i.saldo_pedido != i.cantidad or i.saldo_pedido <=0:
				i.oculto = True
			else:
				i.oculto = False


	@api.one
	def generar(self):

		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		g1_ids = all_groups.search([('name','=',u'Generar Licitacion Mensual')])
				
		if not g1_ids: 
			raise osv.except_osv('Alerta!', "No existe el grupo 'Generar Licitacion Mensual' creada.") 

		if not g1_ids in all_users.search([('id','=',self.env.uid)])[0].groups_id:	
			raise osv.except_osv('Alerta','No tiene permisos para generar la solicitud.')

		pro_id = None
		flag_cabecera = False
		act_cabe= None
		for i in self.lineas.sorted(key=lambda r: r.proveedor.id):
			if i.saldo_pedido >0:
				if pro_id == None:
					pro_id = i.proveedor.id
					flag_cabecera = True

				if pro_id != i.proveedor.id:
					pro_id = i.proveedor.id
					flag_cabecera = True
				import datetime
				if flag_cabecera:
					pick_type_tmp = self.env['purchase.parameter'].search([])[0].picking_type_default
					if not pick_type_tmp:
						raise osv.except_osv('Alerta!','No se configuro parametros.')
				
					data = {
						'partner_id':i.proveedor.id,
						'pricelist_id':i.proveedor.property_product_pricelist_purchase.id,
						'date_order':datetime.datetime.now().strftime('%Y-%m-%d'),
						'currency_id':self.env['res.currency'].search([('name','=','PEN')])[0].id,
						'picking_type_id':pick_type_tmp.id,
						'licitacion_advance_id':self.id,
						'state':'draft',
						'invoice_method':'order',
						'location_id':pick_type_tmp.default_location_dest_id.id,
					}
					act_cabe = self.env['purchase.order'].create(data)
					flag_cabecera= False

				data_l = {
					'product_id':i.product_id.id,
					'product_qty':i.saldo_pedido,
					'product_uom':i.product_id.uom_id.id,
					'name':i.descripcion,
					'date_planned':datetime.datetime.now().strftime('%Y-%m-%d'),
					'account_analytic_id':i.centro_costo.id ,
					'price_unit':i.product_id.standard_price, 
					'licitacion_advance_linea_id':i.id,
					'order_id':act_cabe.id,
				}
				linea = self.env['purchase.order.line'].create(data_l)