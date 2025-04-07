from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired

class DecisionForm(FlaskForm):
    decision = SelectField('Decision', choices=[
        ('', 'Select a decision'),
        ('approved', 'Approve (Fine Waived)'),
        ('rejected', 'Reject (Fine Must be Paid)')
    ], validators=[DataRequired()])
    reason = TextAreaField('Reason for Decision', validators=[DataRequired()], 
                         render_kw={"rows": 4})
