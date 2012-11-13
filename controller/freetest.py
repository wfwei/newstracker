#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 28, 2012

@author: plex
'''
import re

#from main import getUserPostTopic
_summary = '''<table border=\"0\" cellpadding=\"2\" cellspacing=\"7\" style=\"vertical-align:top\"><tr><td width=\"80\" align=\"center\" valign=\"top\"><font style=\"font-size:85%;font-family:arial,sans-serif\"><a href=\"http://news.google.com/news/url?sa=t&amp;fd=R&amp;usg=AFQjCNGTXUJAUzc7PeDdktma7idsXxrz2g&amp;url=http://finance.sina.com.cn/china/dfjj/20121017/110813394032.shtml\"><img src=\"http://news.google.com/news/tbn/llgc0J33PjApzM/6.jpg\" alt=\"\" border=\"1\" width=\"80\" height=\"80\"><br><font size=\"-2\">\u65b0\u6d6a\u7f51</font></a></font></td><td valign=\"top\"><font style=\"font-size:85%;font-family:arial,sans-serif\"><br><div style=\"padding-top:0.8em\"><img alt=\"\" height=\"1\" width=\"1\"></div><div><a href=\"http://news.google.com/news/url?sa=t&amp;fd=R&amp;usg=AFQjCNGTXUJAUzc7PeDdktma7idsXxrz2g&amp;url=http://finance.sina.com.cn/china/dfjj/20121017/110813394032.shtml\"><b><font color=\"#CC0033\">\u676d\u5dde\u70df\u82b1</font>\u5927\u4f1a\u70b8\u4f24\u767e\u4eba\u5e02\u6c11\u6307\u8d23\u52b3\u6c11\u4f24\u8d22</b></a><br><font size=\"-1\"><b><font color=\"#6f6f6f\">\u65b0\u6d6a\u7f51</font></b></font><br><font size=\"-1\"><font color=\"#CC0033\">\u676d\u5dde\u70df\u82b1</font>\u5927\u4f1a\u53d1\u751f<font color=\"#CC0033\">\u4e8b\u6545</font>\u540e\uff0c\u6709\u7f51\u53cb\u8d28\u7591<font color=\"#CC0033\">\u70df\u82b1</font>\u8d28\u91cf\u95ee\u9898\u3002\u4e8b\u53d1\u540e\uff0c\u62f1\u5885\u533a\u8fc5\u901f\u6210\u7acb\u4e86<font color=\"#CC0033\">\u4e8b\u6545</font>\u8c03\u67e5\u7ec4\uff0c14\u65e5\uff0c\u8c03\u67e5\u7ec4\u516c\u5e03\u4e86\u521d\u6b65\u8c03\u67e5\u7ed3\u679c\uff1a<font color=\"#CC0033\">\u4e8b\u6545</font>\u539f\u56e0\u662f\u64cd\u63a7\u95ee\u9898\uff0c<font color=\"#CC0033\">\u70df\u82b1</font>\u5347\u5230\u534a\u7a7a\u8f6c\u5411\uff0c\u5728\u4eba\u7fa4\u4e2d<font color=\"#CC0033\">\u7206\u70b8</font>\u3002\u622a\u81f3\u76ee\u524d\uff0c<font color=\"#CC0033\">\u4e8b\u6545</font>\u5177\u4f53 <b>...</b></font><br><font size=\"-1\"><a href=\"http://news.google.com/news/url?sa=t&amp;fd=R&amp;usg=AFQjCNG2-3f6qKR2n5xcenksRb8VpFZ3OA&amp;url=http://www.zjjzx.cn/news/gnxw/216208.html\"><font color=\"#CC0033\">\u676d\u5dde</font>\u897f\u6e56\u56fd\u9645<font color=\"#CC0033\">\u70df\u82b1</font>\u8282<font color=\"#CC0033\">\u70df\u82b1</font>\u70b8\u4f24\u4eba\u7fa4\u5f15\u5b89\u5168\u53cd\u601d</a><font size=\"-1\" color=\"#6f6f6f\">\u5f20\u5bb6\u754c\u5728\u7ebf</font></font><br><font size=\"-1\"></font><br><font size=\"-1\"><a href=\"http://news.google.com.hk/news/more?ncl=dJcU5VZv9v0Q4qMo0O3hA1KYM55wM&amp;ned=cn\"><b>\u6b64\u4e13\u9898\u6240\u6709 35 \u7bc7\u62a5\u9053\u00a0\u00bb</b></a></font></div></font></td></tr></table>'''

## Init google reader
#from libgreader import GoogleReader
#reader = GoogleReader()
#print 'Google Reader 登录信息:\t' + reader.getUserInfo()['userName']

from libweibo.weiboAPI import weiboAPI
##测试OAuth2登录
_wb = weiboAPI()
url = _wb.client.get_authorize_url()
print url
code = raw_input()
_r = _wb.client.request_access_token(code)
access_token = _r.access_token  # 新浪返回的token，类似abc123xyz456
expires_in = _r.expires_in

if __name__ == '__main__':
    _res = re.findall('<td[^>]*>(.*?)</td>', _summary)
    _summary_pic = _res[0]
    print _summary_pic
    
    _summary_content = _res[1]
    _summary_content = re.sub('<[/]?font[^>]*>', '', _summary_content)
    _summary_content = re.sub('<[/]?div[^>]*>', '', _summary_content)
    link = re.search('href="([^"]*)"', _summary_content).group(1)
    _summary_content = re.sub('<a[^>]*>.*?</a>', '', _summary_content)
    print _summary_content
#    getUserPostTopic()
    pass

