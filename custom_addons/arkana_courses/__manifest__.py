{
  'name': 'Arkana Courses',
  'author': 'Adha',
  'version': '0.1',
  'depends': [
    # 'nama_modul',
    'base',
    'contacts',
    'hr',
    'mail',
    'stock',
    'product',
    'sale_management',

  ],
  'data': [
    # 'views/nama_file.xml',
    'security/ir.model.access.csv',
    'data/partner_data.xml',
    'data/sequence_mentee.xml',
    'data/sequence_booking.xml',
    'views/sale_order_inheret_view.xml',
    'views/course_mentor_view.xml',
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