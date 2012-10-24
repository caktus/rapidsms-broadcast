# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding unique constraint on 'ForwardingRule', fields ['keyword']
        db.create_unique('broadcast_forwardingrule', ['keyword'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'ForwardingRule', fields ['keyword']
        db.delete_unique('broadcast_forwardingrule', ['keyword'])


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
        'broadcast.forwardingrule': {
            'Meta': {'object_name': 'ForwardingRule'},
            'dest': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dest_rules'", 'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '160'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '160', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_rules'", 'to': "orm['groups.Group']"})
        },
        'groups.group': {
            'Meta': {'object_name': 'Group'},
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['rapidsms.Contact']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'primary_backend': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contact_primary'", 'null': 'True', 'to': "orm['rapidsms.Backend']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        }
    }

    complete_apps = ['broadcast']
