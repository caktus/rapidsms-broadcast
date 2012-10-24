# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DateAttribute'
        db.create_table('broadcast_dateattribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('value', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=16)),
        ))
        db.send_create_signal('broadcast', ['DateAttribute'])

        # Adding unique constraint on 'DateAttribute', fields ['type', 'value']
        db.create_unique('broadcast_dateattribute', ['type', 'value'])

        # Adding model 'Broadcast'
        db.create_table('broadcast_broadcast', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_last_notified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('schedule_end_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('schedule_frequency', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=16, null=True, blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('broadcast', ['Broadcast'])

        # Adding M2M table for field weekdays on 'Broadcast'
        db.create_table('broadcast_broadcast_weekdays', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('broadcast', models.ForeignKey(orm['broadcast.broadcast'], null=False)),
            ('dateattribute', models.ForeignKey(orm['broadcast.dateattribute'], null=False))
        ))
        db.create_unique('broadcast_broadcast_weekdays', ['broadcast_id', 'dateattribute_id'])

        # Adding M2M table for field months on 'Broadcast'
        db.create_table('broadcast_broadcast_months', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('broadcast', models.ForeignKey(orm['broadcast.broadcast'], null=False)),
            ('dateattribute', models.ForeignKey(orm['broadcast.dateattribute'], null=False))
        ))
        db.create_unique('broadcast_broadcast_months', ['broadcast_id', 'dateattribute_id'])

        # Adding M2M table for field groups on 'Broadcast'
        db.create_table('broadcast_broadcast_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('broadcast', models.ForeignKey(orm['broadcast.broadcast'], null=False)),
            ('group', models.ForeignKey(orm['groups.group'], null=False))
        ))
        db.create_unique('broadcast_broadcast_groups', ['broadcast_id', 'group_id'])

        # Adding model 'BroadcastMessage'
        db.create_table('broadcast_broadcastmessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('broadcast', self.gf('django.db.models.fields.related.ForeignKey')(related_name='messages', to=orm['broadcast.Broadcast'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='broadcast_messages', to=orm['rapidsms.Contact'])),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_sent', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='queued', max_length=16, db_index=True)),
        ))
        db.send_create_signal('broadcast', ['BroadcastMessage'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'DateAttribute', fields ['type', 'value']
        db.delete_unique('broadcast_dateattribute', ['type', 'value'])

        # Deleting model 'DateAttribute'
        db.delete_table('broadcast_dateattribute')

        # Deleting model 'Broadcast'
        db.delete_table('broadcast_broadcast')

        # Removing M2M table for field weekdays on 'Broadcast'
        db.delete_table('broadcast_broadcast_weekdays')

        # Removing M2M table for field months on 'Broadcast'
        db.delete_table('broadcast_broadcast_months')

        # Removing M2M table for field groups on 'Broadcast'
        db.delete_table('broadcast_broadcast_groups')

        # Deleting model 'BroadcastMessage'
        db.delete_table('broadcast_broadcastmessage')


    models = {
        'broadcast.broadcast': {
            'Meta': {'object_name': 'Broadcast'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {}),
            'date_last_notified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'broadcasts'", 'symmetrical': 'False', 'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'months': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'broadcast_months'", 'blank': 'True', 'to': "orm['broadcast.DateAttribute']"}),
            'schedule_end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'schedule_frequency': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'weekdays': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'broadcast_weekdays'", 'blank': 'True', 'to': "orm['broadcast.DateAttribute']"})
        },
        'broadcast.broadcastmessage': {
            'Meta': {'object_name': 'BroadcastMessage'},
            'broadcast': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'messages'", 'to': "orm['broadcast.Broadcast']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {}),
            'date_sent': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'broadcast_messages'", 'to': "orm['rapidsms.Contact']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'queued'", 'max_length': '16', 'db_index': 'True'})
        },
        'broadcast.dateattribute': {
            'Meta': {'ordering': "('value',)", 'unique_together': "(('type', 'value'),)", 'object_name': 'DateAttribute'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'value': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'groups.group': {
            'Meta': {'object_name': 'Group'},
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['rapidsms.Contact']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['broadcast']
