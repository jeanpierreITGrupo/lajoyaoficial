# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _

class ple_mayor_wizard(osv.TransientModel):
	_name='ple.mayor.wizard'
	
	period = fields.Many2one('account.period','Periodo')
	check_wizard = fields.Boolean('Es cierre?')
	

	@api.multi
	def do_rebuild(self):
		self.env.cr.execute("""
			SELECT T.*,
CASE WHEN ap.id != ap2.id THEN (CASE WHEN am.ckeck_modify_ple THEN  '9' ELSE '8' END ) ELSE '1' END as campo34
from get_libro_mayor(false,0,219001) AS T
inner join account_period ap on ap.name = T.periodo
inner join account_move_line aml on aml.id = T.aml_id
inner join account_move am on am.id = aml.move_id
inner join account_period ap2 on ap2.id = am.period_modify_ple
where ap2.id = """ +str(self.period.id)+ """ """)

		tra = self.env.cr.fetchall()
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		m_code_sunat = None
		if self.env['main.parameter'].search([])[0].template_account_contable:
			m_code_sunat = self.env['main.parameter'].search([])[0].template_account_contable.code_sunat
		else:
			raise exceptions.Warning(_("No esta configurado la Plantilla para el Codigo Sunat")) 
		rpta = ""
		for i in tra:
			rpta += (unicode(self.period.code[3:7]+ self.period.code[:2]+ '00')).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(i[22]) )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( ('A' if self.period.code[:2]=='00' else 'C' if self.period.code[:2]=='13' else 'M')+ str(i[3])[-9:].replace('/','-')  )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(m_code_sunat) )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(i[4]).replace('.','') )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(i[12])[8:10] + '/'+ str(i[12])[5:7] + '/' + str(i[12])[0:4] )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(i[18]).replace('?','') )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( "%0.2f"%(i[6]) )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( "%0.2f"%(i[7]) )).encode('iso-8859-1','ignore')+ '|'
			rpta += (unicode( str(i[3]).replace('/','-') )).encode('iso-8859-1','ignore') + '|'+ '|'+ '|'
			rpta += (unicode( str(i[23]) )).encode('iso-8859-1','ignore')+ '|' + '\n'

		ruc = self.env['res.company'].search([])[0].partner_id.type_number
		mond = self.env['res.company'].search([])[0].currency_id.name

		if not ruc:
			raise osv.except_osv('Alerta!', 'No esta configurado el RUC en la compañia')
		
		#vals = {
		#	'output_name': 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+'0006010000'+ ('2' if self.check_wizard else '1')+('1' if len(tra) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt',
		#	'output_file': base64.encodestring("\r\n" if rpta=="" else rpta),		
		#}



		direccion_ple = self.env['main.parameter'].search([])[0].dir_ple_create_file

		if not direccion_ple:
			raise osv.except_osv('Alerta!', 'No esta configurado el directorio para los PLE Sunat en parametros.')
			
		file_ple = open( direccion_ple + 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+'0006010000'+ ('2' if self.check_wizard else '1')+('1' if len(tra) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt','w')
		file_ple.write(rpta)
		file_ple.close()

		rep = "Se genero exitosamente el archivo: "+ 'LE' + ruc + self.period.code[3:7]+ self.period.code[:2]+'0006010000'+ ('2' if self.check_wizard else '1')+('1' if len(tra) >0 else '0') + ('1' if mond == 'PEN' else '2') +'1.txt'
		obj_id = self.env['warning'].create({'title': 'Generar PLE Diario', 'message': rep, 'type': 'info'})

		res = {
			'name': 'Generar PLE Diario',
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
		}"""


