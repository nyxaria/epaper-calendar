from icalevents.icalevents import events
import datetime
import pytz # timezone
import configparser
from config import *

TIMEZONE= "Europe/Berlin"


timezone = pytz.timezone(TIMEZONE)
#basetime = datetime.datetime.strptime("Apr 23 2019 01:15AM", '%b %d %Y %I:%M%p').replace(tzinfo=timezone)
basetime = datetime.datetime.now(timezone)
basetime.astimezone(timezone)

start = basetime.replace(hour=BEGIN_DAY,minute=0)
print(start)
end = start + datetime.timedelta(days=DAYS)

def collision(e, evs):
    for e_ in evs:
        if not (e["start"] >= e_["end"] or e_["start"] >= e["end"]):
            return True
    return False

def detect_collisions(drawables, base, max_):
    """ Takes a list of drawable events (generated by split_events) and checks them 
    for collisions, i.e. events that need to be drawn side by side. Returns the same
    list of events with two parameters added to each event: index to be drawn in and
    number of events at that point. """ 

    groups = []
    for e in drawables:
        e_group = None
        for g in groups:
            first = True
            if collision(e, g):
                if first:
                    g.append(e)
                    e_group = g
                    first = False
                else:
                    groups.remove(g)
                    e_group.extend(g)
        if e_group is None:
            groups.append([e])
    
    print("GROUPS: {}".format(groups))
                    
    for g in groups:
        matrix = [[]]
        g.sort(key=lambda i : (i["start"], i["end"]))
        for e in g:
            appended = False
            for column in matrix: 
                if not collision(e, column):
                    column.append(e)
                    appended = True
                    break
            if not appended:
                matrix.append([e])

        for i, column in enumerate(matrix):
            for e in column:
                e["max_collision"] = len(matrix)
                e["column"] = i

#    print("MATRIX: {}".format(matrix))
    return drawables
    
def split_events(evs):
    drawables = [[] for x in range(DAYS)]
    all_days = []
    for ev in evs:
        start = ev.start.astimezone(timezone)
        end = ev.end.astimezone(timezone)
        if ev.all_day:
            event = {}
            event["start"] = max((start.date() - basetime.date()).days, 0)
            event["end"] = min((end.date() - basetime.date()).days, DAYS)
            event["title"] = ev.summary
            all_days.append(event)
        else:
            """ We will be drawing events that last across more than one day separately for
            each day. 
            
            variable explanations: (this shit is complicated...)

            days_duration: the number of days the event spans. For an event going from midnight
                        to midnight, this would be 1. For an event going from 23:55 to 00:05 this
                        would be 2.
                        This reflects the actual properties of the event and NOT the number
                        of days inside the calendar timeframe.
            
            start_day:  The index of the day on which the event starts, relative to our calendar
                        timeframe. 0 is the first day shown on the calendar, 1 the second etc.
                        start_day can be negative if the event has already started outside the
                        calendar timeframe (e.g. two days ago, then it would be -2)

            These two variables are then used to iterate over the intersection of the days that
            the event spans and the days inside the calendar timeframe, with the loop counter
            (named days) again being the current day's index relative to the calendar timeframe,
            just as start_day.
            So essentially we are iterating over range(start_day, start_day + days_duration), but
            because calendars are a bitch it's more complicated. The min and max just make sure 
            we only iterate over the days of the event that are in our calendar timeframe.
            """
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
                        event["start"] = BEGIN_DAY * 60 
                    else:
                        event["start"] = start.hour * 60 + start.minute
                else: # any later iteration - event going on from midnight
                    event["start"] = BEGIN_DAY * 60

                if day == start_day + days_duration - 1: # last iteration - real end time
                    if end.hour < BEGIN_DAY:
                        continue
                    elif end.hour >= END_DAY:
                        event["end"] = END_DAY * 60
                    else:
                        event["end"] = end.hour * 60 + end.minute
                else: # any earlier iteration - event going until end of day
                    event["end"] = END_DAY * 60
                event["title"] = ev.summary
                event["day"] = day
                # check duration to prevent event from being too small
                minutes_duration = event["end"] - event["start"]
                if minutes_duration < 60:
                    if event["end"] + 60 - minutes_duration >= END_DAY * 60:
                        event["end"] = END_DAY * 60
                        event["start"] = END_DAY * 60 - 60 
                    else:
                        event["end"] += 60 - minutes_duration
                #draw_short_event(d, event)
                drawables[day].append(event)
    return (drawables, all_days)  

def get_drawable_events():
    all_events = []
    for url in URLS:
        try:
            if "icloud.com" in url:
                evs = events(url, start=start, end=end, fix_apple=True)
            elif "cam.ac.uk" in url:
                evs = events(url, start=start, end=end, fix_apple=True)
                for e in evs:
                    e.summary += "!"
            else:
                evs = events(url, start=start, end=end)
                for e in evs:
                    e.summary += "!"
            all_events.extend(evs)
            print("Loaded ", url)
            print([(x.summary) for x in evs])
        except Exception as e:
            print("Failed to load ", url)
            print(e)

    print("Got {} events".format(len(all_events)))
    all_events.sort()
    (drawables, all_days) = split_events(all_events)
    drawables_new = []
    for d in drawables:
        drawables_new.append(detect_collisions(d, BEGIN_DAY * 60, END_DAY * 60))

    all_days = detect_collisions(all_days, 0, DAYS)

    return (drawables, all_days)


