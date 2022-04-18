# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs


class account_journal(models.Model):
	_inherit = 'account.journal'
	register_sunat = fields.Selection((('1','Compras'),
									('2','Ventas'),
									('3','Honorarios'),
									('4','Retenciones'),
									('5','Percepciones'),
									('6','No Deducibles')
									),'Registro Sunat')



class account_purchase_register_nodeducible_wizard(osv.TransientModel):
	_name='account.purchase.register.nodeducible.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('txt','Txt')], 'Mostrar en', required=True)
	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)

	@api.onchange('fiscalyear_id')
	def onchange_fiscalyear(self):
		if self.fiscalyear_id:
			return {'domain':{'period_ini':[('fiscalyear_id','=',self.fiscalyear_id.id )], 'period_end':[('fiscalyear_id','=',self.fiscalyear_id.id )]}}
		else:
			return {'domain':{'period_ini':[], 'period_end':[]}}

	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini


	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		
		filtro = []
		direccion = self.env['main.parameter'].search([])[0].dir_create_file

			
		if self.type_show == 'txt':

			self.env.cr.execute("""
				copy (
					select
t3.code as periodo,
t2.code as libro,
t1.name as voucher,
t1.date as fecha,
t5.type_number,
t6.code as tdp,
t5.name as empresa,
t4.code as tc,
t1.dec_reg_nro_comprobante as nro_comprobante,
base1,base2,base3,cng,igv1,igv2,igv3,otros,isc,total,t8.name as motivo_rep, CASE WHEN t7.is_employee = true then he.name_related else rp.name end
          as
          beneficiario
           from (SELECT move_id,
 SUM(BASE1) AS BASE1,
 SUM(BASE2) AS BASE2, 
 SUM(BASE3) AS BASE3,
 SUM(CNG) AS CNG, 
 SUM(IGV1) AS IGV1,
 SUM(IGV2) AS IGV2,
 SUM(IGV3) AS IGV3,
 SUM(ISC) AS ISC,
 SUM(OTROS) AS OTROS,
 SUM(BASE1) + SUM(BASE2) + SUM(BASE3) + SUM(CNG) + SUM(ISC) + SUM(OTROS) + SUM(IGV1) + SUM(IGV2) + SUM(IGV3) AS TOTAL
FROM  (
select move_id,
case when account_tax_code.record_shop='1' then tax_amount else 0 end as BASE1,
case when account_tax_code.record_shop='2' then tax_amount else 0 end as BASE2,
case when account_tax_code.record_shop='3' then tax_amount else 0 end as BASE3,
case when account_tax_code.record_shop='4' then tax_amount else 0 end as CNG,
case when account_tax_code.record_shop='5' then tax_amount else 0 end as ISC,
case when account_tax_code.record_shop='6' then tax_amount else 0 end as OTROS,
case when account_tax_code.record_shop='7' then tax_amount else 0 end as IGV1,
case when account_tax_code.record_shop='8' then tax_amount else 0 end as IGV2,
case when account_tax_code.record_shop='9' then tax_amount else 0 end as IGV3
from account_move_line 
left join account_journal on account_journal.id=account_move_line.journal_id
left join account_tax_code on account_tax_code.id=account_move_line.tax_code_id
where account_journal.register_sunat='6' and
account_move_line.tax_code_id is not null
order by move_id) AS TT
GROUP BY move_id) as ee
left join account_move t1 on t1.id=ee.move_id
left join account_journal t2 on t2.id=t1.journal_id
left join account_period t3 on t3.id=t1.period_id
left join it_type_document t4 on t4.id=t1.dec_reg_type_document_id
left join res_partner t5 on t5.id=t1.partner_id
left join it_type_document_partner t6 on t6.id=t5.type_document_id
left join account_invoice t7 on t7.move_id=t1.id
left join motivo_reparables t8 on t8.id=t7.motivo_reparables_id


          LEFT JOIN hr_employee he on he.id = t7.b_employee_id 
          LEFT JOIN res_partner rp on rp.id = t7.b_partner_id

where periodo_num(t3.code) >=periodo_num('""" + period_ini.code + """') and periodo_num(t3.code) <=periodo_num('""" + period_end.code + """')
order by periodo,libro,voucher
	)	
TO '"""+ str( direccion + 'register_purchase_nodeducible.csv' )+ """'
with delimiter '|'  CSV HEADER
		""")
		

			exp = open( str( direccion + 'register_purchase_nodeducible.csv' ), 'r').read().replace("\\N","")


			vals = {
				'output_name': 'RegistroComprasNoDeducible.txt',
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



		self.env.cr.execute("""
			CREATE OR REPLACE view account_purchase_register_nodeducible as (
			select t1.ID as id,
t3.code as periodo,
t2.code as libro,
t1.name as voucher,
t1.date as fecha,
t5.type_number,
t6.code as tdp,
t5.name as empresa,
t4.code as tc,
t1.dec_reg_nro_comprobante as nro_comprobante,
base1,base2,base3,cng,igv1,igv2,igv3,otros,isc,total,t8.name as motivo_rep, CASE WHEN t7.is_employee = true then he.name_related else rp.name end
          as
          beneficiario
           from (SELECT move_id,
 SUM(BASE1) AS BASE1,
 SUM(BASE2) AS BASE2, 
 SUM(BASE3) AS BASE3,
 SUM(CNG) AS CNG, 
 SUM(IGV1) AS IGV1,
 SUM(IGV2) AS IGV2,
 SUM(IGV3) AS IGV3,
 SUM(ISC) AS ISC,
 SUM(OTROS) AS OTROS,
 SUM(BASE1) + SUM(BASE2) + SUM(BASE3) + SUM(CNG) + SUM(ISC) + SUM(OTROS) + SUM(IGV1) + SUM(IGV2) + SUM(IGV3) AS TOTAL
FROM  (
select move_id,
case when account_tax_code.record_shop='1' then tax_amount else 0 end as BASE1,
case when account_tax_code.record_shop='2' then tax_amount else 0 end as BASE2,
case when account_tax_code.record_shop='3' then tax_amount else 0 end as BASE3,
case when account_tax_code.record_shop='4' then tax_amount else 0 end as CNG,
case when account_tax_code.record_shop='5' then tax_amount else 0 end as ISC,
case when account_tax_code.record_shop='6' then tax_amount else 0 end as OTROS,
case when account_tax_code.record_shop='7' then tax_amount else 0 end as IGV1,
case when account_tax_code.record_shop='8' then tax_amount else 0 end as IGV2,
case when account_tax_code.record_shop='9' then tax_amount else 0 end as IGV3
from account_move_line 
left join account_journal on account_journal.id=account_move_line.journal_id
left join account_tax_code on account_tax_code.id=account_move_line.tax_code_id
where account_journal.register_sunat='6' and
account_move_line.tax_code_id is not null
order by move_id) AS TT
GROUP BY move_id) as ee
left join account_move t1 on t1.id=ee.move_id
left join account_journal t2 on t2.id=t1.journal_id
left join account_period t3 on t3.id=t1.period_id
left join it_type_document t4 on t4.id=t1.dec_reg_type_document_id
left join res_partner t5 on t5.id=t1.partner_id
left join it_type_document_partner t6 on t6.id=t5.type_document_id
left join account_invoice t7 on t7.move_id=t1.id
left join motivo_reparables t8 on t8.id=t7.motivo_reparables_id 


          LEFT JOIN hr_employee he on he.id = t7.b_employee_id 
          LEFT JOIN res_partner rp on rp.id = t7.b_partner_id

where periodo_num(t3.code) >= periodo_num('""" + period_ini.code + """') and periodo_num(t3.code) <=periodo_num('""" + period_end.code + """')
order by periodo,libro,voucher
		)""")


		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_purchase_register_nodeducible_it', 'action_account_purchase_register_nodeducible_it')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.purchase.register.nodeducible',
				'view_mode': 'tree',
				'view_type': 'form',
				'res_id': id,
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook(direccion + 'tempo_librocomprasnodeducible.xlsx')
			worksheet = workbook.add_worksheet("Registro Compras No Deducible")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#FCFFC5')


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)


			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,20,"REGISTRO DE COMPRA NO DEDUCIBLE",title)

			worksheet.write(1,0, "Registro Compras:", bold)

			worksheet.write(1,1, self.period_ini.name, normal)

			worksheet.write(1,2, self.period_end.name, normal)


	

			worksheet.write(4,0, "Periodo",boldbord)
			worksheet.write(4,1, "Libro",boldbord)
			worksheet.write(4,2, "Voucher",boldbord)
			worksheet.write(4,3, u"Fecha",boldbord)
			worksheet.write(4,4, u"T.C.",boldbord)
			worksheet.write(4,5, u"Nro Comprobante",boldbord)
			worksheet.write(4,6, "T.D.P.",boldbord)
			worksheet.write(4,7, u"RUC",boldbord)
			
			worksheet.write(4,8, "Empresa",boldbord)
			worksheet.write(4,9, "BIOGE",boldbord)
			worksheet.write(4,10, "BIOGENG",boldbord)
			worksheet.write(4,11, u"BIONG",boldbord)
			worksheet.write(4,12, u"CNG",boldbord)
			worksheet.write(4,13, u"ISC",boldbord)
			worksheet.write(4,14, "IGVA",boldbord)
			worksheet.write(4,15, "IGVB",boldbord)
			worksheet.write(4,16, u"IGVC",boldbord)
			worksheet.write(4,17, u"OTROS",boldbord)
			worksheet.write(4,18, u"TOTAL",boldbord)
			worksheet.write(4,19, u"Motivo",boldbord)
			worksheet.write(4,20, u"Beneficiario",boldbord)

			for line in self.env['account.purchase.register.nodeducible'].search([]):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.fecha if line.fecha else '',bord)
				worksheet.write(x,4,line.tc if line.tc else '',bord)
				worksheet.write(x,5,line.nro_comprobante if line.nro_comprobante  else '',bord)
				worksheet.write(x,6,line.tdp if line.tdp else '',bord)
				worksheet.write(x,7,line.type_number if line.type_number else '',bord)
				
				worksheet.write(x,8,line.empresa if line.empresa else '',bord)	
				worksheet.write(x,9,line.base1 ,numberdos)
				worksheet.write(x,10,line.base2 ,numberdos)
				worksheet.write(x,11,line.base3 ,numberdos)
				worksheet.write(x,12,line.cng ,numberdos)
				worksheet.write(x,13,line.isc ,numberdos)
				worksheet.write(x,14,line.igv1 ,numberdos)
				worksheet.write(x,15,line.igv2 ,numberdos)
				worksheet.write(x,16,line.igv3 ,numberdos)
				worksheet.write(x,17,line.otros ,numberdos)
				worksheet.write(x,18,line.total ,numberdos)
				worksheet.write(x,19,line.motivo_rep if line.motivo_rep else '',bord)
				worksheet.write(x,20,line.beneficiario if line.beneficiario else '',bord)


				x = x +1


			tam_col = [7,5,9,10,4,12,3,15,40,11,11,11,11,11,11,11,11,11,11,43,11,11,35,6,9,13,13,13,9,7,9,9]

			worksheet.set_row(0, 31)

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

			worksheet.set_column('U:U', tam_col[20])
			worksheet.set_column('V:V', tam_col[21])
			worksheet.set_column('W:W', tam_col[22])
			worksheet.set_column('X:X', tam_col[23])
			worksheet.set_column('Y:Y', tam_col[24])
			worksheet.set_column('Z:Z', tam_col[25])
			worksheet.set_column('AA:AA', tam_col[26])
			worksheet.set_column('AB:AB', tam_col[27])
			worksheet.set_column('AC:AC', tam_col[28])
			worksheet.set_column('AD:AD', tam_col[29])
			worksheet.set_column('AE:AE', tam_col[30])
			worksheet.set_column('AF:AF', tam_col[31])

			workbook.close()
			
			f = open( direccion + 'tempo_librocomprasnodeducible.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'RegistroComprasNoDeducible.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
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
	def csv_verif_integer(self,data):
		if data:
			return '"' + str(data) + '"'
		else:
			return '""'

	@api.multi
	def csv_verif(self,data):
		if data:
			return '"' + data.replace('"','\'') + '"'
		else:
			return '""'
	@api.multi
	def csv_convert(self,data,separador):
		tmp = self.csv_verif(data.periodo)
		tmp += separador+ self.csv_verif(data.libro)
		tmp += separador+ self.csv_verif(data.voucher)
		tmp += separador+ self.csv_verif(data.fechaemision)
		tmp += separador+ self.csv_verif(data.fechavencimiento)
		tmp += separador+ self.csv_verif(data.tipodocumento)
		tmp += separador+ self.csv_verif(data.serie)
		tmp += separador+ self.csv_verif(data.numero)
		tmp += separador+ self.csv_verif(data.anio)
		tmp += separador+ self.csv_verif(data.tdp)
		tmp += separador+ self.csv_verif(data.ruc)
		tmp += separador+ self.csv_verif(data.razonsocial)
		tmp += separador+ self.csv_verif_integer(data.bioge)
		tmp += separador+ self.csv_verif_integer(data.biogeng)
		tmp += separador+ self.csv_verif_integer(data.biong)
		tmp += separador+ self.csv_verif_integer(data.cng)
		tmp += separador+ self.csv_verif_integer(data.isc)
		tmp += separador+ self.csv_verif_integer(data.igva)
		tmp += separador+ self.csv_verif_integer(data.igvb)
		tmp += separador+ self.csv_verif_integer(data.igvc)
		tmp += separador+ self.csv_verif_integer(data.otros)
		tmp += separador+ self.csv_verif_integer(data.total)
		tmp += separador+ self.csv_verif(data.comprobante)
		tmp += separador+ self.csv_verif(data.moneda)
		tmp += separador+ self.csv_verif_integer(data.tc)
		tmp += separador+ self.csv_verif(data.fechad)
		tmp += separador+ self.csv_verif(data.numerod)
		tmp += separador+ self.csv_verif(data.fechadm)
		tmp += separador+ self.csv_verif(data.td)
		tmp += separador+ self.csv_verif(data.seried)
		tmp += separador+ self.csv_verif(data.numerodd)
		tmp += separador
		return unicode(tmp)
	@api.multi
	def cabezera_csv(self,separador):
		tmp = self.csv_verif("Periodo")
		tmp += separador+ self.csv_verif("Libro")
		tmp += separador+ self.csv_verif("Voucher")
		tmp += separador+ self.csv_verif("Fecha Emision")
		tmp += separador+ self.csv_verif("Fecha Vencimiento")
		tmp += separador+ self.csv_verif("Tipo de Documento")
		tmp += separador+ self.csv_verif("Serie")
		tmp += separador+ self.csv_verif("Numero")
		tmp += separador+ self.csv_verif("Año")
		tmp += separador+ self.csv_verif("Tipo Documento")
		tmp += separador+ self.csv_verif("Nro. Documento")
		tmp += separador+ self.csv_verif("Partner")
		tmp += separador+ self.csv_verif("Bioge")
		tmp += separador+ self.csv_verif("Biogeng")
		tmp += separador+ self.csv_verif("Biong")
		tmp += separador+ self.csv_verif("Cng")
		tmp += separador+ self.csv_verif("Isc")
		tmp += separador+ self.csv_verif("IgvA")
		tmp += separador+ self.csv_verif("IgvB")
		tmp += separador+ self.csv_verif("IgvC")
		tmp += separador+ self.csv_verif("Otros")
		tmp += separador+ self.csv_verif("Total")
		tmp += separador+ self.csv_verif("Comprobante Nro. Domicilio")
		tmp += separador+ self.csv_verif("Moneda")
		tmp += separador+ self.csv_verif("T.C.")
		tmp += separador+ self.csv_verif("Fecha D.")
		tmp += separador+ self.csv_verif("Numero D.")
		tmp += separador+ self.csv_verif("Fecha D.M.")
		tmp += separador+ self.csv_verif("T.D.")
		tmp += separador+ self.csv_verif("Serie D.")
		tmp += separador+ self.csv_verif("Numero D.")
		tmp += separador+ self.csv_verif("Motivo")
		tmp += separador
		return unicode(tmp)