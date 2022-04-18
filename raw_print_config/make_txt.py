# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
import os
import tempfile
import datetime
import codecs
import base64

class make_txt(osv.osv_memory):
	_name='make.txt'
	def makefile(self,cr,uid,texto,doctype,context=None):
		user = self.pool.get('res.users').browse(cr,uid,uid,context)
		destination = user.company_id.printer_directory
		# doclst=self.pool.get('raw.extension').search(cr,uid,['name','=',doctype])
		cr.execute("select name from raw_extension where tipodoc='"+doctype+"'")
		doclst=cr.fetchall()
		# raise osv.except_osv('Alerta', doctype)
		doc=doclst[0][0]
		# raise osv.except_osv('Alerta', doc.name)
		# ('Directorio de destino {0}'.format(destination))
		if not os.path.exists(destination):
			os.makedirs(destination)
		# raise osv.except_osv('Alerta', texto)
		# self.eliminarAcentos(linea["product_name"])
		codecs.open(os.path.join(destination,self.makefilename(cr,uid,doc,context)),'w','latin1').write(self.eliminarAcentos(texto))
		# file(os.path.join(destination,self.makefilename(cr,uid,doc,context)),'w','utf-8').write(texto.encode('utf-8','ignore'))
		return True
	def makefilename(self,cr,uid,extenc,context):
		basename = extenc 
		suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
		filename = "_".join([basename, suffix])+"."+extenc 
		return filename
	def	eliminarAcentos(self,cadena):
		d	=	{	'Á':'A',
			'É':'E',
			'Í':'I',
			'Ó':'O',
			'Ú':'U',
			'Ü':'U',
			'Ñ':'N',
			'Ç':'C',
			'í':'i',
			'ó':'o',
			'ñ':'n',
			'ç':'c',
			'á':'a',
			'à':'a',
			'ä':'a',
			'é':'e',
			'è':'e',
			'ë':'e',
			'í':'i',
			'ì':'i',
			'ï':'i',
			'ó':'o',
			'ò':'o',
			'ö':'o',
			'ù':'u',
			'ú':'u',
			'ü':'u',
		}
		
		nueva_cadena=cadena
		# raise osv.except_osv('Alerta', nueva_cadena.replace('ñ','n'))
		for	c in d.keys():
			nueva_cadena=nueva_cadena.replace(c.decode('utf-8'),d[c])
		auxiliar	=	nueva_cadena.encode('utf-8')
		return	nueva_cadena		
make_txt()