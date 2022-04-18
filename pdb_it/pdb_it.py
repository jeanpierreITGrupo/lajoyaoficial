# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
import decimal


class pdb_excel_it(osv.osv):
	_name = 'pdb.excel.it'

	period_id = fields.Many2one('account.period','Periodo',required=True)

	@api.multi
	def generar_pdb_excel(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		self.env.cr.execute("""
				copy (
				select campo1,campo2,campo3,campo4,campo5,campo6,campo7,campo8,campo9,campo10,campo11,campo12,campo13 from (
select distinct am.id as modid,		
case when rp.is_resident = true then '02' else '01' end as campo1,
itd.code as campo2,
--to_char(am.date,'dd/mm/yyyy') as campo3,
CASE WHEN itd.code in ('91','98') THEN 
	      CASE
		    WHEN "position"(am.nro_formulario_compra_externa ::text, '-'::text) = 0 THEN NULL::text
		    ELSE "substring"(am.nro_formulario_compra_externa ::text, 0, "position"(am.nro_formulario_compra_externa ::text, '-'::text))
	      END
      else
	CASE WHEN itd.code in ('50','52','53','54') THEN am.codigo_aduana else 
		CASE WHEN itd.code in ('10','12') THEN '' ELSE
			CASE
				WHEN "position"(am.dec_reg_nro_comprobante::text, '-'::text) = 0 THEN NULL::text
				ELSE "substring"(am.dec_reg_nro_comprobante::text, 0, "position"(am.dec_reg_nro_comprobante::text, '-'::text))
			END
		END
	END
END AS campo3,
CASE WHEN itd.code in ('91','98') THEN 
	      CASE
			WHEN "position"(am.nro_formulario_compra_externa ::text, '-'::text) = 0 THEN am.nro_formulario_compra_externa ::text
			ELSE "substring"(am.nro_formulario_compra_externa ::text, "position"(am.nro_formulario_compra_externa ::text, '-'::text) + 1)
	      END
      ELSE
		CASE WHEN itd.code in ('50','52','53','54') THEN '' ELSE
			CASE
				WHEN "position"(am.dec_reg_nro_comprobante::text, '-'::text) = 0 THEN am.dec_reg_nro_comprobante::text
				ELSE "substring"(am.dec_reg_nro_comprobante::text, "position"(am.dec_reg_nro_comprobante::text, '-'::text) + 1)
			END
		END
END AS campo4,
CASE WHEN rp.is_resident = true THEN '03' ELSE
   CASE WHEN rp.is_company = true THEN '02' ELSE '01' END
END as campo5,
CASE WHEN itdp.code = '0' THEN '-'
ELSE itdp.code END as campo6,
rp.type_number as campo7,



--CASE WHEN pagoX.debit <= 3500 and coalesce(pagoX.code,'098') not in ('009','011','013','014') then '009' else 
--coalesce(pagoX.code,'098') end as campo8,
coalesce(pagoX.code,'098')  as campo8,

case when coalesce(pagoX.code,'098') = '098' then '' else  coalesce(pagoX.codebancario,'') end as campo9,

case when coalesce(pagoX.code,'098') = '098' then '' else  coalesce(pagoX.nbancario,'')  end as campo10,

case when coalesce(pagoX.code,'098') = '098' then '' else  case when pagoX.code in ('009','098') then '' else coalesce( to_char(pagoX.date::date,'dd/mm/yyyy'::varchar) ,'') end end as campo11,

case when coalesce(pagoX.code,'098') = '098' then '' else  coalesce(pagoX.debit::varchar,0::varchar) end as campo12 ,
''::varchar as campo13,
pagoX.idpagox





FROM account_move am
JOIN account_journal aj ON am.journal_id = aj.id
LEFT JOIN res_currency rc on rc.id = am.com_det_currency
JOIN account_period ap ON am.period_id = ap.id
LEFT JOIN it_type_document itd ON am.dec_reg_type_document_id = itd.id
LEFT JOIN res_partner rp ON am.partner_id = rp.id
LEFT JOIN it_type_document_partner itdp ON rp.type_document_id = itdp.id
LEFT JOIN it_type_document itd_r on itd_r.id = am.dec_mod_type_document_id
left join get_compra_1_1_1(false,"""+self.period_id.fiscalyear_id.name+"""01,"""+self.period_id.fiscalyear_id.name+"""12) compra on compra.am_id = am.id
INNER JOIN (
	select am.id,
	max(CASE WHEN atc.record_pdb = '1' THEN 1 else 0 end) as tipo1,
	max(CASE WHEN atc.record_pdb = '2' THEN 1 else 0 end) as tipo2,
	max(CASE WHEN atc.record_pdb = '3' THEN 1 else 0 end) as tipo3,
	max(CASE WHEN atc.record_pdb = '4' THEN 1 else 0 end) as tipo4
	from account_move am
	inner join account_move_line aml on aml.move_id = am.id
	inner join account_tax_code atc on atc.id = aml.tax_code_id
	group by am.id ) as COL1 on COL1.id = am.id
INNER JOIN (
	select am.id,atc.record_pdb,
	sum(CASE WHEN atc.record_shop in ('1','2','3','4') THEN CASE WHEN rc.name = 'USD' then abs(aml.amount_currency) else abs(aml.tax_amount) end else 0 end) as valor1,
	sum(CASE WHEN atc.record_shop in ('5') THEN CASE WHEN rc.name = 'USD' then abs(aml.amount_currency) else abs(aml.tax_amount) end else 0 end) as valor2,
	sum(CASE WHEN atc.record_shop in ('7','8','9') THEN CASE WHEN rc.name = 'USD' then abs(aml.amount_currency) else abs(aml.tax_amount) end else 0 end) as valor3,
	sum(CASE WHEN atc.record_shop in ('6') THEN CASE WHEN rc.name = 'USD' then abs(aml.amount_currency) else abs(aml.tax_amount) end else 0 end) as valor4
	from account_move am
	inner join account_move_line aml on aml.move_id = am.id
	inner join account_tax_code atc on atc.id = aml.tax_code_id
	left join res_currency rc on rc.id = am.com_det_currency
	group by am.id,atc.record_pdb) as VAL1 on VAL1.id = am.id

LEFT JOIN (  
	

select itd.code || '-' || aml.nro_comprobante || '-' || coalesce(rp.type_number,'') as idu, aml.debit,
CASE WHEN left(dtp.ref_int,2) = 'RE' then impdel.code else
CASE WHEN left(dtp.ref_int,2) = 'RG' then '009' else
--CASE WHEN aml.debit <= 3500 and mp.account_detracciones != aml.account_id then '009' else  X.code end end end as code , 
 X.code end end as code , 
am.date, 
CASE WHEN left(dtp.ref_int,2) = 'RG' or (left(dtp.ref_int,2) = 'RE' and impdel.code in ('009','011','013','014','098') ) then '' else
CASE WHEN (left(dtp.ref_int,2) = 'RE' and impdel.code not in ('009','011','013','014','098') ) then aadel.cashbank_code  else
CASE WHEN (aml.debit <= 3500 and mp.account_detracciones != aml.account_id) or X.code in ('009','011','013','014','098') then '' else aa.cashbank_code end
end end as codebancario,

CASE WHEN left(dtp.ref_int,2) = 'RG' or (left(dtp.ref_int,2) = 'RE' and impdel.code in ('009','011','013','014') ) then '' else
CASE WHEN (left(dtp.ref_int,2) = 'RE' and impdel.code not in ('009','011','013','014') ) then CASE WHEN impdel.code = '99' then aadel.cashbank_financy else dtp.memory end else
	CASE WHEN (aml.debit <= 3500 and mp.account_detracciones != aml.account_id) or X.code in ('009','011','013','014') then '' else 
		CASE WHEN X.code = '99' then aa.cashbank_financy else X.nrooperation end
	end
end end as nbancario ,
aml.id as idpagox 
	from account_move am
	inner join account_move_line aml on aml.move_id = am.id
	inner join account_journal aj on aj.id = am.journal_id and aj.type in ('cash','bank')
	inner join account_account aa on aa.id = aj.default_debit_account_id
	inner join it_type_document itd on itd.id = aml.type_document_id
	inner join account_period ap on ap.id = am.period_id
	left join deliveries_to_pay dtp on dtp.id = aml.rendicion_id
	left join it_means_payment impdel on impdel.id = dtp.means_payment_id
	left join account_journal ajdel on ajdel.id = dtp.deliver_journal_id
	left join account_account aadel on aadel.id = ajdel.default_debit_account_id
	left join res_partner rp on rp.id = aml.partner_id	
	left join (
			  select am.id,imp.code,aml.nro_comprobante as nrooperation from account_move am
			inner join account_move_line aml on aml.move_id = am.id
			inner join account_journal aj on aj.id = am.journal_id and aj.type in ('cash','bank')
			inner join account_period ap on ap.id = am.period_id
			inner join it_means_payment imp on imp.id = aml.means_payment_id
			left join res_partner rp on rp.id = aml.partner_id
			where periodo_num(ap.code) >= periodo_num('00/""" +self.period_id.fiscalyear_id.name+ """') and periodo_num(ap.code) <= periodo_num('""" +self.period_id.code+ """')
			and am.state != 'draft' 
	   ) X on X.id = am.id
	  cross join main_parameter mp
	where periodo_num(ap.code) >= periodo_num('00/""" +self.period_id.fiscalyear_id.name+ """') and periodo_num(ap.code) <= periodo_num('""" +self.period_id.code+ """')
	and am.state != 'draft' and aml.debit != 0


) as pagoX on pagoX.idu = itd.code || '-' || am.dec_reg_nro_comprobante || '-' || rp.type_number
WHERE aj.register_sunat::text = '1'::text and periodo_num(ap.name) >= periodo_num('""" +self.period_id.code+ """') and periodo_num(ap.name) <= periodo_num('""" +self.period_id.code+ """')
and ( 
	( itd.code in ('01','03','04','05','06','07','08','10','11','12','13','14','15','16','17','18','21','22','23','24','25','26','27','28','29','30','32','34','35','36','37','55','87','88') and rp.is_resident!= true)
	or
	( itd.code in ('50','52','53','54','91','97','98') and rp.is_resident= true)
)
and am.state != 'draft'
ORDER BY campo3 ) as total
	)	
TO '"""+ str( direccion + 'pdb_compra.csv' )+ """'
with delimiter '|'  
		""")
	

		exp = open( str( direccion + 'pdb_compra.csv' ), 'r').read().replace("\\N","").replace('\n','\r\n')

		name = 'F'
		ruc = self.env['res.company'].search([])[0].partner_id.type_number
		name += ruc
		name += self.period_id.code.split('/')[1]
		name += self.period_id.code.split('/')[0]

		vals = {
			'output_name': name + '.txt',
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






class pdb_compra_it(osv.osv):
	_name = 'pdb.compra.it'

	period_id = fields.Many2one('account.period','Periodo',required=True)

	@api.multi
	def generar_pdb_compra(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		self.env.cr.execute("""
				copy (
					select 		
case when rp.is_resident = true then '02' else '01' end as campo1,
itd.code as campo2,
to_char(am.date,'dd/mm/yyyy') as campo3,
CASE WHEN itd.code in ('91','98') THEN 
	      CASE
		    WHEN "position"(am.nro_formulario_compra_externa ::text, '-'::text) = 0 THEN NULL::text
		    ELSE "substring"(am.nro_formulario_compra_externa ::text, 0, "position"(am.nro_formulario_compra_externa ::text, '-'::text))
	      END
      else
	CASE WHEN itd.code in ('50','52','53','54') THEN am.codigo_aduana else 
		CASE WHEN itd.code in ('10','12') THEN '' ELSE
			CASE
				WHEN "position"(am.dec_reg_nro_comprobante::text, '-'::text) = 0 THEN NULL::text
				ELSE "substring"(am.dec_reg_nro_comprobante::text, 0, "position"(am.dec_reg_nro_comprobante::text, '-'::text))
			END
		END
	END
END AS campo4,
CASE WHEN itd.code in ('91','98') THEN 
	      CASE
			WHEN "position"(am.nro_formulario_compra_externa ::text, '-'::text) = 0 THEN am.nro_formulario_compra_externa ::text
			ELSE "substring"(am.nro_formulario_compra_externa ::text, "position"(am.nro_formulario_compra_externa ::text, '-'::text) + 1)
	      END
      ELSE
		CASE WHEN itd.code in ('50','52','53','54') THEN '' ELSE
			CASE
				WHEN "position"(am.dec_reg_nro_comprobante::text, '-'::text) = 0 THEN am.dec_reg_nro_comprobante::text
				ELSE "substring"(am.dec_reg_nro_comprobante::text, "position"(am.dec_reg_nro_comprobante::text, '-'::text) + 1)
			END
		END
END AS campo5,
CASE WHEN rp.is_resident = true THEN '03' ELSE
   CASE WHEN rp.is_company = true THEN '02' ELSE '01' END
END as campo6,
CASE WHEN itdp.code = '0' THEN '-'
ELSE itdp.code END as campo7,
rp.type_number as campo8,
CASE WHEN rp.is_resident = true THEN substring(rp.name from 1 for 40) ELSE
   CASE WHEN rp.is_company = true THEN substring(rp.name from 1 for 40) ELSE '' END
END as campo9,
coalesce(rp.last_name_f,'') as campo10,
coalesce(rp.last_name_m,'') as campo11,
coalesce(rp.first_name,'') as campo12,
'' as campo13,
CASE WHEN rc.name is null THEN '1' ELSE rc.cod_pdb END as campo14,
CASE WHEN COL1.tipo1 + COL1.tipo2 + COL1.tipo3 + COL1.tipo4 >1 then '5' ELSE
	CASE WHEN COL1.tipo1 >0 then '1'ELSE
		CASE WHEN COL1.tipo2 >0 then '2'ELSE
			CASE WHEN COL1.tipo3 >0 then '3'ELSE 				
				CASE WHEN COL1.tipo4 >0 then '4'ELSE ''
				END
			END
		END
	END
END as campo15,
CASE WHEN COL1.tipo1 + COL1.tipo2 + COL1.tipo3 + COL1.tipo4 =1 then '1' ELSE
	VAL1.record_pdb END as campo16,

CASE WHEN VAL1.valor1 = 0 then 0.00 else coalesce(VAL1.valor1,0.00) end as campo17,
CASE WHEN VAL1.valor2 = 0 then '' else coalesce(VAL1.valor2::varchar,'') end as campo18,
CASE WHEN VAL1.valor3 = 0 then 0.00 else coalesce(VAL1.valor3,0.00) end as campo19,
CASE WHEN VAL1.valor4 = 0 then 0.00 else coalesce(VAL1.valor4,0.00) end as campo20,

CASE WHEN am.com_det_code_operation is not null and am.com_det_code_operation!= '' then '1' else '0' end as campo21,
coalesce(am.com_det_code_operation,'') as campo22,
coalesce( reverse(substring( reverse(am.com_det_number) from 1 for 8)),'') as campo23,
CASE WHEN am.sujeto_a_retencion = true THEN '1' else '0' end as campo24,
CASE WHEN itd.code in ('07','08','87','88','97','98','91') then itd_r.code else '' end as campo25,
CASE WHEN itd.code in ('07','08','87','88','97','98','91') then 
			CASE
				WHEN "position"(am.dec_mod_nro_comprobante::text, '-'::text) = 0 THEN NULL::text
				ELSE "substring"(am.dec_mod_nro_comprobante::text, 0, "position"(am.dec_mod_nro_comprobante::text, '-'::text))
			END
else '' end as campo26,
CASE WHEN itd.code in ('07','08','87','88','97','98','91') then 
		CASE
			WHEN "position"(am.dec_mod_nro_comprobante ::text, '-'::text) = 0 THEN am.dec_mod_nro_comprobante ::text
			ELSE "substring"(am.dec_mod_nro_comprobante ::text, "position"(am.dec_mod_nro_comprobante ::text, '-'::text) + 1)
	      END
else '' end as campo27,
CASE WHEN itd.code in ('07','08','87','88','97','98','91') then coalesce(to_char(am.dec_mod_fecha,'dd/mm/yyyy'),'') else '' end as campo28,
CASE WHEN itd.code in ('07','08','87','88','97','98','91') then CASE WHEN am.dec_mod_base_imponible = 0 then 0.00::varchar else coalesce(am.dec_mod_base_imponible,0.00)::varchar end  else '' end as campo29,
CASE WHEN itd.code in ('07','08','87','88','97','98','91') then CASE WHEN am.dec_mod_igv = 0 then 0.00::varchar else coalesce(am.dec_mod_igv,0.00)::varchar end  else '' end as campo30,
''::varchar as campo31
FROM account_move am
JOIN account_journal aj ON am.journal_id = aj.id
LEFT JOIN res_currency rc on rc.id = am.com_det_currency
JOIN account_period ap ON am.period_id = ap.id
LEFT JOIN it_type_document itd ON am.dec_reg_type_document_id = itd.id
LEFT JOIN res_partner rp ON am.partner_id = rp.id
LEFT JOIN it_type_document_partner itdp ON rp.type_document_id = itdp.id
LEFT JOIN it_type_document itd_r on itd_r.id = am.dec_mod_type_document_id
INNER JOIN (
	select am.id,
	max(CASE WHEN atc.record_pdb = '1' THEN 1 else 0 end) as tipo1,
	max(CASE WHEN atc.record_pdb = '2' THEN 1 else 0 end) as tipo2,
	max(CASE WHEN atc.record_pdb = '3' THEN 1 else 0 end) as tipo3,
	max(CASE WHEN atc.record_pdb = '4' THEN 1 else 0 end) as tipo4
	from account_move am
	inner join account_move_line aml on aml.move_id = am.id
	inner join account_tax_code atc on atc.id = aml.tax_code_id
	group by am.id ) as COL1 on COL1.id = am.id
INNER JOIN (
	select am.id,atc.record_pdb,
	sum(CASE WHEN atc.record_shop in ('1','2','3','4') THEN CASE WHEN rc.name = 'USD' then CASE WHEN aml.currency_rate_it != 0 THEN round(aml.tax_amount / coalesce(aml.currency_rate_it,1),2) ELSE 0 END else aml.tax_amount end else 0 end) as valor1,
	sum(CASE WHEN atc.record_shop in ('5') THEN CASE WHEN rc.name = 'USD' then aml.amount_currency else aml.tax_amount end else 0 end) as valor2,
	sum(CASE WHEN atc.record_shop in ('7','8','9') THEN CASE WHEN rc.name = 'USD' then CASE WHEN aml.currency_rate_it != 0 THEN round(aml.tax_amount / coalesce(aml.currency_rate_it,1),2) ELSE 0 END else aml.tax_amount end else 0 end) as valor3,
	sum(CASE WHEN atc.record_shop in ('6') THEN CASE WHEN rc.name = 'USD' then aml.amount_currency else aml.tax_amount end else 0 end) as valor4
	from account_move am
	inner join account_move_line aml on aml.move_id = am.id
	inner join account_tax_code atc on atc.id = aml.tax_code_id
	left join res_currency rc on rc.id = am.com_det_currency
	group by am.id,atc.record_pdb) as VAL1 on VAL1.id = am.id
WHERE aj.register_sunat::text = '1'::text and periodo_num(ap.name) >= periodo_num('""" +self.period_id.code+ """') and periodo_num(ap.name) <= periodo_num('""" +self.period_id.code+ """')
and ( 
	( itd.code in ('01','03','04','05','06','07','08','10','11','12','13','14','15','16','17','18','21','22','23','24','25','26','27','28','29','30','32','34','35','36','37','55') and rp.is_resident!= true)
	or
	( itd.code in ('50','52','53','54','91','97','98') and rp.is_resident= true)
)
and am.state != 'draft'
ORDER BY am.dec_reg_nro_comprobante
	)	
TO '"""+ str( direccion + 'pdb_compra.csv' )+ """'
with delimiter '|'  
		""")
	

		exp = open( str( direccion + 'pdb_compra.csv' ), 'r').read().replace("\\N","").replace('\n','\r\n')

		name = 'C'
		ruc = self.env['res.company'].search([])[0].partner_id.type_number
		name += ruc
		name += self.period_id.code.split('/')[1]
		name += self.period_id.code.split('/')[0]
		vals = {
			'output_name': name + '.txt',
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




class pdb_venta_it(osv.osv):
	_name = 'pdb.venta.it'

	period_id = fields.Many2one('account.period','Periodo',required=True)

	@api.multi
	def generar_pdb_venta(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		self.env.cr.execute("""
				copy (
					select 		
case when rp.is_resident = true then '02' else '01' end as campo1,
itd.code as campo2,
to_char(am.date,'dd/mm/yyyy') as campo3,
			CASE
				WHEN "position"(am.dec_reg_nro_comprobante::text, '-'::text) = 0 THEN NULL::text
				ELSE "substring"(am.dec_reg_nro_comprobante::text, 0, "position"(am.dec_reg_nro_comprobante::text, '-'::text))
			END AS campo4,
			CASE
				WHEN "position"(am.dec_reg_nro_comprobante::text, '-'::text) = 0 THEN am.dec_reg_nro_comprobante::text
				ELSE "substring"(am.dec_reg_nro_comprobante::text, "position"(am.dec_reg_nro_comprobante::text, '-'::text) + 1)
			END AS campo5,
CASE WHEN rp.is_resident = true THEN '03' ELSE
   CASE WHEN rp.is_company = true THEN '02' ELSE '01' END
END as campo6,
CASE WHEN itdp.code = '0' THEN '-'
ELSE itdp.code END as campo7,
rp.type_number as campo8,
CASE WHEN rp.is_company = true then rp.name else '' end as campo9,
coalesce(trim(rp.last_name_f),'') as campo10,
coalesce(trim(rp.last_name_m),'') as campo11,
coalesce(trim(rp.first_name),'') as campo12,
'' as campo13,
CASE WHEN rc.name is null THEN '1' ELSE rc.cod_pdb END as campo14,
CASE WHEN COL1.tipo1 + COL1.tipo2 >1 then '3' ELSE
	CASE WHEN COL1.tipo1 >0 then '1'ELSE
		CASE WHEN COL1.tipo2 >0 then '2'ELSE ''
		END
	END
END as campo15,
CASE WHEN COL1.tipo1 + COL1.tipo2 = 1 then '1' ELSE
	VAL1.record_pdb_venta END as campo16,
CASE WHEN VAL1.valor1 = 0 then 0.00 else coalesce(VAL1.valor1,0.00) end as campo17,
CASE WHEN VAL1.valor2 = 0 then 0.00 else coalesce(VAL1.valor2,0.00) end as campo18,
CASE WHEN VAL1.valor3 = 0 then 0.00 else coalesce(VAL1.valor3,0.00) end as campo19,
CASE WHEN VAL1.valor4 = 0 then 0.00 else coalesce(VAL1.valor4,0.00) end as campo20,

CASE WHEN am.dec_percep_numero_serie is not null and am.dec_percep_numero_serie!= '' then '1' else '0' end as campo21,
coalesce(am.dec_percep_tipo_tasa_percepcion,'') as campo22,

CASE
				WHEN "position"(am.dec_percep_numero_serie::text, '-'::text) = 0 THEN NULL::text
				ELSE "substring"(am.dec_percep_numero_serie::text, 0, "position"(am.dec_percep_numero_serie::text, '-'::text))
			END AS campo23,

			CASE
				WHEN "position"(am.dec_percep_numero_serie::text, '-'::text) = 0 THEN am.dec_percep_numero_serie::text
				ELSE "substring"(am.dec_percep_numero_serie::text, "position"(am.dec_percep_numero_serie::text, '-'::text) + 1)
			END AS campo24,

CASE WHEN itd.code in ('07','08') then itd_r.code else '' end as campo25,
CASE WHEN itd.code in ('07','08') then 
			CASE
				WHEN "position"(am.dec_mod_nro_comprobante::text, '-'::text) = 0 THEN NULL::text
				ELSE "substring"(am.dec_mod_nro_comprobante::text, 0, "position"(am.dec_mod_nro_comprobante::text, '-'::text))
			END
else '' end as campo26,
CASE WHEN itd.code in ('07','08') then 
		CASE
			WHEN "position"(am.dec_mod_nro_comprobante ::text, '-'::text) = 0 THEN am.dec_mod_nro_comprobante ::text
			ELSE "substring"(am.dec_mod_nro_comprobante ::text, "position"(am.dec_mod_nro_comprobante ::text, '-'::text) + 1)
	      END
else ''::varchar end as campo27,
CASE WHEN itd.code in ('07','08') then coalesce(to_char(am.dec_mod_fecha,'dd/mm/yyyy'),'')::varchar else ''::varchar end as campo28,
CASE WHEN itd.code in ('07','08') then CASE WHEN am.dec_mod_base_imponible = 0 then 0.00::varchar else coalesce(am.dec_mod_base_imponible,0.00)::varchar end else ''::varchar end as campo29,
CASE WHEN itd.code in ('07','08') then CASE WHEN am.dec_mod_igv = 0 then 0.00::varchar else coalesce(am.dec_mod_igv,0.00)::varchar end else ''::varchar end as campo30,
''::varchar as campo31
FROM account_move am
JOIN account_journal aj ON am.journal_id = aj.id
LEFT JOIN res_currency rc on rc.id = am.com_det_currency
JOIN account_period ap ON am.period_id = ap.id
LEFT JOIN it_type_document itd ON am.dec_reg_type_document_id = itd.id
LEFT JOIN res_partner rp ON am.partner_id = rp.id
LEFT JOIN it_type_document_partner itdp ON rp.type_document_id = itdp.id
LEFT JOIN it_type_document itd_r on itd_r.id = am.dec_mod_type_document_id
INNER JOIN (
	select am.id,
	max(CASE WHEN atc.record_pdb_venta = '1' THEN 1 else 0 end) as tipo1,
	max(CASE WHEN atc.record_pdb_venta = '2' THEN 1 else 0 end) as tipo2
	from account_move am
	inner join account_move_line aml on aml.move_id = am.id
	inner join account_tax_code atc on atc.id = aml.tax_code_id
	group by am.id ) as COL1 on COL1.id = am.id
INNER JOIN (
	select am.id,atc.record_pdb_venta,
	sum(CASE WHEN atc.record_sale in ('1','2','3','4') THEN CASE WHEN rc.name = 'USD' then abs(aml.amount_currency) else abs(aml.tax_amount) end else 0 end) as valor1,
	sum(CASE WHEN atc.record_sale in ('5') THEN CASE WHEN rc.name = 'USD' then abs(aml.amount_currency) else abs(aml.tax_amount) end else 0 end) as valor2,
	sum(CASE WHEN atc.record_sale in ('7') THEN CASE WHEN rc.name = 'USD' then abs(aml.amount_currency) else abs(aml.tax_amount) end else 0 end) as valor3,
	sum(CASE WHEN atc.record_sale in ('6') THEN CASE WHEN rc.name = 'USD' then abs(aml.amount_currency) else abs(aml.tax_amount) end else 0 end) as valor4
	from account_move am
	inner join account_move_line aml on aml.move_id = am.id
	inner join account_tax_code atc on atc.id = aml.tax_code_id
	left join res_currency rc on rc.id = am.com_det_currency
	group by am.id,atc.record_pdb_venta) as VAL1 on VAL1.id = am.id
CROSS JOIN main_parameter 
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
WHERE am.partner_id != anulado.id and aj.register_sunat::text = '2'::text and periodo_num(ap.name) >= periodo_num('""" +self.period_id.code+ """') and periodo_num(ap.name) <= periodo_num('""" +self.period_id.code+ """')
and ( 
	( itd.code in ('01','03','05','06','07','08','12','15','16','23','25','34','35','36','37') and rp.is_resident!= true)
	or
	( itd.code in ('01','03','07','08','12','34','35','36','37') and rp.is_resident= true)
)
and am.state != 'draft'
ORDER BY am.dec_reg_nro_comprobante
	)	
TO '"""+ str( direccion + 'pdb_venta.csv' )+ """'
with delimiter '|'   
		""")
	

		exp = open( str( direccion + 'pdb_venta.csv' ), 'r').read().replace("\\N","").replace('\n','\r\n')

		name = 'V'
		ruc = self.env['res.company'].search([])[0].partner_id.type_number
		name += ruc
		name += self.period_id.code.split('/')[1]
		name += self.period_id.code.split('/')[0]
		vals = {
			'output_name': name + '.txt',
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






class pdb_caja_it(osv.osv):
	_name = 'pdb.caja.it'

	period_id = fields.Many2one('account.period','Periodo',required=True)

	@api.multi
	def generar_pdb_caja(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		self.env.cr.execute("""

select 

aj.code as libro,
am.name as voucher,
rp.name as Partner,
case when rp.is_resident = true then '02' else '01' end as TipodeCompra,
itd.code as TipodeComprobante,
CASE WHEN itd.code in ('91','98') THEN 
	      CASE
		    WHEN "position"(am.nro_formulario_compra_externa ::text, '-'::text) = 0 THEN NULL::text
		    ELSE "substring"(am.nro_formulario_compra_externa ::text, 0, "position"(am.nro_formulario_compra_externa ::text, '-'::text))
	      END
      else
	CASE WHEN itd.code in ('50','52','53','54') THEN am.codigo_aduana else 
		CASE WHEN itd.code in ('10','12') THEN '' ELSE
			CASE
				WHEN "position"(aml.nro_comprobante::text, '-'::text) = 0 THEN NULL::text
				ELSE "substring"(aml.nro_comprobante::text, 0, "position"(aml.nro_comprobante::text, '-'::text))
			END
		END
	END
END AS seriecomprobante,
CASE WHEN itd.code in ('91','98') THEN 
	      CASE
			WHEN "position"(am.nro_formulario_compra_externa ::text, '-'::text) = 0 THEN am.nro_formulario_compra_externa ::text
			ELSE "substring"(am.nro_formulario_compra_externa ::text, "position"(am.nro_formulario_compra_externa ::text, '-'::text) + 1)
	      END
      ELSE
		CASE WHEN itd.code in ('50','52','53','54') THEN '' ELSE
			CASE
				WHEN "position"(aml.nro_comprobante::text, '-'::text) = 0 THEN aml.nro_comprobante::text
				ELSE "substring"(aml.nro_comprobante::text, "position"(aml.nro_comprobante::text, '-'::text) + 1)
			END
		END
END AS nrocomprobante,
CASE WHEN rp.is_resident = true THEN '03' ELSE
   CASE WHEN rp.is_company = true THEN '02' ELSE '01' END
END as tipopersona,
CASE WHEN itdp.code = '0' THEN '-'
ELSE itdp.code END as tipodocumento,
rp.type_number as nrodocumento,
imp.code as mediopago,
aa_pago.cashbank_code as codigooentidad,
case when aa_pago.cashbank_code = '99' then aa_pago.cashbank_financy else am_pago.ref end nrooperacion,
to_char(am_pago.date ,'dd/mm/yyyy') as fechaoperacion,
aml.debit as montooperacion,
aa.code as cuentap
--''::varchar as vacio

 from account_move am_pago
inner join account_move_line aml_pago on aml_pago.move_id = am_pago.id
inner join account_account aa_pago on aa_pago.id = aml_pago.account_id
inner join account_journal aj_pago on aj_pago.id= am_pago.journal_id
LEFT join it_means_payment imp on imp.id = aml_pago.means_payment_id
LEFT join res_partner rp_pago on rp_pago.id = aml_pago.partner_id
inner join (
		select am.id as am_id,aml.id as aml_id from account_move am
		inner join account_move_line aml on aml.move_id = am.id
		inner join account_journal aj on aj.id= am.journal_id
		inner join account_account aa on aa.id = aml.account_id
		where aa.type = 'payable' and aj.type in ('cash','bank')
) origen on am_pago.id = origen.am_id
inner join account_move am on am.id = origen.am_id
inner join account_move_line aml on aml.id = origen.aml_id
join account_account aa on aa.id = aml.account_id
JOIN account_period ap ON am.period_id = ap.id
JOIN account_journal aj ON am.journal_id = aj.id
left join res_partner rp on rp.id = aml.partner_id
LEFT JOIN res_currency rc on rc.id = am.com_det_currency
LEFT JOIN it_type_document itd ON aml.type_document_id= itd.id
LEFT JOIN it_type_document_partner itdp ON rp.type_document_id = itdp.id
LEFT JOIN it_type_document itd_r on itd_r.id = am.dec_mod_type_document_id
where aj_pago.type in ('cash','bank') and aml_pago.account_id = aj_pago.default_credit_account_id and aml_pago.credit >0
and periodo_num(ap.name) >= periodo_num('""" +self.period_id.code+ """') and periodo_num(ap.name) <= periodo_num('""" +self.period_id.code+ """')
and am.state != 'draft'

		""")

		elementos = self.env.cr.fetchall()

		if True:

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'pdb_caja.xlsx')
			worksheet = workbook.add_worksheet("PDB Caja")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 4				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, "PDB Caja:", bold)
			worksheet.write(0,1, self.period_id.name, normal)


			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			

			worksheet.write(3,0, "Libro",boldbord)
			worksheet.write(3,1, "Voucher",boldbord)
			worksheet.write(3,2, "Partner",boldbord)
			worksheet.write(3,3, "Tipo de Compra",boldbord)
			worksheet.write(3,4, "Tipo de Comprobante",boldbord)
			worksheet.write(3,5, u"Número de Serie",boldbord)
			worksheet.write(3,6, u"Número de Comprobante",boldbord)
			worksheet.write(3,7, u"Tipo de Persona",boldbord)
			worksheet.write(3,8, "Tipo de Documento",boldbord)
			worksheet.write(3,9, u"Número de Documento",boldbord)
			worksheet.write(3,10, "Medio de Pago",boldbord)
			worksheet.write(3,11, u"Código del banco o entidad",boldbord)
			worksheet.write(3,12, u"Número de operaicon o nombre banco",boldbord)
			worksheet.write(3,13, u"Fecha de Operación",boldbord)
			worksheet.write(3,14, u"Monto de Operación",boldbord)
			worksheet.write(3,15, u"Cuenta contable",boldbord)

			for line in elementos:
				worksheet.write(x,0,line[0] if line[0] else '' ,bord )
				worksheet.write(x,1,line[1] if line[1] else '' ,bord )
				worksheet.write(x,2,line[2] if line[2] else '' ,bord )
				worksheet.write(x,3,line[3] if line[3] else '' ,bord )
				worksheet.write(x,4,line[4] if line[4] else '' ,bord )
				worksheet.write(x,5,line[5] if line[5] else '' ,bord )
				worksheet.write(x,6,line[6] if line[6] else '' ,bord )
				worksheet.write(x,7,line[7] if line[7] else '' ,bord )
				worksheet.write(x,8,line[8] if line[8] else '' ,bord )
				worksheet.write(x,9,line[9] if line[9] else '' ,bord )
				worksheet.write(x,10,line[10] if line[10] else '' ,bord )
				worksheet.write(x,11,line[11] if line[11] else '' ,bord )
				worksheet.write(x,12,line[12] if line[12] else '' ,bord )
				worksheet.write(x,13,line[13] if line[13] else '' ,bord )
				worksheet.write(x,14,line[14] if line[14] else 0,numberdos)
				worksheet.write(x,15,line[15] if line[15] else '' ,bord )

				x = x +1

			tam_col = [11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]


			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:B', tam_col[1])
			worksheet.set_column('C:C', tam_col[2])
			worksheet.set_column('D:D', tam_col[3])
			worksheet.set_column('E:E', tam_col[4])
			worksheet.set_column('F:F', tam_col[5])
			worksheet.set_column('G:G', tam_col[6])
			worksheet.set_column('H:H', tam_col[7])
			worksheet.set_column('I:I', tam_col[8])
			worksheet.set_column('J:J', tam_col[9])
			worksheet.set_column('K:K', tam_col[10])
			worksheet.set_column('L:L', tam_col[11])
			worksheet.set_column('M:M', tam_col[12])
			worksheet.set_column('N:N', tam_col[13])
			worksheet.set_column('O:O', tam_col[14])
			worksheet.set_column('P:P', tam_col[15])
			worksheet.set_column('Q:Q', tam_col[16])
			worksheet.set_column('R:R', tam_col[17])
			worksheet.set_column('S:S', tam_col[18])
			worksheet.set_column('T:T', tam_col[19])

			workbook.close()
			
			f = open(direccion + 'pdb_caja.xlsx', 'rb')
			
			
			name = 'F'
			ruc = self.env['res.company'].search([])[0].partner_id.type_number
			name += ruc
			name += self.period_id.code.split('/')[1]
			name += self.period_id.code.split('/')[0]
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': name + '.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			sfs_id = self.env['export.file.save'].create(vals)
			result = {}
			view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( [view_id] )

			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}



class factura_pagos(osv.osv):
	_name = 'factura.pagos'

	period_id = fields.Many2one('account.period','Periodo',required=True)

	@api.multi
	def generar_factura_pagos(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		self.env.cr.execute("""
				copy (


select 	rp.name as Partner,itd.code as TipoDocumento,am.name as AsientoContable,aml_m.credit as Monto ,imp.code as MedioPago,
aa_pago.cashbank_code as CodigoBanco,
case when aa_pago.cashbank_code = '99' then aa_pago.cashbank_financy else am_pago.ref end as EntidadFinanciera,
to_char(am_pago.date ,'dd/mm/yyyy') as Fecha,
aml_pago.debit as Monto

FROM account_move am
JOIN account_journal aj ON am.journal_id = aj.id
LEFT JOIN res_currency rc on rc.id = am.com_det_currency
JOIN account_period ap ON am.period_id = ap.id
LEFT JOIN it_type_document itd ON am.dec_reg_type_document_id = itd.id
LEFT JOIN res_partner rp ON am.partner_id = rp.id
LEFT JOIN it_type_document_partner itdp ON rp.type_document_id = itdp.id
LEFT JOIN it_type_document itd_r on itd_r.id = am.dec_mod_type_document_id
inner join account_move_line aml_m on aml_m.move_id = am.id and aml_m.credit >0

left JOIN (
	select concat(aml.account_id,aml.partner_id,aml.type_document_id,aml.nro_comprobante) as key, am.id as am_id, aml.id as aml_id from account_move_line aml
	inner join account_move am on am.id = aml.move_id
) as PAGOS on PAGOS.key = concat(aml_m.account_id,aml_m.partner_id,aml_m.type_document_id,aml_m.nro_comprobante) and PAGOS.am_id != am.id
left join account_move_line aml_pago on aml_pago.id = PAGOS.aml_id
left join account_move am_pago on am_pago.id = aml_pago.move_id
left join it_means_payment imp on imp.id = aml_pago.means_payment_id
left join account_journal aj_pago on aj_pago.id = am_pago.journal_id
left join account_account aa_pago on aa_pago.id = aj_pago.default_debit_account_id
--inner join account_tax_code atc_m on atc_m.id = aml_m.tax_code_id and atc_m.record_shop is not null and atc_m.record_shop != ''
WHERE aj.register_sunat::text = '1'::text and periodo_num(ap.name) >= periodo_num('""" +self.period_id.code+ """') and periodo_num(ap.name) <= periodo_num('""" +self.period_id.code+ """')
and am.state != 'draft'
ORDER BY am.dec_reg_nro_comprobante







	)	
TO '"""+ str( direccion + 'factura_pagos.csv' )+ """'
with delimiter '|'  CSV HEADER
		""")
	

		exp = open( str( direccion + 'factura_pagos.csv' ), 'r').read().replace("\\N","").replace('\n','\r\n')

		vals = {
			'output_name':  'FacturasPagos.txt',
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





class pagos_factura(osv.osv):
	_name = 'pagos.factura'

	period_id = fields.Many2one('account.period','Periodo',required=True)

	@api.multi
	def generar_factura_pagos(self):
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		self.env.cr.execute("""
				copy (



select 	imp.code as MedioPago,
aa_pago.cashbank_code as CodigoBanco,
case when aa_pago.cashbank_code = '99' then aa_pago.cashbank_financy else am_pago.ref end as EntidadFinanciera,
to_char(am_pago.date ,'dd/mm/yyyy') as Fecha,
aml_pago.debit as Monto,
rp.name as Partner,itd.code as TipoDocumento,am.name as AsientoContable,aml_m.credit as Monto 

from account_move_line aml_pago
inner join account_move am_pago on am_pago.id = aml_pago.move_id
inner join account_journal aj_pago on aj_pago.id = am_pago.journal_id
inner join account_account aa_pago on aa_pago.id = aj_pago.default_debit_account_id
inner join account_period ap_pago on ap_pago.id = am_pago.period_id
left join it_means_payment imp on imp.id = aml_pago.means_payment_id
left JOIN (
	select concat(aml.account_id,aml.partner_id,aml.type_document_id,aml.nro_comprobante) as key, am.id as am_id, aml.id as aml_id from account_move_line aml
	inner join account_move am on am.id = aml.move_id
	inner join account_journal aj on aj.id = am.journal_id
	WHERE aj.register_sunat::text = '1'::text
) as FAC on FAC.key = concat(aml_pago.account_id,aml_pago.partner_id,aml_pago.type_document_id,aml_pago.nro_comprobante) and FAC.am_id != am_pago.id
left join account_move_line aml_m on FAC.aml_id = aml_m.id and aml_m.credit >0
left join account_move am on am.id = aml_m.move_id
left join account_journal aj ON am.journal_id = aj.id
left JOIN res_currency rc on rc.id = am.com_det_currency
left join account_period ap ON am.period_id = ap.id
LEFT JOIN it_type_document itd ON am.dec_reg_type_document_id = itd.id
LEFT JOIN res_partner rp ON am.partner_id = rp.id
LEFT JOIN it_type_document_partner itdp ON rp.type_document_id = itdp.id
LEFT JOIN it_type_document itd_r on itd_r.id = am.dec_mod_type_document_id
where aj_pago.type in ('bank','cash') and aml_pago.debit>0 and
periodo_num(ap_pago.name) >= periodo_num('""" +self.period_id.code+ """') and periodo_num(ap_pago.name) <= periodo_num('""" +self.period_id.code+ """')
and am_pago.state != 'draft'








	)	
TO '"""+ str( direccion + 'factura_pagos.csv' )+ """'
with delimiter '|'  CSV HEADER
		""")
	

		exp = open( str( direccion + 'factura_pagos.csv' ), 'r').read().replace("\\N","").replace('\n','\r\n')

		vals = {
			'output_name':  'PagosFactura.txt',
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





