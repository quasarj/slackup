from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django import forms
from django.http import HttpResponseRedirect
from zipfile import ZipFile
from archive.models import *
import json
import os
from datetime import datetime, timezone

# Create your views here.
class MessageSearchForm(forms.Form):
    text = forms.CharField()

def base_context(request):
    d = {}
    if request.user.is_authenticated():
        d['channels'] = Channel.objects.all().order_by('name')
        d['users'] = SUser.objects.all()
    else:
        d['channels'] = []
        d['users'] = []
    search = MessageSearchForm()
    d['search_form'] = search
    return d

def home(request):
    d = {}
    d['message_count'] = Message.objects.count()
    return render(request, 'archive/home.html', d)

@login_required
def channel_full(request, channel_name):
    channel = Channel.objects.get(name=channel_name)
    all_messages = Message.objects.filter(channel=channel).order_by('timestamp')
    paginator = Paginator(all_messages, 1000)

    page = request.GET.get('page')
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    prev = None
    for message in messages:
        message.prev = prev
        prev = message.user

    d = {}
    d['messages'] = messages
    d['channel'] = channel
    return render(request, 'archive/channel.html', d)

class UploadFileForm(forms.Form):
    file = forms.FileField()

@login_required
def search(request):
    if request.method == 'POST':
        form = MessageSearchForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['text']
            messages = Message.objects.filter(text__icontains=search_term)
            return render(request, 'archive/search.html', {'messages': messages,
                                                           'search_term': search_term,
                                                           'num_results': len(messages)})
    return HttpResponseRedirect('/')

@login_required
def upload_archive(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            process_archive(request.FILES['file'])
            return HttpResponseRedirect('/')
    else:
        form = UploadFileForm()
    return render(request, 'archive/upload.html', {'form': form})

def normally_formed(message, users):
    if message['type'] != 'message':
        return False
    if 'user' not in message:
        return False
    if message['user'] not in users:
        return False
    if 'subtype' in message and message['subtype'] != 'file_share':
        return False
    return True

def process_users(user_json):
    users = json.load(user_json)
    for user in users:
        u, created = SUser.objects.get_or_create(pk=user['id'],
                                                 name = user['name'],
                                                 color = user['color'],
                                                 real_name = user['real_name'])
        if 'image_original' in user['profile']:
            u.image = user['profile']['image_original'].replace('original', '{}')
        if 'title' in user['profile']:
            u.title = user['profile']['title']
        u.save()

def process_channels(channel_json):
    channels = json.load(channel_json)
    for channel in channels:
        c, created = Channel.objects.get_or_create(pk=channel['id'],
                                                   name = channel['name'],
                                                   is_archived = channel['is_archived'])
        if 'value' in channel['topic']:
            c.topic = channel['topic']['value']
        if 'value' in channel['purpose']:
            c.purpose = channel['purpose']['value']
        c.save()

def process_file(file_share):
    f, created = File.objects.get_or_create(pk=file_share['id'],
                                           url=file_share['url_private'],
                                           filetype=file_share['filetype'])
    if 'name' in file_share:
        f.name = file_share['name']
    if 'title' in file_share:
        f.title = file_share['title']
    f.save()
    return f

def process_message_day(messages, users, c):
    for m in messages:
        if normally_formed(m, users):
            ts_hash = "{}{}".format(m['user'], m['ts'])
            time = datetime.fromtimestamp(float(m['ts']), timezone.utc)
            message, created = Message.objects.get_or_create(pk=ts_hash,
                                                             user = users[m['user']],
                                                             text = m['text'],
                                                             timestamp = time,
                                                             channel = c)
            if 'subtype' in m and m['subtype'] == 'file_share':
                message.file_upload = process_file(m['file'])
                message.save()

def process_archive(archive):
    with open('archive.zip', 'wb+') as dest:
        for chunk in archive.chunks():
            dest.write(chunk)
    with ZipFile('archive.zip') as zipfile:
        zipfile.extractall('to_process')
    with open('to_process/users.json') as user_json:
        process_users(user_json)
    with open('to_process/channels.json') as channel_json:
        process_channels(channel_json)
    for root, dirs, files in os.walk('to_process'):
        if root != 'to_process':
            c = Channel.objects.get(name=os.path.basename(root))
            users = {}
            for u in SUser.objects.all():
                users[u.id] = u
            for f in files:
                with open(os.path.join(root, f)) as day_file:
                    messages = json.load(day_file)
                    process_message_day(messages, users, c)
