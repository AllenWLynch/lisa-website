from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import TextAreaField, BooleanField, SubmitField, SelectMultipleField, SelectField, StringField
from wtforms.validators import DataRequired, Required, length, optional, Email
from wtforms.fields.html5 import EmailField

class LISAForm(FlaskForm):
    genes = TextAreaField('Genes', validators=[Required()])
    labels = StringField('labels', validators=[optional()])

    genes2 = TextAreaField('Genes2', validators=[optional()])
    labels2 = StringField('labels 2', validators=[optional()])

    background = TextAreaField('Background', validators=[optional()])

    name = StringField('Job Name', validators=[optional()]) ## change to optional and give out a warning information
    mail = EmailField('Optional email', validators=[optional(), Email()])
    method = SelectField("Binding Data",
                         choices=[('chipseq', 'ChIP-seq'),
                                  ('motifs', 'Motif Hits')
                                ],
                         default='chipseq')

    species = SelectField("Species", choices=[('hg38', 'Human'), ('mm10', 'Mouse')], default='hg38')
