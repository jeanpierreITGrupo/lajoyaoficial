# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
class raw_print(osv.osv):
	_name='raw.print'
	_columns={
		'texto':fields.text('Texto'),
	}
	def imprimir(self, cr, uid, ids, context=None):
		p = Printer() 
		p.setPageHeight( 36 ) 
		p.write( 64, "data" ) 
		p.write( 15, "a lot of data that should be printed in multiple lines with 20 character width", 20 ) 
		p.newPage() 
		p.close() 
		return True
raw_print()
