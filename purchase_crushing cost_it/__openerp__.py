# -*- encoding: utf-8 -*-
{
    'name': 'Crushing Cost IT',
    'category': 'Manufacture',
    'author': 'ITGrupo',
    'depends': ['account', 'stock', 'previous_requirements_joya'],
    'version': '1.0',
    'description':"""
        Módulo que agrega menú y funcionalidad para obtener el costo del proceso de chancado.
    """,
    'auto_install': False,
    'demo': [],
    'data': ['crushing_cost_data.xml',
            'crushing_cost.xml'],
    'installable': True
}