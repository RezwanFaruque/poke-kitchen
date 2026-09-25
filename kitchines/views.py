from django.shortcuts import render
from .models import Kitchen


# Create your views here.

def restaurants(request):
    kitchen_members = Kitchen.objects.all().values()
    return render(request, 'member.html',{'kitchen_members': kitchen_members})