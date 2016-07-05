#! /usr/bin/python
# -*- coding: UTF-8 -*-

import argparse
import datetime
import os
import random
import re
import sqlite3
import urllib2
import lxml.html
import redis
import requests
from selenium import webdriver

wget_es = {
    0: "No problems occurred.",
    2: "User interference.",
    1 << 8: "Generic error code.",
    2 << 8: "Parse error - for instance, when parsing command-line "
            "optio.wgetrc or .netrc...",
    3 << 8: "File I/O error.",
    4 << 8: "Network failure.",
    5 << 8: "SSL verification failure.",
    6 << 8: "Username/password authentication failure.",
    7 << 8: "Protocol errors.",
    8 << 8: "Server issued an error response."
}

s = '\x1b[%d;%dm%s\x1b[0m'  # terminual color template

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml; "
              "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "text/html",
    "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/48.0.2564.109 Safari/537.36",
    "Cookie": "language=cn_CN"
}

cookies = {
    "language": "cn_CN"
}


class download91:
    def __init__(self, url=None):
        self.host = url
        self.urls = []
        self.browser = requests.session()
        self.proxy = {}
        self.page = ''

    def start(self):
        print '----------------开始运行 ' + datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S') + '-----------------------\n'

        self.loadvideos()
        for index in range(0, len(self.urls)):
            print '正在执行第 %s 条记录 共%s条  url:%s \n' % (index + 1, len(self.urls), self.urls[index])
            try:
                self.page = self.urls[index]
                self.get_infos(self.urls[index])
            except Exception, e:
                print e

        print '----------------执行完毕 %s-----------------------\n' % (datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'))

    def start_url(self, url):
        print '----------------开始运行 ' + datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S') + '-----------------------\n'
        print '正在执行第 1 条记录 共 1 条  url:%s \n' % url
        try:
            self.page = url
            self.get_infos_share(url)
        except Exception, e:
            print e.message

        print '----------------执行完毕 %s-----------------------\n' % (datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'))

    def get_infos(self, url):
        try:
            r = requests.get(url, headers=headers, proxies=self.proxy, timeout=10)
        except Exception, e:
            print '获取酒店详情页出现错误:%s' % e.message
            self.switchproxy()
            self.get_infos(url)
        if r and r.ok:
            n1 = re.search(r'so.addVariable\(\'file\',\'(\d+)\'', r.content)
            n2 = re.search(r'so.addVariable\(\'seccode\',\'(.+?)\'', r.content)
            n3 = re.search(r'so.addVariable\(\'max_vid\',\'(\d+)\'', r.content)
            if n1 and n2 and n3:
                name = re.search(
                    '<div\s+id="viewvideo-title">\s*(.+)\s*</div>', r.content).group(1)
                apiurl = '%s/getfile.php' \
                         % self.host
                params = {
                    'VID': n1.group(1),
                    'mp4': '1',
                    'seccode': n2.group(1),
                    'max_vid': n3.group(1),
                }
                apiurl = apiurl + '?' + '&'.join(['='.join(item) for item in params.items()])
                print '视频API地址:%s' % apiurl
                try:
                    r = requests.get(apiurl, timeout=10, proxies=self.proxy)
                except Exception, e:
                    print e
                    print '请求视频API出现错误............'
                if r and r.ok:
                    path = './' + datetime.datetime.now().strftime('%Y-%m-%d')
                    if os.path.isdir(path):
                        pass
                    else:
                        os.mkdir(path)
                    dlink = re.search(
                        r'file=(http.+?)$', r.content).group(1)
                    key = re.search(
                        r'viewkey=([\d\w]+)', url).group(1)
                    infos = {
                        'name': '%s.mp4' % name,
                        'file': os.path.join(path, '%s.mp4' % name),
                        'dir_': path,
                        'dlink': urllib2.unquote(dlink),
                        'key': key
                    }
                    self.download(infos)
                else:
                    print s % (1, 91, '  Error at get(apiurl)')
            else:
                print 'IP : 已被禁,更换IP'
                self.switchproxy()
                self.get_infos(url)
        else:
            print '获取视频详情页出现未知错误!'
            self.switchproxy()
            self.get_infos(url)

    def get_infos_share(self, url):
        print 'get_infos_share'
        try:
            r = requests.get(url, headers=headers, proxies=self.proxy, timeout=10)
        except Exception, e:
            print '获取酒店详情页出现错误:%s' % e.message
            self.switchproxy()
            self.get_infos_share(url)
        if r and r.ok:
            n1 = re.search(r'so.addVariable\(\'file\',\'(\d+)\'', r.content)
            n2 = re.search(r'so.addVariable\(\'seccode\',\'(.+?)\'', r.content)
            n3 = re.search(r'so.addVariable\(\'max_vid\',\'(\d+)\'', r.content)
            if n1 and n2 and n3:
                self.get_video_path(r.content)
            else:
                if r.status_code == 403:
                    print 'IP需要验证码'
                else:
                    print 'IP : 已被禁,更换IP'
                self.switchproxy()
                self.get_infos_share(url)
        else:
            print '获取视频详情页出现未知错误!'
            self.switchproxy()
            self.get_infos_share(url)

    def get_video_path(self, content):
        print 'get_video_path'
        tree = lxml.html.fromstring(content)
        # name = str(tree.xpath("//div[@id='viewvideo-title']/text()")[0]).lstrip().rstrip() if tree.xpath(
        #     "//div[@id='viewvideo-title']/text()") else ''
        name = re.search(
            '<div\s+id="viewvideo-title">\s*(.+)\s*</div>', content).group(1)
        url = tree.xpath("//form[@id='linkForm']/textarea/embed/@src")
        url = url[0] if url else ''
        if url:
            print 'url:' + url
            params = {'vid': '', 'mp4': ''}
            param = url.split('?')[1].split('&')
            for i in range(0, len(param)):
                if param[i].lower().startswith('video_id'):
                    params['vid'] = param[i].split('=')[1]
                if param[i].lower().startswith('mp4'):
                    params['mp4'] = param[i].split('=')[1]
            apiurl = 'http://91.9p91.com/getfile_jw.php?VID=%s&v=NaN&mp4=%s' % (params['vid'], params['mp4'])
            print '视频API地址:%s' % apiurl
            try:
                r = requests.get(apiurl)
            except Exception, e:
                print e
                print '请求视频API出现错误............'
            if r and r.ok:
                path = './' + datetime.datetime.now().strftime('%Y-%m-%d')
                if os.path.isdir(path):
                    pass
                else:
                    os.mkdir(path)
                dlink = re.search(
                    r'file=(http.+?)$', r.content).group(1)
                # key = re.search(
                #     r'viewkey=([\d\w]+)', url).group(1)
                print r.content
                infos = {
                    'name': '%s.mp4' % name,
                    'file': os.path.join(path, '%s.mp4' % name),
                    'dir_': path,
                    'dlink': urllib2.unquote(dlink),
                    'key': '123'
                }
                print infos
                self.download(infos)
            else:
                print s % (1, 91, '  Error at get(apiurl)')
        else:
            print '获取分享Url出现错误'

    def switchproxy(self):
        self.browser = requests.session()
        self.browser.cookies.update(cookies)
        self.browser.headers.update(headers)
        self.proxy = {
            'http': '127.0.0.1:2345'
        }
        os.system('sudo killall -HUP tor')

    def download(self, infos):
        num = random.randint(0, 7) % 7
        col = s % (2, num + 90, infos['file'])
        print '\n  ++ 正在下载: %s' % col
        cookies = '; '.join(
            ['%s=%s' % (i, ii) for i, ii in self.browser.cookies.items()])
        cmd = 'wget -c -O "%s.tmp" --header "User-Agent: %s" ' \
              '--header "Cookie: %s" "%s"' \
              % (infos['file'], headers['User-Agent'], cookies, infos['dlink'])
        status = os.system(cmd)
        if status != 0:
            wget_exit_status_info = wget_es[status]
            print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> '
                  '\x1b[1;91m%d (%s)\x1b[0m   ###--- \n\n'
                  % (status, wget_exit_status_info))
            print s % (1, 91, '  ===> '), cmd
            os.remove("%s.tmp" % infos['file'])
        else:
            os.rename('%s.tmp' % infos['file'], infos['file'])
            self.save(infos)

    def save(self, info):
        conn = sqlite3.connect(os.path.join(os.getcwd(), '91porn.db'))
        cur = conn.cursor()
        stat = "insert into video values (?,?,?,?)"
        data = (info['key'], self.page, info['dlink'], info['name'])
        cur.execute(stat, data)
        conn.commit()
        conn.close()

    def loadvideos(self):
        video = self.loadvideokeys()
        for index in range(1, 5):
            print '正在加载第 %s 页数据.............' % str(index)
            r = requests.get(
                '%s/v.php?next=watch&page=%s' % (self.host, index))
            if r.ok:
                ls = re.findall(
                    r'(/view_video.php\?viewkey=(\w+).*&category=mr)', r.content)[0::2]
                for i in range(0, len(ls)):
                    if ls[i][1] not in video:
                        self.urls.append(self.host + ls[i][0])
        print '数据库中存在' + str(len(video)) + '条记录  本次共有' + \
              str(len(self.urls)) + '条记录需要下载!\n'

    def loadvideokeys(self):
        print '正在加载已存在的video列表..............'
        if not os.path.isfile(os.path.join(os.getcwd(), '91porn.db')):
            conn = sqlite3.connect(os.path.join(os.getcwd(), '91porn.db'))
            cur = conn.cursor()
            cur.execute('CREATE TABLE video (viewkey,url,downurl,title)')
            conn.commit()
            conn.close()
        conn = sqlite3.connect('91porn.db')
        cur = conn.cursor()
        command = 'select viewkey from video'
        cur.execute(command)
        data = cur.fetchall()
        conn.close()
        return [item[0] for item in data]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="91Porn下载器")
    parser.add_argument('-l', help='下载单个视频')
    parser.add_argument('-x', help='代理')
    args = parser.parse_args()

    print '程序启动中.........'
    print '正在初始化91Porn网址.................'
    driver = webdriver.PhantomJS()
    driver.get('http://mybigbangtheory.space/Cazn2/')
    url = driver.current_url
    driver.close()
    print 'url 获取完毕!!! 最新地址为: %s' % str(url)
    download = download91(url)
    if args.x:
        download.proxy = {
            'http': args.x
        }
    if args.l:
        download.start_url(args.l)
    else:
        download.start()
    print '程序已结束..........'
