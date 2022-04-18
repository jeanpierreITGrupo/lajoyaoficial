# -*- coding: utf-8 -*-
import time
from lxml import etree
import pprint
from openerp import models, fields, api
from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw
import openerp
import base64


class it_flujo_caja(models.Model):
	_name = 'it.flujo.caja'

	name = fields.Char(required=True, string="Código")
	concepto = fields.Char(required=True, string="Concepto")

	_order = 'name'


	def name_get(self, cr, uid, ids, context=None):
		res = []
			
		for record in self.browse(cr, uid, ids, context=context):
			if 'show_concepto' in context:
				name = record.concepto
				res.append((record.id, name))
			else:
				name = record.name
				res.append((record.id, name))
		return res


	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, [('concepto','=',name)]+ args, limit=limit, context=context)
			if not ids:
				# Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
				# on a database with thousands of matching products, due to the huge merge+unique needed for the
				# OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
				# Performing a quick memory merge of ids in Python will give much better performance
				ids = set()
				ids.update(self.search(cr, user, args + [('name',operator,name)], limit=limit, context=context))
				if not limit or len(ids) < limit:
					# we may underrun the limit because of dupes in the results, that's fine
					ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					# vivek
					# Purpose  : To filter the product by using part_number
					ids.update(self.search(cr, user, args + [('concepto',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					#End
				ids = list(ids)
			if not ids:
				ptrn = re.compile('(\[(.*?)\])')
				res = ptrn.search(name)
				if res:
					ids = self.search(cr, user, [('name','=', res.group(2))] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context=context)
		return result



class account_move_line(models.Model):
	_inherit = 'account.move.line'
	flujo_caja_id = fields.Many2one('it.flujo.caja',string ="F. Caja",index = True,ondelete='restrict')
	



class account_voucher(models.Model):
	_inherit = 'account.voucher'
	flujo_caja_id = fields.Many2one('it.flujo.caja',string ="F. Caja",index = True,ondelete='restrict')

	rendicion_bool = fields.Boolean('Rendicion',related="journal_id.is_fixer")

	def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
		t = super(account_voucher,self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency, current_currency, context)
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		if voucher.flujo_caja_id  and voucher.journal_id.default_debit_account_id.id == t['account_id']:
			t['flujo_caja_id'] = voucher.flujo_caja_id.id
		return t

	def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
		t = super(account_voucher,self).writeoff_move_line_get(cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context)
		if t == {}:
			return {}

		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		if voucher.flujo_caja_id  and voucher.journal_id.default_debit_account_id.id == t['account_id']:
			t['flujo_caja_id'] = voucher.flujo_caja_id.id
		return t



	def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
		'''
		Create one account move line, on the given account move, per voucher line where amount is not 0.0.
		It returns Tuple with tot_line what is total of difference between debit and credit and
		a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

		:param voucher_id: Voucher id what we are working with
		:param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
		:param move_id: Account move wher those lines will be joined.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
		:rtype: tuple(float, list of int)
		'''
		if context is None:
			context = {}
		move_line_obj = self.pool.get('account.move.line')
		currency_obj = self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		tot_line = line_total
		rec_lst_ids = []

		date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
		ctx = context.copy()
		ctx.update({'date': date})
		voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
		voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
		ctx.update({
			'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
			'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
		prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
		for line in voucher.line_ids:
			#create one move line per voucher line where amount is not 0.0
			# AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
			if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
				continue
			# convert the amount set on the voucher line into the currency of the voucher's company
			# this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
			amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
			# if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
			# currency rate difference
			if line.amount == line.amount_unreconciled:
				if not line.move_line_id:
					raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
				sign = line.type =='dr' and -1 or 1
				currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
			else:
				currency_rate_difference = 0.0
			move_line = {
				'journal_id': voucher.journal_id.id,
				'period_id': voucher.period_id.id,
				'name': line.name or '/',
				'account_id': line.account_id.id,
				'move_id': move_id,
				'partner_id': voucher.partner_id.id,
				'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
				'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
				'quantity': 1,
				'credit': 0.0,
				'debit': 0.0,
				'date': voucher.date
			}
			if amount < 0:
				amount = -amount
				if line.type == 'dr':
					line.type = 'cr'
				else:
					line.type = 'dr'

			if (line.type=='dr'):
				tot_line += amount
				move_line['debit'] = amount
			else:
				tot_line -= amount
				move_line['credit'] = amount

			if voucher.tax_id and voucher.type in ('sale', 'purchase'):
				move_line.update({
					'account_tax_id': voucher.tax_id.id,
				})

			# compute the amount in foreign currency
			foreign_currency_diff = 0.0
			amount_currency = False
			if line.move_line_id:
				# We want to set it on the account move line as soon as the original line had a foreign currency
				if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
					# we compute the amount in that foreign currency.
					if line.move_line_id.currency_id.id == current_currency:
						# if the voucher and the voucher line share the same currency, there is no computation to do
						sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
						amount_currency = sign * (line.amount)
					else:
						# if the rate is specified on the voucher, it will be used thanks to the special keys in the context
						# otherwise we use the rates of the system
						amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
				if line.amount == line.amount_unreconciled:
					foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)

			move_line['amount_currency'] = amount_currency
			# aqui comienza modificacion actual ( Version Final )
			if voucher.type_document_id:
				move_line['type_document_id'] = voucher.type_document_id.id
			if voucher.type_document_dialog :
				move_line['type_document_id'] = voucher.type_document_dialog.id

			if line.type_document_line_id:
				move_line['type_document_id'] = line.type_document_line_id.id
			if voucher.means_payment_id  and voucher.journal_id.default_debit_account_id.id == move_line['account_id']:   
				move_line['means_payment_id'] = voucher.means_payment_id.id
			if voucher.flujo_caja_id  and voucher.journal_id.default_debit_account_id.id == move_line['account_id']:   
				move_line['flujo_caja_id'] = voucher.flujo_caja_id.id
			if voucher.name:
				move_line['name'] = voucher.name
			if voucher.fefectivo_id and voucher.journal_id.default_debit_account_id.id == move_line['account_id']:
				move_line['fefectivo_id'] = voucher.fefectivo_id.id
			if line.nro_comprobante:
				move_line['nro_comprobante'] = line.nro_comprobante
			
			if voucher.nro_comprobante_invoice:
				move_line['nro_comprobante'] = voucher.nro_comprobante_invoice
				

			voucher_line = move_line_obj.create(cr, uid, move_line)
			rec_ids = [voucher_line, line.move_line_id.id]
			
			if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
				
				exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
				new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
				move_line_obj.create(cr, uid, exch_lines[1], context)
				rec_ids.append(new_id)

			if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
				
				move_line_foreign_currency = {
					'journal_id': line.voucher_id.journal_id.id,
					'period_id': line.voucher_id.period_id.id,
					'name': _('change')+': '+(line.name or '/'),
					'account_id': line.account_id.id,
					'move_id': move_id,
					'partner_id': line.voucher_id.partner_id.id,
					'currency_id': line.move_line_id.currency_id.id,
					'amount_currency': -1 * foreign_currency_diff,
					'quantity': 1,
					'credit': 0.0,
					'debit': 0.0,
					'date': line.voucher_id.date,
				}
				if voucher.type_document_id:
					move_line_foreign_currency['type_document_id'] = voucher.type_document_id.id

				if voucher.means_payment_id and line.voucher_id.journal_id.default_debit_account_id.id == move_line_foreign_currency['account_id']:
					move_line_foreign_currency['means_payment_id'] = voucher.means_payment_id.id     
				if voucher.flujo_caja_id and line.voucher_id.journal_id.default_debit_account_id.id == move_line_foreign_currency['account_id']:
					move_line_foreign_currency['flujo_caja_id'] = voucher.flujo_caja_id.id     
				if line.nro_comprobante:
					move_line_foreign_currency['nro_comprobante'] = line.nro_comprobante
				if voucher.fefectivo_id and line.voucher_id.journal_id.default_debit_account_id.id == move_line_foreign_currency['account_id']:
					move_line_foreign_currency['fefectivo_id'] = voucher.fefectivo_id.id
					
				
				if voucher.type_document_dialog :
					move_line_foreign_currency['type_document_id'] = voucher.type_document_dialog.id
				if line.type_document_line_id:
					move_line_foreign_currency['type_document_id'] = line.type_document_line_id.id
				if voucher.name:
					move_line_foreign_currency['name'] = voucher.name

				new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
				rec_ids.append(new_id)
			if line.move_line_id.id:
				rec_lst_ids.append(rec_ids)

			
		return (tot_line, rec_lst_ids)




class account_move_line_book(models.Model):
	_inherit = 'account.move.line.book'
	_auto = False

	flujo_caja_id = fields.Many2one('it.flujo.caja',string ="F. Caja",related='aml_id.flujo_caja_id')


class account_move_line_book_report(models.Model):
	_inherit = 'account.move.line.book.report'
	_auto = False

	aml_id = fields.Many2one('account.move.line', 'aml id')

	flujo_caja_id = fields.Many2one('it.flujo.caja',string ="F. Caja",related='aml_id.flujo_caja_id')




class account_move_line_book_report_wizard(models.TransientModel):
	_inherit ='account.move.line.book.report.wizard'
	

	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		has_currency = self.moneda
		
		filtro = []
		
		currency = False
		if has_currency.id != False:
			user = self.env['res.users'].browse(self.env.uid)
			if user.company_id.id == False:
				raise osv.except_osv('Alerta!', "No existe una compañia configurada para el usuario actual.")
			if user.company_id.currency_id.id == False:
				raise osv.except_osv('Alerta!', "No existe una moneda configurada para la compañia del usuario actual.")
			
			if has_currency.id != user.company_id.currency_id.id:
				currency = True
				
		self.env.cr.execute("""
			CREATE OR REPLACE view account_move_line_book_report as (
				SELECT * 
				FROM get_libro_diario("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
		)""")

		filtro.append( ('statefiltro','=','posted') )
		
		if self.type_show == 'pantalla':

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_contable_book_it', 'action_account_moves_all_report_it')
			id = result and result[1] or False
			print id
			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.move.line.book.report',
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

			worksheet.write(0,0, "Libro Diario:", bold)
			tam_col[0] = tam_letra* len("Libro Diario:") if tam_letra* len("Libro Diario:")> tam_col[0] else tam_col[0]

			worksheet.write(0,1, self.period_ini.name, normal)
			tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

			worksheet.write(0,2, self.period_end.name, normal)
			tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

			worksheet.write(1,0, "Fecha:",bold)
			tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(1,1, str(datetime.datetime.today())[:10], normal)
			tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
			

			worksheet.write(3,0, "Periodo",boldbord)
			tam_col[0] = tam_letra* len("Periodo") if tam_letra* len("Periodo")> tam_col[0] else tam_col[0]
			worksheet.write(3,1, "Libro",boldbord)
			tam_col[1] = tam_letra* len("Libro") if tam_letra* len("Libro")> tam_col[1] else tam_col[1]
			worksheet.write(3,2, "Voucher",boldbord)
			tam_col[2] = tam_letra* len("Voucher") if tam_letra* len("Voucher")> tam_col[2] else tam_col[2]
			worksheet.write(3,3, "Cuenta",boldbord)
			tam_col[3] = tam_letra* len("Cuenta") if tam_letra* len("Cuenta")> tam_col[3] else tam_col[3]
			worksheet.write(3,4, "Debe",boldbord)
			tam_col[4] = tam_letra* len("Debe") if tam_letra* len("Debe")> tam_col[4] else tam_col[4]
			worksheet.write(3,5, "Haber",boldbord)
			tam_col[5] = tam_letra* len("Haber") if tam_letra* len("Haber")> tam_col[5] else tam_col[5]
			worksheet.write(3,6, "Divisa",boldbord)
			tam_col[6] = tam_letra* len("Divisa") if tam_letra* len("Divisa")> tam_col[6] else tam_col[6]
			worksheet.write(3,7, "Tipo Cambio",boldbord)
			tam_col[7] = tam_letra* len("Tipo Cambio") if tam_letra* len("Tipo Cambio")> tam_col[7] else tam_col[7]
			worksheet.write(3,8, "Importe Divisa",boldbord)
			tam_col[8] = tam_letra* len("Importe Divisa") if tam_letra* len("Importe Divisa")> tam_col[8] else tam_col[8]
			worksheet.write(3,9, u"Código",boldbord)
			tam_col[9] = tam_letra* len(u"Código") if tam_letra* len(u"Código")> tam_col[9] else tam_col[9]
			worksheet.write(3,10, "Partner",boldbord)
			tam_col[10] = tam_letra* len("Partner") if tam_letra* len("Partner")> tam_col[10] else tam_col[10]
			worksheet.write(3,11, "Tipo Documento",boldbord)
			tam_col[11] = tam_letra* len("Tipo Documento") if tam_letra* len("Tipo Documento")> tam_col[11] else tam_col[11]
			worksheet.write(3,12, u"Número",boldbord)
			tam_col[12] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[12] else tam_col[12]
			worksheet.write(3,13, u"Fecha Emisión",boldbord)
			tam_col[13] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[13] else tam_col[13]
			worksheet.write(3,14, "Fecha Vencimiento",boldbord)
			tam_col[14] = tam_letra* len("Fecha Vencimiento") if tam_letra* len("Fecha Vencimiento")> tam_col[14] else tam_col[14]
			worksheet.write(3,15, "Glosa",boldbord)
			tam_col[15] = tam_letra* len("Glosa") if tam_letra* len("Glosa")> tam_col[15] else tam_col[15]
			worksheet.write(3,16, u"Cta. Analítica",boldbord)
			tam_col[16] = tam_letra* len(u"Cta. Analítica") if tam_letra* len(u"Cta. Analítica")> tam_col[16] else tam_col[16]
			worksheet.write(3,17, u"Referencia Conciliación",boldbord)
			tam_col[17] = tam_letra* len(u"Referencia Conciliación") if tam_letra* len(u"Referencia Conciliación")> tam_col[17] else tam_col[17]

			worksheet.write(3,18, u"Estado",boldbord)
			tam_col[18] = tam_letra* len(u"Estado") if tam_letra* len(u"Estado")> tam_col[18] else tam_col[18]

			worksheet.write(3,19, u"Flujo Caja",boldbord)
			

			for line in self.env['account.move.line.book.report'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.cuenta if line.cuenta  else '',bord)
				worksheet.write(x,4,line.debe ,numberdos)
				worksheet.write(x,5,line.haber ,numberdos)
				worksheet.write(x,6,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,7,line.tipodecambio ,numbertres)
				worksheet.write(x,8,line.importedivisa ,numberdos)
				worksheet.write(x,9,line.codigo if line.codigo else '',bord)
				worksheet.write(x,10,line.partner if line.partner else '',bord)
				worksheet.write(x,11,line.tipodocumento if line.tipodocumento else '',bord)
				worksheet.write(x,12,line.numero if line.numero  else '',bord)
				worksheet.write(x,13,line.fechaemision if line.fechaemision else '',bord)
				worksheet.write(x,14,line.fechavencimiento if line.fechavencimiento else '',bord)
				worksheet.write(x,15,line.glosa if line.glosa else '',bord)
				worksheet.write(x,16,line.ctaanalitica if line.ctaanalitica  else '',bord)
				worksheet.write(x,17,line.refconcil if line.refconcil  else '',bord)
				worksheet.write(x,18,line.state if line.state  else '',bord)
				worksheet.write(x,19,(line.flujo_caja_id.name + '-' + line.flujo_caja_id.concepto) if line.flujo_caja_id.name  else '',bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.cuenta if line.cuenta  else '') if tam_letra* len(line.cuenta if line.cuenta  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len("%0.2f"%line.debe ) if tam_letra* len("%0.2f"%line.debe )> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len("%0.2f"%line.haber ) if tam_letra* len("%0.2f"%line.haber )> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len(line.divisa if  line.divisa else '') if tam_letra* len(line.divisa if  line.divisa else '')> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len("%0.3f"%line.tipodecambio ) if tam_letra* len("%0.3f"%line.tipodecambio )> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len("%0.2f"%line.importedivisa ) if tam_letra* len("%0.2f"%line.importedivisa )> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len(line.codigo if line.codigo else '') if tam_letra* len(line.codigo if line.codigo else '')> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len(line.partner if line.partner else '') if tam_letra* len(line.partner if line.partner else '')> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len(line.glosa if line.glosa else '') if tam_letra* len(line.glosa if line.glosa else '')> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '') if tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '')> tam_col[16] else tam_col[16]
				tam_col[17] = tam_letra* len(line.refconcil if line.refconcil  else '') if tam_letra* len(line.refconcil if line.refconcil  else '')> tam_col[17] else tam_col[17]
				tam_col[18] = tam_letra* len(line.state if line.state  else '') if tam_letra* len(line.state if line.state  else '')> tam_col[18] else tam_col[18]
				x = x +1


			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10,10]

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
			worksheet.set_column('T:T', tam_col[19])

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



class account_move_line_book_wizard(models.TransientModel):
	_inherit='account.move.line.book.wizard'
	

	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		period_end = self.period_end
		has_currency = self.moneda
		
		filtro = []
		
		currency = False
		if has_currency.id != False:
			user = self.env['res.users'].browse(self.env.uid)
			if user.company_id.id == False:
				raise osv.except_osv('Alerta!', "No existe una compañia configurada para el usuario actual.")
			if user.company_id.currency_id.id == False:
				raise osv.except_osv('Alerta!', "No existe una moneda configurada para la compañia del usuario actual.")

			if has_currency.id != user.company_id.currency_id.id:
				currency = True
			
		self.env.cr.execute("""
			CREATE OR REPLACE view account_move_line_book as (
				SELECT * 
				FROM get_libro_diario("""+ str(currency)+ """,periodo_num('""" + period_ini.code + """'),periodo_num('""" + period_end.code +"""')) 
		)""")

		if self.asientos:
			if self.asientos == 'posted':
				filtro.append( ('statefiltro','=','posted') )
			if self.asientos == 'draft':
				filtro.append( ('statefiltro','=','draft') )
		
		if self.libros:
			libros_list = []
			for i in  self.libros:
				libros_list.append(i.code)
			filtro.append( ('libro','in',tuple(libros_list)) )
		
		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']

			result = mod_obj.get_object_reference('account_contable_book_it', 'action_account_moves_all_it')
			
			id = result and result[1] or False
			print id
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.move.line.book',
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

			worksheet.write(0,0, "Libro Diario:", bold)
			tam_col[0] = tam_letra* len("Libro Diario:") if tam_letra* len("Libro Diario:")> tam_col[0] else tam_col[0]

			worksheet.write(0,1, self.period_ini.name, normal)
			tam_col[1] = tam_letra* len(self.period_ini.name) if tam_letra* len(self.period_ini.name)> tam_col[1] else tam_col[1]

			worksheet.write(0,2, self.period_end.name, normal)
			tam_col[2] = tam_letra* len(self.period_end.name) if tam_letra* len(self.period_end.name)> tam_col[2] else tam_col[2]

			worksheet.write(1,0, "Fecha:",bold)
			tam_col[0] = tam_letra* len("Fecha:") if tam_letra* len("Fecha:")> tam_col[0] else tam_col[0]

			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(1,1, str(datetime.datetime.today())[:10], normal)
			tam_col[1] = tam_letra* len(str(datetime.datetime.today())[:10]) if tam_letra* len(str(datetime.datetime.today())[:10])> tam_col[1] else tam_col[1]
			

			worksheet.write(3,0, "Periodo",boldbord)
			tam_col[0] = tam_letra* len("Periodo") if tam_letra* len("Periodo")> tam_col[0] else tam_col[0]
			worksheet.write(3,1, "Libro",boldbord)
			tam_col[1] = tam_letra* len("Libro") if tam_letra* len("Libro")> tam_col[1] else tam_col[1]
			worksheet.write(3,2, "Voucher",boldbord)
			tam_col[2] = tam_letra* len("Voucher") if tam_letra* len("Voucher")> tam_col[2] else tam_col[2]
			worksheet.write(3,3, "Cuenta",boldbord)
			tam_col[3] = tam_letra* len("Cuenta") if tam_letra* len("Cuenta")> tam_col[3] else tam_col[3]
			worksheet.write(3,4, "Debe",boldbord)
			tam_col[4] = tam_letra* len("Debe") if tam_letra* len("Debe")> tam_col[4] else tam_col[4]
			worksheet.write(3,5, "Haber",boldbord)
			tam_col[5] = tam_letra* len("Haber") if tam_letra* len("Haber")> tam_col[5] else tam_col[5]
			worksheet.write(3,6, "Divisa",boldbord)
			tam_col[6] = tam_letra* len("Divisa") if tam_letra* len("Divisa")> tam_col[6] else tam_col[6]
			worksheet.write(3,7, "Tipo Cambio",boldbord)
			tam_col[7] = tam_letra* len("Tipo Cambio") if tam_letra* len("Tipo Cambio")> tam_col[7] else tam_col[7]
			worksheet.write(3,8, "Importe Divisa",boldbord)
			tam_col[8] = tam_letra* len("Importe Divisa") if tam_letra* len("Importe Divisa")> tam_col[8] else tam_col[8]
			worksheet.write(3,9, u"Código",boldbord)
			tam_col[9] = tam_letra* len(u"Código") if tam_letra* len(u"Código")> tam_col[9] else tam_col[9]
			worksheet.write(3,10, "Partner",boldbord)
			tam_col[10] = tam_letra* len("Partner") if tam_letra* len("Partner")> tam_col[10] else tam_col[10]
			worksheet.write(3,11, "Tipo Documento",boldbord)
			tam_col[11] = tam_letra* len("Tipo Documento") if tam_letra* len("Tipo Documento")> tam_col[11] else tam_col[11]
			worksheet.write(3,12, u"Número",boldbord)
			tam_col[12] = tam_letra* len(u"Número") if tam_letra* len(u"Número")> tam_col[12] else tam_col[12]
			worksheet.write(3,13, u"Fecha Emisión",boldbord)
			tam_col[13] = tam_letra* len(u"Fecha Emisión") if tam_letra* len(u"Fecha Emisión")> tam_col[13] else tam_col[13]
			worksheet.write(3,14, "Fecha Vencimiento",boldbord)
			tam_col[14] = tam_letra* len("Fecha Vencimiento") if tam_letra* len("Fecha Vencimiento")> tam_col[14] else tam_col[14]
			worksheet.write(3,15, "Glosa",boldbord)
			tam_col[15] = tam_letra* len("Glosa") if tam_letra* len("Glosa")> tam_col[15] else tam_col[15]
			worksheet.write(3,16, u"Cta. Analítica",boldbord)
			tam_col[16] = tam_letra* len(u"Cta. Analítica") if tam_letra* len(u"Cta. Analítica")> tam_col[16] else tam_col[16]
			worksheet.write(3,17, u"Referencia Conciliación",boldbord)
			tam_col[17] = tam_letra* len(u"Referencia Conciliación") if tam_letra* len(u"Referencia Conciliación")> tam_col[17] else tam_col[17]

			worksheet.write(3,18, u"Estado",boldbord)
			tam_col[18] = tam_letra* len(u"Estado") if tam_letra* len(u"Estado")> tam_col[18] else tam_col[18]
			worksheet.write(3,19, u"Flujo Caja",boldbord)
			
			for line in self.env['account.move.line.book'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.cuenta if line.cuenta  else '',bord)
				worksheet.write(x,4,line.debe ,numberdos)
				worksheet.write(x,5,line.haber ,numberdos)
				worksheet.write(x,6,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,7,line.tipodecambio ,numbertres)
				worksheet.write(x,8,line.importedivisa ,numberdos)
				worksheet.write(x,9,line.codigo if line.codigo else '',bord)
				worksheet.write(x,10,line.partner if line.partner else '',bord)
				worksheet.write(x,11,line.tipodocumento if line.tipodocumento else '',bord)
				worksheet.write(x,12,line.numero if line.numero  else '',bord)
				worksheet.write(x,13,line.fechaemision if line.fechaemision else '',bord)
				worksheet.write(x,14,line.fechavencimiento if line.fechavencimiento else '',bord)
				worksheet.write(x,15,line.glosa if line.glosa else '',bord)
				worksheet.write(x,16,line.ctaanalitica if line.ctaanalitica  else '',bord)
				worksheet.write(x,17,line.refconcil if line.refconcil  else '',bord)
				worksheet.write(x,18,line.state if line.state  else '',bord)
				worksheet.write(x,19,(line.flujo_caja_id.name + '-' + line.flujo_caja_id.concepto) if line.flujo_caja_id.name  else '',bord)

				tam_col[0] = tam_letra* len(line.periodo if line.periodo else '' ) if tam_letra* len(line.periodo if line.periodo else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.libro if line.libro  else '') if tam_letra* len(line.libro if line.libro  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.voucher if line.voucher  else '') if tam_letra* len(line.voucher if line.voucher  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.cuenta if line.cuenta  else '') if tam_letra* len(line.cuenta if line.cuenta  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len("%0.2f"%line.debe ) if tam_letra* len("%0.2f"%line.debe )> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len("%0.2f"%line.haber ) if tam_letra* len("%0.2f"%line.haber )> tam_col[5] else tam_col[5]
				tam_col[6] = tam_letra* len(line.divisa if  line.divisa else '') if tam_letra* len(line.divisa if  line.divisa else '')> tam_col[6] else tam_col[6]
				tam_col[7] = tam_letra* len("%0.3f"%line.tipodecambio ) if tam_letra* len("%0.3f"%line.tipodecambio )> tam_col[7] else tam_col[7]
				tam_col[8] = tam_letra* len("%0.2f"%line.importedivisa ) if tam_letra* len("%0.2f"%line.importedivisa )> tam_col[8] else tam_col[8]
				tam_col[9] = tam_letra* len(line.codigo if line.codigo else '') if tam_letra* len(line.codigo if line.codigo else '')> tam_col[9] else tam_col[9]
				tam_col[10] = tam_letra* len(line.partner if line.partner else '') if tam_letra* len(line.partner if line.partner else '')> tam_col[10] else tam_col[10]
				tam_col[11] = tam_letra* len(line.tipodocumento if line.tipodocumento else '') if tam_letra* len(line.tipodocumento if line.tipodocumento else '')> tam_col[11] else tam_col[11]
				tam_col[12] = tam_letra* len(line.numero if line.numero  else '') if tam_letra* len(line.numero if line.numero  else '')> tam_col[12] else tam_col[12]
				tam_col[13] = tam_letra* len(line.fechaemision if line.fechaemision else '') if tam_letra* len(line.fechaemision if line.fechaemision else '')> tam_col[13] else tam_col[13]
				tam_col[14] = tam_letra* len(line.fechavencimiento if line.fechavencimiento else '') if tam_letra* len(line.fechavencimiento if line.fechavencimiento else '')> tam_col[14] else tam_col[14]
				tam_col[15] = tam_letra* len(line.glosa if line.glosa else '') if tam_letra* len(line.glosa if line.glosa else '')> tam_col[15] else tam_col[15]
				tam_col[16] = tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '') if tam_letra* len(line.ctaanalitica if line.ctaanalitica  else '')> tam_col[16] else tam_col[16]
				tam_col[17] = tam_letra* len(line.refconcil if line.refconcil  else '') if tam_letra* len(line.refconcil if line.refconcil  else '')> tam_col[17] else tam_col[17]
				tam_col[18] = tam_letra* len(line.state if line.state  else '') if tam_letra* len(line.state if line.state  else '')> tam_col[18] else tam_col[18]
				x = x +1


			tam_col = [11.2,10,8.8,7.14,11,11,7,10,11,13,36,7.29,14.2,14,14,25,16,10,10,10,10]

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
			worksheet.set_column('T:T', tam_col[19])

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



class account_transfer(models.Model):
	_inherit = 'account.transfer'

	flujo_caja_id_origen = fields.Many2one('it.flujo.caja','Flujo Caja') 
	flujo_caja_id_destino = fields.Many2one('it.flujo.caja','Flujo Caja') 


	@api.multi
	def aprove(self):
		ids_move = []
		for transfer in self:

			name_tmp= 'None'
			if transfer.name == 'Transferencia Borrador':
				name_tmp = self.pool.get('ir.sequence').get(self.env.cr, self.env.uid, 'account.transfer') or '/'
			else:
				name_tmp = transfer.name

			transfer.write({'name':name_tmp})
			transfer.refresh()
			#Validate debit and internal account
			if transfer.origen_journal_id.default_debit_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'El diario Origen debe tener configurada una cuenta de Debito por defecto.')
			if transfer.origen_journal_id.internal_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'El diario Origen debe tener configurada una cuenta de Transferencias.')
			if transfer.destiny_journal_id.default_debit_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'El diario Destino debe tener configurada una cuenta de Debito por defecto.')
			if transfer.destiny_journal_id.internal_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'El diario Destino debe tener configurada una cuenta de Transferencias.')
			
			user = self.env['res.users'].browse(self.env.uid)
			
			amount_origin = 0.00
			amount_currency_origin = 0.00
			currency_rate_origin = 0.00
			
			amount_destiny = 0.00
			amount_currency_destiny = 0.00
			currency_rate_destiny = 0.00
			
			res_currency_id = self.env['main.parameter'].search([])[0].currency_id
			
			#Si el origen es en dolares
			if transfer.origen_journal_id.currency.id != False:
				if transfer.destiny_journal_id.currency.id != False:
					if transfer.destiny_exchange != 0:
						currency_rate_origin = transfer.destiny_exchange
						currency_rate_destiny = transfer.destiny_exchange
					else:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', res_currency_id.id)])
						#currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							#currency_rate_origin = 1.00
							#currency_rate_destiny = 1.00
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						else:
							currency_rate_origin = currency_rate[0].type_sale
							currency_rate_destiny = currency_rate[0].type_sale
					amount_currency_origin = transfer.origen_amount
					amount_currency_destiny = transfer.destiny_amount
					amount_origin = transfer.origen_amount * currency_rate_origin
					amount_destiny = transfer.destiny_amount * currency_rate_destiny
				else:
					if transfer.destiny_exchange != 0:
						currency_rate_origin = transfer.destiny_exchange
						currency_rate_destiny = transfer.destiny_exchange
					else:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', res_currency_id.id)])
						#currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							#currency_rate_origin = 1.00
							#currency_rate_destiny = 1.00
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						else:
							currency_rate_origin = currency_rate[0].type_sale
							currency_rate_destiny = currency_rate[0].type_sale
					amount_currency_origin = transfer.origen_amount
					amount_currency_destiny = 0.00
					amount_origin = transfer.origen_amount * currency_rate_origin
					amount_destiny = transfer.destiny_amount
			#Si el origen es en soles
			else:
				if transfer.destiny_journal_id.currency.id != False:
					if transfer.destiny_exchange != 0:
						currency_rate_origin = transfer.destiny_exchange
						currency_rate_destiny = transfer.destiny_exchange
					else:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', res_currency_id.id)])
						#currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							#currency_rate_origin = 1.00
							#currency_rate_destiny = 1.00
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						else:
							currency_rate_origin = currency_rate[0].type_sale
							currency_rate_destiny = currency_rate[0].type_sale
					amount_currency_origin = 0.00
					amount_currency_destiny = transfer.destiny_amount
					amount_origin = transfer.origen_amount
					amount_destiny = transfer.origen_amount
				else:
					if transfer.destiny_exchange != 0:
						currency_rate_origin = transfer.destiny_exchange
						currency_rate_destiny = transfer.destiny_exchange
					else:
						currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', res_currency_id.id)])
						#currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
						if len(currency_rate) == 0:
							#currency_rate_origin = 1.00
							#currency_rate_destiny = 1.00
							raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
						else:
							currency_rate_origin = currency_rate[0].type_sale
							currency_rate_destiny = currency_rate[0].type_sale
					amount_currency_origin = 0.00
					amount_currency_destiny = 0.00
					amount_origin = transfer.origen_amount
					amount_destiny = transfer.destiny_amount
			
			
			'''
			amount_origin = transfer.origen_amount
			amount_currency_origin = 0.00
			currency_rate_origin = 0.00
			if transfer.origen_journal_id.currency.id != False:
				currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.origen_journal_id.currency.id)])
				if len(currency_rate) == 0:
					raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
				currency_rate_origin = currency_rate[0].type_sale
				if transfer.destiny_exchange != 0:
					currency_rate_origin = transfer.destiny_exchange
				amount_currency_origin = amount_origin
				amount_origin = transfer.origen_amount * currency_rate_origin 
			
			amount_destiny = transfer.destiny_amount
			amount_currency_destiny = 0.00
			currency_rate_destiny = 0.00
			if transfer.destiny_journal_id.currency.id != False:
				currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',transfer.date), ('currency_id','=', transfer.destiny_journal_id.currency.id)])
				if len(currency_rate) == 0:
					raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
				currency_rate_destiny = currency_rate[0].type_sale
				if transfer.destiny_exchange != 0:
					currency_rate_destiny = transfer.destiny_exchange
				amount_currency_destiny = amount_destiny
				amount_destiny = transfer.destiny_amount * currency_rate_destiny 
			'''	
			cc = []
			#Ingreso la devolucion
			refund_cc = (0,0,{
					'tax_amount': 0.0, 
					'name': transfer.glosa, 
					'ref': False,
					'nro_comprobante': transfer.doc_origen,
					'currency_id': transfer.origen_journal_id.currency.id, 
					'debit': 0.00,
					'credit': amount_origin, 
					'date_maturity': False, 
					'date': transfer.date,
					'amount_currency': -1 * amount_currency_origin,
					'account_id': transfer.origen_journal_id.default_debit_account_id.id,
					'currency_rate_it': currency_rate_origin,
					'flujo_caja_id':self.flujo_caja_id_origen.id,
					})
			cc.append(refund_cc)

			#parcho al empleado
			employee_fix_cc = (0,0,{
					'tax_amount': 0.0, 
					'name': transfer.glosa, 
					'ref': False, 
					'nro_comprobante': transfer.doc_origen,
					'currency_id': False, 
					'debit': amount_origin,
					'credit': 0.00, 
					'date_maturity': False, 
					'date': transfer.date,
					'amount_currency': 0.00, 
					'account_id': transfer.origen_journal_id.internal_account_id.id,
					'currency_rate_it': currency_rate_origin,
					})
			cc.append(employee_fix_cc)
			lst = self.env['account.period'].search([('date_start','<=',transfer.date),('date_stop','>=',transfer.date)])
			period_id=lst[0]
			# raise osv.except_osv('Alerta', cc)					
			obj_sequence = self.pool.get('ir.sequence')
			id_seq = transfer.origen_journal_id.sequence_id.id


			name = None
			if transfer.period_id_move_id.id != period_id.id:
				context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
				name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
				self.write({'name_move_1': name, 'period_id_move_id':period_id.id})
			else:
									
				if transfer.name_move_1 == False:
					context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
					name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
					self.write({'name_move_1': name})
				else:
					name = transfer.name_move_1

			"""
			context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
			name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)					
			"""

			move = {
					'name':name,
					'ref': transfer.name,
					'line_id': cc,
					'date': transfer.date,
					'journal_id': transfer.origen_journal_id.id,
					'period_id':period_id.id,
					'company_id': user.company_id.id,
				}
			move_obj = self.pool.get('account.move')
			move_id1 = move_obj.create(self.env.cr, self.env.uid, move, context=None)

			self.write({'move_move_1_id':move_id1})

			move_id_act=move_id1
			move_obj.post(self.env.cr, self.env.uid, [move_id1], context=None)
			ids_move.append(move_id_act)

			#Asiento de vuelta
			cc2 = []
			#Ingreso la devolucion
			refund_cc2 = (0,0,{
					'tax_amount': 0.0, 
					'name': transfer.glosa, 
					'ref': False,
					'nro_comprobante': transfer.doc_destiny,
					'currency_id': transfer.destiny_journal_id.currency.id, 
					'debit': amount_destiny,
					'credit': 0, 
					'date_maturity': False, 
					'date': transfer.date,
					'amount_currency': amount_currency_destiny, 
					'account_id': transfer.destiny_journal_id.default_debit_account_id.id,
					'currency_rate_it': currency_rate_destiny,					
					'flujo_caja_id':self.flujo_caja_id_destino.id,
					})
			cc2.append(refund_cc2)

			#parcho al empleado
			employee_fix_cc2 = (0,0,{
					'tax_amount': 0.0, 
					'name': transfer.glosa, 
					'ref': False, 
					'nro_comprobante': transfer.doc_destiny,
					'currency_id': False, 
					'debit': 0,
					'credit': amount_destiny, 
					'date_maturity': False, 
					'date': transfer.date,
					'amount_currency': 0.00, 
					'account_id': transfer.destiny_journal_id.internal_account_id.id,
					'currency_rate_it': currency_rate_destiny,
					})
			cc2.append(employee_fix_cc2)
			#lst2 = self.env['account.period'].search([('date_start','<=',transfer.date),('date_stop','>=',transfer.date)])
			#period_id=lst2[0]
			# raise osv.except_osv('Alerta', cc)					
			obj_sequence = self.pool.get('ir.sequence')
			id_seq2 = transfer.destiny_journal_id.sequence_id.id
			context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}


			name2 = None
			if transfer.period_id_move_id.id != period_id.id:
				context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
				name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
				self.write({'name_move_2': name2, 'period_id_move_id':period_id.id})
			else:
									
				if transfer.name_move_2 == False:
					context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
					name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
					self.write({'name_move_2': name2})
				else:
					name2 = transfer.name_move_2

			"""
			name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
			"""

			move2 = {
					'name':name2,
					'ref': transfer.name,
					'line_id': cc2,
					'date': transfer.date,
					'journal_id': transfer.destiny_journal_id.id,
					'period_id':period_id.id,
					'company_id': user.company_id.id,
				}
			move_obj2 = self.pool.get('account.move')
			move_id12 = move_obj.create(self.env.cr, self.env.uid, move2, context=None)


			self.write({'move_move_2_id':move_id12})
			move_id_act2=move_id12
			move_obj2.post(self.env.cr, self.env.uid, [move_id12], context=None)
			ids_move.append(move_id_act2)
			
			self.write({'state' : 'done', 'done_move': [(6, 0, ids_move)]})	



class deliveries_to_pay(models.Model):
	_inherit = 'deliveries.to.pay'

	flujo_caja_id_deliver = fields.Many2one('it.flujo.caja','Flujo Caja')

	@api.multi
	def balance_deliver(self):
		ids_move = []
		ids_move_hidden = []
		#Reviso si existe el objeto parametros
		parameters = self.env['main.parameter'].search([])
		if len(parameters)==0:
			raise osv.except_osv('Error!', 'No existe el objeto Parametros en la configuracion contable. Contacte a su administrador!')
		parameter = parameters[0]
		
		name_deliver = None
		if self.name == 'Rendicion Borrador' or self.name is None or self.name == False:
			name_deliver = self.pool.get('ir.sequence').get(self.env.cr, self.env.uid, 'deliveries.to.pay') or '/'
			self.write({'name': name_deliver})
		else:
			name_deliver = self.name
			
		for deliver in self:
			journal = None
			#Reviso si estan configuradas las cuentas de rendiciones
			if deliver.deliver_journal_id.currency.id != False:
				if parameter.deliver_account_me.id == False:
					raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de rendiciones en Moneda Extranjera.')
				if parameter.loan_journal_me.id == False:
					raise osv.except_osv('Acción Inválida!', 'Debe configurar un diario de rendiciones en Moneda Extranjera.')
				journal = parameter.loan_journal_me
			else:
				if parameter.deliver_account_mn.id == False:
					raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de rendiciones en Moneda Nacional.')
				if parameter.loan_journal_mn.id == False:
					raise osv.except_osv('Acción Inválida!', 'Debe configurar un diario de rendiciones en Moneda Nacional.')
				journal = parameter.loan_journal_mn
			
			currency_id = deliver.deliver_journal_id.currency.id
			monto = deliver.deliver_amount
			monto_currency = 0
			
			if currency_id != False:
				currency_rate = self.env['res.currency.rate'].search([('date_sunat','<=',deliver.deliver_date), ('currency_id','=', currency_id)])
				if len(currency_rate) == 0:
					raise osv.except_osv('Acción Inválida!', 'No existe un tipo de cambio para la fecha.')
				monto_currency = monto
				monto = monto * currency_rate[0].type_sale
			
			obj_sequence = self.pool.get('ir.sequence')
			
			
			if deliver.deliver_journal_id.internal_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de transferencias internas para el Metodo de Pago seleccionado.')
			if journal.internal_account_id.id == False:
				raise osv.except_osv('Acción Inválida!', 'Debe configurar una cuenta de transferencias internas para el diario de Entregas a Rendir.')
			
			lst = self.env['account.period'].search([('date_start','<=',deliver.deliver_date),('date_stop','>=',deliver.deliver_date)])
			if len(lst) == 0:
				raise osv.except_osv('Alerta!', 'No existe un periodo para la fecha ' + deliver.deliver_date + '.')
			period_id=lst[0]
			
			#Asiento que saca el dinero de la caja
			id_seq = deliver.deliver_journal_id.sequence_id.id
			#name = None
			"""
			context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
			name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
			self.write({'deliver_a': name, 'period_id':period_id.id})
			"""
			name = None
			if deliver.period_id.id != period_id.id:
				#self.env.context.update({'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}) 
				context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
				name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
				self.write({'deliver_a': name, 'period_id':period_id.id})
			else:
				if deliver.deliver_a == False:
					context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
					name=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq, context)
					self.write({'deliver_a': name})
				else:
					name = deliver.deliver_a
			
			cc = [(0,0,{
					'tax_amount': 0.0, 
					'name': deliver.memory, 
					'ref': False,
					'nro_comprobante':deliver.invoice_number,
					'currency_id': False, 
					'debit': monto,
					'credit': 0, 
					'date_maturity': False, 
					'date': deliver.deliver_date,
					'amount_currency': 0, 
					'account_id': deliver.deliver_journal_id.internal_account_id.id,
					'partner_id': deliver.partner_id.id,
					'rendicion_id': deliver.id,
					}),
				(0,0,{
					'tax_amount': 0.0, 
					'name': deliver.memory, 
					'ref': False, 
					'nro_comprobante':deliver.invoice_number,
					'currency_id': currency_id if currency_id != False else None, 
					'debit': 0,
					'credit': monto,
					'date_maturity': False, 
					'date': deliver.deliver_date,
					'amount_currency': -1 * monto_currency,
					'account_id': deliver.deliver_journal_id.default_debit_account_id.id,
					'partner_id': False,
					'rendicion_id': deliver.id,
					'flujo_caja_id': self.flujo_caja_id_deliver.id,
				})]
			
			# raise osv.except_osv('Alerta', cc)					
								
			move = {
					'name':name,
					'ref': deliver.name,
					'line_id': cc,
					'date': deliver.deliver_date,
					'journal_id': deliver.deliver_journal_id.id,
					'period_id':period_id.id,
					'company_id': deliver.partner_id.company_id.id,
				}
			move_obj = self.pool.get('account.move')
			move_id1 = move_obj.create(self.env.cr, self.env.uid, move, context=None)


			self.write({'asiento_d_a':move_id1})

			move_id_act=move_id1
			move_obj.post(self.env.cr, self.env.uid, [move_id1], context=None)
			#ids_move.append(move_id_act)
			ids_move_hidden.append(move_id_act)

			
			#Asiento que mete el dinero al diario de rendicion
			id_seq2 = journal.sequence_id.id
			#name2 = None
			"""
			context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
			name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
			self.write({'deliver_b': name2, 'period_id':period_id.id})
			"""

			name2 = None
			if deliver.period_id.id != period_id.id:
				#self.env.context.update({'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}) 
				context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
				name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
				self.write({'deliver_b': name2, 'period_id':period_id.id})
			else:
				if deliver.deliver_b == False:
					context = {'fiscalyear_id':period_id.fiscalyear_id.id, 'period':period_id}
					name2=obj_sequence.next_by_id(self.env.cr, self.env.uid, id_seq2, context)
					self.write({'deliver_b': name2})
				else:
					name2 = deliver.deliver_b
			
			cc2 = [(0,0,{
					'tax_amount': 0.0, 
					'name': deliver.memory, 
					'ref': False,
					'nro_comprobante':deliver.name,
					'currency_id': currency_id if currency_id != False else None, 
					'debit': monto,
					'credit': 0, 
					'date_maturity': False, 
					'date': deliver.deliver_date,
					'amount_currency': monto_currency, 
					'account_id': parameter.deliver_account_mn.id if currency_id == False else parameter.deliver_account_me.id,
					'partner_id': deliver.partner_id.id,
					'rendicion_id': deliver.id,
					}),
				(0,0,{
					'tax_amount': 0.0, 
					'name': deliver.memory, 
					'ref': False, 
					'nro_comprobante':deliver.name,
					'currency_id': False, 
					'debit': 0,
					'credit': monto,
					'date_maturity': False, 
					'date': deliver.deliver_date,
					'amount_currency': 0.00,
					'account_id': journal.internal_account_id.id,
					'partner_id': False,
					'rendicion_id': deliver.id,
				})]
				
								
			move2 = {
					'name':name2,
					'ref': deliver.name,
					'line_id': cc2,
					'date': deliver.deliver_date,
					'journal_id': journal.id,
					'period_id':period_id.id,
					'company_id': deliver.partner_id.company_id.id,
				}
			move_obj2 = self.pool.get('account.move')
			move_id12 = move_obj.create(self.env.cr, self.env.uid, move2, context=None)

			self.write({'asiento_d_b':move_id12})

			move_id_act2=move_id12
			move_obj2.post(self.env.cr, self.env.uid, [move_id12], context=None)
			ids_move.append(move_id_act2)
			ids_move_hidden.append(move_id_act2)
	
		self.write({'state': 'delivered', 'name': name_deliver, 'deliver_move': [(6, 0, ids_move)], 'deliver_move_hidden': [(6, 0, ids_move_hidden)]})
		return True
	