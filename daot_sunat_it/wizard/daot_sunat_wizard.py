# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class daot_sunat_wizard(osv.TransientModel):
	_name='daot.sunat.wizard'
	type = fields.Selection([('compra', 'Compra'), ('venta', 'Venta')], 'Tipo', required=True)
	fiscal_id = fields.Many2one('account.fiscalyear',string='Año Fiscal',required=True)
	amount = fields.Integer('Monto',required=True)
	type_document_ids = fields.Many2many('it.type.document','datos_sunat_rel_type_document','type_document_id','datos_sunat_id',string='Tipos de Documentos A No Considerarse:')



	@api.multi
	def do_rebuild_compra(self):
		per_ini = self.fiscal_id.code + '00'
		per_fin = self.fiscal_id.code + '13'
		code_tp = self.type_document_ids.mapped('code')
		id_tp = self.type_document_ids.mapped('id')
		txt_code_tp = "where account_move.check_daot=false or account_move.check_daot is Null "
		txt_id_tp = ""
		if len(code_tp) > 0:
			if len(code_tp) == 1:
				code_tp = tuple( [str(i) for i in code_tp] )
				txt_code_tp = "and tipodocumento not in ('"+str(code_tp[0])+"')"
				
				id_tp = tuple( [str(i) for i in id_tp] )
				txt_id_tp = "and tipo_doc not in ("+str(id_tp[0])+")"
			else:
				code_tp = tuple( [str(i) for i in code_tp] )
				txt_code_tp = "and tipodocumento not in "+str(code_tp)
				
				id_tp = tuple( [str(i) for i in id_tp] )
				txt_id_tp = "and tipo_doc not in "+str(id_tp)

		self.env.cr.execute(""" 
		select row_number() OVER () AS id,itdpc.code,rcp.type_number,"""+ str(self.fiscal_id.code)+""" as periodo,
		CASE WHEN rp.is_resident THEN 3 ELSE
		 CASE WHEN rp.is_company THEN 1 ELSE 2 END
		END AS tipopersona,
		itdp.code, rp.type_number,A.monto,
		CASE WHEN rp.is_company THEN Null::varchar ELSE rp.last_name_f END as app,
		CASE WHEN rp.is_company THEN Null::varchar ELSE rp.last_name_m END as apm, 
		CASE WHEN rp.is_company THEN Null::varchar ELSE rp.first_name END as fn, 
		CASE WHEN rp.is_company=false THEN Null::varchar ELSE rp.name END as rz
		from (
			select sum(monto) as monto, razonsocial from (
				select coalesce(bioge,0) +coalesce(biogeng,0) +coalesce(biong,0) +coalesce(cng,0) +coalesce(isc,0) +coalesce(otros,0) as monto ,razonsocial from get_compra_1_1_1(false,"""+str(per_ini)+""","""+str(per_fin)+""") as T inner join account_move on account_move.id = T.am_id """+txt_code_tp+"""
			union all
				select total as monto, razonsocial from daot_register where type_operation='costo' """+txt_id_tp+"""
			) AS T GROUP by razonsocial
		) as A
		inner join res_partner rp on  rp.name = A.razonsocial
		left join it_type_document_partner itdp on itdp.id = rp.type_document_id
		cross join res_company rc
		inner join res_partner rcp on rcp.id = rc.partner_id
		left join it_type_document_partner itdpc on itdpc.id = rcp.type_document_id
		where monto >"""+str(self.amount)+"""
		""")
		tra = self.env.cr.fetchall()
		
		
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		rpta = ""
		for i in tra:
			n1=''
			n2=''
			if i[10] != None:
				t = i[10].split(' ',1)
				if len(t) == 1:
					n1= t[0]
				else:
					n1=t[0]
					n2=t[1]
			rpta += (unicode( str(int(i[0]) if i[0]!= None else '')+ '|'+str(int(i[1]) if i[1]!= None else '')+ '|'+str(i[2]  if i[2]!= None else '')+ '|'+str(int(i[3])  if i[3]!= None else '')+ '|'+str(int(i[4])  if i[4]!= None else '')+ '|'+str(int(i[5])  if i[5]!= None else '')+ '|'+str(i[6]  if i[6]!= None else '')+ '|'+str(int(i[7]) if i[7]!= None else '')+ '|'+str(i[8] if i[8]!= None else '')+ '|'+str(i[9] if i[9]!= None else '')+ '|'+str(n1 if i[10]!= None else '')+ '|'+str(n2 if i[10]!= None else '')+ '|'+str(i[11] if i[11]!= None else '')+ '|'  )).encode('iso-8859-1','ignore') + "\n"

		vals = {
			'output_name': 'COSTOS.txt',
			'output_file': base64.encodestring(" " if rpta=="" else rpta),		
		}
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
	



	@api.multi
	def do_rebuild_venta(self):
		per_ini = self.fiscal_id.code + '00'
		per_fin = self.fiscal_id.code + '13'
		code_tp = self.type_document_ids.mapped('code')
		id_tp = self.type_document_ids.mapped('id')
		txt_code_tp = " where account_move.check_daot=false or account_move.check_daot is Null "
		txt_id_tp = ""
		if len(code_tp) > 0:
			if len(code_tp) == 1:
				code_tp = tuple( [str(i) for i in code_tp] )
				txt_code_tp = "and tipodocumento not in ('"+str(code_tp[0])+"')"
				
				id_tp = tuple( [str(i) for i in id_tp] )
				txt_id_tp = "and tipo_doc not in ("+str(id_tp[0])+")"
			else:
				code_tp = tuple( [str(i) for i in code_tp] )
				txt_code_tp = "and tipodocumento not in "+str(code_tp)
				
				id_tp = tuple( [str(i) for i in id_tp] )
				txt_id_tp = "and tipo_doc not in "+str(id_tp)

		self.env.cr.execute(""" 
		select row_number() OVER () AS id,itdpc.code,rcp.type_number,"""+ str(self.fiscal_id.code)+""" as periodo,
		CASE WHEN A.check_every THEN 4 ELSE
			CASE WHEN rp.is_resident THEN 3 ELSE
			 CASE WHEN rp.is_company THEN 1 ELSE 2 END
			END 
		END AS tipopersona,
		itdp.code, rp.type_number,A.monto,
		CASE WHEN rp.is_company THEN Null::varchar ELSE rp.last_name_f END as app,
		CASE WHEN rp.is_company THEN Null::varchar ELSE rp.last_name_m END as apm, 
		CASE WHEN rp.is_company THEN Null::varchar ELSE rp.first_name END as fn, 
		CASE WHEN rp.is_company=false THEN Null::varchar ELSE rp.name END as rz
		from (
			select sum(monto) as monto, razonsocial,every(tipo_doc = '12') as check_every from (
			select coalesce(valorexp,0) +coalesce(baseimp,0) +coalesce(inafecto,0) +coalesce(exonerado,0) +coalesce(isc,0) +coalesce(otros,0) as monto ,partner as razonsocial,tipodocumento as tipo_doc  from get_venta_1_1_1(false,"""+str(per_ini)+""","""+str(per_fin)+""") as T inner join account_move on account_move.id = T.am_id """+txt_code_tp+"""
			union all
			select total as monto, razonsocial, itd.code from daot_register inner join it_type_document itd on itd.id= daot_register.tipo_doc where type_operation='ingreso' """+txt_id_tp+"""
			) AS T GROUP by razonsocial
		) as A
		inner join res_partner rp on  rp.name = A.razonsocial
		left join it_type_document_partner itdp on itdp.id = rp.type_document_id
		cross join res_company rc
		inner join res_partner rcp on rcp.id = rc.partner_id
		left join it_type_document_partner itdpc on itdpc.id = rcp.type_document_id
		where monto >"""+str(self.amount)+"""
		""")
		tra = self.env.cr.fetchall()
		
		
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		rpta = ""
		for i in tra:
			n1=''
			n2=''
			if i[10] != None:
				t = i[10].split(' ',1)
				if len(t) == 1:
					n1= t[0]
				else:
					n1=t[0]
					n2=t[1]
			rpta += (unicode( str(int(i[0]) if i[0]!= None else '')+ '|'+str(int(i[1]) if i[1]!= None else '')+ '|'+str(i[2]  if i[2]!= None else '')+ '|'+str(int(i[3])  if i[3]!= None else '')+ '|'+str(int(i[4])  if i[4]!= None else '')+ '|'+str(int(i[5])  if i[5]!= None else '')+ '|'+str(i[6]  if i[6]!= None else '')+ '|'+str(int(i[7]) if i[7]!= None else '')+ '|'+str(i[8] if i[8]!= None else '')+ '|'+str(i[9] if i[9]!= None else '')+ '|'+str(n1 if i[10]!= None else '')+ '|'+str(n2 if i[10]!= None else '')+ '|'+str(i[11] if i[11]!= None else '')+ '|'  )).encode('iso-8859-1','ignore') + "\n"

		vals = {
			'output_name': 'INGRESOS.txt',
			'output_file': base64.encodestring(" " if rpta=="" else rpta),		
		}
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
	@api.multi
	def do_rebuild(self):
		if self.type == 'compra':
			return self.do_rebuild_compra()
		else:
			return self.do_rebuild_venta()