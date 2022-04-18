# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
class raw_extension(osv.osv):
	_name='raw.extension'
	_columns={
		'name':fields.char('Extension',size=10),
		'tipodoc':fields.selection([('gsa','Guía de salida almacén'),
								   ('gsv','Guía de salida ventas'),
								   ('nti','Nota de ingreso'),
								   ('nts','Nota de salida'),
								   ('fac','Facturas'),
								   ('bol','Boletas'),
								   ('cdp','Comprobante de percepción'),
								   ('nil','Nota de ingtreso logística'),
								   ('chk','Cheques'),
								   ('prtfactura','Factura Print'),
								   ('nsv','Nota de salida valorizada'),]),
		'company_id':fields.many2one('res.company','compania'),
	}
raw_extension()

class res_company(osv.osv):
	_name='res.company'
	_inherit='res.company'
	_columns={
		'printer_directory':fields.char('Directorio de impresión (en el servidor)',size=200),
		'extesion_ids':fields.one2many('raw.extension','company_id','Extensiones de archivos')
	}
res_company()

