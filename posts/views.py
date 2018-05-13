from django.shortcuts import render, render_to_response

from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.template import loader, RequestContext

from posts.models import Post, Vote, Ban, AntiSpamHash, Log, Tag, Count, ConfirmedMeme, PotentialMeme
from posts.models import PostForm, PostReplyForm, BanForm, MemeForm
from posts.models import is_banned

from django.contrib.admin.models import LogEntry, DELETION, ADDITION
from django.contrib.contenttypes.models import ContentType

from django.views.decorators.csrf import csrf_protect

from django.core.exceptions import ValidationError

import socket, struct

import datetime

import re

import pdb

# Reverse resolution of URLs
# e.g. reverse('posts.views.index') => '/'
from django.core.urlresolvers import reverse

# Pagination (https://docs.djangoproject.com/en/1.6/topics/pagination/)
from django.core.paginator import PageNotAnInteger, EmptyPage

from digg_paginator import DiggPaginator as Paginator

from django.core.paginator import Paginator as OldPaginator

# JSON for AJAX interaction
import json
import hashlib
from django.utils import timezone

import pdb

import hashlib

# Loaders are used to load templates from the templates dir.

YOUTUBE_REGEX = (r'(https?://)?(www\.)?'
                 '(youtube|youtu|youtube-nocookie)\.(com|be)/'
                 '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')


def index(request):
    """The home page. It displays a list of the most recent posts.
    Morover, it handles POST requests from Post forms."""
    if request.POST:
        ipaddr = request.META.get('REMOTE_ADDR')
        st = timezone.now() - datetime.timedelta(hours=24)
        et = timezone.now()
        upd = len(Post.objects.filter(time__range=(st, et)).order_by().values_list('ipaddr').distinct())
        cob = Count.objects.get(id=1)
        cob.upd = upd
        cob.save()
        if is_banned(ipaddr): return HttpResponseRedirect('/banned')
        post_form = PostForm(request.POST)

        if post_form.is_valid():
            youtube_id = None
            body = post_form.cleaned_data['body']
            try:
                youtube = post_form.cleaned_data['youtube']
                if youtube != '':
                    youtube_match = re.search(YOUTUBE_REGEX, youtube)
                    if youtube_match:
                        youtube_id = youtube_match.group(6)
                    else:
                        return HttpResponse("Invalid Youtube URL")
            except:
                pass

            if body.count('\r\n') > 30:
                return HttpResponse("Your feel is too tall.")
            if is_spam(body): return HttpResponseRedirect('/')

            # contains a blacklist to check against
            blacklist = [".it", ".ru", "itquest", "autoking", "mehrotra", "ekzoplugin", "gcsupplies", ".mx",
                         "avsquires"]

            time_threshold = timezone.now() - datetime.timedelta(seconds=3)
            spam_threshold = timezone.now() - datetime.timedelta(days=3)
            if Post.objects.filter(time__gte=time_threshold, ipaddr=ipaddr).exists():
                return HttpResponse('You are feeling too fast.')

            if not Post.objects.filter(time__gte=spam_threshold, ipaddr=ipaddr).exists():
                if "http://" in body or "https://" in body or "[url=" in body or "[URL=" in body:
                    return HttpResponseRedirect("/")

            for bl in blacklist:
                if bl in body:
                    return HttpResponseRedirect("/")

            tag_text = post_form.cleaned_data['tag']
            hash = hashlib.sha1(ipaddr).hexdigest()[:10]
            p = Post(body=body, ipaddr=ipaddr, youtube=youtube_id, is_thread=True, hash=hash)
            p.save()
            tag = Tag(post=p, name=tag_text)
            tag.save()
            v = Vote(post=p, count=0)
            v.save()

            # Prevent duplicate posts
            h = AntiSpamHash(hash=body)
            h.create_hash()
            h.save()

            return HttpResponseRedirect('/submitted/')
    else:
        post_form = PostForm()

    sort = request.GET.get('sort')
    if sort:
        recent_posts = Post.objects.filter(tag__name=sort).order_by('-id')
    else:
        recent_posts = Post.objects.filter(is_thread=True).order_by('-id')

    search = request.GET.get('search')
    if search:
        recent_posts = recent_posts.filter(body__contains=search).order_by('-id')

    quick_reply = PostReplyForm()

    startTime = timezone.now() - datetime.timedelta(minutes=60)
    endTime = timezone.now()
    fph = len(Post.objects.filter(time__range=(startTime, endTime)))
    ban = request.GET.get('ban')
    banned = request.GET.get('banned')
    log = request.GET.get('log')
    paginator = Paginator(recent_posts, 15)  # Show 15 posts per page
    page = request.GET.get('page')
    try:
        if page:
            posts = paginator.page(page)
        else:
            posts = paginator.page(1)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        # if page is out of range, deliver last page of results
        posts = paginator.page(paginator.num_pages)
    except:
        posts = paginator.page(1)
    cob = Count.objects.get(id=1)

    ctx = RequestContext(request, {
        'posts': posts,
        'post_form': post_form,
        'quick_reply': quick_reply,
        'ban': ban,
        'log': log,
        'banned': banned,
        'fph': fph,
        'sort': sort,
        'cob': cob,
        'search': search
    })

    template = loader.get_template('posts/index.html')
    return HttpResponse(template.render(ctx))


def top_memes(request):
    if request.method == 'POST':
        form = MemeForm(request.POST)
        ipaddr = request.META.get('REMOTE_ADDR')
        if is_banned(ipaddr): return HttpResponseRedirect('/banned')
        if form.is_valid():
            meme = form.cleaned_data['meme']
            time_threshold = timezone.now() - datetime.timedelta(seconds=30)
            if PotentialMeme.objects.filter(time__gte=time_threshold, ipaddr=ipaddr).exists():
                valid = "too_fast"
            else:
                valid = "valid"
                new_meme = PotentialMeme(ipaddr=ipaddr, meme=meme)
                new_meme.save()
        else:
            valid = "invalid"

    else:
        form = MemeForm()
        valid = None

    memes = ConfirmedMeme.objects.all()
    top_five = memes.order_by('-score')[:5]
    ctx = RequestContext(request, {
        'memes': memes,
        'form': form,
        'valid': valid,
        'top_five': top_five,
    })

    template = loader.get_template('posts/top_meme.html')

    return HttpResponse(template.render(ctx))


def rules(request):
    ctx = RequestContext(request, {
        'test': None,
    })

    template = loader.get_template('posts/rules.html')

    return HttpResponse(template.render(ctx))


def pages(request):
    recent_posts = Post.objects.filter(is_thread=True).order_by('-id')
    paginator = OldPaginator(recent_posts, 15)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        # if page is out of range, deliver last page of results
        posts = paginator.page(paginator.num_pages)

    return render_to_response('posts/pages.html', locals())


def quick_reply(request):
    if request.method == 'POST':
        form = PostReplyForm(request.POST)
        ipaddr = request.META.get('REMOTE_ADDR')
        if is_banned(ipaddr): return HttpResponseRedirect('/banned')

        blacklist = [".it", ".ru", "itquest", "autoking", "mehrotra", "ekzoplugin", "gcsupplies", ".mx", "avsquires"]

        spam_threshold = timezone.now() - datetime.timedelta(days=3)

        if form.is_valid():
            body = form.cleaned_data['body']
            if body.count('\r\n') > 30:
                return HttpResponse("Your feel is too tall.")
            thread = form.cleaned_data['thread']
            if is_spam(body): return HttpResponseRedirect('/')
            thread = Post.objects.get(id=int(thread))
            time_threshold = timezone.now() - datetime.timedelta(seconds=30)
            ipaddr = request.META.get('REMOTE_ADDR')
            if Post.objects.filter(time__gte=time_threshold, ipaddr=ipaddr).exists():
                return HttpResponse('You are feeling too fast.')

            if not Post.objects.filter(time__gte=spam_threshold, ipaddr=ipaddr).exists():
                if "http://" in body or "https://" in body or "[url=" in body or "[URL=" in body:
                    return HttpResponseRedirect("/")

            for bl in blacklist:
                if bl in body:
                    return HttpResponseRedirect("/")
            if thread:
                hash = hashlib.sha1(ipaddr).hexdigest()[:10]
                p = Post(body=body, ipaddr=ipaddr, is_thread=False, thread=thread, hash=hash)
                p.save()
                return HttpResponseRedirect(reverse('posts.views.replies', args=(thread.id,)))
    else:
        form = PostForm()

    return HttpResponse(json.dumps({'success': 'false'}), content_type='text/json')


def redirect(request):
    return HttpResponseRedirect('/')


def replies(request, pid):
    """Displays a post with its set of foreign keyed posts.
    In other words, it displays a thread with its post replies.
    Moreover, it returns a form, allowing users to submit a reply."""
    if request.method == 'POST':
        if is_banned(request.META.get('REMOTE_ADDR')):
            return HttpResponseRedirect('/banned')
        post_form = PostForm(request.POST)
        if post_form.is_valid():

            blacklist = [".it", ".ru", "itquest", "autoking", "mehrotra", "ekzoplugin", "gcsupplies", ".mx",
                         "avsquires"]

            spam_threshold = timezone.now() - datetime.timedelta(days=3)

            body = post_form.cleaned_data['body']
            if body.count('\r\n') > 30:
                return HttpResponse("Your feel is too tall.")
            thread_id = request.POST['thread_id']
            try:
                # Select only valid threads
                post = Post.objects.get(pk=thread_id, is_thread=True)
            except (KeyError, Post.DoesNotExist):
                raise Http404()
            time_threshold = timezone.now() - datetime.timedelta(seconds=3)
            ipaddr = request.META.get('REMOTE_ADDR')
            if Post.objects.filter(time__gte=time_threshold, ipaddr=ipaddr).exists():
                return HttpResponse('You are feeling too fast.')

            if not Post.objects.filter(time__gte=spam_threshold, ipaddr=ipaddr).exists():
                if "http://" in body or "https://" in body or "[url=" in body or "[URL=" in body:
                    return HttpResponseRedirect("/")

            for bl in blacklist:
                if bl in body:
                    return HttpResponseRedirect("/")

            hash = hashlib.sha1(ipaddr).hexdigest()[:10]
            # Create new post under the given thread
            post.post_set.create(
                body=body, ipaddr=request.META.get('REMOTE_ADDR'), is_thread=False, hash=hash)
            # No need to call save(). It's already saved.

            return HttpResponseRedirect(reverse('posts.views.replies', args=(pid,)))
    try:
        # Find request thread
        p = Post.objects.get(pk=pid, is_thread=True)
    except Post.DoesNotExist:
        raise Http404

    try:
        youtube_id = p.youtube
    except:
        youtube_id = None

    post_form = PostForm()
    if youtube_id:
        return render(request, 'posts/replies.html', {
            'post': p,
            'post_form': post_form,
            'youtube': youtube_id,
        })
    else:
        return render(request, 'posts/replies.html', {
            'post': p,
            'post_form': post_form,
        })


def book(request):
    all_objects = []
    llist = [{16: 'December 2014'}, {20: 'January 2015'}, {4616: 'February 2015'},
             {12845: 'March 2015'}, {18322: 'April 2015'}, {24491: 'May 2015'}, {34965: 'June 2015'},
             {47008: 'July 2015'}, {58772: 'August 2015'}, {75987: 'September 2015'},
             {92092: 'October 2015'}, {107332: 'November 2015'}, {123324: 'December 2015'},
             {138684: 'January 2016'}, {158411: 'February 2016'}, {172125: 'March 2016'}, {999999999999: 'wew lad'}]
    threads = Post.objects.filter(thread=None)
    x = 0
    new_month = ["", []]
    for thread in threads:
        if thread.id == llist[x].keys()[0]:
            x += 1
            if len(new_month) != 0:
                all_objects.append(new_month)
            new_month = [str(llist[x-1][llist[x-1].keys()[0]]), [thread]]
        else:
            new_month[1].append(thread)

    return render(request, 'book.html', {
        'all_objects': all_objects
    })


# Generate limits for book
def get_limits(request):
    threads = Post.objects.filter(thread=None)
    limit_list = []
    new_limit = 0
    monthDict = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

    x = 0
    for thread in threads:
        if thread.time.year == 2014:
            if x <= thread.time.month < x + 1:
                pass
            else:
                limit_list.append({thread.id: monthDict[int(thread.time.month)] + " 2014"})
                x += 1
        else:
            pass

    x = 0
    for thread in threads:
        if thread.time.year == 2015:
            if x <= thread.time.month < x + 1:
                pass
            else:
                limit_list.append({thread.id: monthDict[int(thread.time.month)] + " 2015"})
                new_limit = thread.id
                x += 1
        else:
            pass

    x = 0
    for thread in threads:
        if thread.time.year == 2016:
            if x <= thread.time.month < x + 1:
                pass
            else:
                if thread.id > new_limit:
                    limit_list.append({thread.id: monthDict[int(thread.time.month)] + " 2016"})
                    x += 1
        else:
            pass

    return HttpResponse(str(limit_list))


def most_replied(request):
    paginator = Paginator(most_replied, 10)  # Show 10 posts per page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        # if page is out of range, deliver last page of results
        posts = paginator.page(paginator.num_pages)

    ctx = RequestContext(request, {
        'posts': posts,
    })

    template = loader.get_template('posts/index.html')
    return HttpResponse(template.render(ctx))


def banned(request):
    ipaddr = request.META.get('REMOTE_ADDR')
    ban = Ban.objects.get(ipaddr=ipaddr)

    return render(request, 'posts/banned.html', {'ban': ban})


def is_spam(body):
    hash = hashlib.sha1(body.encode('utf-8')).hexdigest()
    try:
        h = AntiSpamHash.objects.get(hash=hash)
    except AntiSpamHash.DoesNotExist:
        return False
    return True


def memes_mod(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        meme_id = int(request.POST['pmeme'])
        action = str(request.POST['action'])
        if action == 'dismiss':
            meme = PotentialMeme.objects.get(id=meme_id)
            meme.delete()
        elif action == 'dismiss_by_ip':
            meme = PotentialMeme.objects.get(id=meme_id)
            ip = meme.ipaddr
            all_memes = PotentialMeme.objects.filter(ipaddr=ip)
            for todel in all_memes:
                todel.delete()
        elif action == 'approve':
            meme = PotentialMeme.objects.get(id=meme_id)
            toadd = ConfirmedMeme(meme=meme.meme, score=0)
            toadd.save()
            meme.delete()
        else:
            return HttpResponse('Invalid')
    pmemes = PotentialMeme.objects.all()
    cmemes = ConfirmedMeme.objects.all()

    ctx = RequestContext(request, {
        'pmemes': pmemes,
        'cmemes': cmemes,

    })

    template = loader.get_template('posts/memes_mod.html')

    return HttpResponse(template.render(ctx))


@csrf_protect
def mod(request):
    if not request.user.is_authenticated() or request.method != 'POST':
        return HttpResponseRedirect('/')

    if request.POST.get('action') == 'delete':
        id = request.POST.get('id')
        if id.isdigit():
            obj = Post.objects.get(id=id)
            Post.objects.filter(id=id).delete()
            log = Log(ipaddr=request.META.get('REMOTE_ADDR'),
                      time=timezone.now(),
                      text="Deleted post #" + unicode(obj.id) + " (" + unicode(obj.body[0:30]) + ")",
                      name=request.user)
            log.save()
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(Post).pk,
                object_id=obj,
                object_repr=unicode(obj.body[0:15]),
                action_flag=DELETION)

            if request.POST.get('reply') == '1' or "page" in request.META.get('HTTP_REFERER'):
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            return HttpResponseRedirect('/')
        else:
            return HttpResponseRedirect('/')

    if request.POST.get('action') == 'cap':
        id = request.POST.get('id')
        if id.isdigit():
            obj = Post.objects.get(id=id)
            to_cap = Post.objects.get(id=id)
            to_cap.capcode = True
            to_cap.save()
            log = Log(ipaddr=request.META.get('REMOTE_ADDR'),
                      time=timezone.now(),
                      text="Capped post: " + unicode(obj.id) + " (" + unicode(obj.body[0:30]) + ")",
                      name=request.user)
            log.save()

            if request.POST.get('reply') == '1' or "page" in request.META.get('HTTP_REFERER'):
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            return HttpResponseRedirect('/')
        else:
            return HttpResponseRedirect('/')

    if request.POST.get('action') == 'deleteban':
        id = request.POST.get('id')
        if id.isdigit():
            obj = Ban.objects.get(id=id)
            Ban.objects.filter(id=id).delete()
            log = Log(ipaddr=request.META.get('REMOTE_ADDR'),
                      time=timezone.now(),
                      text="Removed ban #" + unicode(obj.id) + " for " + unicode(obj.ipaddr),
                      name=request.user)
            log.save()
            LogEntry.objects.log_action(user_id=request.user.id,
                                        content_type_id=ContentType.objects.get_for_model(Ban).pk,
                                        object_id=obj.id,
                                        object_repr=unicode(obj.ipaddr),
                                        action_flag=DELETION)
        if "page" in request.META.get('HTTP_REFERER'):
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        return HttpResponseRedirect('/moderation')

    if request.POST.get('action') == 'ban':
        # The ban form class should validate ALL fields.
        ban_form = BanForm(request.POST)

        if ban_form.is_valid():
            post = Post.objects.get(id=ban_form.cleaned_data['post_id'])

            if is_banned(post.ipaddr):
                if "page" in request.META.get('HTTP_REFERER'):
                    referer = request.META.get('HTTP_REFERER').strip('&banned=true')
                    return HttpResponseRedirect(referer + '&banned=true')
                else:
                    return HttpResponseRedirect('/?banned=true')
            duration = request.POST.get('duration')
            if duration:
                ban_duration = " for " + " ".join("{}{}".format(m.group()[:-1],
                                                                {'d': ' days', 'm': ' minutes', 'h': ' hours',
                                                                 'w': ' weeks', 'y': ' years'}[m.group()[-1]]) for m in
                                                  re.finditer('([0-9]+[a-z])', str(duration)))
            else:
                ban_duration = " permanently"
            ban = Ban(ipaddr=post.ipaddr,
                      time=timezone.now(),
                      name=request.user,
                      expiration=ban_form.cleaned_data['duration'],
                      reason=ban_form.cleaned_data['reason'],
                      post=post)
            ban.save()
            log = Log(ipaddr=request.META.get('REMOTE_ADDR'),
                      time=timezone.now(),
                      text="Banned " + unicode(post.ipaddr) + unicode(ban_duration) + " because " + unicode(
                          ban_form.cleaned_data['reason']),
                      name=request.user,
                      post=post)
            log.save()
            LogEntry.objects.log_action(user_id=request.user.id,
                                        content_type_id=ContentType.objects.get_for_model(Ban).pk,
                                        object_id=ban.id,
                                        object_repr=unicode(ban.ipaddr),
                                        action_flag=ADDITION)

            if ban_form.cleaned_data['delete']:
                post.delete()

            if "page" in request.META.get('HTTP_REFERER'):
                referer = request.META.get('HTTP_REFERER').strip('&ban=true')
                referer = referer.strip('&banned=true')
                return HttpResponseRedirect(referer + '&ban=true')

            return HttpResponseRedirect('/?ban=true')
        else:
            # TODO(anachronos): Return ban_form when the form is invalid.
            return HttpResponse('There was an error in the form.')

    return HttpResponseRedirect('/')


@csrf_protect
def moderation(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    page = request.GET.get('page')
    if not request.GET.get("log"):
        bans = Ban.objects.all().order_by('-id')
        paginator = Paginator(bans, 10)  # Show 10 posts per page
        try:
            if page:
                bans = paginator.page(page)
            else:
                bans = paginator.page(1)
        except PageNotAnInteger:
            bans = paginator.page(1)
        except EmptyPage:
            # if page is out of range, deliver last page of results
            bans = paginator.page(paginator.num_pages)
        except:
            bans = paginator.page(1)

        ctx = RequestContext(request, {
            'bans': bans,
        })

    if request.GET.get("log"):
        logs = Log.objects.all().order_by('-id')
        paginator = Paginator(logs, 10)  # Show 10 posts per page
        try:
            if page:
                logs = paginator.page(page)
            else:
                logs = paginator.page(1)
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            # if page is out of range, deliver last page of results
            logs = paginator.page(paginator.num_pages)
        except:
            logs = paginator.page(1)

        ctx = RequestContext(request, {
            'logs': logs
        })

    template = loader.get_template('posts/moderation.html')
    return HttpResponse(template.render(ctx))


def generate_datagraph(request):
    f = open("wow.csv", 'r+')
    for month in range(1, 11):
        for day in range(1, 32):
            if month < 10:
                if day < 10:
                    csv_date = '20150' + str(month) + '0' + str(day)
                    s_data_date = '2015-0' + str(month) + '-0' + str(day)
                    e_data_date = '2015-0' + str(month) + '-0' + str(day + 1)
                else:
                    csv_date = '20150' + str(month) + str(day)
                    s_data_date = '2015-0' + str(month) + '-' + str(day)
                    e_data_date = '2015-0' + str(month) + '-' + str(day + 1)

            else:
                if day < 10:
                    csv_date = '2015' + str(month) + '0' + str(day)
                    s_data_date = '2015-' + str(month) + '-0' + str(day)
                    e_data_date = '2015-' + str(month) + '-0' + str(day + 1)

                else:
                    csv_date = '2015' + str(month) + str(day)
                    s_data_date = '2015-' + str(month) + '-' + str(day)
                    e_data_date = '2015-' + str(month) + '-' + str(day + 1)

            try:
                feelsday = len(Post.objects.filter(time__range=[s_data_date, e_data_date]))
                line = csv_date + ',' + str(feelsday)
                f.write(line + '\n')
            except:
                pass
    f.close()


def stats_json(request):
    fph = len(Post.objects.filter(time__range=(timezone.now() - datetime.timedelta(minutes=60), timezone.now())))
    fpd = len(Post.objects.filter(time__range=(timezone.now() - datetime.timedelta(hours=24), timezone.now())))
    upd = len(Post.objects.filter(
        time__range=(timezone.now() - datetime.timedelta(hours=24), timezone.now())).order_by().values_list(
        'ipaddr').distinct())
    return JsonResponse({'fph': fph, 'fpd': fpd, 'upd': upd})


def latest_json(request):
    thread = Post.objects.filter(is_thread=True).order_by('-id')[0]
    feel = Post.objects.order_by('-id')[0]
    return JsonResponse({'latest_thread': thread.body, 'latest_feel': feel.body})


def stats(request):
    return render(request, 'posts/stats.html')


def reported(request):
    if request.method == 'POST':
        pass

    else:
        return Http404


def upload_image(request):
    pdb.set_trace()


def search_view(request):
    ctx = RequestContext(request, {
        'banned': banned,
    })

    template = loader.get_template('posts/search.html')
    return HttpResponse(template.render(ctx))


def comments(request):
    sort = request.GET.get('sort')
    recent_posts = Post.objects.filter(is_thread=False).order_by('-id')

    search = request.GET.get('search')
    if search:
        recent_posts = recent_posts.filter(body__contains=search).order_by('-id')

    startTime = timezone.now() - datetime.timedelta(minutes=60)
    endTime = timezone.now()
    fph = len(Post.objects.filter(time__range=(startTime, endTime)))
    ban = request.GET.get('ban')
    banned = request.GET.get('banned')
    log = request.GET.get('log')
    paginator = Paginator(recent_posts, 15)  # Show 10 posts per page
    page = request.GET.get('page')
    try:
        if page:
            posts = paginator.page(page)
        else:
            posts = paginator.page(1)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        # if page is out of range, deliver last page of results
        posts = paginator.page(paginator.num_pages)
    except:
        posts = paginator.page(1)
    cob = Count.objects.get(id=1)

    ctx = RequestContext(request, {
        'posts': posts,
        'quick_reply': quick_reply,
        'ban': ban,
        'log': log,
        'banned': banned,
        'fph': fph,
        'sort': sort,
        'cob': cob,
        'search': search
    })

    template = loader.get_template('posts/comments.html')
    return HttpResponse(template.render(ctx))
