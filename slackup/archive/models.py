from django.db import models

# Create your models here.
class Channel(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=22)
    topic = models.TextField(null=True)
    purpose = models.TextField(null=True)
    is_archived = models.NullBooleanField()

    def __str__(self):
        return self.name

class SUser(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=22)
    color = models.CharField(max_length=6)
    real_name = models.CharField(max_length=50)
    image = models.CharField(max_length=100, null=True)
    title = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name

    def get_image(self, size):
        return self.image.format(size)

class File(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)

class Message(models.Model):
    user = models.ForeignKey(SUser)
    channel = models.ForeignKey(Channel)
    timestap = models.DateTimeField()
    text = models.TextField()
    file_upload = models.ForeignKey(File, null=True)

    def __str__(self):
        return self.text
