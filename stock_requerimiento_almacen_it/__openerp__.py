# -*- coding: utf-8 -*-
{
    'name': "Requerimiento para Almacén IT",

    'description': """
        - Crea menú para requerimientos de almacén
    """,

    'author': "ITGrupo",
    'category': 'mrp',
    'version': '0.1',
    'auto_install': False,
    'installable': True,
    'depends': ['mrp','stock_account','stock_picking_motive','ordenes_produccion_joya'],
    'data': ['security/stock_picking_security.xml','stock_picking_view.xml'],
}