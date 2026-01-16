from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
# Create your views here.
def home (request):
    return render (request,'index.html')


def index(request):
  return HttpResponse('hello world')

def about(request):
  return HttpResponse(' about response')

def add(request,a,b):
  return HttpResponse(a+b)

def intro(request,name,age):
   mydictionary={
      "Name":name,
      "Age":age
   }
   return JsonResponse(mydictionary)

def second(request):
   return render(request,'second.html')

def third(request):
   var="Hello World"
   greetings= "Hey! how are you?"
   fruits =['apple','mango','litichi','grapes']
   num1,num2 =5,7
   ans = num1 >num2

   mydictionary = {
      "var": var,
      "msg": greetings,
      "myfruits": fruits,
      "num1": num1,
      "num2": num2,
      "ans": ans,
      
   }
   return render(request,'third.html',context=mydictionary)

def image(request):
   return render(request,'imagepage.html')

def form(request):
   return render(request,'myform.html')


def submitmyform(request):
   mydictionary = {
      "Name":request.GET['username'],
      "Password":request.GET['pass'],
      "Method": request.method
   }
   return JsonResponse(mydictionary)

