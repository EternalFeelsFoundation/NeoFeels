import os

os.system("apt-get update")
os.system("apt-get install python && apt-get install python-pip")
os.system("pip install -r requirements.txt")
os.system("cp ./posts/models_no_tags.py ./posts/models.py")
os.system("python manage.py makemigrations && python manage.py migrate")
os.system("cp ./models_with_tags.py ./posts.models.py")
# os.system("python manage.py makemigrations && python manage.py migrate")
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "feelday.settings")
django.setup()

from posts.models import Count
c = Count(upd=0)
c.save()

os.system("python manage.py createsuperuser")
print("Run: python manage.py runserver 0.0.0.0:80")
