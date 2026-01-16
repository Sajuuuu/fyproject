from django.urls import path
from . import views
urlpatterns = [
    path('', views.home,name='home'),
    path('index', views.index,name='index'),
    path('about',views.home,name='about'),
    path('add/<int:a>/<int:b>', views.add,name='add'),
    path('intro/<str:name>/<int:age>',views.intro,name='intro'),
    path('second',views.second,name='second'),
    path('third',views.third,name='third'),
    path('image',views.image,name='image'),
    path('form',views.form,name='form'),
    path('submitmyform',views.submitmyform,name='submitmyform'),
    

]