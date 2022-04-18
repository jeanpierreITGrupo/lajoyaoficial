# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from openerp.osv import osv
import base64
from zipfile import ZipFile

class resumen_fe(models.Model):
	_name = 'resumen.fe'

	fecha = fields.Date('Fecha',required=True)
	motivo = fields.Selection([('1','Conexion a Internet'),('2','Falla Fluido Electrico'),('3','Desastres Naturales'),('4','Robo'),('5','Falla en el sistema de emisión electrónico'),('6','Ventas por emisores itinerantes'),('7','Otros')],'Motivo',required=True)
	nro_correlativo = fields.Char('Correlativo',size=2,required=True)
	enviado = fields.Boolean('Enviado a Sunat')

	@api.onchange('nro_correlativo')
	def onchange_nro_correlativo(self):
		if self.nro_correlativo and len(self.nro_correlativo)== 1:
			self.nro_correlativo = '0'+ self.nro_correlativo

	@api.multi
	def do_rebuild(self):

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if True:
			self.env.cr.execute("""
			COPY (select 
			'""" +self.motivo+ """' as campo1,
			'""" +self.fecha.split('-')[2] + '/' + self.fecha.split('-')[1] + '/' + self.fecha.split('-')[0] + """' as campo2,
			compra.tipodocumento as campo3,
CASE WHEN			compra.serie is not Null THEN repeat('0',4-char_length(compra.serie)) || compra.serie ELSE '' END as campo4,
			CASE WHEN compra.numero is not Null THEN compra.numero ELSE '' END as campo5,
			''::varchar as campo6,



CASE WHEN (anulid.name = compra.partner and anulid.type_number = compra.numdoc) or (anulado.name = compra.partner and anulado.type_number = compra.numdoc) or (ventaboleta.name = compra.partner and ventaboleta.type_number = compra.numdoc) THEN '0' ELSE
CASE WHEN compra.tipodoc is not Null THEN compra.tipodoc::varchar ELSE '0' END end as campo7,

CASE WHEN (anulid.name = compra.partner and anulid.type_number = compra.numdoc) or (anulado.name = compra.partner and anulado.type_number = compra.numdoc) or (ventaboleta.name = compra.partner and ventaboleta.type_number = compra.numdoc) THEN '0' ELSE
CASE WHEN compra.numdoc is not Null THEN compra.numdoc ELSE '0' END END as campo8,

CASE WHEN (anulid.name = compra.partner and anulid.type_number = compra.numdoc) or (anulado.name = compra.partner and anulado.type_number = compra.numdoc) or (ventaboleta.name = compra.partner and ventaboleta.type_number = compra.numdoc) THEN 
   CASE WHEN (anulado.name = compra.partner and anulado.type_number = compra.numdoc) THEN 'Anulado' else 'Clientes Varios' END
 ELSE
CASE WHEN compra.partner is not Null THEN CASE WHEN position('(' in compra.partner) = 0 THEN compra.partner ELSE trim(substring(compra.partner,0 ,position('(' in compra.partner) )) END ELSE '' END END as campo9,

CASE WHEN compra.baseimp is not Null THEN ABS(compra.baseimp)::varchar ELSE '0.00' END as campo10,
CASE WHEN compra.exonerado is not Null THEN ABS(compra.exonerado )::varchar ELSE '0.00' END as campo11,
CASE WHEN compra.inafecto is not Null THEN ABS(compra.inafecto)::varchar ELSE '0.00' END as campo12,
CASE WHEN compra.isc is not Null THEN ABS(compra.isc)::varchar ELSE '0.00' END as campo13,
CASE WHEN compra.igv is not Null THEN ABS(compra.igv)::varchar ELSE '0.00' END as campo14,
CASE WHEN compra.otros is not Null THEN ABS(compra.otros)::varchar ELSE '0.00' END as campo15,
CASE WHEN compra.total is not Null THEN ABS(compra.total)::varchar ELSE '0.00' END as campo16,
CASE WHEN compra.tipodocmod is not Null THEN compra.tipodocmod ELSE '' END as campo17,
CASE WHEN compra.seriemod is not Null THEN repeat('0',4-char_length(compra.seriemod)) || compra.seriemod ELSE '' END as campo18,
CASE WHEN compra.numeromod is not Null THEN compra.numeromod ELSE '' END as campo19,
''::varchar as campo20

from get_venta_1_1_1(false,0,209501) compra
inner join account_period ap on ap.name = compra.periodo
inner join account_move am on am.id = compra.am_id
left join account_period ap2 on ap2.id = am.periodo_ajuste_modificacion_ple_venta
cross join main_parameter 
left join res_partner anulado on anulado.id = main_parameter.partner_null_id
left join res_partner anulid on anulid.id = 47
left join res_partner ventaboleta on ventaboleta.id = main_parameter.partner_venta_boleta
inner join account_journal aj on aj.id = am.journal_id
where am.date = '"""+ str(self.fecha) + """' 
and anulado.name != compra.partner and anulado.type_number != compra.numdoc
order by compra.tipodocumento, compra.serie, compra.numero) 
TO '"""+ str( direccion + 'sale.csv' )+ """'
with delimiter '|'
		""")

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
			
		exp = "".join(open( str( direccion + 'sale.csv' ), 'r').readlines() ) 
		

		direccion_ple = self.env['main.parameter'].search([])[0].dir_ple_create_file


		if not direccion_ple:
			raise osv.except_osv('Alerta!', 'No esta configurado el directorio para los PLE Sunat en parametros.')
			

		#file_ple = open(direccion_ple + 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+name_camb+('1' if len(exp) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt','w')
		#file_ple.write(exp)
		#file_ple.close()


		with ZipFile( direccion + 'ojo.zip','w') as myzip:
			myzip.writestr(ruc + '-RF-' + self.fecha.split('-')[2] + self.fecha.split('-')[1] + self.fecha.split('-')[0] + '-' + self.nro_correlativo  +'.txt',exp)
			myzip.close()

		expZip = "".join(open(str(direccion + 'ojo.zip'),'rb').readlines() )
		vals = {
			'output_name': ruc + '-RF-' + self.fecha.split('-')[2] + self.fecha.split('-')[1] + self.fecha.split('-')[0] + '-' + self.nro_correlativo  +'.zip',
			'output_file': base64.encodestring(  expZip ),		
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
