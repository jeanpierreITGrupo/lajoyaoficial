# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

#Orden de Compra


class production_parameter(models.Model):
	_inherit = "production.parameter"

	seq_ruma = fields.Many2one('ir.sequence','Secuencia para Ruma')


class armado_ruma_line(models.Model):
	_name = 'armado.ruma.line'


	stock_move = fields.Many2one('stock.move','Asiento Contable')
	nro_expediente = fields.Many2one('purchase.costing', "Expediente",readonly=True)
	nro_lote = fields.Many2one('purchase.liquidation','Nro de Lote')
	exp_oro = fields.Float('Expect. de Oro',digits=(12,2),readonly=True)
	product_id = fields.Many2one('product.product','Producto',readonly=True)
	tn = fields.Float('Tn.',digits=(12,3),readonly=True)
	valor = fields.Float('Valor',digits=(12,2),readonly=True)
	por = fields.Float('Por',digits=(12,6),readonly=True)
	nueva_valor = fields.Float('Nuevo Valor',digits=(12,2),readonly=True)
	nuevo_c_uni = fields.Float('Nuevo C. Uni.',digits=(12,6),readonly=True)

	padre = fields.Many2one('armado.ruma','Padre')


	@api.one
	def write(self,vals):
		params = self.env['production.parameter'].search([])
		picking_type = params.top_origen_ruma

		if 'nro_lote' in vals.keys():

			t = self.env['costeo.line.it'].search([('lote','=',vals['nro_lote']),('padre','!=',False)])
			if len(t)>0:
				t = t[0]
				exp =  self.env['purchase.costing'].search([('lineas','=',vals['nro_lote'])])
				if len(exp)>0:				
					vals['nro_expediente'] = exp[0].name

				vals['exp_oro'] = t.costo_oro
				vals['product_id'] = t.producto.id
				vals['tn'] = t.toneladas_secas
				vals['valor'] = t.costo_oro
		return super(armado_ruma_line, self).write(vals)


	@api.model
	def create(self,vals):		
		params = self.env['production.parameter'].search([])
		picking_type = params.top_origen_ruma
	
		res = super(armado_ruma_line, self).create(vals)
		
		t = self.env['costeo.line.it'].search([('lote','=',vals['nro_lote']),('padre','!=',False)])
		if len(t)>0:
			t = t[0]
			exp =  self.env['purchase.costing'].search([('lineas','=',vals['nro_lote'])])
			if len(exp)>0:				
				res.nro_expediente = exp[0].name

			res.exp_oro = t.costo_oro
			res.product_id = t.producto.id
			res.tn = t.toneladas_secas
			res.valor = t.costo_oro
			
		return res


	@api.one
	@api.onchange('nro_lote')
	def onchange_nro_lote(self):
		params = self.env['production.parameter'].search([])
		picking_type = params.top_origen_ruma

		if self.nro_lote.id:

			t = self.env['costeo.line.it'].search([('lote','=',self.nro_lote.id),('padre','!=',False)])
			if len(t)>0:
				t = t[0]
				exp =  self.env['purchase.costing'].search([('lineas','=',self.nro_lote.id)])
				if len(exp)>0:				
					valsself.nro_expediente = exp[0].name

				self.exp_oro = t.costo_oro
				self.product_id = t.producto.id
				self.tn = t.toneladas_secas
				self.valor = t.costo_oro				


class armado_ruma(models.Model):
	_name = 'armado.ruma'

	@api.one
	def get_toneladas(self):
		cont = 0		
		for i in self.lines:
			cont += i.tn
		self.toneladas = cont

	@api.one
	def get_oro_exp(self):
		cont = 0		
		for i in self.lines:
			cont += i.exp_oro
		self.oro_expectativa = cont

	state = fields.Selection([('draft','Borrador'),('updated','Actualizado'),('transfered','Transferido'),('done','Asentado')], default='draft')
	name = fields.Char(u'Número de Ruma',readonly=True)
	toneladas = fields.Float('Toneladas',digits=(12,2),compute="get_toneladas",readonly=True)
	oro_expectativa = fields.Float('Expectativa Oro',digits=(12,2),compute="get_oro_exp",readonly=True)
	fecha_creacion = fields.Date('Fecha Creación',readonly=False,required=True)
	period_id = fields.Many2one('account.period','Periodo',required=True)
	analytic_id = fields.Many2one('account.analytic.account','Cuenta Analítica',required=False)
	total_costo_armado = fields.Float('Total Costo Armado',digits=(12,2),readonly=True)
	lines = fields.One2many('armado.ruma.line','padre','Lineas')

	picking_1 = fields.Many2one('stock.picking','Albarán a Producción Virtual')
	picking_2 = fields.Many2one('stock.picking','Albarán a Destino')
	
	_rec_name = 'name'


	@api.one
	def cancel_last(self):
		if self.state == 'updated':
			self.state = 'draft'
		elif self.state == 'transfered':
			if self.picking_1.id:
				if self.picking_1.state != 'draft':
					self.picking_1.action_revert_done()
					self.picking_1.unlink()
				else:
					self.picking_1.unlink()

				if self.picking_2.state != 'draft':
					self.picking_2.action_revert_done()
					self.picking_2.unlink()
				else:
					self.picking_2.unlink()
			self.state = 'updated'
		else:
			print "Nada"

	@api.model
	def create(self,vals):
		t = super(armado_ruma,self).create(vals)
		parameter = self.env['production.parameter'].search([])[0]


		sequence_id = self.env['ir.sequence'].search([('name','=','Build Ruma')])
		if len(sequence_id)== 0:
			dic_new_seq = {
					'name': 'Build Ruma',
					'padding': 6,
					'number_next_actual': 1,
					'number_increment': 1,
					'implementation': 'no_gap',
					'prefix': '',
					}
			sequence_id = self.env['ir.sequence'].create(dic_new_seq)
		else:
			sequence_id =sequence_id[0] 

		t.write({'name': self.env['ir.sequence'].next_by_id(sequence_id.id) })
		import datetime
		#t.write({'fecha_creacion': str(datetime.datetime.now())[:10] })

		return t

	@api.one
	def actualizar(self):
		if len(self.lines)==0:
			raise osv.except_osv('Alerta!',"No existe lotes seleccionados.")

		params = self.env['production.parameter'].search([])
		picking_type = params.top_origen_ruma

		self.env.cr.execute(""" 
			select sum(debit-credit) from account_move am 
			inner join account_move_line aml on aml.move_id = am.id
			inner join account_period ap on ap.id = am.period_id
			where ap.id = """+ str(self.period_id.id)  +"""
			and aml.analytic_account_id = """ + str(self.analytic_id.id if self.analytic_id.id else -1) + """
			""")
		cant = 0

		for i in self.env.cr.fetchall():
			cant = i[0] if i[0] else 0
		
		self.write({'total_costo_armado':cant})
		self.refresh()

		for i in self.lines:


			if i.nro_lote.id:

				t = self.env['costeo.line.it'].search([('lote','=',i.nro_lote.id),('padre','!=',False)])
				if len(t)>0:
					t = t[0]
					exp =  self.env['purchase.costing'].search([('lineas','=',i.nro_lote.id)])
					if len(exp)>0:				
						i.nro_expediente = exp[0].name

					i.exp_oro = t.costo_oro
					i.product_id = t.producto.id
					i.tn = t.toneladas_secas
					i.valor = t.costo_oro		



		#self.refresh()
		#for i in self.lines:
		#	i.write({'por': (i.exp_oro / self.oro_expectativa) if self.oro_expectativa!= 0 else 0 })
		#	i.refresh()
		##	i.write({'nueva_valor': ( i.por * self.total_costo_armado ) + i.valor })
		#	i.refresh()
		#	i.write({'nuevo_c_uni': (i.nueva_valor / i.tn ) if i.tn != 0 else 0  })
		self.state = 'updated'		

	@api.one
	def armar_ruma(self):
		from datetime import datetime
		if self.picking_1.id or self.picking_2.id:
			pass
		else:
			picking = self.env['stock.picking']
			move = self.env['stock.move']


			params = self.env['production.parameter'].search([])

			picking_type = params.top_origen_ruma
			#Traslado de productos a ubicación de producción.
			picking_vals = {
				'motivo_guia'		: '7',
				'move_type'			: 'direct',
				'picking_type_id'	: picking_type.id,
				'priority'			: '1',
				'date'				:  self.fecha_creacion,
			}
			picking_obj = picking.create(picking_vals)

			self.write({'picking_1':picking_obj.id})

			picking_type = params.top_origen_ruma

			for line in self.lines:
				move_vals = {
				#'expedient_id'		: line.stock_move.expedient_id.id,
					'picking_id'		: picking_obj.id,
					'lot_num'			: line.nro_lote.id,
					'product_id'		: line.product_id.id,
					'gold_expected'		: line.exp_oro,
					'ponderation'		: line.por,
					'product_uom_qty'	: line.tn,
					'product_uom'		: line.product_id.uom_id.id,
					'precio_unitario_manual'	:  (line.f_total_costo/line.tn) if line.tn != 0 else 0,
					'location_id'		: picking_type.default_location_src_id.id,
					'location_dest_id'	: picking_type.default_location_dest_id.id,
					'name'				: line.product_id.name,
					'invoice_state'		: line.stock_move.invoice_state if line.stock_move.invoice_state else 'none' ,
					'date'				: self.fecha_creacion,
					'date_expected'		: self.fecha_creacion,
					'state'				: 'done',
				}
				print move_vals,'oko'
				move_obj = move.create(move_vals)

			

			picking_obj.action_confirm()
			picking_obj.force_assign()
			picking_obj.do_transfer()

			#Traslado de productos a almacén destino.
			picking_type = params.top_destino_ruma
			picking_vals = {
				'motivo_guia'		: '8',
				'move_type'			: 'direct',
				'picking_type_id'	: picking_type.id,
				'priority'			: '1',
				'date'				:  self.fecha_creacion,
			}
			picking_obj_dest = picking.create(picking_vals)


			ex_oro_Acum = 0
			n_pt2a = 0		
			cantidad = 0
			for i in self.lines:
				ex_oro_Acum += i.exp_oro
				n_pt2a += i.f_total_costo
				cantidad += i.tn 

			n_pt2a = (n_pt2a / cantidad) if cantidad != 0 else 0


			picking_type = params.top_destino_ruma
			self.write({'picking_2':picking_obj_dest.id})
			move_vals = {
				'picking_id'		: picking_obj_dest.id,
				'product_id'		: params.ruma_product.id,
				'gold_expected'		: ex_oro_Acum,
				'product_uom_qty'	: 1,
				'product_uom'		: params.ruma_product.uom_id.id,
				'precio_unitario_manual'				: n_pt2a,
				'location_id'		: picking_type.default_location_src_id.id,
				'location_dest_id'	: picking_type.default_location_dest_id.id,
				'name'				: "Ruma: " + self.name,
				'invoice_state'		: 'invoiced',
				'date'				: self.fecha_creacion,
				'date_expected'		: self.fecha_creacion,
				'state'				: 'done',
			}
			move_obj_dest = move.create(move_vals)


			picking_obj_dest.action_confirm()
			picking_obj_dest.force_assign()
			picking_obj_dest.do_transfer()
			
			self.state = 'transfered'







class purchase_liquidation(models.Model):
	_inherit= 'purchase.liquidation'

	ruma_relation_id = fields.Many2one('armado.ruma','Nro. Ruma')
	fecha_consumo =  fields.Date('Fecha Consumo')



class costeo_ruma_linea(models.Model):
	_name = 'costeo.ruma.linea'

	ruma_id = fields.Many2one('armado.ruma','Ruma')
	toneladas = fields.Float('Toneladas',digits=(12,3))
	valor_materia_prima = fields.Float('Valor Materia Prima',digits=(12,2))
	factor = fields.Float('Factor',digits=(12,8))
	gastos_armados = fields.Float('Gastos Armado',digits=(12,8))
	total = fields.Float('Total',digits=(12,4))
	p_unit = fields.Float('Precio Unitario',digits=(12,8))

	costeo_id = fields.Many2one('costeo.ruma','Costeo')


class costeo_ruma(models.Model):
	_name = 'costeo.ruma'

	periodo = fields.Many2one('account.period','Periodo',required=True)
	lineas = fields.One2many('costeo.ruma.linea','costeo_id','Lineas')
	cuentas = fields.Many2many('account.analytic.account','analytic_rel_costeo_ruma_it','analytic_id','costeo_ruma_id','Cuentas Analiticas')

	_rec_name = 'periodo'



	@api.one
	def unlink(self):
		for i in lineas:
			i.unlink()

		return super(costeo_ruma,self).unlink()


	@api.one
	def actualizar(self):
		rumas = self.env['armado.ruma'].search([('period_id','=',self.periodo.id)])

		for i in self.lineas:
			i.unlink()

		for i in rumas:
			ton_total = 0
			vmp_total = 0

			for j in i.lines:
				ton_total += j.tn
				vmp_total += j.valor


			data={
				'ruma_id': i.id,
				'toneladas':ton_total,
				'valor_materia_prima':vmp_total,
				'costeo_id':self.id,
			}
			self.env['costeo.ruma.linea'].create(data)

	@api.one
	def calcular(self):
		total_tone = 0
		total_gasto = 0
		for i in self.lineas:
			total_tone += i.toneladas

		cuentas = [0,0,0,0,0]
		for i in self.cuentas:
			cuentas.append(i.id)

		self.env.cr.execute("""
			select debit - credit as monto from account_move am 
			inner join account_move_line aml on aml.move_id = am.id
			inner join account_analytic_account aaa on aaa.id = aml.analytic_account_id
			where aaa.id in """ + str(tuple(cuentas)) + """ and am.period_id = """ + str(self.periodo.id) + """ and am.state != 'done'
		 """)

		for i in self.env.cr.fetchall():
			total_gasto += i[0]

		for i in self.lineas:
			i.factor = i.toneladas / total_tone if total_tone != 0 else 0
			i.refresh()
			i.gastos_armados = i.factor * total_gasto
			i.refresh()
			i.total = i.valor_materia_prima + i.gastos_armados
			i.refresh()
			i.p_unit = i.total / i.toneladas if i.toneladas != 0 else 0
			i.refresh()

			for w in i.ruma_id.picking_2.move_lines:
				w.precio_unitario_manual = i.p_unit


