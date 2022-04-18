# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class reporte_kardex_joya(osv.TransientModel):
	_name='reporte.kardex.joya'
	
	period_ini = fields.Many2one('account.period','Periodo Inicial')	
	period_fin = fields.Many2one('account.period','Periodo Final')	
	tipo = fields.Selection( [('1','Kardex Lotes'),('2','Kardex Ruma'),('3','Kardex Producto Terminado'),('4','Kardex Producto en Proceso')],'Reporte')

	@api.multi
	def do_rebuild(self):
		if self.tipo == '1':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			if not direccion:
				raise osv.except_osv('Alerta!','No esta configurado la dirección de Directorio en Parametros')

			self.env.cr.execute("""		
			COPY (	


	select * from (


select
sl_p.name || '/' || sl.name as origen, sl2_p.name || '/' || sl2.name as destino,  sl2_p.name || '/' || sl2.name as almacen,
'8' as t_op,
'All products' as Categoria,
'M0001' as codigo_p,
't' as unidad,
'MINERAL AURIFERO Y ARGENTIFERO SIN PROCESAR' as producto,
ap.date_stop as fecha_alb,
ap.date_stop as fecha,
'' as periodo,
'COSTEO-' || ap.code as doc_almacen,
'00' as t_doc,
'' as serie,
'COSTEO-' || ap.code as nro_documento,
'' as proveedor,
coalesce(cli.toneladas_secas,0) as ingreso, 0 as salida,  coalesce(cli.total_costo,0) as debe, 0 as haber, cli.p_unit, pl.name as lote

	from
	costeo_it ci
	inner join account_period ap on ap.id = ci.periodo
	inner join costeo_line_it cli on cli.padre = ci.id
	inner join purchase_liquidation pl on pl.id = cli.lote
	inner join product_product pp on pp.id = cli.producto
	cross join production_parameter param
	inner join stock_location sl on sl.id = param.virtual_location_id
	inner join stock_location sl_p on sl_p.id = sl.location_id
	inner join stock_picking_type spt on spt.id = param.picking_type_trasferencias_costeo
	inner join stock_location sl2 on sl2.id = spt.default_location_dest_id
	inner join stock_location sl2_p on sl2_p.id = sl2.location_id

	union all

select
 sl2_p.name || '/' || sl2.name as origen, sl_p.name || '/' || sl.name as destino,  sl2_p.name || '/' || sl2.name as almacen,
'10' as t_op,
'All products' as Categoria,
'M0001' as codigo_p,
't' as unidad,
'MINERAL AURIFERO Y ARGENTIFERO SIN PROCESAR' as producto,
ap.date_stop as fecha_alb,
ap.date_stop as fecha,
'' as periodo,
ar.name as doc_almacen,
'00' as t_doc,
'' as serie,
ar.name as nro_documento,
'' as proveedor,
0 as ingreso ,coalesce(arl.tn,0) as salida , 0 as debe, coalesce(cli.total_costo,0) as haber, cli.p_unit, pl.name as lote
	from
	armado_ruma ar
	inner join account_period ap on ap.id = ar.period_id
	inner join armado_ruma_line arl on arl.padre = ar.id
	inner join purchase_liquidation pl on pl.id = arl.nro_lote
	inner join product_product pp on pp.id = arl.product_id
	cross join production_parameter param
	inner join stock_location sl on sl.id = param.virtual_location_id
	inner join stock_location sl_p on sl_p.id = sl.location_id
	inner join stock_picking_type spt on spt.id = param.picking_type_trasferencias_costeo
	inner join stock_location sl2 on sl2.id = spt.default_location_dest_id
	inner join stock_location sl2_p on sl2_p.id = sl2.location_id
	left join costeo_line_it cli on cli.padre is not null and cli.lote = arl.nro_lote

	) as T where  ( fecha >= '""" + str(self.period_ini.date_start) +"""' and fecha <=  '""" + str(self.period_fin.date_stop) +"""' )  
	order by lote, fecha , haber


	)
	TO '""" + str( direccion + 'newkardex.csv') + """'
	with delimiter '|' csv header
	""")


			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			file_name = 'a.txt'
			
			txt_act = None
			corredor = 1
			#exp = ("".join(open( str( direccion + 'newkardex.csv' ), 'r').readlines() ) )
			
			todos = open( str( direccion + 'newkardex.csv' ), 'r').readlines()
			rst = []
			lote = 'None'
			saldos = [0,0] #17 al 20
			unica = 0
			for i in todos:
				if unica == 0:
					rst.append(i.replace('\n','') + '|SaldoFisico|SaldoValorado\n')
					unica +=1
				else:
					linea = i.replace('\n','').split('|')
					if len(linea)>1:
						if lote != linea[21]:
							lote = linea[21]
							saldos = [0,0]

						try:
							saldos[0] += float(linea[16])
						except:
							pass
						try:
							saldos[0] -= float(linea[17])
						except:
							pass
						try:
							saldos[1] += float(linea[18])
						except:
							pass
						try:
							saldos[1] -= float(linea[19])
						except:
							pass

						rst.append(i.replace('\n','') + '|' + str(saldos[0])+ '|' + str(saldos[1]) +'\n')


			exp = ("".join(rst) )


			vals = {
				'output_name': 'KardexLote.csv',
				'output_file': base64.encodestring(  "-- Sin Registros --" if exp =="" else exp ),		
			}

			sfs_id = self.env['export.file.save'].create(vals)

			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}



		if self.tipo == '2':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			if not direccion:
				raise osv.except_osv('Alerta!','No esta configurado la dirección de Directorio en Parametros')

			self.env.cr.execute("""		
			COPY (	


	select * from (
	select
'Ubicacion virtuales/Produccion' as origen, '/ARUM /Existencias' as destino,'/ARUM /Existencias' as almacen,
'8' as t_op,
'All products' as Categoria,
'' as codigo_p,
't' as unidad,
'RUMA' as producto,
ap.date_stop as fecha_alb,
ap.date_stop as fecha,
'' as periodo,
'COSTEORUMA-' || ap.code as doc_almacen,
'00' as t_doc,
'' as serie,
'COSTEORUMA-' || ap.code as nro_documento,
'' as proveedor,
coalesce(crl.toneladas,0) as ingreso, 0 as salida, coalesce(crl.total,0) as debe,0 as haber, crl.p_unit, ar.name as lote

from
costeo_ruma cr
inner join account_period ap on ap.id = cr.periodo
inner join costeo_ruma_linea crl on crl.costeo_id = cr.id
inner join armado_ruma ar on ar.id = crl.ruma_id

union all

	select
 '/ARUM /Existencias' as origen, 'Ubicacion virtuales/Produccion' as destino,'/ARUM /Existencias' as almacen,
'10' as t_op,
'All products' as Categoria,
'' as codigo_p,
't' as unidad,
'RUMA' as producto,
ap.date_stop as fecha_alb,
ap.date_stop as fecha,
'' as periodo,
cc.name as doc_almacen,
'00' as t_doc,
'' as serie,
cc.name as nro_documento,
'' as proveedor,
0 as ingreso, coalesce(crl.toneladas,0) as salida, 0 as debe,coalesce(crl.total,0) as haber, crl.p_unit, ar.name as lote

from
costeo_ruma cr
inner join costeo_ruma_linea crl on crl.costeo_id = cr.id
inner join armado_ruma ar on ar.id = crl.ruma_id
inner join consumo_ruma_line ccc on ccc.nro_ruma = crl.ruma_id
inner join consumo_ruma cc on cc.id = ccc.padre
inner join account_period ap on ap.id = cc.period_id



	) as T where  ( fecha >= '""" + str(self.period_ini.date_start) +"""' and fecha <=  '""" + str(self.period_fin.date_stop) +"""' )  
	order by lote, fecha, haber


	)
	TO '""" + str( direccion + 'newkardex.csv') + """'
	with delimiter '|' csv header
	""")


			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			file_name = 'a.txt'
			
			txt_act = None
			corredor = 1


			todos = open( str( direccion + 'newkardex.csv' ), 'r').readlines()
			rst = []
			lote = 'None'
			saldos = [0,0] #17 al 20
			unica = 0
			for i in todos:
				if unica == 0:
					rst.append(i.replace('\n','') + '|SaldoFisico|SaldoValorado\n')
					unica +=1
				else:
					linea = i.replace('\n','').split('|')
					if len(linea)>1:
						if lote != linea[21]:
							lote = linea[21]
							saldos = [0,0]
						try:
							saldos[0] += float(linea[16])
						except:
							pass
						try:
							saldos[0] -= float(linea[17])
						except:
							pass
						try:
							saldos[1] += float(linea[18])
						except:
							pass
						try:
							saldos[1] -= float(linea[19])
						except:
							pass

						rst.append(i.replace('\n','') + '|' + str(saldos[0])+ '|' + str(saldos[1]) +'\n')

					unica +=1

			exp = ("".join(rst) )
			#exp = ("".join(open( str( direccion + 'newkardex.csv' ), 'r').readlines() ) )
			
			vals = {
				'output_name': 'KardexRuma.csv',
				'output_file': base64.encodestring(  "-- Sin Registros --" if exp =="" else exp ),		
			}

			sfs_id = self.env['export.file.save'].create(vals)

			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}








		if self.tipo == '3':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			if not direccion:
				raise osv.except_osv('Alerta!','No esta configurado la dirección de Directorio en Parametros')

			self.env.cr.execute("""		
			COPY (	


	select * from (
	


select 
'Ubicacion virtuales / Produccion' as origen,
'/PT BL /Existencias' as destino,
'/PT BL /Existencias' as Almacen,
'8' as t_op,
'Bullon Oro' as categoria,
'45-B1' as codigo_p,
'g' as unidad,
'BULLON' as producto,
ap.date_stop as fecha_alb,
ap.date_stop as fecha,
'' as periodo,
ltt.name as doc_almacen,
'' as t_doc,
'' as serie,
ltt.name as nro_documento,
'' as partner,
coalesce(ltt.au_fino,0)  as ingreso, 0 as salida, coalesce(ltt.costo_total,0) as debe,  0 as haber, 
CASE WHEN coalesce(ltt.au_fino,0) = 0 then 0 else 
ltt.costo_total / ltt.au_fino end as p_unit
from
lote_terminado_tabla ltt
inner join account_period ap on ap.id = ltt.period_id

union all

select
'/PT BL /Existencias' as origen,
'Ubicacion de Clientes' as destino,
'/PT BL /Existencias' as Almacen,
'1' as t_op,
'Bullon Oro' as categoria,
'45-B1' as codigo_p,
'g' as unidad,
'BULLON' as producto,
ap.date_stop as fecha_alb,
ap.date_stop as fecha,
'' as periodo,
ltt.name as doc_almacen,
'' as t_doc,
'' as serie,
ltt.name as nro_documento,
T.name as partner,
0  as ingreso, 
coalesce(ltt.au_fino,0) as salida, 
0 as debe,  
coalesce(ltt.costo_total,0) as haber, 
CASE WHEN coalesce(ltt.au_fino,0) = 0 then 0 else 
ltt.costo_total / ltt.au_fino end as p_unit

from
lote_terminado_tabla ltt
inner join account_period ap on ap.id = ltt.period_id
inner join (
select sm.lote_terminado_tabla_id,rp.name,sp.date from stock_picking sp
inner join stock_move sm on sm.picking_id = sp.id
inner join res_partner rp on rp.id = sp.partner_id
where sm.lote_terminado_tabla_id is not null
) T on T.lote_terminado_tabla_id = ltt.id





	) as T where  ( fecha >= '""" + str(self.period_ini.date_start) +"""' and fecha <=  '""" + str(self.period_fin.date_stop) +"""' )  
order by nro_documento, fecha, haber


	)
	TO '""" + str( direccion + 'newkardex.csv') + """'
	with delimiter '|'  csv header
	""")


			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			file_name = 'a.txt'
			
			txt_act = None
			corredor = 1


			todos = open( str( direccion + 'newkardex.csv' ), 'r').readlines()
			rst = []
			lote = 'None'
			saldos = [0,0] #17 al 20
			unica = 0
			for i in todos:
				if unica == 0:
					rst.append(i.replace('\n','') + '|SaldoFisico|SaldoValorado\n')
					unica +=1
				else:
					linea = i.replace('\n','').split('|')
					if len(linea)>1:
						if lote != linea[11]:
							lote = linea[11]
							saldos = [0,0]
						try:
							saldos[0] += float(linea[16])
						except:
							pass
						try:
							saldos[0] -= float(linea[17])
						except:
							pass
						try:
							saldos[1] += float(linea[18])
						except:
							pass
						try:
							saldos[1] -= float(linea[19])
						except:
							pass

						rst.append(i.replace('\n','') + '|' + str(saldos[0])+ '|' + str(saldos[1]) +'\n')

					unica +=1

			exp = ("".join(rst) )
			#exp = ("".join(open( str( direccion + 'newkardex.csv' ), 'r').readlines() ) )
			
			vals = {
				'output_name': 'KardexProductoTerminado.csv',
				'output_file': base64.encodestring(  "-- Sin Registros --" if exp =="" else exp ),		
			}

			sfs_id = self.env['export.file.save'].create(vals)

			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}



		if self.tipo == '4':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			if not direccion:
				raise osv.except_osv('Alerta!','No esta configurado la dirección de Directorio en Parametros')

			self.env.cr.execute("""		
			COPY (	


	select * from (
	

select
'Ubicaciones Virtuales/ Produccion' as origen,
'Ubicacion Fisicas/ P P / Existencias' as destino,
'/ P P / Existencias' as almacen,
'8' as T_op,
'Oro en Agitadores' as categoria,
'5966' as codigo_p,
'g' as unidad,
'Oro en Agitadores' as producto,
ppi.fecha as fecha_alb,
ppi.fecha as fecha,
'' as periodo,
'LoteProceso-' || ppi.lote_proceso as doc_almacen,
'00' as t_doc,
'' as serie,
'LoteProceso-' || ppi.lote_proceso as nro_documento,
'' as proveedor,
coalesce(ppi.au_gramo,0) as ingreso,
0 as salida,
coalesce(ppi.costo_total,0) as debe,
0 as haber,
'231101 - Fino en Agitadores' as cuentaproducto

from producto_proceso_it ppi
inner join account_period ap on ap.id = ppi.periodo and  split_part(ap.code,'/',1) != '00'

union all 


select
'Ubicaciones Virtuales/ Produccion' as origen,
'Ubicacion Fisicas/ P P / Existencias' as destino,
'/ P P / Existencias' as almacen,
'7' as T_op,
'Oro en Agitadores' as categoria,
'5966' as codigo_p,
'g' as unidad,
'Oro en Agitadores' as producto,
TO_DATE(ppi.fecha::varchar, 'YYYY-MM-01')  + interval '1 month' as fecha_alb,
TO_DATE(ppi.fecha::varchar, 'YYYY-MM-01')  + interval '1 month' as fecha,
'' as periodo,
'LoteProceso-' || ppi.lote_proceso as doc_almacen,
'00' as t_doc,
'' as serie,
'LoteProceso-' || ppi.lote_proceso as nro_documento,
'' as proveedor,
0 as ingreso,
coalesce(ppi.au_gramo,0) as salida,
0 as debe,
coalesce(ppi.costo_total,0) as haber,
'231101 - Fino en Agitadores' as cuentaproducto

from producto_proceso_it ppi
inner join account_period ap on ap.id = ppi.periodo and  split_part(ap.code,'/',1) != '00'





	) as T where  ( fecha >= '""" + str(self.period_ini.date_start) +"""' and fecha <=  '""" + str(self.period_fin.date_stop) +"""' )  
order by nro_documento,fecha, haber


	)
	TO '""" + str( direccion + 'newkardex.csv') + """'
	with delimiter '|' csv header
	""")


			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			file_name = 'a.txt'
			
			txt_act = None
			corredor = 1

			todos = open( str( direccion + 'newkardex.csv' ), 'r').readlines()
			rst = []
			lote = 'None'
			saldos = [0,0] #17 al 20
			unica = 0
			for i in todos:
				if unica == 0:
					rst.append(i.replace('\n','') + '|SaldoFisico|SaldoValorado\n')
					unica +=1
				else:
					linea = i.replace('\n','').split('|')
					if len(linea)>1:
						if lote != linea[11]:
							lote = linea[11]
							saldos = [0,0]
						try:
							saldos[0] += float(linea[16])
						except:
							pass
						try:
							saldos[0] -= float(linea[17])
						except:
							pass
						try:
							saldos[1] += float(linea[18])
						except:
							pass
						try:
							saldos[1] -= float(linea[19])
						except:
							pass

						rst.append(i.replace('\n','') + '|' + str(saldos[0])+ '|' + str(saldos[1]) +'\n')

					unica +=1

			exp = ("".join(rst) )

			#exp = ("".join(open( str( direccion + 'newkardex.csv' ), 'r').readlines() ) )
			
			vals = {
				'output_name': 'KardexProductoEnProceso.csv',
				'output_file': base64.encodestring(  "-- Sin Registros --" if exp =="" else exp ),		
			}

			sfs_id = self.env['export.file.save'].create(vals)

			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}








