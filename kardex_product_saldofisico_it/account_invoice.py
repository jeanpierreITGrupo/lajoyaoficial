# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv


class stock_move(models.Model):
	_inherit = 'stock.move'


	@api.one
	def write(self,vals):
		t= super(stock_move,self).write(vals)
		self.refresh()
		if 'state' in vals:
			if self.state == 'done' and self.picking_id.id:
				nuevo = self.env['detalle.simple.fisico.total.d.wizard'].create({'fiscalyear_id': self.env['account.fiscalyear'].search([('name','=',str(self.picking_id.date)[:4] )])[0].id })
				nuevo.do_rebuild()
				elem = self.env['detalle.simple.fisico.total.d'].search([('almacen','=',self.location_id.id),('producto','=',self.product_id.id)])
				if len(elem)>0:
					if elem[0].saldo > self.product_uom_qty:
						pass
					else:
						raise osv.except_osv('Alerta','No cuenta con Saldo Disponible del producto: ' + self.product_id.name + ' ,saldo: ' + str(elem[0].saldo))
				else:
					raise osv.except_osv('Alerta','No cuenta con Saldo Disponible del producto: ' + self.product_id.name + ' ,saldo: ' + str(elem[0].saldo))


	
class detalle_simple_fisico_total_d_wizard(models.TransientModel):
	_name = 'detalle.simple.fisico.total.d.wizard'

	fiscalyear_id = fields.Many2one('account.fiscalyear', u'Año fiscal', required=True)

	@api.multi
	def do_rebuild(self):
		self.env.cr.execute(""" 
			drop view if exists detalle_simple_fisico_total_d;
			create view detalle_simple_fisico_total_d as (

select row_number() OVER () AS id, u as almacen,p as producto ,s as saldo from (
select sl.id as u ,pp.id as p ,saldo as s from (
select product_id,ubicacion, sum(saldo) as saldo from (
select product_id,location_id as ubicacion, -product_qty as saldo from vst_stock_move_final_joya where date::date >= '"""+str(self.fiscalyear_id.date_start)+"""'::date
union all
select product_id,location_dest_id as ubicacion, product_qty as saldo from vst_stock_move_final_joya where date::date >= '"""+str(self.fiscalyear_id.date_start)+"""'::date
) as T group by product_id,ubicacion )as X
inner join stock_location sl on sl.id = X.ubicacion
inner join product_product pp on pp.id = X.product_id
where sl.usage = 'internal'
) as MN
order by u,p,s 

			); 
			""")

		view_id = self.env.ref('kardex_product_saldofisico_it.view_kardex_fisico_d',False)
		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'detalle.simple.fisico.total.d',
			# 'res_id'   : self.id,
			'view_id'  : view_id.id,
			'view_type': 'form',
			'view_mode': 'tree',
			'views'    : [(view_id.id, 'tree')],
			#'target'   : 'new',
			#'flags'    : {'form': {'action_buttons': True}},
			#'context'  : {},
		}

class detalle_simple_fisico_total_d(models.Model):
	_name = 'detalle.simple.fisico.total.d'

	producto = fields.Many2one('product.product','Producto')
	almacen = fields.Many2one('stock.location','Almacen')
	saldo = fields.Float('Disponibilidad',digits=(15,3))

	_order = 'producto,almacen'
	_auto = False

class detalle_simple_kfisicot_d(models.Model):
	_name = 'detalle.simple.kfisicot.d'

	producto = fields.Many2one('product.product','Producto')
	almacen = fields.Many2one('stock.location','Almacen')
	saldo = fields.Float('Disponibilidad',digits=(15,3))
	padre = fields.Many2one('detalle.simple.kfisicot','padre')


class detalle_simple_kfisicot(models.Model):
	_name = 'detalle.simple.kfisicot'

	lineas=fields.One2many('detalle.simple.kfisicot.d','padre','Detalle')



class stock_picking(models.Model):
	_inherit = 'stock.picking'

	# select u,p,s from (
	# 		select sl.id as u ,pp.id as p ,saldo as s from (
	# 		select product_id,ubicacion, sum(saldo) as saldo from (
	# 		select product_id,location_id as ubicacion, -product_qty as saldo 
	# 		from vst_stock_move_final_joya
	# 		where date::date between '"""+self.date.split('-')[0]+"""-01-01'::date and '"""+str(int(self.date.split('-')[0])+10)+"""-01-01'::date and product_id in """ +str(tuple(productos))+ """ and location_id = """ +str(locacion)+ """ 
	# 		union all
	# 		select product_id,location_dest_id as ubicacion, product_qty as saldo 
	# 		from vst_stock_move_final_joya
	# 		where date::date between '"""+self.date.split('-')[0]+"""-01-01'::date and '"""+str(int(self.date.split('-')[0])+10)+"""-01-01'::date and product_id in """ +str(tuple(productos))+ """ and location_dest_id = """ +str(locacion)+ """ 
	# 		) as T group by product_id,ubicacion )as X
	# 		inner join stock_location sl on sl.id = X.ubicacion
	# 		inner join product_product pp on pp.id = X.product_id
	# 		where sl.usage = 'internal'
	# 		order by pp.name_template, saldo
	# 		) as MN
	# 		--where p in """ +str(tuple(productos))+ """
	# 		--and u = """ +str(locacion)+ """
	# 		order by u

	@api.multi
	def get_disponibilidad_kfisico(self):
		detalle = self.env['detalle.simple.kfisicot'].create({})
		productos=[-1,-1,-1]

		locacion = -1
		for i in self.move_lines:
			productos.append(i.product_id.id)
			locacion = i.location_id.id

		self.env.cr.execute("""
			select u,p,s 
			from (
				select coalesce(X.ubicacion,""" +str(locacion)+ """) as u ,pp.id as p ,coalesce(saldo,0.000) as s
				from product_product pp 
				left join (
					select product_id,ubicacion, sum(saldo) as saldo 
					from (
						select v.product_id,v.location_id as ubicacion, -v.product_qty as saldo			 
						from vst_stock_move_final_joya v
						join stock_location sl on v.location_id = sl.id
						where date::date between '"""+self.date.split('-')[0]+"""-01-01'::date and '"""+str(int(self.date.split('-')[0])+10)+"""-01-01'::date and v.product_id in """ +str(tuple(productos))+ """ and v.location_id = """ +str(locacion)+ """ and sl.usage = 'internal'
						union all
						select v.product_id,v.location_dest_id as ubicacion, v.product_qty as saldo 
						from vst_stock_move_final_joya v
						join stock_location sl on v.location_dest_id = sl.id
						where date::date between '"""+self.date.split('-')[0]+"""-01-01'::date and '"""+str(int(self.date.split('-')[0])+10)+"""-01-01'::date and v.product_id in """ +str(tuple(productos))+ """ and v.location_dest_id = """ +str(locacion)+ """ and sl.usage = 'internal'
					) as T group by product_id,ubicacion
				)as X on pp.id = X.product_id
				where pp.id in """ +str(tuple(productos))+ """
				order by pp.name_template, saldo
			) as MN
			order by u
		 """)
		for i in self.env.cr.fetchall():
			print i
			self.env['detalle.simple.kfisicot.d'].create({'producto':i[1],'almacen':i[0],'saldo':i[2],'padre':detalle.id})
		
		return {
				'type': 'ir.actions.act_window',
				'res_model': 'detalle.simple.kfisicot',
				'view_mode': 'form',
				'view_type': 'form',
				'target':'new',
				'res_id': detalle.id,
				'views': [(False, 'form')],
			}

















class detalle_simple_kfisico_d(models.Model):
	_name = 'detalle.simple.kfisico.d'

	almacen = fields.Many2one('stock.location','Almacen')
	saldo = fields.Float('Disponibilidad',digits=(15,3))
	padre = fields.Many2one('detalle.simple.kfisico','padre')


class detalle_simple_kfisico(models.Model):
	_name = 'detalle.simple.kfisico'

	name = fields.Char('Producto')
	lineas=fields.One2many('detalle.simple.kfisico.d','padre','Detalle')



class product_template(models.Model):
	_inherit = 'product.template'

	@api.one
	def get_saldofisico(self):
		self.env.cr.execute("""
			select u,p,s from (
select sl.complete_name as u ,pp.product_tmpl_id as p ,saldo as s from (
select product_id,ubicacion, sum(saldo) as saldo from (
select product_id,location_id as ubicacion, -product_qty as saldo from vst_stock_move_final_joya
union all
select product_id,location_dest_id as ubicacion, product_qty as saldo from vst_stock_move_final_joya
) as T group by product_id,ubicacion )as X
inner join stock_location sl on sl.id = X.ubicacion
inner join product_product pp on pp.id = X.product_id
where sl.usage = 'internal'
) as MN
where p = """ +str(self.id)+ """
order by u,p,s 
		 """)
		tmp = 0
		for i in self.env.cr.fetchall():
			tmp += i[2]
		self.saldo_kardexfisico = tmp

	saldo_kardexfisico = fields.Float('Disponibilidad',compute="get_saldofisico")



	@api.multi
	def get_saldo_kardexfisico(self):
		detalle = self.env['detalle.simple.kfisico'].create({'name':self.name})

		self.env.cr.execute("""
			select u,p,s from (
select sl.id as u ,pp.product_tmpl_id as p ,saldo as s from (
select product_id,ubicacion, sum(saldo) as saldo from (
select product_id,location_id as ubicacion, -product_qty as saldo from vst_stock_move_final_joya
union all
select product_id,location_dest_id as ubicacion, product_qty as saldo from vst_stock_move_final_joya
) as T group by product_id,ubicacion )as X
inner join stock_location sl on sl.id = X.ubicacion
inner join product_product pp on pp.id = X.product_id
where sl.usage = 'internal'
) as MN
where p = """ +str(self.id)+ """
order by u,p,s 
		 """)
		txt = ""
		for i in self.env.cr.fetchall():
			self.env['detalle.simple.kfisico.d'].create({'almacen':i[0],'saldo':i[2],'padre':detalle.id})
		
		return {
				'type': 'ir.actions.act_window',
				'res_model': 'detalle.simple.kfisico',
				'view_mode': 'form',
				'view_type': 'form',
				'target':'new',
				'res_id': detalle.id,
				'views': [(False, 'form')],
			}
