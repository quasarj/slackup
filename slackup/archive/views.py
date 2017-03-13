from django.shortcuts import render
from django import forms
from django.http import HttpResponseRedirect
from zipfile import ZipFile
from archive.models import *
import json

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
                u.image = user['profile']['image_original'].replace('original', '\{\}')
            if 'title' in user['profile']:
                u.title = user['profile']['title']
            u.real_name = user['real_name']
            u.save()
