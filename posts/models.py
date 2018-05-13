from django.db import models
from django.utils.html import escape
from django import forms
import datetime
import hashlib
import re
from django.utils import timezone
from precise_bbcode.bbcode.tag import BBCodeTag
from precise_bbcode.tag_pool import tag_pool

"""
class SmallBBCodeTag(BBCodeTag):
    name = 'small'
    definition_string = '[small]{TEXT}[/small]'
    format_string = '<span style="font-size: 8px">{TEXT}</span>'

    class Options:
        render_embedded = True
        strip = False

tag_pool.register_tag(SmallBBCodeTag)


class BigBBCodeTag(BBCodeTag):
    name = 'big'
    definition_string = '[big]{TEXT}[/big]'
    format_string = '<span style="font-size: 28px">{TEXT}</span>'

    class Options:
        render_embedded = True
        strip = False

tag_pool.register_tag(BigBBCodeTag)


class ShakeBBCodeTag(BBCodeTag):
    name = 'shake'
    definition_string = '[shake]{TEXT}[/shake]'
    format_string = '<div class="shake shake-constant shake-constant--hover">{TEXT}</div>'

    class Options:
        render_embedded = False
        strip = False

tag_pool.register_tag(ShakeBBCodeTag)


class BlinkBBCodeTag(BBCodeTag):
    name = 'blink'
    definition_string = '[blink]{TEXT}[/blink]'
    format_string = '<span class="blink_me">{TEXT}</span>'

    class Options:
        render_embedded = False
        strip = False


tag_pool.register_tag(BlinkBBCodeTag)
"""

class Poll(models.Model):
    text = models.CharField(max_length=2500)
    timestamp = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)


class PollChoice(models.Model):
    text = models.CharField(max_length=1000)
    poll = models.ForeignKey(Poll)


class Reply(models.Model):
    ipaddr = models.GenericIPAddressField()
    poll = models.ForeignKey(Poll)
    choice = models.ForeignKey(PollChoice)
    timestamp = models.DateTimeField(auto_now_add=True)


class ConfirmedMeme(models.Model):
    meme = models.CharField(max_length=50)
    score = models.IntegerField()


class PotentialMeme(models.Model):
    ipaddr = models.IPAddressField(verbose_name="IP Address")
    time = models.DateTimeField(auto_now_add=True)
    meme = models.CharField(max_length=50)

"""
class SpoilerBBCodeTag(BBCodeTag):
    name = 'spoiler'
    definition_string = '[spoiler]{TEXT}[/spoiler]'
    format_string = '<span class="spoiler">{TEXT}</span>'

    class Options:
        render_embedded = False
        strip = False

tag_pool.register_tag(SpoilerBBCodeTag)
"""

class Count(models.Model):
    upd = models.IntegerField()


class Post(models.Model):
    """Post model encapsulates a post or thread.
    A thread is a post that has a set of reply posts."""
    time = models.DateTimeField(auto_now=True, verbose_name="Dated Posted")
    ipaddr = models.IPAddressField(verbose_name="IP Address")
    body = models.CharField(max_length=400)
    is_thread = models.BooleanField()
    thread = models.ForeignKey('Post', null=True, blank=True)
    capcode = models.BooleanField(default=False)
    hash = models.CharField(max_length=50, null=True, blank=True)
    youtube = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        if len(self.body) > 15:
            return self.body[0:14] + '...'
        else:
            return self.body

    def htmlBody(self):
        return escape(self.body)

    def vote_count(self):
        """post.vote_set returns a Related Manager
        https://docs.djangoproject.com/en/1.6/ref/models/relations/"""
        return self.vote_set.get().count

    @property
    def sorted_post_set(self):
        return self.post_set.order_by('time')


"""class PostManager(models.Manager):"""

# I commented this out because I needed to change the default
# widget of body
"""class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['body']"""


# Add report field to database
class Report(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    ipaddr = models.GenericIPAddressField()
    postID = models.ForeignKey(Post)

    def __str__(self):
        return '{}'.format(self.postID)


class ReportForm(forms.Form):
    reason = forms.CharField(max_length=100)


class MemeForm(forms.Form):
    meme = forms.CharField(max_length=50)


class PostForm(forms.Form):
    """PostForm defines the body field and its corresponding widget."""
    body = forms.CharField(widget=forms.Textarea, max_length=400)
    tag = forms.CharField(widget=forms.Textarea, max_length=12, required=False)
    youtube = forms.CharField(widget=forms.Textarea, max_length=100, required=False)


class DurationField(forms.Field):
    widget = forms.TextInput

    def to_python(self, value):
        """Convert a time length string (i.e. 4d5h) into a datetime object."""
        regex_pattern = re.compile(r'([0-9]+[y|w|d|h|m])')

        if not value:
            return None

        match = re.findall(regex_pattern, value)
        if not match:
            raise forms.ValidationError('Your duration input has an invalid format.')

        time_units = {
            'weeks': 'w',
            'years': 'y',
            'days': 'd',
            'hours': 'h',
            'minutes': 'm',
        }

        duration_units = {}

        # Map the individual durations into a dictionary
        for group in match:
            for name, unit in time_units.items():
                if group.find(unit) != -1:
                    duration_units[name] = int(re.sub(r'\w$', '', group))
                    break

        # Convert the duration units into a date in the future
        duration = timezone.now() + datetime.timedelta(**duration_units)
        return duration


class BanForm(forms.Form):
    post_id = forms.IntegerField()
    duration = DurationField(required=False)
    reason = forms.CharField(widget=forms.Textarea, max_length=150, required=False)
    delete = forms.BooleanField(required=False)


class PostReplyForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea, max_length=400)
    thread = forms.IntegerField(
        widget=forms.HiddenInput
    )


class Tag(models.Model):
    post = models.ForeignKey(Post)
    name = models.CharField(max_length=12)


class Ban(models.Model):
    ipaddr = models.GenericIPAddressField()
    time = models.DateTimeField(auto_now=True, verbose_name="Creation Date")
    expiration = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=128, null=True)
    reason = models.TextField()
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '{}'.format(self.ipaddr)


class Log(models.Model):
    ipaddr = models.GenericIPAddressField()
    time = models.DateTimeField(auto_now=True, verbose_name="Creation Date")
    name = models.CharField(max_length=128)
    text = models.TextField()
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '{}'.format(self.ipaddr)


class Vote(models.Model):
    """Unused for now"""
    post = models.ForeignKey(Post)
    count = models.IntegerField(default=0)

    def __str__(self):
        # Note about self.post: This is accessing an instance of the
        # post associated via the foreign key
        # https://docs.djangoproject.com/en/1.6/topics/db/queries/#related-objects
        return '{0} votes for {1}'.format(self.count, self.post)


class AntiSpamHash(models.Model):
    hash = models.CharField(max_length=40, unique=True)
    time = models.DateTimeField(auto_now=True, verbose_name="Time of Creation")

    def create_hash(self):
        """Call this function BEFORE save()."""
        self.hash = hashlib.sha1(self.hash.encode('utf-8')).hexdigest()


def is_banned(ipaddr):
    # banip = socket.inet_ntoa('c6f5329b'.decode('hex'))
    # banip = socket.inet_aton(ipaddr).encode('hex')
    # cursor = connections['tinyboard'].cursor()
    # future = datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    # expiration = str(calendar.timegm(future.timetuple()))
    # cursor.execute("SELECT ipstart FROM `bans` WHERE ipstart = %s AND (expires is NULL OR expires > %s)", (banip.decode('hex'),expiration,))
    # row = cursor.fetchone()
    # if row is not None:
    #   return HttpResponseRedirect("http://www.wizardchan.org/banned.php")
    b = Ban.objects.filter(ipaddr=ipaddr)
    if b:
        return True
    return False
