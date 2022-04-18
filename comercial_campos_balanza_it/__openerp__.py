# -*- encoding: utf-8 -*-
{
    'name': 'Campos Importación Balanza IT',
    'category': 'Purchase',
    'author': 'ITGrupo',
    'depends': ['purchase_liquidation_it','purchase_parameters_it'],
    'version': '1.0',
    'description':"""
        Agrega 2 campos necesarios para la importación desde la balanza.
    """,
    'auto_install': False,
    'demo': [],
    'data': [
            'purchase_liquidation.xml',
            ],
    'installable': True
}