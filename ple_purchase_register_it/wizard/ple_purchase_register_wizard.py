# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import os

class ple_purchase_register_wizard(osv.TransientModel):
	_name='ple.purchase.register.wizard'
	period_ini = fields.Many2one('account.period','Periodo',required=True)
	tipo_ple = fields.Selection([('81','8.1'),('82','8.2'),('83','8.3')], string="Formato",required=True)
	

	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

		if not direccion:
			raise osv.except_osv('Alerta!', 'No esta configurado la dirección de Directorio en Parametros')

		if self.tipo_ple == '81':			
			self.env.cr.execute("""
	COPY (select  distinct
	CASE WHEN ap.code is not Null THEN substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || '00' ELSE '' END as campo1,

substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name as campo2,
	--CASE WHEN ai_ple.id is not Null THEN ai_ple.id || 'AI' ELSE compra.am_id || 'AM' END as campo2,
	-- CASE WHEN compra.am_id is not Null THEN (compra.am_id)::varchar ELSE '' END as campo2,
	CASE WHEN compra.voucher is not Null THEN  'M' || reverse( substring ( reverse(compra.voucher) , 0 , (CASE WHEN position('/' in reverse(compra.voucher))= 0 THEN 1000 ELSE position('/' in reverse(compra.voucher)) END)  ) ) ELSE '' END as campo3,
	CASE WHEN compra.fechaemision is not Null THEN (to_char( compra.fechaemision::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo4,
	CASE WHEN compra.fechavencimiento is not Null THEN (to_char( compra.fechavencimiento::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo5,
	CASE WHEN anulado.name = compra.razonsocial and anulado.type_number = compra.ruc THEN '00' ELSE
		CASE WHEN compra.tipodocumento is not Null THEN 
			CASE WHEN compra.tipodocumento = 'CP' THEN '00' ELSE compra.tipodocumento END
		ELSE '' 
	END END as campo6,
	CASE WHEN compra.tipodocumento = '05' or compra.tipodocumento = '50' THEN compra.serie else
CASE WHEN compra.tipodocumento = '10' THEN '1683' ELSE
	CASE WHEN compra.serie is not Null THEN repeat('0',4-char_length(compra.serie)) || compra.serie ELSE '' END END END as campo7,
	CASE WHEN compra.tipodocumento in ('50','52') THEN substring(ap.code,4,5 ) else '' END as campo8,
	CASE WHEN compra.numero is not Null THEN compra.numero ELSE '' END as campo9,
	CASE WHEN am.ultimo_numero_consolidado is not Null THEN am.ultimo_numero_consolidado::varchar ELSE ''::varchar END as campo10,

		CASE WHEN anulado.name = compra.razonsocial and anulado.type_number = compra.ruc THEN '' ELSE
	CASE WHEN compra.tdp is not Null THEN compra.tdp ELSE '' END END as campo11,

	CASE WHEN anulado.name = compra.razonsocial and anulado.type_number = compra.ruc THEN '' ELSE
	CASE WHEN compra.ruc is not Null THEN compra.ruc ELSE '' END END as campo12,

CASE WHEN anulado.name = compra.razonsocial and anulado.type_number = compra.ruc THEN '' ELSE
	CASE WHEN compra.razonsocial is not Null THEN compra.razonsocial ELSE '' END END as campo13,
	CASE WHEN compra.bioge is not Null THEN (compra.bioge)::varchar ELSE '0.00' END as campo14,
	CASE WHEN compra.igva is not Null THEN (compra.igva)::varchar ELSE '0.00' END as campo15,
	CASE WHEN compra.biogeng is not Null THEN (compra.biogeng)::varchar ELSE '0.00' END as campo16,
	CASE WHEN compra.igvb is not Null THEN (compra.igvb)::varchar ELSE '0.00' END as campo17,
	CASE WHEN compra.biong is not Null THEN (compra.biong)::varchar ELSE '0.00' END as campo18,
	CASE WHEN compra.igvc is not Null THEN (compra.igvc)::varchar  ELSE '0.00' END as campo19,
	CASE WHEN compra.cng is not Null THEN (compra.cng)::varchar ELSE '0.00' END as campo20,
	CASE WHEN compra.isc is not Null THEN (compra.isc)::varchar ELSE '0.00' END as campo21,
	CASE WHEN compra.otros is not Null THEN (compra.otros)::varchar ELSE '0.00' END as campo22,
	CASE WHEN compra.total is not Null THEN (compra.total)::varchar ELSE '0.00' END as campo23,
CASE WHEN compra.moneda is not Null THEN 
	CASE WHEN compra.moneda = '' THEN 'PEN' ELSE compra.moneda END
ELSE 'PEN' END as campo24,
	CASE WHEN compra.tc is not Null THEN ( round(compra.tc,3) )::varchar ELSE '1.000' END as campo25,
	CASE WHEN compra.fechadm is not Null THEN (to_char( compra.fechadm::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo26,
	CASE WHEN compra.td is not Null THEN compra.td ELSE '' END as campo27,
	CASE WHEN compra.seried is not Null THEN repeat('0',4-char_length(compra.seried)) || compra.seried ELSE '' END as campo28,
	CASE WHEN compra.td in ('50','52') THEN compra.seried ELSE '' END as campo29,
	CASE WHEN compra.numerodd is not Null THEN compra.numerodd ELSE '' END as campo30,

	CASE WHEN compra.fechad is not Null THEN (to_char( compra.fechad::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo31,
	CASE WHEN compra.numerod is not Null THEN compra.numerod ELSE '' END as campo32,

	CASE WHEN am.sujeto_a_retencion THEN '1'::varchar ELSE ''::varchar END as campo33,
	CASE WHEN am.tipo_adquisicion is not Null THEN am.tipo_adquisicion::varchar ELSE ''::varchar END as campo34,
	CASE WHEN am.contrato_o_proyecto is not Null THEN am.contrato_o_proyecto::varchar else ''::varchar END as campo35,
	CASE WHEN am.inconsistencia_tipo_cambio THEN '1'::varchar ELSE ''::varchar END as campo36,
	CASE WHEN am.proveedor_no_habido THEN '1'::varchar ELSE ''::varchar END as campo37,
	CASE WHEN am.renuncio_a_exoneracion_igv THEN '1'::varchar ELSE ''::varchar END as campo38,
	CASE WHEN am.inconsistencia_dni_liquidacion_comp THEN '1'::varchar ELSE ''::varchar END as campo39,
	CASE WHEN am.cancelado_medio_pago THEN '1'::varchar ELSE ''::varchar END as campo40,

	am.ple_compra as campo41,
	'' as campo35
	from get_compra_1_1_1(false,0,219001) compra
	inner join account_period ap on ap.name = compra.periodo
	inner join account_move am on am.id = compra.am_id
	left join account_period ap2 on ap2.id = am.periodo_ajuste_modificacion_ple_compra
	left join res_partner rp_veri on rp_veri.id = am.partner_id
inner join account_journal aj on aj.id = am.journal_id
cross join main_parameter
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
	where  compra.tipodocumento !='91' and  rp_veri.is_resident != True and (ap2.id = """+ str(self.period_ini.id) + """ or ap.id = """+ str(self.period_ini.id) + """ ) )
	TO '"""+ str( direccion +  'purchase.csv' )+ """'
	with delimiter '|'
			""")


	
		
		if self.tipo_ple == '82':
			self.env.cr.execute("""
	COPY ( select * from (select  distinct
	CASE WHEN ap.code is not Null THEN substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || '00' ELSE '' END as campo1,
substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name as campo2,
	--CASE WHEN ai_ple.id is not Null THEN ai_ple.id || 'AI' ELSE compra.am_id || 'AM' END as campo2,
	-- CASE WHEN compra.am_id is not Null THEN (compra.am_id)::varchar ELSE '' END as campo2,
	CASE WHEN compra.voucher is not Null THEN  'M' || reverse( substring ( reverse(compra.voucher) , 0 , (CASE WHEN position('/' in reverse(compra.voucher))= 0 THEN 1000 ELSE position('/' in reverse(compra.voucher)) END)  ) ) ELSE '' END as campo3,
	
	CASE WHEN compra.fechaemision is not Null THEN (to_char( compra.fechaemision::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo4,
	CASE WHEN anulado.name = compra.razonsocial and anulado.type_number = compra.ruc THEN '00' ELSE
		CASE WHEN compra.tipodocumento is not Null THEN 
			CASE WHEN compra.tipodocumento = 'CP' THEN '00' ELSE compra.tipodocumento END
		ELSE '' 
	END END as campo5,
CASE WHEN compra.tipodocumento = '10' THEN '1683' ELSE
	CASE WHEN compra.serie is not Null THEN repeat('0',4-char_length(compra.serie)) || compra.serie  ELSE '' END END as campo6,
	CASE WHEN compra.numero is not Null THEN compra.numero ELSE '' END as campo7,
	

	CASE WHEN compra.bioge is not Null THEN (compra.bioge)::varchar ELSE '0.00' END as campo8,
	CASE WHEN compra.otros is not Null THEN (compra.otros)::varchar ELSE '0.00' END as campo9,
	CASE WHEN compra.total is not Null THEN (compra.total)::varchar ELSE '0.00' END as campo10,


	CASE WHEN am.tipo_sustento_credito_fiscasl is not Null THEN am.tipo_sustento_credito_fiscasl ELSE '' END as campo11,
	CASE WHEN am.serie_sustento_credito_fiscasl is not Null THEN am.serie_sustento_credito_fiscasl ELSE '' END as campo12,
	CASE WHEN am.anio_sustento_credito_fiscasl is not Null THEN am.anio_sustento_credito_fiscasl ELSE '' END as campo13,
	CASE WHEN am.nro_comp_sustento_credito_fiscasl is not Null THEN am.nro_comp_sustento_credito_fiscasl ELSE '' END as campo14,
	CASE WHEN am.impuesto_retenido is not Null THEN am.impuesto_retenido ELSE 0.00 END as campo15,
	
CASE WHEN compra.moneda is not Null THEN 
	CASE WHEN compra.moneda = '' THEN 'PEN' ELSE compra.moneda END
ELSE 'PEN' END as campo16,

	CASE WHEN compra.tc is not Null THEN (  round(compra.tc,3) )::varchar ELSE '1.000' END as campo17,
	CASE WHEN rp.pais_residencia_nd is not Null THEN rp.pais_residencia_nd::varchar ELSE '' END as campo18,
	CASE WHEN rp.name is not Null THEN rp.name::varchar ELSE '' END as campo19,
	CASE WHEN rp.domicilio_extranjero_nd is not Null THEN rp.domicilio_extranjero_nd::varchar ELSE '' END as campo20,
	CASE WHEN rp.numero_identificacion_nd is not Null THEN rp.numero_identificacion_nd::varchar ELSE '' END as campo21,
	CASE WHEN rpb.numero_identificacion_nd is not Null THEN rpb.numero_identificacion_nd::varchar ELSE '' END as campo22,

	CASE WHEN rpb.name is not Null THEN rpb.name::varchar ELSE '' END as campo23,
	CASE WHEN rpb.pais_residencia_nd is not Null THEN rpb.pais_residencia_nd::varchar ELSE '' END as campo24,
	CASE WHEN rp.vinculo_contribuyente_residente_extranjero is not Null THEN rp.vinculo_contribuyente_residente_extranjero::varchar ELSE '' END as campo25,


CASE WHEN am.renta_bruta is not Null THEN am.renta_bruta::varchar ELSE '' END as campo26,
CASE WHEN am.deduccion_costo_enajenacion is not Null THEN am.deduccion_costo_enajenacion::varchar ELSE '' END as campo27,
CASE WHEN am.renta_neta is not Null THEN am.renta_neta::varchar ELSE '' END as campo28,
CASE WHEN am.tasa_de_retencion is not Null THEN am.tasa_de_retencion::varchar ELSE '' END as campo29,
CASE WHEN am.impuesto_retenido is not Null THEN am.impuesto_retenido ELSE 0.00 END as campo30,

	CASE WHEN rp.convenios_evitar_doble_imposicion is not Null THEN rp.convenios_evitar_doble_imposicion::varchar ELSE '' END as campo31,

	CASE WHEN am.exoneracion_aplicada is not Null THEN am.exoneracion_aplicada::varchar ELSE '' END as campo32,
	CASE WHEN am.tipo_de_renta is not Null THEN am.tipo_de_renta::varchar ELSE '' END as campo33,
	CASE WHEN am.modalidad_servicio_prestada is not Null THEN  am.modalidad_servicio_prestada::varchar ELSE ''  END as campo34,
	CASE WHEN am.aplica_art_del_impuesto THEN '1'::varchar ELSE ''::varchar END as campo35,

	am.ple_compra as campo36,

	'' as campo37
	from get_compra_1_1_1(false,0,219001) compra
	inner join account_period ap on ap.name = compra.periodo
	inner join account_move am on am.id = compra.am_id
	left join account_period ap2 on ap2.id = am.periodo_ajuste_modificacion_ple_compra
	left join res_partner rp on rp.id = am.partner_id
	left join res_partner rpb on rpb.id = am.beneficiario_de_pagos
inner join account_journal aj on aj.id = am.journal_id
cross join main_parameter 
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
	where  (rp.is_resident=true or compra.tipodocumento ='91') and  ( ap2.id = """+ str(self.period_ini.id) + """ or ap.id = """+ str(self.period_ini.id) + """ )) as TOTALCS where campo5 in ('00','91','97','98') )  
	TO '"""+ str( direccion +  'purchase.csv' )+ """'
	with delimiter '|'
			""")

		
		if self.tipo_ple == '83':
			self.env.cr.execute("""
	COPY (select  distinct
	CASE WHEN ap.code is not Null THEN substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || '00' ELSE '' END as campo1,
substring(ap.code,4,5 ) || substring(ap.code,0,3 ) || aj.code || am.name as campo2,
	--CASE WHEN ai_ple.id is not Null THEN ai_ple.id || 'AI' ELSE compra.am_id || 'AM' END as campo2,
	-- CASE WHEN compra.am_id is not Null THEN (compra.am_id)::varchar ELSE '' END as campo2,
	CASE WHEN compra.voucher is not Null THEN  'M' || reverse( substring ( reverse(compra.voucher) , 0 , (CASE WHEN position('/' in reverse(compra.voucher))= 0 THEN 1000 ELSE position('/' in reverse(compra.voucher)) END)  ) ) ELSE '' END as campo3,
	CASE WHEN compra.fechaemision is not Null THEN (to_char( compra.fechaemision::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo4,
	CASE WHEN compra.fechavencimiento is not Null THEN (to_char( compra.fechavencimiento::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo5,
	CASE WHEN anulado.name = compra.razonsocial and anulado.type_number = compra.ruc THEN '00' ELSE
		CASE WHEN compra.tipodocumento is not Null THEN 
			CASE WHEN compra.tipodocumento = 'CP' THEN '00' ELSE compra.tipodocumento END
		ELSE '' 
	END END as campo6,
CASE WHEN compra.tipodocumento = '10' THEN '1683' ELSE
	CASE WHEN compra.serie is not Null THEN repeat('0',4-char_length(compra.serie)) || compra.serie ELSE '' END END as campo7,
	CASE WHEN compra.numero is not Null THEN compra.numero ELSE '' END as campo8,
	CASE WHEN am.ultimo_numero_consolidado is not Null THEN am.ultimo_numero_consolidado::varchar ELSE ''::varchar END as campo9,
	CASE WHEN compra.tdp is not Null THEN ((compra.tdp)::integer)::varchar ELSE '' END as campo10,
	CASE WHEN compra.ruc is not Null THEN compra.ruc ELSE '' END as campo11,
CASE WHEN anulado.name = compra.razonsocial and anulado.type_number = compra.ruc THEN '' ELSE
	CASE WHEN compra.razonsocial is not Null THEN compra.razonsocial ELSE '' END END as campo12,


	CASE WHEN compra.bioge is not Null THEN (compra.bioge)::varchar ELSE '0.00' END as campo13,
	CASE WHEN compra.igva is not Null THEN (compra.igva)::varchar ELSE '0.00' END as campo14,
	CASE WHEN compra.otros is not Null THEN (compra.otros)::varchar ELSE '0.00' END as campo15,
	CASE WHEN compra.total is not Null THEN (compra.total)::varchar ELSE '0.00' END as campo16,
	

CASE WHEN compra.moneda is not Null THEN 
	CASE WHEN compra.moneda = '' THEN 'PEN' ELSE compra.moneda END
ELSE 'PEN' END as campo17,


	CASE WHEN compra.tc is not Null THEN ( round(compra.tc,3))::varchar ELSE '1.000' END as campo18,
	CASE WHEN compra.fechadm is not Null THEN (to_char( compra.fechadm::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo19,
	CASE WHEN compra.td is not Null THEN compra.td ELSE '' END as campo20,
	CASE WHEN compra.seried is not Null THEN repeat('0',4-char_length(compra.seried)) || compra.seried ELSE '' END as campo21,
	CASE WHEN compra.numerodd is not Null THEN compra.numerodd ELSE '' END as campo22,

	CASE WHEN compra.fechad is not Null THEN (to_char( compra.fechad::date , 'DD/MM/YYYY'))::varchar ELSE '' END as campo23,
	CASE WHEN compra.numerod is not Null THEN compra.numerod ELSE '' END as campo24,

	CASE WHEN am.sujeto_a_retencion THEN '1'::varchar ELSE ''::varchar END  as campo25,


	CASE WHEN am.tipo_adquisicion is not Null THEN am.tipo_adquisicion::varchar ELSE ''::varchar END as campo26,
	

	CASE WHEN am.inconsistencia_tipo_cambio THEN '1'::varchar ELSE ''::varchar END as campo27,
	CASE WHEN am.proveedor_no_habido THEN '1'::varchar ELSE ''::varchar END as campo28,
	CASE WHEN am.renuncio_a_exoneracion_igv THEN '1'::varchar ELSE ''::varchar END as campo29,
	CASE WHEN am.cancelado_medio_pago THEN '1'::varchar ELSE ''::varchar END as campo30,

	am.ple_compra as campo31,
	'' as campo32
	from get_compra_1_1_1(false,0,219001) compra
	inner join account_period ap on ap.name = compra.periodo
	inner join account_move am on am.id = compra.am_id
	left join account_period ap2 on ap2.id = am.periodo_ajuste_modificacion_ple_compra
inner join account_journal aj on aj.id = am.journal_id
cross join main_parameter 
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
	where ( ap2.id = """+ str(self.period_ini.id) + """ or ap.id = """+ str(self.period_ini.id) + """  ) )
	TO '"""+ str( direccion +  'purchase.csv' )+ """'
	with delimiter '|'
			""")
		#CASE WHEN ap.id != ap2.id THEN (CASE WHEN am.ckeck_modify_ple THEN  '9' ELSE '8' END ) ELSE '1' END as campo34,

		ruc = self.env['res.company'].search([])[0].partner_id.type_number
		mond = self.env['res.company'].search([])[0].currency_id.name

		if not ruc:
			raise osv.except_osv('Alerta!', 'No esta configurado el RUC en la compañia')

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		file_name = 'a.txt'
			
		exp = "".join(open( str( direccion + 'purchase.csv' ), 'r').readlines() )
		
		#vals = {
		#	'output_name': 'LE' + ruc + self.period_ini.code[3:7]+ self.period_ini.code[:2]+'00080100001'+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt',
		#	'output_file': base64.encodestring(  "\r\n" if exp =="" else exp ),		
		#}


		direccion_ple = self.env['main.parameter'].search([])[0].dir_ple_create_file


		if not direccion_ple:
			raise osv.except_osv('Alerta!', 'No esta configurado el directorio para los PLE Sunat en parametros.')
		
		name_camb = ""	
		if self.tipo_ple == "81":
			name_camb = "00080100001"
		if self.tipo_ple == "82":
			name_camb = "00080200001"
		if self.tipo_ple == "83":
			name_camb = "00080300001"

		#file_ple = open(direccion_ple + 'LE' + ruc + self.period_ini.code[3:7]+ self.period_ini.code[:2]+name_camb+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt','w')
		#file_ple.write(exp)
		#file_ple.close()


		vals = {
			'output_name': 'LE' + ruc + self.period_ini.code[3:7]+ self.period_ini.code[:2]+name_camb+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt',
			'output_file': base64.encodestring(  "== Sin Registros ==" if exp =="" else exp ),		
		}

		"""

		rep = "Se genero exitosamente el archivo: "+ 'LE' + ruc + self.period_ini.code[3:7]+ self.period_ini.code[:2]+name_camb+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt'
		obj_id = self.env['warning'].create({'title': 'Generar PLE Compra', 'message': rep, 'type': 'info'})

		res = {
			'name': 'Generar PLE Compra',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'warning',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': obj_id.id
		}
		return res

		"""
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

