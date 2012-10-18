#coding=utf-8
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User

from newstracker.account.models import Account
from forms import RegisterForm, LoginForm, UserForm

from libweibo.weiboAPI import weiboAPI
import re

_DEBUG = True
 
def register(request):
    template_var = {}
    form = RegisterForm()
    if request.method == "POST":
        form = RegisterForm(request.POST.copy())
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user_obj = User.objects.create_user(username, email, password)
            account = Account(user=user_obj)
            account.save()
            _login(request, username, password)  #注册完毕 直接登陆
            return HttpResponseRedirect("/")
        else:
            messages.add_message(request, messages.INFO, 'something is wrong')
            
    template_var["form"] = form
    return render_to_response("account/register.html",
            template_var,
            context_instance=RequestContext(request))

def login(request):
    template_var = {}
    ## 用户weibo登录的认证链接
    authorize_url = weiboAPI().getAuthorizeUrl()
    template_var['authorize_url'] = authorize_url
    
    form = LoginForm()    
    if request.method == 'POST':
        form = LoginForm(request.POST.copy())
        if form.is_valid():
            if _login(request,
                   form.cleaned_data["username"],
                   form.cleaned_data["password"]):
                return HttpResponseRedirect("/")
    template_var["form"] = form
    return render_to_response("account/login.html",
            template_var,
            context_instance=RequestContext(request))

def _login(request, name, password):
    ## check if name is email
    if re.match('^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', name):
        try:
            temp = User.objects.get(email=name)
        except (User.MultipleObjectsReturned, User.DoesNotExist):
            messages.add_message(request, messages.INFO, 'user not exist')
            return False
        else:
            name = temp.username
    user = authenticate(username=name, password=password)
    if user:
        if user.is_active:
            auth_login(request, user)
            return True
        else:
            messages.add_message(request, messages.INFO, 'user not activated or destroyed')
    else:
        messages.add_message(request, messages.INFO, 'user not exist or pwd is wrong')
    return False

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect('login/')

def userinfo(request):
    template_var = {}
    form = UserForm()
    if request.method ==  'POST':
        form = UserForm(request.POST.copy())
        if form.is_valid():
            User.objects.filter(id=request.user.id).update(username=form.cleaned_data["username"],
                                                            email=form.cleaned_data["email"])
    else :
        form = UserForm( initial = {'username':request.user.username, 'email':request.user.email})
    template_var["form"] = form
    return render_to_response("account/userinfo.html", template_var, context_instance=RequestContext(request))

def weiboLogin(request):
    code = request.GET.get('code')
    print code
#    print 'request'
#    print request
#    template_var = {}
#    authorize_url = weiboAPI().getAuthorizeUrl()
#    template_var['authorize_url'] = authorize_url
#    return render_to_response("account/login.html",
#            template_var,
#            context_instance=RequestContext(request))