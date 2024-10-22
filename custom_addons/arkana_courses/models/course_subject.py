from odoo import _, api, fields, models

class CourseSubject(models.Model):
    _name = 'course.subject'
    _description = 'Course Subject'
    _inherit = ['mail.thread', 'mail.activity.mixin']  
        

    company_id = fields.Many2one('res.company', string='Company', index = True,
                                 tracing = True, default = lambda self : self.env.company, ondelete='restrict')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  related='company_id.currency_id',
                                  store=True,)
    
    name = fields.Char('Name', index = 'trigram', tracking= True)
    reference = fields.Char('Reference', index = 'trigram', tracking= True)
    employee_id = fields.Many2one('hr.employee', string='Mentor', index = True, tracking= True)
    employee_ids = fields.Many2many('hr.employee', 'course_subject_mentor_rel', 
                                    'course_subject_id', 'employee_id',
                                    string='Mentor', index = True, tracking= True)
    sale_price = fields.Monetary('Sale Price', currency_field='currency_id')
    description = fields.Text('Description', copy=False)
    product_id = fields.Many2one('product.product', string='Product', index= True)
    subject_line_ids = fields.One2many('course.subject.line', 'course_subject_id', string='Subject Line')
    
    
class CourseSubjectLibe(models.Model):
    _name = 'course.subject.line'
    _description = 'Course Subject Line'

    name = fields.Char(string='Description')
    course_subject_id = fields.Many2one('course.subject', string='Course Subject')