#!/usr/bin/python3

from icalevents.icalevents import events
#from dateutil.parser import parse
import datetime
import pytz # timezone
import configparser

import math
import sys

import epd7in5
from PIL import Image, ImageDraw, ImageFont

BEGIN_DAY = 8
END_DAY = 24
DAYS = 4
TIMEZONE = 'Europe/Berlin'

width = epd7in5.EPD_WIDTH 
height = epd7in5.EPD_HEIGHT
timezone = pytz.timezone(TIMEZONE)
basetime = datetime.datetime.now(timezone)
basetime.astimezone(timezone)

offset_top = 0 
offset_left = 0
bar_top = 42
bar_left = 20
hours_day = END_DAY - BEGIN_DAY
per_hour = math.floor((height - bar_top - offset_top) / hours_day)
per_day = math.floor((width - bar_left - offset_left) / DAYS)

text_size = 15

ftext = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Light.ttf', text_size)
fawesome = ImageFont.truetype('fa-regular.otf', text_size)


print("DAYS: {}".format(DAYS))
print("hours_day: {}".format(hours_day))
print("per_hour: {}\t lost: {}".format(per_hour, height - bar_top - offset_top - hours_day * per_hour))
print("per_day: {}\t lost: {}".format(per_day, width - bar_left - offset_left - per_day * DAYS))
epd = epd7in5.EPD()



conf = configparser.ConfigParser()
conf.read("config.ini")

url = conf['DEFAULT']['URL']


start = basetime.replace(hour=BEGIN_DAY,minute=0)
end = start + datetime.timedelta(days=10)
#
evs = events(url, start=start, end=end)
#
evs.sort()
#


def prepare_grid(d):
    """ Prepares the Days X Hours grid for drawing events into it """

    # separate top bar from rest
    d.line([(offset_left, offset_top + bar_top - 1), (width, offset_top + bar_top - 1)], width=2)
    # separate the left bar from the rest
    d.line([(offset_left + bar_left -1, offset_top), (offset_left + bar_left - 1, height)], width=2)

    # draw the vertical day separators and day headlines
    for i in range(0, DAYS):
        x = offset_left + bar_left + per_day * i
        # for every but the first, draw separator to the left
        if i > 0: 
            d.line([(x, offset_top), (x, height)])
        # draw date headline
        day = basetime + datetime.timedelta(days=i)
        headline = day.strftime('%a, %d')
        textsize_x = d.textsize(headline, ftext)[0]
        textoffs_x = math.floor((per_day - textsize_x) / 2)
        d.text((x + textoffs_x, offset_top), headline, font=ftext) 
    
    # draw horizontal hour separators and hour numbers
    for i in range(0, hours_day):
        y = offset_top + bar_top + per_hour * i
        # for every but the first, draw separator before
        if i > 0:
            # separator = dotted line with every fourth pixel
            for j in range(offset_left, width, 4):
                d.point([(j, y)])
        # draw the hour number
        textoffs_y = math.floor((per_hour - text_size) / 2)
        d.text((offset_left, y + textoffs_y - 1), "%02d" % (BEGIN_DAY + i), font=ftext)

def draw_short_event(d, e):
    """
    Internal function for drawing events into the grid.
    
    Not to be used for drawing events manually, please use draw_event for that.
    
    This function cannot draw events lasting across midnight. Instead, such events are split up
    into several calls of draw_short_event and draw_allday_event by draw_event. 
    
    """
    x_start = offset_left + bar_left + e["day"] * per_day + 1
    y_start = offset_top + bar_top + math.floor((e["start_h"] - BEGIN_DAY + e["start_min"] / 60) * per_hour)
    x_end = x_start + per_day - 2 # TODO collision management
    y_end = offset_top + bar_top + math.floor((e["end_h"] - BEGIN_DAY + e["end_min"] / 60) * per_hour)
    d.rectangle((x_start, y_start, x_end, y_end), outline=0, fill=200)
    
    print(e)

def draw_allday_event():
    """ 
    Internal function for drawing events that shouldn't appear in the grid.
    
    Not to be used for drawing events manually, please use draw_event for that.
    """
    pass

    
def draw_event(d, ev):
    """
    High-level function for drawing an event as it is generated by the iCal Library 

    d -- the Pillow.ImageDraw Object to draw onto
    ev -- the icalendar event Object to draw
    """

    start = ev.start.astimezone(timezone)
    end = ev.end.astimezone(timezone)

    if ev.all_day:
        draw_allday_event(d, ev)
    else:
        """ We will be drawing events that last across more than one day separately for
        each day. """
        days_duration = (end.date() - start.date() + datetime.timedelta(days=1)).days
        start_day = (start.date() - basetime.date()).days # the start day index on our calendar (starting at 0 for today)
        #if start.date() < basetime.date(): # i.e. if event has started already
            #days_duration = (end.date() - basetime.date() + datetime.timedelta(days=1)).days
            #start_day = 0
        print("days_duration: {}\nstart_day: {}".format(days_duration, start_day))
        # correct for events that end at midnight the next day
        if end.hour == 0 and end == 0:
            days_duration -= 1
        for day in range(max(0, start_day), min(start_day + days_duration, DAYS)):
            event = {}
            if day == start_day: # first iteration - real start time
                if start.hour >= END_DAY:
                    continue
                elif start.hour < BEGIN_DAY:
                    event["start_h"] = BEGIN_DAY
                    event["start_min"] = 0
                else:
                    event["start_h"] = start.hour
                    event["start_min"] = start.minute
            else: # any later iteration - event going on from midnight
                event["start_h"] = BEGIN_DAY
                event["start_min"] = 0

            if day == start_day + days_duration - 1: # last iteration - real end time
                if end.hour < BEGIN_DAY:
                    continue
                elif end.hour >= END_DAY:
                    event["end_h"] = END_DAY
                    event["end_min"] = 0
                else:
                    event["end_h"] = end.hour
                    event["end_min"] = end.minute
            else: # any earlier iteration - event going until end of day
                event["end_h"] = END_DAY
                event["end_min"] = 0
            event["title"] = ev.summary
            event["day"] = day
            # check duration to prevent event from being too small
            minutes_duration = event["end_h"] * 60 + event["end_min"] - event["start_h"] * 60 - event["start_min"]
            if minutes_duration < 60:
                if event["end_h"] + 1 >= END_DAY:
                    event["start_h"] -= 1
                else:
                    event["end_h"] += 1
            draw_short_event(d, event)
    


if __name__ == "__main__":
    im = Image.new('1', (width, height), 255)
    d = ImageDraw.Draw(im)

    prepare_grid(d)
    draw_event(d, evs[1]) 

    im.save(open("out.jpg", "w+"))


    epd.init() 
    epd.display(epd.getbuffer(im))
    epd.sleep()


    #logostr = ''
    #evstr = ''
    #for e in evs:
    #    title = e.summary
    #    #begin = e.start
    #    #end = e.end
    #    left = e.time_left()
    #    if left.total_seconds() > 0: # event in future
    #        if left.days > 0:
    #            leftstr = "{} days".format(left.days)
    #        else if left.seconds <= 3600: # more than one hour in future
    #            leftstr = "next hour"
    #        else:
    #            hours = left.seconds / 3600
    #            leftstr = "{} hours".format(hours)
    #    else: # event has started
    #        to_end = 
    #print(evstr)
    #d.text((0,  0), logostr, font=fawesome)
    #d.text((20, 0), evstr, font=f)
    

