# -*- coding: utf-8 -*-
{
    'name': "Reporte de Maximos y Minimos IT",

    'description': """
        - Genera Reporte de Maximos y Minimos
    """,

    'author': "ITGrupo",
    'category': 'mrp',
    'version': '0.1',
    'auto_install': False,
    'installable': True,
    'depends': ['kardex_saldos','warehouse_parameters'],
    'data': ['security/max_min_security.xml','security/ir.model.access.csv','wizard/min_max_wizard_view.xml','min_max_view.xml','stock_warehouse_orderpoint_view.xml','warehouse_parameters_view.xml'],
}