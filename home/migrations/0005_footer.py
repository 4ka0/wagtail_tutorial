# Generated by Django 3.1.8 on 2021-05-06 05:40

from django.db import migrations, models
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_auto_20210506_0510'),
    ]

    operations = [
        migrations.CreateModel(
            name='Footer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', wagtail.core.fields.RichTextField(null=True)),
            ],
        ),
    ]
