# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs

class account_move_line_book_destino_wizard(osv.TransientModel):
	_name='account.move.line.book.destino.wizard'
	
	period_id = fields.Many2one('account.period','Periodo',required=True)
	

	@api.multi
	def do_rebuild(self):
		period_ini = self.period_id
		period_end = self.period_id
		
		filtro = []
		
				
		self.env.cr.execute("""

			select

				periodo,
				libro,
				voucher,
				cuenta,
				debe,
				haber,
				divisa,
				tipodecambio,
				importedivisa,
				codigo,
				partner,
				tipodocumento,
				numero,
				fechaemision,
				fechavencimiento,
				glosa,
				ctaanalitica,
				refconcil,
				state
 
			from 
			(
				SELECT 
				periodo,
				libro,
				voucher,
				cuenta,
				debe,
				haber,
				divisa,
				tipodecambio,
				importedivisa,
				codigo,
				partner,
				tipodocumento,
				numero,
				fechaemision,
				fechavencimiento,
				glosa,
				ctaanalitica,
				refconcil,
				state

				FROM get_libro_diario(false,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
				where libro != '99'

				union all


select 
				ap.code,
				aj.code,
				am.name,
				T.cuenta,
				T.debe,
				T.haber,
				'' as divisa,
				0 as tipodecambio,
				0 as importedivisa,
				itdp.code as codigo,
				rp.name as partner,
				itd.code as tipodocumento,
				aml.nro_comprobante as numero,
				am.date as fechaemision,
				aml.date_maturity as  fechavencimiento,
				aml.name as glosa,
				aaa.code as ctaanalitica,
				'' as refconcil,
				am.state as state

from(
select cuenta, period, 
CASE WHEN debe-haber>0 THEN debe-haber else 0 END as debe,
CASE WHEN -debe+haber>0 THEN -debe+haber else 0 END as haber, lineaid from 
(
select 
account_move_line.id as lineaid,
aa3.id as cuenta,
account_period.id as period,
case when account_move_line.debit - account_move_line.credit > 0 then account_move_line.debit - account_move_line.credit
else 0 end as debe,
case when account_move_line.debit - account_move_line.credit > 0 then 0
else -account_move_line.debit + account_move_line.credit end as haber
from account_move
inner join account_period on account_move.period_id = account_period.id
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
where account_move.state = 'posted'
and aa2.id is not null and aa3.id is not null and account_analytic_account.id is null and account_move_line.analytics_id is null
and aa1.type != 'view' 


union all


select 
aml.id as lineaid,
aa3.id as cuenta,
ap.id as period,

case when aal.amount > 0 then 0
else -1*aal.amount end as debe,

case when aal.amount > 0 then aal.amount
else 0 end as haber
from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
inner join account_period ap on ap.id = am.period_id
where aa1.check_moorage = True  and am.state != 'draft'


union all


select 
aml.id as lineaid,
aa2.id as cuenta,
ap.id as period,

case when aal.amount > 0 then aal.amount
else 0 end as debe,
case when aal.amount > 0 then 0
else -1*aal.amount end as haber
from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
inner join account_period ap on ap.id = am.period_id
where aa1.check_moorage = True and am.state != 'draft'


union all
select
account_move_line.id as lineaid, 
aa2.id as cuenta,
account_period.id as period,
case when account_move_line.debit - account_move_line.credit > 0 then 0
else -account_move_line.debit + account_move_line.credit end as debe,
case when account_move_line.debit - account_move_line.credit > 0 then account_move_line.debit - account_move_line.credit
else 0 end as haber

from account_move
inner join account_period on account_move.period_id = account_period.id
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
where account_move.state = 'posted' 
and aa2.id is not null and aa3.id is not null and account_analytic_account.id is null and account_move_line.analytics_id is null
and aa1.type != 'view'

order by period,haber,debe
) AS M

order by period,haber,debe
) AS T 
inner join account_move_line aml on aml.id = T.lineaid
inner join account_move am on am.id = aml.move_id
inner join account_journal aj on aj.id = am.journal_id
inner join account_period ap on ap.id = am.period_id
left join it_type_document itd on itd.id = am.dec_reg_type_document_id
left join res_partner rp on rp.id = am.partner_id
left join it_type_document_partner itdp on itdp.id = rp.type_document_id
left join account_analytic_account aaa on aaa.id = aml.analytic_account_id



where period =  """ + str(self.period_id.id) + """ ) as TTX
order by libro,partner, voucher

		""")

		elementos = self.env.cr.dictfetchall()



		if True:

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_librodiario.xlsx')
			worksheet = workbook.add_worksheet("Libro Diario")
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
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, "Libro Diario con Destino:", bold)
			worksheet.write(0,1, self.period_id.name, normal)
			worksheet.write(1,0, "Fecha:",bold)
			

			worksheet.write(3,0, "Periodo",boldbord)
			worksheet.write(3,1, "Libro",boldbord)
			worksheet.write(3,2, "Voucher",boldbord)
			worksheet.write(3,3, "Cuenta",boldbord)
			worksheet.write(3,4, "Debe",boldbord)
			worksheet.write(3,5, "Haber",boldbord)
			worksheet.write(3,6, "Divisa",boldbord)
			worksheet.write(3,7, "Tipo Cambio",boldbord)
			worksheet.write(3,8, "Importe Divisa",boldbord)
			worksheet.write(3,9, u"Código",boldbord)
			worksheet.write(3,10, "Partner",boldbord)
			worksheet.write(3,11, "Tipo Documento",boldbord)
			worksheet.write(3,12, u"Número",boldbord)
			worksheet.write(3,13, u"Fecha Emisión",boldbord)
			worksheet.write(3,14, "Fecha Vencimiento",boldbord)

			worksheet.write(3,15, "Glosa",boldbord)
			worksheet.write(3,16, "Cta. Analitica",boldbord)
			worksheet.write(3,17, "Ref. Concil.",boldbord)
			worksheet.write(3,18, "Estado",boldbord)
			
			for line in elementos:
				worksheet.write(x,0,line['periodo'] if line['periodo'] else '' ,bord )
				worksheet.write(x,1,line['libro'] if line['libro'] else '',bord )
				worksheet.write(x,2,line['voucher'] if line['voucher'] else '',bord)
				worksheet.write(x,3,line['cuenta'] if line['cuenta'] else '',bord)
				worksheet.write(x,4,line['debe'] ,numberdos)
				worksheet.write(x,5,line['haber'] ,numberdos)
				worksheet.write(x,6,line['divisa'] if  line['divisa'] else '',bord)
				worksheet.write(x,7,line['tipodecambio'] ,numbertres)
				worksheet.write(x,8,line['importedivisa'] ,numberdos)
				worksheet.write(x,9,line['codigo'] if line['codigo'] else '',bord)
				worksheet.write(x,10,line['partner'] if line['partner'] else '',bord)
				worksheet.write(x,11,line['tipodocumento'] if line['tipodocumento'] else '',bord)
				worksheet.write(x,12,line['numero'] if line['numero'] else '',bord)
				worksheet.write(x,13,line['fechaemision'] if line['fechaemision'] else '',bord)
				worksheet.write(x,14,line['fechavencimiento'] if line['fechavencimiento'] else '',bord)
				worksheet.write(x,15,line['glosa'] if line['glosa'] else '',bord)
				worksheet.write(x,16,line['ctaanalitica'] if line['ctaanalitica'] else '',bord)
				worksheet.write(x,17,line['refconcil'] if line['refconcil'] else '',bord)
				worksheet.write(x,18,line['state'] if line['state'] else '',bord)

				x = x +1


			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10]

			worksheet.set_row(3, 60)
			
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

			workbook.close()
			
			f = open( direccion + 'tempo_librodiario.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'LibroDiario.xlsx',
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
