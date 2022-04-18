# -*- encoding: utf-8 -*-
from openerp.osv import osv

from openerp import models, fields, api


class account_move(models.Model):
	_name='account.move'
	_inherit='account.move'
	automatic_destiny = fields.Boolean('Destino Automatico')


class account_move_line_rep_wizard(osv.TransientModel):
	_name='account.move.line.rep.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	type_product = fields.Selection((('t1','Almacenable'),
									('t2','Consumible'),
									('t3','Servicio')									
									),'Tipo Producto')

	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini

	@api.multi
	def do_rebuild(self):
		fechaini_obj = self.period_ini
		fechafin_obj = self.period_end
		
		move_obj=self.env['account.move.line.rep']
		filtro = []
		filtro.append( ('start','>=',fechaini_obj.date_start) )
		filtro.append( ('stop','<=',fechafin_obj.date_stop) )
		
		diccionario = {
			't1': 'Almacenable',
			't2': 'Consumible',
			't3': 'Servicio'
		}
		
		filtro.append( ('tipoproducto','=','Almacenable') )
		lstidsmove = move_obj.search( filtro )
		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		


		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		result = mod_obj.get_object_reference('repaccount_move_line_it', 'account_move_line_rep_action')
		
		id = result and result[1] or False
		return {
			'domain' : filtro,
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line.rep',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}




class account_move_line_rep_asiento_wizard(osv.TransientModel):
	_name='account.move.line.rep.asiento.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	#journal_id = fields.Many2one('account.journal','Libro',required=True, domain="[('type', '=', 'general')]")
	fecha = fields.Date('Fecha Asiento',required=True)
	

	@api.multi
	def do_Clase9(self):

		fechaD = self.fecha
		fecha_obj = self.period_ini
		diario_parameter = self.env['main.parameter'].search([])[0]


		if not diario_parameter.diario_destino.id:
			raise osv.except_osv('Alerta','No tiene configurado el Diario para el Asiento Unico.')

		move_obj=self.env['account.account.analytic.rep.contable.unico']
		
		mlra_obj = move_obj.search([('period','=',fecha_obj.id)])
		if (len(mlra_obj) == 0):
			return -1
			
		verif = self.env['account.account.analytic.rep'].search([('periodo','=',self.period_ini.name),'|',('destinodebe','=',False),('destinohaber','=',False)])

		if len(verif)>0:
			return -1


		periodo = fecha_obj

		asiento_delete = self.env['account.move'].search([('automatic_destiny','=',True),('period_id','=',periodo.id) ])

		if asiento_delete or len(asiento_delete)>0:

			for move in asiento_delete:
				move.button_cancel()
				for lineas in move.line_id:
					lineas.unlink()
				move.unlink()

		#caddel = "delete from account_move where journal_id = "+str(lst_journals)+" and period_id = "+str(fecha_obj.id) + " and ref='" +'Existencias para '+periodo.name + "'"
		#print caddel
		#cr.execute(caddel)
		lineas = []
		for mlra in mlra_obj:
			debit = round(mlra.debe,2)
			credit = round(mlra.haber,2)
			vals = (0,0,{
				'analytic_account_id': False, 
				'tax_code_id': False, 
				'analytic_lines': [], 
				'tax_amount': 0.0, 
				'name': "%s"%('DEST-'+periodo.name), 
				'ref': 'DEST-'+periodo.name, 
				'debit': debit,
				'credit': credit, 
				'product_id': False, 
				'date_maturity': False, 
				'date': fechaD,
				'product_uom_id': False, 
				'quantity': 0, 
				'partner_id': False, 
				'account_id': int(mlra.cuenta),
				'analytic_line_id': False,
				'nro_comprobante': 'DEST-'+periodo.name,
				'glosa': 'DEST-',
			})
			lineas.append(vals)
			
		move_id = self.env['account.move'].create({
			'company_id': periodo.company_id.id,
			'journal_id': diario_parameter.diario_destino.id,
			'period_id': periodo.id,
			'date': fechaD,
			'automatic_destiny':True,
			'ref': 'DEST-'+periodo.name, 
			'numopelibro':False,
			'before_numlibro':False,
			'before_numdiario':False,
			'line_id':lineas})
		return True



	@api.multi
	def do_GastoVinculado(self):
		return True

		fechaD = self.fecha
		fecha_obj = self.period_ini
		lst_journals = self.journal_id

		if (len(lst_journals) == 0) :
			raise osv.except_osv('Alerta','No tiene configurado el Diario para el Asiento Unico.')
		move_obj=self.env['account.expense.asiento.contable.unico']
		
		mlra_obj = move_obj.search([('period','=',fecha_obj.id)])
		if (len(mlra_obj) == 0):
			return -1
		
		periodo = fecha_obj
		#caddel = "delete from account_move where journal_id = "+str(lst_journals)+" and period_id = "+str(fecha_obj.id) + " and ref='" +'Existencias para '+periodo.name + "'"
		#print caddel
		#cr.execute(caddel)
		lineas = []
		for mlra in mlra_obj:
			debit = round(mlra.debe,2)
			credit = round(mlra.haber,2)
			vals = (0,0,{
				'analytic_account_id': False, 
				'tax_code_id': False, 
				'analytic_lines': [], 
				'tax_amount': 0.0, 
				'name': "%s"%('GASV-'+periodo.name), 
				'ref': 'GASV-'+periodo.name, 
				'debit': debit,
				'credit': credit, 
				'product_id': False, 
				'date_maturity': False, 
				'date': fechaD,
				'product_uom_id': False, 
				'quantity': 0, 
				'partner_id': False, 
				'account_id': int(mlra.cuenta),
				'analytic_line_id': False,
				'nro_comprobante': 'GASV-'+periodo.name,
				'glosa': 'GASV-'+periodo.name,
			})
			lineas.append(vals)
			
		move_id = self.env['account.move'].create({
			'company_id': periodo.company_id.id,
			'journal_id': lst_journals.id,
			'period_id': periodo.id,
			'date': fechaD,
			'ref': 'GASV-'+periodo.name, 
			'numopelibro':False,
			'before_numlibro':False,
			'before_numdiario':False,
			'line_id':lineas})		
		return True


	@api.multi
	def do_Existencia(self):

		fechaD = self.fecha
		fecha_obj = self.period_ini
		lst_journals = self.journal_id

		if (len(lst_journals) == 0) :
			raise osv.except_osv('Alerta','No tiene configurado el Diario para el Asiento Unico.')
		move_obj=self.env['account.move.line.asiento.contable.unico']
		
		mlra_obj = move_obj.search([('period','=',fecha_obj.id)])
		if (len(mlra_obj) == 0):
			return -1
		
		periodo = fecha_obj
		#caddel = "delete from account_move where journal_id = "+str(lst_journals)+" and period_id = "+str(fecha_obj.id) + " and ref='" +'Existencias para '+periodo.name + "'"
		#print caddel
		#cr.execute(caddel)
		lineas = []
		for mlra in mlra_obj:
			debit = round(mlra.debe,2)
			credit = round(mlra.haber,2)
			vals = (0,0,{
				'analytic_account_id': False, 
				'tax_code_id': False, 
				'analytic_lines': [], 
				'tax_amount': 0.0, 
				'name': "%s"%('EXIST-'+periodo.name), 
				'ref': 'EXIST-'+periodo.name, 
				'debit': debit,
				'credit': credit, 
				'product_id': False, 
				'date_maturity': False, 
				'date': fechaD,
				'product_uom_id': False, 
				'quantity': 0, 
				'partner_id': False, 
				'account_id': int(mlra.cuenta),
				'analytic_line_id': False,
				'nro_comprobante': 'EXIST-'+periodo.name,
				'glosa': 'EXIST-'+periodo.name,
			})
			lineas.append(vals)
			
		move_id = self.env['account.move'].create({
			'company_id': periodo.company_id.id,
			'journal_id': lst_journals.id,
			'period_id': periodo.id,
			'date': fechaD,
			'ref': 'EXIST-'+periodo.name, 
			'numopelibro':False,
			'before_numlibro':False,
			'before_numdiario':False,
			'line_id':lineas})			
		return True



	@api.multi
	def do_rebuild(self):
		t_c9 = self.do_Clase9()
		#t_exis = self.do_Existencia()
		#t_gvinc = self.do_GastoVinculado()
		rep = ""
		if t_c9 == -1:
			rep += "\nDestino: No contiene datos o no esta configurado sus cuentas de amarre.\n"
		else:
			rep += "\nDestino: Se genero exitosamente.\n"
			
		#if t_exis == -1:
		#	rep += "\nExistencias: No contiene datos.\n"
		#else:
		#	rep += "\nExistencias: Se genero exitosamente.\n"
			
		#if t_gvinc == -1:
		#	rep += "\nGastos Vinculados: No contiene datos.\n"
		#else:
		#	rep += "\nGastos Vinculados: Se genero exitosamente.\n"

		obj_id = self.env['warning'].create({'title': 'Generar Asientos Unicos', 'message': rep, 'type': 'info'})

		res = {
			'name': 'Generar Asientos Unicos',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'warning',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': obj_id.id
		}
		print res
		return res
