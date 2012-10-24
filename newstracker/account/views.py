#coding=utf-8
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User

from newstracker.account.models import Account
from forms import RegisterForm, LoginForm, UserForm

from libweibo.weiboAPI import weiboAPI
from djangodb import dbop

import re
import simplejson
import base64

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
    print dbop.Account.objects.all()
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
    # TODO: bug 目前还有错，不知道是哪儿的原因：
    # 用WeBless和新闻追踪００７可以正常登录，但是用ｚｚｙ和幸运女神的帐号登录就没有user_id!!!
    signed_request = request.POST.get('signed_request')
    # signed_request传到python这边, 数据结构是一个字符串型的list
    if isinstance(signed_request, list):
        signed_request = signed_request[0]
    encoded_sig, payload = signed_request.split(".", 2)

    # 余数2, 那么需要补一个=
    payload = str(payload)
    if len(payload)%3 == 2:
        payload += '='
    # 余数1, 那么需要补两个=  
    if len(payload)%3 == 1:
        payload += '=='
    # urlsafe_b64decode() Decode string s using a URL-safe alphabet, 
    # which substitutes - instead of + and _ instead of / in the standard Base64 alphabet.
    # 得到data    
    data = simplejson.loads(base64.urlsafe_b64decode(payload))
    
    # 得到sig
    encoded_sig = str(encoded_sig)
    if len(encoded_sig)%3 == 2:
        encoded_sig += '='
    if len(encoded_sig)%3 == 1:
        encoded_sig += '==' 
    sig = base64.urlsafe_b64decode(encoded_sig)

    try: 
        user_id = data['user_id']
        oauth_token = data['oauth_token']
        expires= data['expires']
    except:
        print '认证错误，这个错误还未解决！！！'
            
    if _DEBUG:
        print 'signed_request: ', signed_request
        print 'data: ',data
        print user_id
    
    ##判断用户是否已经登录过（第一次登录会自动帮用户注册）
    try:
        _account = Account.objects.get(weiboId = user_id)
    except:
        print 'create new Account for:'+str(user_id)
        _weibo = weiboAPI(oauth_token, expires, user_id)
        _account = dbop.get_or_create_account_from_weibo(_weibo.getUserInfo())
    
    _login(request, _account.user.username, _account.user.password)
    if _DEBUG:
        print 'login success: ' + str(user_id) + ' ' + _account.user.username
#        print 'request: ', request
    ## TODO: bug 这样登录后直接跳转到主页request.user.username是空的，而用户名密码直接登录就OK。。。为什么？？
    ## 目前把需要的参数通过ｕｒｌ传递过去。。。
    return HttpResponseRedirect('/topic_list/' + str(_account.id))

def call_back(request):
    code = request.GET.get('code')
    
    