# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-09-27 04:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carshare', '0005_auto_20170927_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='paid',
            field=models.BooleanField(default=False),
        ),
    ]
