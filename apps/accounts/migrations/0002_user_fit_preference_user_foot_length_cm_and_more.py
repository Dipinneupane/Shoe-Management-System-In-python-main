
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='fit_preference',
            field=models.CharField(choices=[('standard', 'Standard Fit'), ('snug', 'Snug Fit'), ('loose', 'Loose Fit')], default='standard', max_length=20),
        ),
        migrations.AddField(
            model_name='user',
            name='foot_length_cm',
            field=models.FloatField(blank=True, help_text='Foot length in cm', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='shoe_size_preference',
            field=models.CharField(blank=True, help_text='Preferred EU size', max_length=20),
        ),
    ]
