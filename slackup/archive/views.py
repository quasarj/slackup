from django.shortcuts import render
from django import forms
from django.http import HttpResponseRedirect
from zipfile import ZipFile
from archive.models import *
import json
import os

# Create your views here.
class UploadFileForm(forms.Form):
    file = forms.FileField()

def upload_archive(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            process_archive(request.FILES['file'])
            return HttpResponseRedirect('/')
    else:
        form = UploadFileForm()
    return render(request, 'archive/upload.html', {'form': form})

def process_archive(archive):
    with open('archive.zip', 'wb+') as dest:
        for chunk in archive.chunks():
            dest.write(chunk)
    with ZipFile('archive.zip') as zipfile:
        zipfile.extractall('to_process')
    with open('to_process/users.json') as user_json:
        users = json.load(user_json)
        for user in users:
            u, created = SUser.objects.get_or_create(pk=user['id'])
            u.name = user['name']
            u.color = user['color']
            if 'image_original' in user['profile']:
                u.image = user['profile']['image_original'].replace('original', '{}')
            if 'title' in user['profile']:
                u.title = user['profile']['title']
            u.real_name = user['real_name']
            u.save()
    with open('to_process/channels.json') as channel_json:
        channels = json.load(channel_json)
        for channel in channels:
            c, created = Channel.objects.get_or_create(pk=channel['id'])
            c.name = channel['name']
            c.is_archived = channel['is_archived']
            if 'value' in channel['topic']:
                c.topic = channel['topic']['value']
            if 'value' in channel['purpose']:
                c.purpose = channel['purpose']['value']
            c.save()
    for root, dirs, files in os.walk('to_process'):
        if root != 'to_process':
            c = Channel.objects.get(name=os.path.basename(root))
            users = {}
            for u in SUser.objects.all():
                users[u.id] = u
            for f in files:
                with open(f) as day_file:
                    m = json.load(day_file)
                    ts_hash = t
                    message = Message.objects.create()
                    message.user = users[m['user']]
                    message.text = m['text']
                    message.channel = c
                    message.save()
