# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp     import models, fields, api
import base64
import codecs

import datetime
import decimal

class stock_move_clean_wizard(models.TransientModel):
	_name = 'stock.move.clean.wizard'

	aviso = fields.Char('Aviso', default="¿Estas seguro de eliminar?. Se eliminarán los productos en estado de espera")

	@api.multi
	def do_rebuild(self):
		sp = self.env['stock.picking'].search([('id','=',self.env.context['clean_id'])])[0]
		print sp
		return sp.clean_confirmed_action()

class stock_move(models.Model):
	_inherit = 'stock.move'

	disponibilidad = fields.Float('Disponibilidad')

	@api.one
	def compute_disponibilidad(self):
		if self.env.context['default_picking_id'] == self.picking_id.id:
			if self.location_id.usage == 'internal':
				productos   = "{"+str(self.product_id.id)+"}"
				ubicaciones = "{"+str(self.location_id.id)+"}"
				sql = """
					select
						get_kardex_v.product_id as "producto_id",
						get_kardex_v.name_template as "Producto",
						get_kardex_v.unidad as "Uni",
						get_kardex_v.default_code as "Codigo P.",
						sum(get_kardex_v.ingreso) as "Ingreso",
						sum(get_kardex_v.salida) as "Salida",
						sum(get_kardex_v.ingreso)-sum(get_kardex_v.salida) as "Saldo F"
					from get_kardex_v("""+ "20170101" + "," + str(self.picking_id.date).replace("-","") + ",'" + productos + """'::INT[], '""" + ubicaciones + """'::INT[]) 
					inner join stock_location origen on get_kardex_v.ubicacion_origen = origen.id
					inner join stock_location destino on get_kardex_v.ubicacion_destino  = destino.id
					where product_id = """+str(self.product_id.id)+"""
					group by product_id, name_template, unidad, default_code
					order by name_template
				"""
				self.env.cr.execute(sql)
				print "final"
				# file = open('C:/odoo/csv/sqldelavida.txt','w')
				# file.write(sql)
				# file.close()
				res = self.env.cr.fetchall()
				print res
				if len(res):
					res = res[0][-1]
				else:
					res = 0
				self.disponibilidad = res
			else:
				self.disponibilidad = 0

	@api.one
	def write(self, vals):
		t = super(stock_move,self).write(vals)
		self.refresh()
		if 'product_uom_qty' in vals:
			self.write({'state':'confirmed'})
		return t

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	check_forced = fields.Boolean('check forced', default=False)
	forzar       = fields.Boolean('Forzar Disponibilidad', compute="get_forzar_disponibilidad")

	@api.one
	def get_forzar_disponibilidad(self):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		g1_ids = all_groups.search([('name','=',u'Permite Utilizar Forzar Disponibilidad')])

		if not g1_ids: 
			raise osv.except_osv('Alerta!', "No existe el grupo 'Permite Utilizar Forzar Disponibilidad' creado.")

		if self.state == 'draft' or self.state == 'confirmed' or self.state == 'partially_available':
			if not g1_ids in all_users.search([('id','=',self.env.uid)])[0].groups_id:
				self.forzar = False
			else:
				self.forzar = True

	@api.one
	def force_assign(self):
		t = super(stock_picking,self).force_assign()
		self.check_forced = True
		return t

	@api.one
	def get_disponibilidad(self):  
		for i in self.move_lines:
			i.state='assigned'     
		return True
		# no_disp = []
		# disp = {}
		# productos_str =""
		# location_src = ""
		# ldata=[]
		# llocation=[]
		# for i in self.move_lines:
		# 	if i.product_id.id not in ldata:
		# 		ldata.append(i.product_id.id)
		# 		productos_str=productos_str+str(i.product_id.id)+","
		# 	if i.location_id.id not in llocation:
		# 		location_src=str(i.location_id.id)
		# 		llocation.append(i.location_id.id)


		# productos_str=productos_str[:-1]
		# productos   = "{"+productos_str+"}"
		# ubicaciones = "{"+location_src+"}"
		# # disp = dict.fromkeys(list(ldata),0)
		# sql = """
		# 		select
		# 			get_kardex_v.product_id as "producto_id",
		# 			get_kardex_v.name_template as "Producto",
		# 			get_kardex_v.unidad as "Uni",
		# 			get_kardex_v.default_code as "Codigo P.",
		# 			sum(get_kardex_v.ingreso) as "Ingreso",
		# 			sum(get_kardex_v.salida) as "Salida",
		# 			sum(get_kardex_v.ingreso)-sum(get_kardex_v.salida) as "Saldo F"
		# 		from get_kardex_v("""+ "20170101" + "," + str(self.date).replace("-","") + ",'" + productos + """'::INT[], '""" + ubicaciones + """'::INT[]) 
		# 		inner join stock_location origen on get_kardex_v.ubicacion_origen = origen.id
		# 		inner join stock_location destino on get_kardex_v.ubicacion_destino  = destino.id
		# 		where product_id in ("""+productos_str+""") 
		# 		group by product_id, name_template, unidad, default_code
		# 		order by name_template
		# 	"""
		# # raise osv.except_osv('Alerta!', sql)
		# self.env.cr.execute(sql)
		# saldos = self.env.cr.dictfetchall()
		# saldo_dic = {}
		# for saldo in saldos:
		# 	saldo_dic[saldo['producto_id']]= saldo['Saldo F']
		

		# n=0
		# cadsql = ""
		# lastdisp=0
		# n2=0
		# for i in self.move_lines:
		# 	n=n+1
		# 	if i.location_id.usage == 'internal' and i.product_id.product_tmpl_id.type == 'product':

		# 		pqty = i.product_uom_qty/i.product_uom.factor*i.product_id.product_tmpl_id.uom_id.factor
		# 		if i.product_id.id not in disp:
		# 			disp.update({i.product_id.id: saldo_dic[i.product_id.id]})

		# 		if pqty <= disp[i.product_id.id]:
		# 			# i.state = 'assigned'
		# 			cadsql = cadsql +"update stock_move set state='assigned' where id = "+str(i.id)+";\n"
		# 			lastdisp=i.id
		# 			print disp[i.product_id.id]
		# 			i.disponibilidad = disp[i.product_id.id]
		# 			disp[i.product_id.id] -= pqty
		# 		else:
		# 			no_disp.append(str(i.product_id.default_code)+' / '+i.product_id.name+' --> '+str(pqty)+' / '+str(disp[i.product_id.id]))
		# 			i.disponibilidad = disp[i.product_id.id]
		# 		print 'Disponibilidad ',n,i.product_id.name,disp[i.product_id.id],pqty

		# 	else:
		# 		i.state = 'assigned'
		# if len(cadsql)>0:
		# 	self.env.cr.execute(cadsql)
		# if lastdisp>0:
		# 	moveline = self.env['stock.move'].browse(lastdisp)
		# 	moveline.state = 'draft'
		# 	moveline.state = 'assigned'



		# # raise osv.except_osv('Alerta!', disp)
		# return True
		

	@api.multi
	def clean_confirmed(self):
		return {
			"context"  : {"clean_id": self.id},
			"type"     : "ir.actions.act_window",
			"res_model": "stock.move.clean.wizard",
			"view_type": "form",
			"view_mode": "form",
			"target"   : "new",
		}

	@api.one
	def clean_confirmed_action(self):
		for i in self.move_lines:
			if i.state != 'assigned':
				i.state = 'draft'
				i.unlink()

class stock_transfer_details(models.TransientModel):
	_inherit = 'stock.transfer_details'

	stock_picking_id = fields.Many2one('stock.picking','id picking')

	@api.multi
	def wizard_view(self):
		if 'active_model' in self.env.context and 'active_id' in self.env.context:
			if self.env.context['active_model'] == 'stock.picking':
				self.write({'stock_picking_id':self.env.context['active_id']})
		t = super(stock_transfer_details,self).wizard_view()
		return t

	@api.one
	def do_detailed_transfer(self):
		sp = self.stock_picking_id if self.stock_picking_id.id else self.env.context['active_id']

		prod = set()
		prod2 = set()
		for i in sp.move_lines:
			prod.add(i.product_id.name_template)
			prod2.add(i.product_id.id)
		prod_dispon = dict.fromkeys(list(prod),0)


		count = 1

		lcantprod=dict.fromkeys(list(prod2),0)
		print lcantprod

		for i in sp.move_lines:
			pqty = i.product_uom_qty/i.product_uom.factor*i.product_id.product_tmpl_id.uom_id.factor
			prod_dispon[i.product_id.name_template] += pqty + (i.disponibilidad if count == 1 else 0)
			lcantprod[i.product_id.id]+=pqty
			count += 1

		print 'cantidadnormal',lcantprod

		for i in self.item_ids:
			sm = self.env['stock.move'].search([('picking_id','=',sp.id),('product_id','=',i.product_id.id)])
			if len(sm) > 0:
				prod_dispon[sm[0].product_id.name_template] -= i.quantity/i.product_uom_id.factor*i.product_id.product_tmpl_id.uom_id.factor


		# print prod_dispon

		


		# if sp.picking_type_id.default_location_src_id.usage == 'supplier' and sp.picking_type_id.default_location_dest_id.usage == 'internal':
		# 	pass
		# else:
		if sp.check_forced == True:
			pass
		else:			
			for i in self.item_ids:
				if i.product_id.product_tmpl_id.type == 'consu':
					pass
					if (i.quantity/i.product_uom_id.factor*i.product_id.product_tmpl_id.uom_id.factor)>lcantprod[i.product_id.id]:
						raise osv.except_osv('Alerta!', 'El producto ' + i.product_id.name_template + ' no tiene disponible la cantidad solicitada')

			# if sp.picking_type_id.default_location_src_id.usage == 'internal':
			# 	for k,v in prod_dispon.items():
			# 		#print k
			# 		pp = self.env['product.product'].search([('name_template','=',k)])
			# 		#print pp
					
			# 		if len(pp) > 0:
			# 			pp = pp[0]
			# 			if pp.product_tmpl_id.type == 'consu':
			# 				pass
			# 			elif v < 0:
			# 				raise osv.except_osv('Alerta!', 'El producto ' + k + ' no tiene disponible la cantidad solicitada')
			# 		else:
			# 			if v < 0:
			# 				raise osv.except_osv('Alerta!', 'El producto ' + k + ' no tiene disponible la cantidad solicitada')
		return super(stock_transfer_details,self).do_detailed_transfer()