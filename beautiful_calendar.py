#!/usr/bin/python3
import datetime
import math
import sys

import pytz

from waveshare_epd import epd7in5b_V2

# import epd7in5
from PIL import Image, ImageDraw, ImageFont

import ical_worker
from config import *

#
# URLS = [
#     "webcal://calendar.google.com/calendar/u/2?cid=bWtzcXYwcWpiMmhzbXNyNjRmbmdoZGdkYzRAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
#     "webcal://calendar.google.com/calendar/u/2?cid=NTUzdDFvMTRpY2lrNWk0Y3V2aHRxcXVtMm9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
#     "webcal://calendar.google.com/calendar/u/2?cid=cWk3bGdyajN0dmRtdWRiaGhrOXRyc28xam9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ",
#     "webcal://calendar.google.com/calendar/u/2?cid=bXJzaHVyc2hpbEBnbWFpbC5jb20"]

# timezone = pytz.timezone(TIMEZONE)
# ical_worker.basetime = datetime.datetime.now(timezone)
# ical_worker.basetime.astimezone(timezone)

fheadline = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Light.ttf', headline_size)
fhours = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Light.ttf', headline_size-5)
ftext = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Light.ttf', text_size)
fbold = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Bold.ttf', text_size)
# fawesome = ImageFont.truetype('fa-regular.otf', text_size)

print("DAYS: {}".format(DAYS))
print("hours_day: {}".format(hours_day))


def get_drawable_events():
    print("per_hour: {}\t lost: {}".format(per_hour,
                                           height - bar_top - offset_top - offset_allday - hours_day * per_hour))


print("per_day: {}\t lost: {}".format(per_day, width - bar_left - offset_left - per_day * DAYS))
epd = epd7in5b_V2.EPD()


def prepare_grid(d, other):
    """ Prepares the Days X Hours grid for drawing events into it """

    # separate top bar from rest

    import datetime

    now = datetime.datetime.now()

    d.line([(offset_left + bar_left - 1, offset_left + 31), (offset_left + bar_left - 1, epd7in5b_V2.EPD_WIDTH*2)], width=2)

    # separate all-day events from grid
    # d.line([(offset_left + bar_left + offset_allday, offset_left), (offset_left + bar_left + offset_allday, width)], width=2)
    # separate the left bar from the rest
    d.line([(offset_left, offset_top + bar_top - 1), (epd7in5b_V2.EPD_WIDTH*2, offset_top + bar_top - 1,)], width=2)

    # draw the vertical day separators and day headlines
    for i in range(0, DAYS):
        x = offset_left + bar_left + per_day * i
        # for every but the first, draw separator to the left
        if i > 0:
            d.line([(x, offset_top), (x, height*3)])
        # draw date headline
        day = ical_worker.basetime + datetime.timedelta(days=i)
        headline = day.strftime('%a %d')
        textsize_x = d.textsize(headline, fheadline)[0]
        textoffs_x = math.floor((per_day - textsize_x) / 2)
        d.text((x + textoffs_x, offset_top), headline, font=fheadline)

        # draw horizontal hour separators and hour numbers
    for i in range(0, hours_day):
        x = offset_top + bar_top + offset_allday + per_hour * i
        # for every but the first, draw separator before
        if i > 0:
            # separator = dotted line with every fourth pixel
            for j in range(offset_left, width*3, 4):
                d.point([(j, x)])
        # draw the hour number
        textoffs_y = math.floor((per_hour - text_size) / 2)
        d.text((offset_left, x + textoffs_y - 1), "%02d" % (BEGIN_DAY + i), font=fhours)

    x = offset_top + bar_top + offset_allday + per_hour * (hours_day)
    for j in range(offset_left, width*3, 4):
        d.point([(j, x)])
    x = offset_top + bar_top + offset_allday + per_hour * (hours_day + 1)
    for j in range(offset_left, width*3, 4):
        d.point([(j, x)])
    x = offset_top + bar_top + offset_allday + per_hour * (hours_day + 2)
    for j in range(offset_left, width*3, 4):
        d.point([(j, x)])
    d.text((offset_left, offset_top), ("0" if now.hour < 10 else "") + str(now.hour) + ":" +
           ("0" if now.minute < 10 else "") + str(now.minute), font=ftext)

    # clear the all-day events space
    # d.rectangle((offset_left + bar_left + 1, offset_top + bar_left + 1, width, offset_top + bar_left + offset_allday - 1),
    #             fill=200, width=0)


def draw_short_event(d, e, other):
    """
    Internal function for drawing events into the grid.
    
    Not to be used for drawing events manually, please use draw_event for that.
    
    This function cannot draw events lasting across midnight. Instead, such events are split up
    into several calls of draw_short_event and draw_allday_event.
    
    """
    x_start = offset_left + bar_left + e["day"] * per_day + e["column"] * per_day / e["max_collision"]
    y_start = offset_top + bar_top + offset_allday + math.floor((e["start"] - (BEGIN_DAY * 60)) * per_hour / 60)
    width = int(per_day / e["max_collision"])
    # width = (epd7in5b_V2.EPD_WIDTH - 3 - offset_left - bar_left) / DAYS
    y_end = offset_top + bar_top + offset_allday + math.floor((e["end"] - (BEGIN_DAY * 60)) * per_hour / 60)
    # clear the event's area and make the outline
    s = e["title"].lower()
    RED = True
    truth = [x in s for x in keywords]
    if True in truth:
        if not RED:
            d.rectangle((x_start, y_start, x_start + width, y_end), outline=0, width=2, fill=200)
        else:
            other.rectangle((x_start, y_start, x_start + width, y_end), outline=0, width=2, fill=200)
    else:
        d.rectangle((x_start, y_start, x_start + width, y_end), outline=0, width=2, fill=200)

    textoffs_y = 5
    textoffs_x = (per_hour - text_size) // 2 - 3

    fulltext = e["title"]
    while d.textsize(fulltext, font=ftext)[0] > width - 2 * textoffs_x and len(fulltext) > 0:
        fulltext = fulltext[:-1]
    if e["end"] - e["start"] >= 60:
        dt = datetime.datetime.now()
        begintext = "%02d:%02d" % ((e["start"]-60) // 60, e["start"] % 60)
        nowtext = "%02d:%02d" % ((dt.hour - 2)%24, (dt.minute+30)%60)

        endtext = "%02d:%02d" % ((e["end"]-60) // 60, e["end"] % 60)
        datetext = "\n%s-%s" % (begintext, endtext)

        d_h = -(dt.hour - (e["start"] - 60) // 60)
        d_m = (dt.minute - e["start"] % 60)
        datetext_dur = " ({}h{}m)".format(d_h, abs(d_m))
        print("trying", e["title"], e["end"] - e["start"])
        print(d.textsize(datetext + datetext_dur, font=ftext)[0], width-2*textoffs_x, d_h, d_m, e["day"], nowtext < begintext)
        if d.textsize(datetext, font=ftext)[0] > width - 2 * textoffs_x:
            if e["end"] - e["start"] >= 90:
                datetext = "\n%s" % begintext
                if nowtext < begintext and e["day"] == 0:
                    if d_h == 0:
                        print("d_h == 1")
                        datetext_dur = "\n({}mins)".format(d_m)
                    print("passed chunky!")
                    datetext += datetext_dur
            else:
                datetext = "\n%s" % begintext
        elif d.textsize(datetext + datetext_dur, font=ftext)[0] <= width - 2 * textoffs_x and nowtext < begintext \
                and e["day"] == 0:
            if d_h <= 0:
                print("d_h <= 0")
                dt = datetime.datetime.now()
                if "%02d:%02d" % (dt.hour, dt.minute) > begintext:
                    print("PAST", 60 - e["start"] % 60, dt.minute)
                    d_m = (60 - e["start"] % 60) + dt.minute
                    print(d_m)
                    # datetext_dur = " ({}mins)".format(-d_m)
                else:
                    print("-d_m > 0")
                    datetext_dur = " ({}mins)".format(-d_m)
            print("passed!")
            datetext += datetext_dur
        # if d.textsize(datetext, font=ftext)[0] <= width - 2 * textoffs_x:
        fulltext += datetext
    if not RED and True in truth:
        d.text((x_start + textoffs_x, y_start + textoffs_y), fulltext, font=fbold)
    else:
        d.text((x_start + textoffs_x, y_start + textoffs_y), fulltext, font=ftext)

    print(fulltext)
    # d.text((x_start + 5, y_start + text_size + textoffs_y), begintext + "-" + endtext, font=ftext)


    print(e)


def draw_allday_event(d, ev):
    """ 
    Internal function for drawing events that shouldn't appear in the grid.
    
    Not to be used for drawing events manually, please use draw_event for that.
    """
    if e["column"] >= ALLDAY_MAX:
        return
    x_start = offset_left + bar_left + e["start"] * per_day - 1
    x_end = offset_left + bar_left + e["end"] * per_day
    y_start = offset_top + bar_top + e["column"] * allday_size - 1
    width = x_end - x_start

    d.rectangle((x_start, y_start, x_end, y_start + allday_size + 2), outline=0, fill=200, width=2)

    textoffs_x = 5
    textoffs_y = (allday_size - text_size) // 2
    fulltext = e["title"]
    while d.textsize(fulltext, font=ftext)[0] > width - 2 * textoffs_x and len(fulltext) > 0:
        fulltext = fulltext[:-1]
    d.text((x_start + textoffs_x, y_start + textoffs_y), fulltext, font=ftext)


def draw_event(d, ev):
    """
    High-level function for drawing an event as it is generated by the iCal Library 

    d -- the Pillow.ImageDraw Object to draw onto
    ev -- the icalendar event Object to draw
    """
    pass


if __name__ == "__main__":
    (drawables, all_days) = ical_worker.get_drawable_events()
    print("GOT ALL EVENTS")

    epd.init()
    print("DONE INIT, DRAWING")

    im = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
    Other = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
    import datetime

    now = datetime.datetime.now()

    draw_other = ImageDraw.Draw(Other)
    x_start = offset_left + bar_left
    y_start = offset_top + bar_top + offset_allday + math.floor((now.minute+now.hour*60+60 - (BEGIN_DAY * 60)) * per_hour / 60)
    width = int(per_day)
    # width = (epd7in5b_V2.EPD_WIDTH - 3 - offset_left - bar_left) / DAYS
    # clear the event's area and make the outline
    r = 7
    # timezone = pytz.timezone(TIMEZONE)
    # basetime = datetime.datetime.now(timezone)
    # print(datetime.datetime.now(timezone).day , basetime.replace(hour=BEGIN_DAY).day)
    # if datetime.datetime.now(timezone).day != basetime.replace(hour=BEGIN_DAY, minute=0).day:
    #     print("NOT SAME DATE")
    #     y_start = offset_top + bar_top


    d = ImageDraw.Draw(im)
    prepare_grid(d, draw_other)
    # draw_event(d, evs[1])
    no_dupl = []

    # for idx, yy in enumerate(drawables):
    #     no_dupl.append([])
    #     for ll in yy:
    #         print(str(ll))
    #         if len(no_dupl[idx]) == 0:
    #             no_dupl.append(ll)
    #         else:
    #             truth = [ll["title"] == x["title"] and ll["start"] == x["start"] and  for x in no_dupl[idx]]
    #             if True in truth:
    #                 print("found duplicate", ll, "not adding!")
    #             else:
    #                 no_dupl[idx].append(ll)
    #     idx += 1

    print("DRawables BEFORE", drawables)
    drawables = [[i for n, i in enumerate(d_) if i not in d_[n + 1:]] for d_ in drawables]
    drawables = [i for n, i in enumerate(drawables) if i not in drawables[n + 1:]]
    print("DRawables AFTER", drawables)

    for l in drawables:
        for e in l:
            draw_short_event(d, e, draw_other)
    for e in all_days:
        draw_allday_event(d, e)
    im.save(open("out.jpg", "w+"))

    draw_other.ellipse((x_start - r, y_start - r, x_start + r, y_start + r), width=10)

    draw_other.line((x_start, y_start, x_start + width, y_start), width=4)

    epd.display(epd.getbuffer(im), epd.getbuffer(Other))
    print("DONE DRAWING")
    # epd.display(epd.getbuffer(Limage), epd.getbuffer(im))
    epd.sleep()
