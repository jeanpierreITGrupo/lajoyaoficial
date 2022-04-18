# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv
from openerp import netsvc


class detalle_cruce_fac_orden_kardex(models.TransientModel):
	_name = 'detalle.cruce.fac.orden.kardex'

	fecha_ini = fields.Date('Fecha Inicio',required=True)
	fecha_fin = fields.Date('Fecha Final',required=True)

	@api.multi
	def generar_detalle(self):		
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		productos='{'
		almacenes='{'

		lst_products  = self.env['product.product'].search([])

		for producto in lst_products:
			productos=productos+str(producto.id)+','
		productos=productos[:-1]+'}'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
		almacenes=almacenes[:-1]+'}'

		if True:
			self.env.cr.execute("""
				copy (

				select 

F.numero,
F.Partner,
F.tipo_documento,
F.nro_comprobante,
F.asiento_contable,
F.fecha,
F.diario,
F.cuenta,
F.moneda,
F.tipo_cambio,


OP.numero,
OP.licitacion_mensual,
OP.licitacion,
OP.fecha,
OP.ruc,
OP.proveedor,
OP.almacen,
OP.partner_ref,
OP.lista_precio,
OP.moneda,
OP.referencia,
OP.lote,
OP.expectativa_oro,
OP.producto,
OP.unidad,
OP.cantidad,
OP.precio_unidad,
OP.subtotal,
OP.impuesto,
OP.cta_analitica,
OP.estado,


kardex."Ubicación Origen",
kardex."Ubicación Destino",	
kardex."Almacén",
kardex."T. OP",
kardex."Categoria",
kardex."Codigo P.",
kardex."Uni.",
kardex."Producto",
kardex."Fecha Alb.",
kardex."Fecha",
kardex."Periodo",
kardex."Doc. Almacén",
kardex."T. Doc.",
kardex."Serie",
kardex."Nro. Documento",
kardex."Proveedor",
kardex."Ingreso",
kardex."Salida",
kardex."Saldo F",
kardex."C.A.",
kardex."Debe",
kardex."Haber",
kardex."Saldo V.",
kardex."CP",
kardex."Cuenta factura",
kardex."Cuenta producto",
kardex."Cta. Analitica",
kardex."LotePT",
kardex."LoteMP",
kardex."Pedido de Compra",
kardex."Licitacion"


				 from (

					select  
ai.number as numero,
rp.name as Partner,
itd.code as tipo_documento,
ai.supplier_invoice_number as nro_comprobante,
am.name as asiento_contable,
ai.date_invoice as fecha,
aj.name as diario,
aa.code || '-' || aa.name as cuenta,
rc.name as moneda,
ai.currency_rate_auto as tipo_cambio,

ai.po_id as po_id

from account_invoice ai
left join res_partner rp on rp.id = ai.partner_id
left join it_type_document itd on itd.id = ai.type_document_id
left join account_move am on am.id = ai.move_id
left join account_journal aj on aj.id = ai.journal_id
left join account_account aa on aa.id = ai.account_id
left join res_currency rc on rc.id = ai.currency_id


				where ai.date_invoice >= '""" + str(self.fecha_ini)+ """' and ai.date_invoice <= '""" + str(self.fecha_fin) + """' ) as F

				full join (
				select 
				po.name as numero,
				la.number as licitacion_mensual,
				pr.name as licitacion,
				po.date_order as fecha,
				rp.type_number as ruc,
				rp.name as proveedor,
				swx.name || '/' || spt.name as almacen,
				po.partner_ref as partner_ref,
				ppl.name as lista_precio,
				rc.name as moneda,
				po.reference as referencia,

				pl.name as lote,
				pol.gold_expected as expectativa_oro,
				pp.name_template as producto,
				pu.name as unidad,
				pol.product_qty as cantidad,
				pol.price_unit as precio_unidad,
				pol.product_qty * pol.price_unit as subtotal,
				at.name as impuesto,
				aaa.name as cta_analitica,
				CASE WHEN po.state = 'confirmed' THEN 'Esperando aprovacion' ELSE
					CASE WHEN po.state = 'bid' THEN 'Licitacion recibida' ELSE
						CASE WHEN po.state = 'except_invoice' THEN 'Excepcion de factura' ELSE
							CASE WHEN po.state = 'except_picking' THEN 'Excepcion de envio' ELSE
								CASE WHEN po.state = 'draft' THEN 'Borrador' ELSE
									CASE WHEN po.state = 'cancel' THEN 'Cancelado' ELSE
										CASE WHEN po.state = 'done' THEN 'Realizado' ELSE
											CASE WHEN po.state = 'approved' THEN 'Compra confirmada' ELSE
												CASE WHEN po.state = 'sent' THEN 'Peticion presupuesto' ELSE po.state
												END
											END
										END
									END
								END
							END
						END
					END
				END as estado,
				po.id as po_id,
				pp.id as product_id
				from purchase_order po
				left join licitacion_advance la on la.id = po.licitacion_advance_id
				left join purchase_requisition pr on pr.id = po.requisition_id
				left join res_partner rp on rp.id = po.partner_id
				left join stock_picking_type spt on spt.id = po.picking_type_id
				left join stock_warehouse swx on swx.id = spt.warehouse_id
				left join product_pricelist ppl on ppl.id = po.pricelist_id
				left join res_currency rc on rc.id = po.currency_id

				left join purchase_order_line pol on pol.order_id = po.id
				left join purchase_liquidation pl on pl.id = pol.lot_num
				left join product_product pp on pp.id = pol.product_id
				left join product_uom pu on pu.id = pol.product_uom
				left join purchase_order_taxe pot on pot.ord_id = pol.id
				left join account_tax at on at.id = pot.tax_id
				left join account_analytic_account aaa on aaa.id = pol.account_analytic_id
				where po.date_order >= '""" + str(self.fecha_ini)+ """' and po.date_order <= '""" + str(self.fecha_fin) + """'
				) OP on OP.po_id = F.po_id

				full join (
				select 
				origen.complete_name AS "Ubicación Origen",
				destino.complete_name AS "Ubicación Destino",	
				substring(get_kardex_v.almacen,20) AS "Almacén",
				get_kardex_v.operation_type as "T. OP",
				get_kardex_v.categoria as "Categoria",
				get_kardex_v.default_code as "Codigo P.",
				get_kardex_v.unidad as "Uni.",
				get_kardex_v.name_template as "Producto",
				get_kardex_v.fecha_albaran as "Fecha Alb.",
				get_kardex_v.fecha as "Fecha",
				get_kardex_v.periodo as "Periodo",
				get_kardex_v.doc_almac as "Doc. Almacén",
				get_kardex_v.type_doc as "T. Doc.",
				get_kardex_v.serial as "Serie",
				get_kardex_v.nro as "Nro. Documento",
				get_kardex_v.name as "Proveedor",
				get_kardex_v.ingreso as "Ingreso",
				get_kardex_v.salida as "Salida",
				get_kardex_v.saldof as "Saldo F",
				get_kardex_v.cadquiere as "C.A.",
				get_kardex_v.debit as "Debe",
				get_kardex_v.credit as "Haber",
				get_kardex_v.saldov as "Saldo V.",
				get_kardex_v.cprom as "CP",
				--get_kardex_v.cost_account as "Cuenta de costo",
				get_kardex_v.account_invoice as "Cuenta factura",
				get_kardex_v.product_account as "Cuenta producto",
				get_kardex_v.ctanalitica as "Cta. Analitica",
				get_kardex_v.lotept as "LotePT",
				get_kardex_v.lotemp as "LoteMP",
				get_kardex_v.pedido_compra as "Pedido de Compra",
				get_kardex_v.licitacion as "Licitacion",
				get_kardex_v.product_id
				from get_kardex_v("""+ str(self.fecha_ini).replace('/','').replace('-','') + "," + str(self.fecha_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 			
				left join stock_location origen on get_kardex_v.ubicacion_origen = origen.id
				left join stock_location destino on get_kardex_v.ubicacion_destino  = destino.id
				order by get_kardex_v.lotemp,get_kardex_v.location_id,get_kardex_v.product_id,get_kardex_v.fecha,get_kardex_v.esingreso,get_kardex_v.nro
				) kardex on kardex."Pedido de Compra" = op.numero and kardex.product_id = OP.product_id
			)	
TO '"""+ str( direccion + 'detalleordenfackardex.csv' )+ """'
with delimiter '|'  CSV HEADER
		""")
		

			exp = open( str( direccion + 'detalleordenfackardex.csv' ), 'r').read().replace("\\N","")

			newexpo = open(str( direccion + 'DetalleOPVsKardex.csv' ), 'w')
			newexpo.write(exp)
			newexpo.close()

			import zipfile
			try:
				import zlib
				mode= zipfile.ZIP_DEFLATED
			except:
				mode= zipfile.ZIP_STORED
			zf = zipfile.ZipFile(str( direccion + 'newreport.zip' ), 'w',mode)
			zf.write(str( direccion + 'DetalleOPVsKardex.csv' ))
			zf.close()

			newziptxt = open(str( direccion + 'newreport.zip' ),'rb').read()

			vals = {
				'output_name': 'DetalleFacKardexOrdenCompra.zip',
				'output_file': base64.encodestring(  "== Sin Registros ==" if newziptxt =="" else newziptxt ),		
			}

			sfs_id = self.env['export.file.save'].create(vals)
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}




class detalle_orden_compra(models.TransientModel):
	_name = 'detalle.orden.compra'

	fecha_ini = fields.Date('Fecha Inicio',required=True)
	fecha_fin = fields.Date('Fecha Final',required=True)

	@api.multi
	def generar_detalle_orden_compra(self):		
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if True:
			self.env.cr.execute("""
				copy (
					select 
				po.name as numero,
				la.number as licitacion_mensual,
				pr.name as licitacion,
				po.date_order as fecha,
				rp.type_number as ruc,
				rp.name as proveedor,
				spt.name as almacen,
				po.partner_ref as partner_ref,
				ppl.name as lista_precio,
				rc.name as moneda,
				po.reference as referencia,

				pl.name as lote,
				pol.gold_expected as expectativa_oro,
				pp.name_template as producto,
				pu.name as unidad,
				pol.product_qty as cantidad,
				pol.price_unit as precio_unidad,
				pol.product_qty * pol.price_unit as subtotal,
				at.name as impuesto,
				aaa.name as cta_analitica,
				CASE WHEN po.state = 'confirmed' THEN 'Esperando aprovacion' ELSE
					CASE WHEN po.state = 'bid' THEN 'Licitacion recibida' ELSE
						CASE WHEN po.state = 'except_invoice' THEN 'Excepcion de factura' ELSE
							CASE WHEN po.state = 'except_picking' THEN 'Excepcion de envio' ELSE
								CASE WHEN po.state = 'draft' THEN 'Borrador' ELSE
									CASE WHEN po.state = 'cancel' THEN 'Cancelado' ELSE
										CASE WHEN po.state = 'done' THEN 'Realizado' ELSE
											CASE WHEN po.state = 'approved' THEN 'Compra confirmada' ELSE
												CASE WHEN po.state = 'sent' THEN 'Peticion presupuesto' ELSE po.state
												END
											END
										END
									END
								END
							END
						END
					END
				END as estado 
				from purchase_order po
				left join licitacion_advance la on la.id = po.licitacion_advance_id
				left join purchase_requisition pr on pr.id = po.requisition_id
				left join res_partner rp on rp.id = po.partner_id
				left join stock_picking_type spt on spt.id = po.picking_type_id
				left join product_pricelist ppl on ppl.id = po.pricelist_id
				left join res_currency rc on rc.id = po.currency_id

				left join purchase_order_line pol on pol.order_id = po.id
				left join purchase_liquidation pl on pl.id = pol.lot_num
				left join product_product pp on pp.id = pol.product_id
				left join product_uom pu on pu.id = pol.product_uom
				left join purchase_order_taxe pot on pot.ord_id = pol.id
				left join account_tax at on at.id = pot.tax_id
				left join account_analytic_account aaa on aaa.id = pol.account_analytic_id
				where po.date_order >= '""" + str(self.fecha_ini)+ """' and po.date_order <= '""" + str(self.fecha_fin) + """'
	)	
TO '"""+ str( direccion + 'detalleordencompra.csv' )+ """'
with delimiter '|'  CSV HEADER
		""")
		

			exp = open( str( direccion + 'detalleordencompra.csv' ), 'r').read().replace("\\N","")


			vals = {
				'output_name': 'DetalleOrdenCompra.txt',
				'output_file': base64.encodestring(  "== Sin Registros ==" if exp =="" else exp ),		
			}

			sfs_id = self.env['export.file.save'].create(vals)
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}



class detalle_facturas(models.TransientModel):
	_name = 'detalle.facturas'

	fecha_ini = fields.Date('Fecha Inicio',required=True)
	fecha_fin = fields.Date('Fecha Final',required=True)

	@api.multi
	def generar_detalle_orden_compra(self):		
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if True:
			self.env.cr.execute("""
				copy (
					select  
ai.number as numero,
rp.name as Partner,
itd.code as tipo_documento,
ai.supplier_invoice_number as nro_comprobante,
am.name as asiento_contable,
ai.date_invoice as fecha,
aj.name as diario,
aa.code || '-' || aa.name as cuenta,
rc.name as moneda,
ai.currency_rate_auto as tipo_cambio,

sl.name as ubicacion,
pp.name_template as producto,
ail.name as descripcion,
aal.code || '-' || aal.name as cuenta_linea,
aaa.name as cuenta_analitica,
ail.quantity as cantidad,
pu.name as unidad,
ail.price_unit as precio_unitario,
at.name as impuesto,
ail.price_subtotal as subtotal

from account_invoice ai
left join res_partner rp on rp.id = ai.partner_id
left join it_type_document itd on itd.id = ai.type_document_id
left join account_move am on am.id = ai.move_id
left join account_journal aj on aj.id = ai.journal_id
left join account_account aa on aa.id = ai.account_id
left join res_currency rc on rc.id = ai.currency_id

left join account_invoice_line ail on ail.invoice_id = ai.id
left join stock_location sl on sl.id = ail.location_id
left join product_product pp on pp.id = ail.product_id
left join account_account aal on aal.id = ail.account_id
left join account_analytic_account aaa on aaa.id = ail.account_analytic_id
left join product_uom pu on pu.id = ail.uos_id
left join account_invoice_line_tax ailt on ailt.invoice_line_id = ail.id
left join account_tax at on at.id = ailt.tax_id

				where ai.date_invoice >= '""" + str(self.fecha_ini)+ """' and ai.date_invoice <= '""" + str(self.fecha_fin) + """'
	)	
TO '"""+ str( direccion + 'detallefactura.csv' )+ """'
with delimiter '|'  CSV HEADER
		""")
		

			exp = open( str( direccion + 'detallefactura.csv' ), 'r').read().replace("\\N","")


			vals = {
				'output_name': 'DetalleFactura.txt',
				'output_file': base64.encodestring(  "== Sin Registros ==" if exp =="" else exp ),		
			}

			sfs_id = self.env['export.file.save'].create(vals)
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}

