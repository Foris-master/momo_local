# Generated by Django 2.1.7 on 2019-03-25 16:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.CharField(max_length=20)),
                ('is_int', models.BooleanField(default=False)),
                ('order', models.IntegerField()),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='Operator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('tag', models.CharField(max_length=10, unique=True)),
                ('country', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('updated_at',),
            },
        ),
        migrations.CreateModel(
            name='Proof',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('mno_id', models.CharField(max_length=100)),
                ('metadata', models.CharField(blank=True, max_length=255)),
                ('mno_respond', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('updated_at',),
            },
        ),
        migrations.CreateModel(
            name='Sms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('metadata', models.CharField(max_length=255, null=True)),
                ('type', models.CharField(choices=[('partial', 'PARTIAL'), ('whole', 'WHOLE')], default='partial', max_length=25)),
                ('references', models.TextField(blank=True, null=True)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('updated_at',),
            },
        ),
        migrations.CreateModel(
            name='SmsMask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('updated_at',),
            },
        ),
        migrations.CreateModel(
            name='SmsSender',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sms', to='momo_server.Operator')),
            ],
            options={
                'ordering': ('updated_at',),
            },
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('state', models.CharField(choices=[('free', 'FREE'), ('busy', 'BUSY'), ('offline', 'OFFLINE')], default='offline', max_length=100)),
                ('phone_number', models.CharField(blank=True, max_length=14, null=True, unique=True)),
                ('imei', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('imsi', models.CharField(max_length=20, unique=True)),
                ('port', models.CharField(blank=True, max_length=20, null=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stations', to='momo_server.Operator')),
            ],
            options={
                'ordering': ('updated_at',),
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('track_id', models.CharField(max_length=20, unique=True)),
                ('is_deposit', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('new', 'NEW'), ('pending', 'PENDING'), ('paid', 'PAID'), ('proven', 'PROVEN'), ('cancel', 'CANCEL')], default='new', max_length=100)),
                ('recipient', models.CharField(max_length=14)),
                ('user', models.IntegerField()),
                ('mobile_wallet', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('created_at',),
            },
        ),
        migrations.AddField(
            model_name='smsmask',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='momo_server.SmsSender'),
        ),
        migrations.AddField(
            model_name='sms',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='momo_server.SmsSender'),
        ),
        migrations.AddField(
            model_name='sms',
            name='station',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='momo_server.Station'),
        ),
        migrations.AddField(
            model_name='proof',
            name='station',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='momo_server.Station'),
        ),
        migrations.AddField(
            model_name='proof',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='momo_server.Transaction'),
        ),
    ]
