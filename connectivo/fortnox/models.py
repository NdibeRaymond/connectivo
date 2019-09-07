from django.db import models

# Create your models here.

class lastSyncedRecord(models.Model):
    document_number = models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return self.document_number
