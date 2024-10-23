{
  'name': 'Arkana Courses',
  'author': 'Adha',
  'version': '0.1',
  'depends': [
    # 'nama_modul',
    'base',
    'mail',
    'contacts',
    'hr',
    'product',
    'stock'
  ],
  'data': [
    # 'views/nama_file.xml',
    'security/ir.model.access.csv',
    'data/partner_data.xml',
    'data/partner_seq_data.xml',
    # 'views/mentor_student_views.xml',
    'views/course_student_view.xml',
    'views/course_subject_view.xml',
    'views/course_booking_view.xml',
    'views/course_menus.xml',

    

  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': True,
  'category': 'Arkademy Task',
  'summary': 'Task Pertama',
  'license': 'OPL-1',
  'website': 'https://adhamajid.github.io/kostbox.github.io/',
  'description': 'Be The Bestt'
}