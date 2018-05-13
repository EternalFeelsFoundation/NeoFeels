from celery import Celery
from posts.models import Post, ConfirmedMeme
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from datetime import datetime, timedelta

"""
proto_memes = ['JDIMSA', 'scruffers', 'wew lad', 'lexi', 'hunter', 'ruben', 'miranda', 'burger', 'ladmin',
               'butthurt', 'kill ursell', 'chocos', 'chadmin', 'boipussy', 'goypu$$y', 'volcel',
               'chadtango', 'baby sis', 'scrot', 'queer fuck', 'wee slut', 'hapa', 'dank', 'tbh', 'oaky coffee',
                'BLACKED', 'EAT THE BOOTY LIKE GROCERIES', 'wizard', 'ELWAYS', 'Noblemen', 'reddit', 'honk honk']
"""

celery = Celery('tasks',
                backend='djcelery.backends.database.DatabaseBackend',
                broker='django://')


@periodic_task(run_every=crontab(hour="*", minute="*/2", day_of_week="*"))
def update_stats():
    f = open("wow.csv", 'r+')
    f.write("Date, Feels\n")
    for month in range(1, 12):
        for day in range(1, 33):
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
                if day < 9:
                    csv_date = '2015' + str(month) + '0' + str(day)
                    s_data_date = '2015-' + str(month) + '-0' + str(day)
                    e_data_date = '2015-' + str(month) + '-0' + str(day + 1)

                else:
                    csv_date = '2015' + str(month) + str(day)
                    s_data_date = '2015-' + str(month) + '-' + str(day)
                    e_data_date = '2015-' + str(month) + '-' + str(day + 1)

            try:
                try:
                    feel_day = len(Post.objects.filter(time__range=[s_data_date, e_data_date]))
                except:
                    if day > 11:
                        try:
                            if month < 9:
                                e_data_date = '2015-0' + str(month + 1) + '-01'
                            else:
                                e_data_date = '2015-' + str(month + 1) + '-01'

                            feel_day = len(Post.objects.filter(time__range=[s_data_date, e_data_date]))
                        except:
                            feel_day = 0
                    else:
                        feel_day = 0

                if feel_day == 0 and csv_date != "20151019" and csv_date != "20151018" and csv_date != "20151020":
                    pass
                else:
                    line = csv_date + ',' + str(feel_day)
                    f.write(line + '\n')

            except:
                pass
    f.close() 


def load_memes():
    memes = []
    proto_memes = ConfirmedMeme.objects.all()
    for meme in proto_memes:
        memes.append([meme.meme, []])
    return memes


@periodic_task(run_every=crontab(hour="*", minute="1", day_of_week="*"))
def top_memes():
    how_many_days = 3
    memes = load_memes()
    posts = Post.objects.filter(time__gte=datetime.now()-timedelta(days=how_many_days))
    for post in posts:
        text = post.body
        for meme in memes:
            if meme[0].lower() in text.lower():
                meme[1].append(post)
            else:
                pass

    for meme in memes:
        ip_usage = []
        for feel in meme[1]:
            if feel.ipaddr not in ip_usage:
                ip_usage.append(feel.ipaddr)
        spam_blocker = len(ip_usage) * 5
        if spam_blocker < len(meme[1]):
            meme[1] = spam_blocker
        else:
            meme[1] = len(meme[1])

    print str(memes)