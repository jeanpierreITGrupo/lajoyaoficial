# -*- coding: utf-8 -*-
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import openerp.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
values = {}
from datetime import datetime as dt
import datetime

class make_kardex(osv.TransientModel):
	_inherit = "make.kardex"
	@api.v7
	def delete_rest_negative(self,cr,uid,ids,context=None):
		direccion_ids = self.pool.get('main.parameter').search(cr,uid,[])
		direccion = self.pool.get('main.parameter').browse(cr,uid,direccion_ids)[0].dir_create_file
		
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	
		if data['products_ids']==[]:
			if data['allproducts']:
				if data['allproducts']==False:
					raise osv.except_osv('Alerta','No existen productos seleccionados')
					return
				else:
					prods= self.pool.get('product.product').search(cr,uid,[])
					lst_products	= prods
			else:
				raise osv.except_osv('Alerta','No existen productos seleccionados')
				return
		else:
			lst_products	= data['products_ids']

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		
		lst_locations = data['location_ids']
		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']
		if 'allproducts' in data:
			if data['allproducts']:
				lst_products	= self.pool.get('product.product').search(cr,uid,[])
			else:
				lst_products	= data['products_ids']
		else:
			lst_products	= data['products_ids']


		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)

		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])

		cadall = """
		select get_kardex_v.*
		from get_kardex_v("""+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])		 
		left join stock_location origen on get_kardex_v.ubicacion_origen = origen.id
		left join stock_location destino on get_kardex_v.ubicacion_destino = destino.id
		left join stock_move sm on sm.id = get_kardex_v.stock_moveid
		left join stock_picking sp on sp.id = sm.picking_id
		order by get_kardex_v.lotemp,get_kardex_v.location_id,get_kardex_v.product_id,get_kardex_v.fecha,get_kardex_v.esingreso,get_kardex_v.nro
		"""
		cr.execute(cadall)
		allkardex = cr.dictfetchall()


		cadsql = """
		-- seleccionamos todos los productos que tienen negativos
		select distinct o.product_id
		from (
		select get_kardex_v.*
		from get_kardex_v("""+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])		 
		left join stock_location origen on get_kardex_v.ubicacion_origen = origen.id
		left join stock_location destino on get_kardex_v.ubicacion_destino = destino.id
		left join stock_move sm on sm.id = get_kardex_v.stock_moveid
		left join stock_picking sp on sp.id = sm.picking_id
		where saldof <0 
		order by get_kardex_v.lotemp,get_kardex_v.location_id,get_kardex_v.product_id,get_kardex_v.fecha,get_kardex_v.esingreso,get_kardex_v.nro
		) o
		"""
		cr.execute(cadsql)
		productosa = cr.dictfetchall()
		lst_borrados = []
		lst_borrados.append('fecha_albaran|fecha kardex|nro|doc_almacen|Producto|Unidad|ingreso|debit|salida|credit|saldof|saldov|origen|destino|almacen')
		lst_borrados1 = []
		for productoa in productosa:
			repetir = True
			
			# expectedResult = [d for d in allkardex if d['product_id'] == 3751]
			expectedResult = [d for d in allkardex if d['product_id'] == productoa['product_id']]
			while repetir:				
				n=0
				lt_borrar=[]
				nlimit=0
				for hg in expectedResult:
					# print str(hg['name_template']),hg['ingreso'],hg['salida'],hg['saldof']
					if hg['saldof']<0 and hg['salida']>0:
						lst_borrados.append(str(hg['fecha_albaran'])+"|"+str(hg['fecha'])+"|"+str(hg['nro'])+"|"+str(hg['doc_almac'])+"|"+str(hg['name_template'])+"|"+str(hg['unidad'])+"|"+str(hg['ingreso'])+"|"+str(hg['debit'])+"|"+str(hg['salida'])+"|"+str(hg['credit'])+"|"+str(hg['saldof'])+"|"+str(hg['saldov'])+"|"+str(hg['origen'])+"|"+str(hg['destino'])+"|"+str(hg['almacen']))
						lst_borrados1.append(hg['stock_moveid'])
						lt_borrar.append(n)
					if hg['ingreso']>0:
						if len(lt_borrar)>0:
							break				 
					n = n+1
				# recalcular el saldo
				lt_borrar1 = sorted(lt_borrar,reverse=True)
				for lt in lt_borrar1:
					del expectedResult[lt]
				saldo = 0
				for hg in expectedResult:
					saldo = saldo+(hg['ingreso']-hg['salida'])
					hg['saldof']=saldo
				expectedResult2 = [d for d in expectedResult if d['saldof']<0]
				if len(expectedResult2)==0:
					break
		cadids=''
		for lk in lst_borrados1:
			cadids=cadids+str(lk)+","
		cadids=cadids[:-1]
		# raise osv.except_osv('Alertafis',cadids)
		if len(cadids)>0:
			cadsql = "delete from stock_move where id in ("+cadids+");"
			cr.execute(cadsql)
			with open(direccion+'borrados.txt', 'w') as file_handler:
				for item in lst_borrados:
					# cad1 = 'Nro:'+item['nro']+' ID Movimiento:'+str(item['move_id'])+' Producto: '+item['producto']+'\n'
					file_handler.write("{}\n".format(item))

	def last_day_of_month(self,any_day):
		next_month = any_day.replace(day=28) + datetime.timedelta(days=4)	# this will never fail
		return next_month - datetime.timedelta(days=next_month.day)


	@api.v7
	def redate_in_period(self,cr,uid,ids,context=None):
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	
		if data['products_ids']==[]:
			if data['allproducts']:
				if data['allproducts']==False:
					raise osv.except_osv('Alerta','No existen productos seleccionados')
					return
				else:
					prods= self.pool.get('product.product').search(cr,uid,[])
					lst_products	= prods
			else:
				raise osv.except_osv('Alerta','No existen productos seleccionados')
				return
		else:
			lst_products	= data['products_ids']

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		
		lst_locations = data['location_ids']
		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']

		sd = dt.strptime(date_ini, "%Y-%m-%d") 
		ed = dt.strptime(date_fin, "%Y-%m-%d") 

		lst = [dt.strptime('%2.2d-%2.2d' % (y, m), '%Y-%m').strftime('%m-%Y') \
				for y in xrange(sd.year, ed.year+1) \
				for m in xrange(sd.month if y==sd.year else 1, ed.month+1 if y == ed.year else 13)]
		dates_range = []
		for l in lst:
			cada = l.split('-')
			dates_range.append({'ini':cada[1]+"-"+str(cada[0]).ljust(2,'0')+'-01','end':str(self.last_day_of_month(datetime.date(int(cada[1]),int(cada[0]), 1)))})
		# print dates_range
		# input('aaaaaaaa')
		if 'allproducts' in data:
			if data['allproducts']:
				lst_products	= self.pool.get('product.product').search(cr,uid,[])
			else:
				lst_products	= data['products_ids']
		else:
			lst_products	= data['products_ids']
		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])
		cadall = """
		select get_kardex_v.*
		from get_kardex_v("""+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])		 
		left join stock_location origen on get_kardex_v.ubicacion_origen = origen.id
		left join stock_location destino on get_kardex_v.ubicacion_destino = destino.id
		left join stock_move sm on sm.id = get_kardex_v.stock_moveid
		left join stock_picking sp on sp.id = sm.picking_id
		order by get_kardex_v.lotemp,get_kardex_v.location_id,get_kardex_v.product_id,get_kardex_v.fecha,get_kardex_v.esingreso,get_kardex_v.nro
		"""
		cr.execute(cadall)
		allkardex = cr.dictfetchall()

		cadsql = """
		-- seleccionamos todos los productos que tienen negativos
		select distinct o.product_id,o.name_template
		from (
		select get_kardex_v.*
		from get_kardex_v("""+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[])		 
		left join stock_location origen on get_kardex_v.ubicacion_origen = origen.id
		left join stock_location destino on get_kardex_v.ubicacion_destino = destino.id
		left join stock_move sm on sm.id = get_kardex_v.stock_moveid
		left join stock_picking sp on sp.id = sm.picking_id
		where saldof <0 
		order by get_kardex_v.lotemp,get_kardex_v.location_id,get_kardex_v.product_id,get_kardex_v.fecha,get_kardex_v.esingreso,get_kardex_v.nro
		) o
		"""
		cr.execute(cadsql)
		productosa = cr.dictfetchall()
		cadsqlf=""
		for productoa in productosa:
			repetir = True
			for fechar in dates_range:
				ini = fechar['ini']
				end = fechar['end']
				# expectedResult = [d for d in allkardex if d['product_id'] == 3687 and d['fecha']>=ini and d['fecha']<=end ]
				expectedResult = [d for d in allkardex if d['product_id'] == productoa['product_id'] and d['fecha']>=ini and d['fecha']<=end ]

				saldo=0
				maxing = dt.strptime('1900-01-01', "%Y-%m-%d") 
				lstmoves = []
				
				for hg in expectedResult:
					saldo = saldo+(hg['ingreso']-hg['salida'])
					if hg['ingreso']>0:
						if maxing<dt.strptime(hg['fecha'], "%Y-%m-%d"):
							maxing= dt.strptime(hg['fecha'], "%Y-%m-%d")
					if hg['salida']>0 and hg['saldof']<0:
						lstmoves.append(hg['stock_moveid'])
				if saldo>=0:
					for moves in self.pool.get('stock.move').browse(cr,uid,lstmoves):
						if maxing>dt.strptime(moves.picking_id.date, "%Y-%m-%d"):
							print maxing,moves.picking_id.date
							cadsqlf =cadsqlf+ """update stock_picking set date = '"""+str(maxing)+"""' 
							where id = """+str(moves.picking_id.id)+""";\n"""
		# raise osv.except_osv('Alertafis',cadsqlf)
		if len(cadsqlf)>0:
			cr.execute(cadsqlf)