#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of national-geographic-background
#
# Copyright (C) 2017
# Lorenzo Carbonell Cerezo <lorenzo.carbonell.cerezo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Dependencies:
# python3-cssselect

import requests
import os
from lxml.html import fromstring
from lxml import etree
import comun
from gi.repository import Gio
from gi.repository import GLib
from configurator import Configuration
import json
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify
from datetime import datetime


URL00='http://www.nationalgeographic.com/photography/photo-of-the-day/_jcr_content/.gallery.'
URL01 = 'http://www.bing.com/HPImageArchive.aspx?\
format=xml&idx=0&n=1&mkt=en-ww'
URL02 = 'https://api.gopro.com/v2/channels/feed/playlists/\
photo-of-the-day.json?platform=web&page=1&per_page=1'
URL03 = 'http://www.powder.com/photo-of-the-day/'


def set_background(afile=None):
    if os.environ.get("GNOME_DESKTOP_SESSION_ID"):
        gso = Gio.Settings.new('org.gnome.desktop.background')
        if afile and os.path.exists(afile):
            variant = GLib.Variant('s', 'file://%s' % (afile))
            gso.set_value('picture-uri', variant)
    elif os.environ.get("DESKTOP_SESSION") == "mate":
        gso = Gio.Settings.new('org.mate.background')
        if afile and os.path.exists(afile):
            variant = GLib.Variant('s', afile)
            gso.set_value('picture-filename', variant)


def get_national_geographic_data():
    # Filename with data: .gallery.<currentYear>-<currentMonth>.json
    today = datetime.today()
    year = str(today.year)
    if today.month < 10:
        month =  '0' + str(today.month)
    else:
        month = str(today.month)    
    url = URL00 + year + '-' + month +".json"
    r = requests.get(url)
    if r.status_code == 200:    
        data = r.json() 
        if 'items' in data:
            current_photo = data['items'][0]
            url = current_photo['url'] + current_photo['sizes']['1600']  # TODO: include preferred image size in configuration
            return dict(url=url, title=current_photo['title'], caption=current_photo['caption'], credit=current_photo['credit'])
    return None


def notify_photo_caption(title, caption, credit):
    for m in ['<p>', '</p>', '<br>', '<br />']:
        caption = caption.replace(m, '')            
    caption = caption + '<i>Photo credit</i>: ' + credit
    Notify.init(title)
    info = Notify.Notification.new(title, caption, 'dialog-information')
    info.set_timeout(Notify.EXPIRES_NEVER)
    info.set_urgency(Notify.Urgency.CRITICAL) # Notification stays longer
    info.show()


def set_national_geographic_wallpaper():
    data = get_national_geographic_data()
    if data:
        image_url = data['url']
        print(image_url)
        r = requests.get(image_url, stream=True)
        print(r.status_code)
        if r.status_code == 200:
            notify_photo_caption(data['title'], data['caption'], data['credit'])
            try:
                with open(comun.POTD, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                    set_background(comun.POTD)
            except Exception as e:
                print(e)


def set_bing_wallpaper():
    r = requests.get(URL01)
    if r.status_code == 200:
        try:
            parser = etree.XMLParser(recover=True)
            xml = etree.XML(r.content, parser)
            print(etree.tostring(xml))
            print('===========')
            image = xml.find('image')
            urlBase = image.find('urlBase')
            image_url = 'http://www.bing.com%s_1920x1200.jpg' % (urlBase.text)
            print(image_url)
            r = requests.get(image_url, stream=True)
            print(r.status_code)
            if r.status_code == 200:
                with open(comun.POTD, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                set_background(comun.POTD)
            print('===========')
        except Exception as e:
            print(e)


def set_gopro_wallpaper():
    try:
        r = requests.get(URL02)
        if r.status_code == 200:
            data = json.loads(r.text)
            image_url = data['media'][0]['thumbnails']['full']['image']
            r = requests.get(image_url, stream=True)
            print(r.status_code)
            if r.status_code == 200:
                with open(comun.POTD, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                set_background(comun.POTD)
    except Exception as e:
        print(e)


def set_powder_wallpaper():
    try:
        r = requests.get(URL03)
        if r.status_code == 200:
            doc = fromstring(r.text)
            results = doc.cssselect('img.entry-image')
            print(len(results), results[0])
            for key in results[0].keys():
                print(key, results[0].get(key))
            url = results[0].get('data-srcset').split(',')[0].split(' ')[0]
            url = '-'.join(url.split('-')[:-1]) + '.' + url.split('.')[-1]
            r = requests.get(url, stream=True)
            print(r.status_code)
            if r.status_code == 200:
                with open(comun.POTD, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                set_background(comun.POTD)
            print(url)
    except Exception as e:
        print(e)


def change_wallpaper():
    configuration = Configuration()
    source = configuration.get('source')
    if source == 'national-geographic':
        set_national_geographic_wallpaper()
    elif source == 'bing':
        set_bing_wallpaper()
    elif source == 'gopro':
        set_gopro_wallpaper()
    elif source == 'powder':
        set_powder_wallpaper()


if __name__ == '__main__':
    change_wallpaper()
    exit(0)
