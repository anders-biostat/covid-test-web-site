from django.db import models

class Key(models.Model):
    key_name = models.CharField(max_length=50)
    public_key = models.TextField(null=False, blank=False)

    def __str__(self):
        return "Key: %s" % self.key_name