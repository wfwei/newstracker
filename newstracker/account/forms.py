# coding=utf-8
from django import forms
from django.contrib.auth import models as auth_models


def _username_registered(self):
    '''check if the username is registered already'''
    users = auth_models.User.objects.filter(
            username__iexact=self.cleaned_data["username"])
    if users:
        return True
    return False

def _username_valid(self):
    if '@' in self.cleaned_data["username"]:
        return False
    return True


def _email_registered(self):
    '''check if the email has been registered already, django will check correctness；'''
    emails = auth_models.User.objects.filter(
            email__iexact=self.cleaned_data["email"])
    if emails:
        return True
    return False

class RegisterForm(forms.Form):
    '''form for user registeration'''
    email = forms.EmailField(label="Email", max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class':'class_email', }))
    password = forms.CharField(label="Password", max_length=100, widget=forms.PasswordInput(attrs={'size': 100, 'class':'class_password', }))
    username = forms.CharField(label="Nickname", max_length=30, widget=forms.TextInput(attrs={'size': 100, 'class':'class_username', }))

    def clean_username(self):
        if _username_valid(self):
            if _username_registered(self):
                raise forms.ValidationError("this name has been registered --!")
        else:
            raise forms.ValidationError("invalid charactor '@' ")
        return self.cleaned_data["username"]

    def clean_email(self):
        if _email_registered(self):
            raise forms.ValidationError("this email has been registered ==!")
        return self.cleaned_data["email"]

class LoginForm(forms.Form):
    '''form for user login'''
    username = forms.CharField(label="Login or Email", max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class':'class_username', }), error_messages={'required': 'Please enter your name'})
    password = forms.CharField(label="Password", max_length=100, widget=forms.PasswordInput(attrs={'size': 100, 'class':'class_password', }), error_messages={'required': 'Please enter your password'})

    def clean_username(self):
        '''this can be nikename or email addr, we do not check it here'''
        return self.cleaned_data["username"]

    def clean_password(self):
        return self.cleaned_data["password"]

class UserForm(forms.Form):
    '''form to show user info'''
    username = forms.CharField(label="Nickname", max_length=30, widget=forms.TextInput(attrs={'size': 100, 'class':'class_username', }))
    email = forms.EmailField(label="Email", max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class':'class_email', }))

    def clean_username(self):
        if _username_valid(self):
            if _username_registered(self):
                raise forms.ValidationError("this name has not been registered --!")
        else:
            raise forms.ValidationError("invalid charactor '@' ")
        return self.cleaned_data["username"]

    def clean_email(self):
        if _email_registered(self):
            raise forms.ValidationError("this email has been registered ==!")
        return self.cleaned_data["email"]

LimitChoice = (('1', '1 次'), ('2', '2 次'), ('3', '3 次'), ('5', '5 次'), ('8', '8 次'), ('10', '10 次'), ("1000", "不限制"))
class SettingForm(forms.Form):
    '''form to deal with user settings
    注意：这里的名字和Model表不一致！！！
    '''
    username = forms.CharField(label="微博昵称", max_length=30, \
                               widget=forms.TextInput(attrs={'size': 100, \
                                                             'class':'class_username', }))
    email = forms.EmailField(label="常用邮箱", max_length=100, \
                             widget=forms.TextInput(attrs={'size': 100, \
                                                           'class':'class_email', }))

    daily_remind_limit = forms.ChoiceField(label="每天提醒次数上限", choices=LimitChoice)
    at_remind = forms.BooleanField(label="@微博提醒")
    comment_remind = forms.BooleanField(label="评论微博提醒")
    repost_remind = forms.BooleanField(label="转发微博提醒")
    cross_remind = forms.BooleanField(label="开启网友互相提醒")

#    def clean_username(self):
#        if not _username_valid(self):
#            raise forms.ValidationError("invalid charactor '@' ")
#        return self.cleaned_data["username"]
# 
#    def clean_email(self):
#        return self.cleaned_data["email"]
# 
#    def clean_repost_remind(self):
#        print self.cleaned_data["repost_remind"]
# 
#    def clean_comment_remind(self):
#        print self.cleaned_data["comment_remind"]
# 
#    def clean_at_remind(self):
#        print self.cleaned_data["at_remind"]
# 
#    def clean_cross_remind(self):
#        print self.cleaned_data["cross_remind"]
# 
#    def clean_daily_remind_limit(self):
#        print self.cleaned_data["daily_remind_limit"]


