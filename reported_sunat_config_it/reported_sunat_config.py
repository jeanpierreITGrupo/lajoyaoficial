# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class reported_sunat_config(osv.osv):
    _name= 'reported.sunat.config'
    _description= 'Configuracion de los Reportes Sunat'
    _columns = {

        'name': fields.selection([('diario', 'Libro Diario'),
                                         ('mayor', 'Libro Mayor'),
                                         ('compra', 'Libro Compra'),
                                         ('venta', 'Libro Venta'),
                                         ('caja', 'Libro Caja'),
                                         ('banco', 'Libro Banco'),
                                         ('hoja', 'Libro Balance'),
                                         ('kardex','Kardex Sunat'),
                                         ('hojatrabajobalance','Hoja Trabajo Balance'),
                                         ('hojatrabajoregistro','Hoja Trabajo Registro'),
                                         ('cuenta10','Cuenta 10'),
                                         ('cuenta12','Cuenta 12'),
                                         ('cuenta13','Cuenta 13'),
                                         ('cuenta14','Cuenta 14'),
                                         ('cuenta16','Cuenta 16'),
                                         ('cuenta19','Cuenta 19')
                                        ], 'Reporte Sunat', required=True),

        'function': fields.char('Nombre Funcion',required=True),
        'company' : fields.char('Datos Compañia', required=True),
        'description' : fields.char('Descripcion de la tabla',required=True),
        }


reported_sunat_config()