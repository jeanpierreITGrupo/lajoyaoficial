# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
class stock_picking(osv.osv):
	_name='stock.picking'
	_inherit='stock.picking'
	_columns={
		'use_date':fields.boolean('Usar fecha en kardex'),
		# 'move_lines': fields.one2many('stock.move', 'picking_id', 'Internal Moves', states={'cancel': [('readonly', True)]}),
	}
	_defaults = {
		'use_date': True,
	}
	##def copy(self, cr, uid, id, default=None, context=None):
	##	if not default:
	##		default = {}
	##	default.update({'invoice_id':False})
	##	return super(stock_picking, self).copy(cr, uid, id, default, context=context)	
	
	##def _create_invoice_from_picking(self, cr, uid, picking, vals, context=None):
	##	invoice_id = super(stock_picking, self)._create_invoice_from_picking(cr, uid, picking, vals, context=context)
	##	self.pool.get('stock.picking').write(cr,uid,picking.id,{'invoice_id':invoice_id},context)
	##	return invoice_id		
		


	# def create(self, cr,uid,vals,context=None):
	# 	self.validate_duplicates(cr,uid,vals,False,True,context)
	# 	return super(stock_picking,self).create(cr,uid,vals,context)

	# def write(self,cr,uid,ids,vals,context=None):
	# 	for idact in ids:
	# 		self.validate_duplicates(cr,uid,vals,idact,False,context)
	# 	return super(stock_picking,self).write(cr,uid,ids,vals,context)

	# def validate_duplicates(self,cr,uid,vals,idact,iscreate=False,context=None):
	# 	lstprods=[]
	# 	lstrepetidos=[]
	# 	if iscreate:
	# 		for line in vals['move_lines']:
	# 			if line['product_id'] not in lstprods:
	# 				lstprods.append(line['product_id'])
	# 			else:
	# 				prod = self.pool.get('product_product').browse(cr,uid,line['product_id'],context)
	# 				lstrepetidos.append(prod.name_template)
	# 	else:
	# 		cadsql = "select count(*) as cantidad, product_id from stock_move where picking_id = "+str(idact) +" group by product_id"
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

	
stock_picking()


