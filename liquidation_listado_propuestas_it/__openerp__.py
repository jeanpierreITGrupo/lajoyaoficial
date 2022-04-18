# -*- encoding: utf-8 -*-
{
    'name': 'LISTADO DE PROPUESTAS IT',
    'category': 'Purchase',
    'author': 'ITGrupo',
    'depends': ['web','purchase_parameters_it','purchase_liquidation_it'],
    'version': '1.0',
    'description':"""
        Módulo que crea menú Listado de Propuestas.
    """,
    'auto_install': False,
    'demo': [],
    'data': ['security/ir.model.access.csv','listado_propuestas_view.xml'],
    'installable': True
}