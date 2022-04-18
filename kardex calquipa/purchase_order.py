import pytz
from openerp import models, fields, api, _
from openerp import SUPERUSER_ID, workflow
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import attrgetter
from openerp.tools.safe_eval import safe_eval as eval
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record_list, browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.tools.float_utils import float_compare

class account_invoice(osv.osv):
	_name='account.invoice'
	_inherit='account.invoice'

	def name_search(self,cr,uid,name, args=None, operator='ilike', limit=100,context=None):
		args = args or []
		recs = self.pool.get('account.invoice').browse(cr,uid)
		if name:
			recs = self.pool.get('account.invoice').search(cr,uid,[('number', operator, name)] + args, limit=limit)
		if not recs:
			recs = self.pool.get('account.invoice').search(cr,uid,[('name', operator, name)] + args, limit=limit)
		return self.pool.get('account.invoice').name_get(cr,uid,recs)

	def invoice_validate(self, cr, uid, ids, context=None):
		# raise osv.except_osv('Alerta1', context['invoice'])		
		res = super(account_invoice,self).invoice_validate(cr, uid, ids, context)
		for fact in self.pool.get('account.invoice').browse(cr,uid,ids,context):
			procesar=True
			# raise osv.except_osv('Alertafinal',procesar)
			purchase_order_obj = self.pool.get('purchase.order')
			if not purchase_order_obj.check_access_rights(cr, uid, 'read', raise_exception=False):
				user_id = SUPERUSER_ID
			else:
				user_id = uid
			po_ids = purchase_order_obj.search(cr, user_id, [('invoice_ids', 'in', ids)], context=context)
			for purchase in self.pool.get('purchase.order').browse(cr,uid,po_ids):
				if purchase.invoice_method!='picking':
					if purchase.picking_ids:
						for picking in purchase.picking_ids:
							# raise osv.except_osv('Alerta1', vals)
							self.pool.get('stock.picking').write(cr,uid,[picking.id],{'invoice_id':fact.id},context)
			
			cadsql="select * from sale_order_invoice_rel where invoice_id = "+str(fact.id)
			cr.execute(cadsql)
			dataf=cr.dictfetchall()
			if len(dataf)>0:
				lst = []
				for id_data in dataf:
					lst.append(id_data['order_id'])
				for sale in self.pool.get('sale.order').browse(cr,uid,lst,context):
					if sale.order_policy!='picking':
						# raise osv.except_osv('Alerta1', sale.picking_ids)
						if sale.picking_ids:
							for picking in sale.picking_ids:
								self.pool.get('stock.picking').write(cr,uid,[picking.id],{'invoice_id':fact.id},context)
								# for stock_move in picking.move_lines:
								# 	stock_move.invoice_id = fact.id
		return res
	def action_cancel(self, cr, uid, ids, context=None):
		#self.delete_kardex_relations(cr, uid, ids)
		super(account_invoice,self).action_cancel(cr, uid, ids, context)
		return True
	def delete_kardex_relations(self,cr,uid,ids,context=None):
		if not hasattr(ids, "__iter__"):
			ids =[ids]
		for id_invoice in ids:
			lst_picking=self.pool.get('stock.picking').search(cr,uid,[('invoice_id','=',id_invoice)])	
			if lst_picking!=[]:
				for picking in self.pool.get('stock.picking').browse(cr,uid,lst_picking,context):
					picking.invoice_id = None

		return True

	# def validate_duplicates(self,cr,uid,vals,idact,iscreate=False,context=None):
	# 	lstprods=[]
	# 	lstrepetidos=[]
	# 	if iscreate:
	# 		for line in vals['invoice_line']:
	# 			if 'product_id' in line:
	# 				if line['product_id'] not in lstprods:
	# 					lstprods.append(line['product_id'])
	# 				else:
	# 					prod = self.pool.get('product_product').browse(cr,uid,line['product_id'],context)
	# 					lstrepetidos.append(prod.name_template)
	# 			else:
	# 				if type(line[2]) is list:
	# 					for linea in self.pool.get('account.invoice.line').browse(cr,uid,line[2]):
	# 						if linea.product_id:
	# 							if linea.product_id not in lstprods:
	# 								lstprods.append(linea.product_id)
	# 							else:
	# 								prod = self.pool.get('product_product').browse(cr,uid,linea.product_id.id,context)
	# 								lstrepetidos.append(prod.name_template)
	# 				if type(line[2]) is dict:
	# 					if 'product_id' in line[2]:
	# 						if line[2]['product_id']:
	# 							if line[2]['product_id'] not in lstprods:
	# 								lstprods.append(line[2]['product_id'])
	# 							else:
	# 								prod = self.pool.get('product.product').browse(cr,uid,line[2]['product_id'],context)
	# 								lstrepetidos.append(prod.name_template)


	# 	else:
	# 		cadsql = "select count(*) as cantidad, product_id from account_invoice_line where invoice_id = "+str(idact) +" group by product_id"
	# 		cr.execute(cadsql)
	# 		datas = cr.dictfetchall()
	# 		for data in datas:
	# 			if data['cantidad']>1:
	# 				prod = self.pool.get('product.product').browse(cr,uid,data['product_id'],context)
	# 				lstrepetidos.append(prod.name_template)
	# 	if lstrepetidos!=[]:
	# 		cadr=''
	# 		for l in lstrepetidos:
	# 			cadr=cadr+l+','
	# 		raise osv.except_osv('Alerta','Los siguentes productos se encuentran repetidos: '+cadr)
	# 	return True		
	# def create(self, cr,uid,vals,context=None):
	# 	if 'default_type' in context:
	# 		if context['default_type']=='in_invoice':
	# 			self.validate_duplicates(cr,uid,vals,False,True,context)
	# 	return super(account_invoice,self).create(cr,uid,vals,context)

	# def write(self,cr,uid,ids,vals,context=None):
	# 	validar =False
	# 	if 'type' in vals:
	# 		if vals['type']=='in_invoice':
	# 			validar=True
	# 	else:
	# 		for idact in ids:
	# 			actb=self.pool.get('account.invoice').browse(cr,uid,idact,context)
	# 			if actb.type=='in_invoice':
	# 				validar=True
	# 	d=super(account_invoice,self).write(cr,uid,ids,vals,context)
	# 	if validar:
	# 		for idact in ids:
	# 			self.validate_duplicates(cr,uid,vals,idact,False,context)
	# 	return d


account_invoice()


class purchase_order(osv.osv):
	_name='purchase.order'
	_inherit='purchase.order'
	def wkf_confirm_order(self, cr, uid, ids, context=None):
		res = super(purchase_order,self).wkf_confirm_order(cr, uid, ids, context)
		for po in self.browse(cr, uid, ids, context=context):
			if len(po.invoice_ids)>0:
				invoice = po.invoice_ids[0]
				for picking in po.picking_ids:
					picking.invoice_id = invoice.id
					# for line in picking.move_lines:
					# 	line.invoice_id = invoice.id 
		return res
	# def create(self, cr,uid,vals,context=None):
	# 	self.validate_duplicates(cr,uid,vals,False,True,context)
	# 	return super(purchase_order,self).create(cr,uid,vals,context)

	# def write(self,cr,uid,ids,vals,context=None):
	# 	d=super(purchase_order,self).write(cr,uid,ids,vals,context)
	# 	for idact in ids:
	# 		self.validate_duplicates(cr,uid,vals,idact,False,context)
	# 	return d

	# def validate_duplicates(self,cr,uid,vals,idact,iscreate=False,context=None):
	# 	lstprods=[]
	# 	lstrepetidos=[]
	# 	if iscreate:
	# 		if 'order_line' in vals:
	# 			for line in vals['order_line']:
	# 				if line['product_id'] not in lstprods:
	# 					lstprods.append(line['product_id'])
	# 				else:
	# 					prod = self.pool.get('product.product').browse(cr,uid,line['product_id'],context)
	# 					lstrepetidos.append(prod.name_template)
	# 	else:
	# 		cadsql = "select count(*) as cantidad, product_id from purchase_order_line where order_id = "+str(idact) +" group by product_id"
	# 		cr.execute(cadsql)
	# 		datas = cr.dictfetchall()
	# 		for data in datas:
	# 			if data['cantidad']>1:
	# 				prod = self.pool.get('product.product').browse(cr,uid,data['product_id'],context)
	# 				lstrepetidos.append(prod.name_template)
	# 	if lstrepetidos!=[]:
	# 		cadr=''
	# 		for l in lstrepetidos:
	# 			cadr=cadr+l+','
	# 		raise osv.except_osv('Alerta','Los siguentes productos se encuentran repetidos: '+cadr)
	# 	return True		

# class purchase_requisition(osv.osv):
# 	_name='purchase.requisition'
# 	_inherit='purchase.requisition'

	# def create(self, cr,uid,vals,context=None):
	# 	self.validate_duplicates(cr,uid,vals,False,True,context)
	# 	return super(purchase_requisition,self).create(cr,uid,vals,context)

	# def write(self,cr,uid,ids,vals,context=None):
	# 	d=super(purchase_requisition,self).write(cr,uid,ids,vals,context)
	# 	for idact in ids:
	# 		self.validate_duplicates(cr,uid,vals,idact,False,context)
	# 	return d

	# def validate_duplicates(self,cr,uid,vals,idact,iscreate=False,context=None):

	# 	lstprods=[]
	# 	lstrepetidos=[]
	# 	if iscreate:
	# 		if 'line_ids' in vals:
	# 			for line in vals['line_ids']:
	# 				if 'product_id' in line:
	# 					if line['product_id'] not in lstprods:
	# 						lstprods.append(line['product_id'])
	# 					else:
	# 						prod = self.pool.get('product.product').browse(cr,uid,line['product_id'],context)
	# 						lstrepetidos.append(prod.name_template)
	# 				else:
	# 					if type(line[2]) is list:
	# 						for linea in self.pool.get('purchase.requisition.line').browse(cr,uid,line[2]):
	# 							if linea.product_id:
	# 								if linea.product_id not in lstprods:
	# 									lstprods.append(linea.product_id)
	# 								else:
	# 									prod = self.pool.get('product_product').browse(cr,uid,linea.product_id.id,context)
	# 									lstrepetidos.append(prod.name_template)
	# 					if type(line[2]) is dict:
	# 						if 'product_id' in line[2]:
	# 							if line[2]['product_id']:
	# 								if line[2]['product_id'] not in lstprods:
	# 									lstprods.append(line[2]['product_id'])
	# 								else:
	# 									prod = self.pool.get('product.product').browse(cr,uid,line[2]['product_id'],context)
	# 									lstrepetidos.append(prod.name_template)

	# 	else:
	# 		cadsql = "select count(*) as cantidad, product_id from purchase_requisition_line where requisition_id = "+str(idact) +" group by product_id"
	# 		cr.execute(cadsql)
	# 		datas = cr.dictfetchall()
	# 		for data in datas:
	# 			if data['cantidad']>1:
	# 				prod = self.pool.get('product.product').browse(cr,uid,data['product_id'],context)
	# 				lstrepetidos.append(prod.name_template)
	# 	if lstrepetidos!=[]:
	# 		cadr=''
	# 		for l in lstrepetidos:
	# 			cadr=cadr+l+','
	# 		raise osv.except_osv('Alerta','Los siguentes productos se encuentran repetidos: '+cadr)
	# 	return True		
