import re
import sys
import datetime
import pytz
import unittest

__all__ = ['DateFinder']

def to_dt(s, format=None):
    if format is None:
        format = '%Y-%m-%d %H:%M:%S'
        s = s[:19].replace('T',' ')
    return datetime.datetime.strptime(s, format)

def to_utc(dt, timezone, return_naive=False):
    tz = pytz.timezone(timezone)
    dt_utc = tz.localize(dt).astimezone(pytz.utc)
    if return_naive:
        dt_utz.replace(tzinfo=None)
    return dt_utc

def time_range(middle, hours=0, minutes=0, seconds=0):
    delta = datetime.timedelta(hours=hours / 2., minutes=minutes / 2.,
                               seconds=seconds / 2.)
    return (middle - delta, middle + delta)

def timestamps(datetimes, format='%Y-%m-%dT%H:%M:%S'):
    if isinstance(datetimes, (list, tuple)):
        datetimes = type(datetimes)(dt.strftime(format) for dt in datetimes)
    return datetimes

class DateFinder():
    """
    Class to find and normalize dates emebdded in strings in arbitrary format
    """
    months = ['january','february','march','april','may','june',
              'july','august','september','october','november','december']

    def __init__(self, mode='us'):
        """
        the mode specifies whether 5/7/2016 is to be interpreted as May 7 (mode==us) or July 5 (mode=eu)
        """
        days = range(1,32)        
        d = (map(lambda t:'%0.2i'%t,days)+map(lambda t:'%ith'%t,days)+
             ['1st','2nd','3rd','21st','22nd','23rd','31st']+map(str,days))
        m = (self.months+
             map(lambda t:t.upper(),self.months)+
             map(lambda t:t.title(),self.months)+
             map(lambda t:t[:3],self.months)+
             map(lambda t:t[:3].upper(),self.months)+
             map(lambda t:t[:3].title(),self.months)+
             map(lambda t:"%i"%(t+1),range(len(self.months)))+
             map(lambda t:"%0.2i"%(t+1),range(len(self.months))))
        
        self.month_map = {}
        for k,month in enumerate(self.months):
            k += 1
            self.month_map["%i" % k] = k
            self.month_map["%0.2i" % k] = k
            self.month_map[month] = k
            self.month_map[month.upper()] = k
            self.month_map[month.title()] = k
            self.month_map[month[:3]] = k
            self.month_map[month[:3].upper()] = k
            self.month_map[month[:3].title()] = k
        
        r = '(?<!\S)((?P<day>DAYS)[^\d](?P<month>MONTHS)([^\d](?P<year>\d\d(\d\d)?))?)(?!\S)'
        s = '(?<!\S)((?P<month>MONTHS)[^\d](?P<day>DAYS)(([^\d]|,\s)(?P<year>\d\d(\d\d)?))?)(?!\S)'
        if mode == 'us':
            r,s =  s,r

        r = r.replace('DAYS','|'.join(d))
        r = r.replace('MONTHS','|'.join(m))

        s = s.replace('DAYS','|'.join(d))
        s = s.replace('MONTHS','|'.join(m[:-24]))

        self.regex_date1 = re.compile(r)        
        self.regex_date2 = re.compile(s)        
        self.matches = []
        
    def fix_day(self, day):
        return int(day.rstrip('st').rstrip('nd').rstrip('rd').rstrip('th').lstrip('0'))

    def fix_month(self, month):
        return self.month_map[month]

    def fix(self, match):
        day = self.fix_day(match.group('day'))
        month = self.fix_month(match.group('month'))
        year = int(match.group('year') or datetime.date.today().year)
        if year<100: year += 2000
        date = datetime.date(year, month, day)
        text = str(match.group())
        for ((b,e),m,d) in self.matches:
            if b <= match.start() <= e: # exclude is overlapping with date alreday computed
                break
        else:
            self.matches.append(((match.start(), match.end()), text, date))
        return text

    def find_dates(self, text):
        """
        DateFinder.find_dates(string) -> [((a,b), c, d)] 
        where each item is a match represented by:
        (a,b) is the location of the date in the string
        c is the actual date found
        d is the date converted to a datetime.date() object
        """
        self.matches = []
        self.regex_date1.sub(self.fix, text)    
        self.regex_date2.sub(self.fix, text)    
        return self.matches

    def normalize_dates(self, text, format='%d/%m/%Y'):
        """
        DateFinder.replace_dates(string, format='%d/%m/%Y')
        processes the string, finds dates, normalizes using the provided format and returns a new string
        """
        self.matches = []
        self.find_dates(text)
        for ((b,e),m,d) in self.matches:
            text = text.replace(m,d.strftime(format))
        return text

class DateFinderTestCase(unittest.TestCase):
    def test_date_parsing(self):
        INPUT_TEXT = "this is an example dates in a string Jan 1st and 2/2/2015 and 3/3/15 and 04-04-2015 and 5 5 2015 and 6th Jun 15; 7th July 2016 and August 8th, 2016 etc etc"
        EXPECTED_MATCHES = [((37, 44), 'Jan 1st', datetime.date(2016, 1, 1)), ((49, 57), '2/2/2015', datetime.date(2015, 2, 2)), ((62, 68), '3/3/15', datetime.date(2015, 3, 3)), ((73, 83), '04-04-2015', datetime.date(2015, 4, 4)), ((88, 96), '5 5 2015', datetime.date(2015, 5, 5)), ((131, 147), 'August 8th, 2016', datetime.date(2016, 8, 8)), ((101, 108), '6th Jun', datetime.date(2016, 6, 6)), ((113, 126), '7th July 2016', datetime.date(2016, 7, 7))]
        EXPECTED_OUTPUT = "this is an example dates in a string 2016.01.01 and 2015.02.02 and 2015.03.03 and 2015.04.04 and 2015.05.05 and 2016.06.06 15; 2016.07.07 and 2016.08.08 etc etc"
                
        fixer = DateFinder()
        matches = fixer.find_dates(INPUT_TEXT)
        self.assertEqual(fixer.matches, EXPECTED_MATCHES)
        output = fixer.normalize_dates(INPUT_TEXT, format='%Y.%m.%d')
        self.assertEqual(output, EXPECTED_OUTPUT)

if __name__ == '__main__':
    if len(sys.argv)>1:
        fixer = DateFinder()
        print fixer.find_dates(' '.join(sys.argv[1:]))
    else:
        unittest.main()
