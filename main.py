import discord
import asyncio
import secrets

from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib.const import LIST_OBJECTS
from geopy.geocoders import Nominatim
import pytz
from tzwhere import tzwhere
import requests
import us
import re
import logging
import rollbar

from dateutil.parser import parse

client = discord.Client()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('zodiac.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@client.event
async def on_ready():
    logger.info('Logged in as')
    logger.info(client.user.name)
    logger.info(client.user.id)
    logger.info('------')
    game = discord.Game(name="The TRUE Zodiac")
    client.change_presence(game=game, status=None, afk=False)

@client.event
async def on_message(message):
    l = message.content.split(' ')
    logger.info(message.content)
    if l[0] == '!help':
        await cmd_help(message)
    if l[0] == '!sun':
        if len(l) != 2:
            await cmd_help(message)
        else:
            await cmd_sun(message)
    if l[0] == '!chart':
        if len(l) < 4:
            await cmd_help(message)
        else:
            await cmd_chart(message)


async def cmd_sun(message):
    l = message.content.split(' ')
    try:
        date = parse(l[1])
        datetime = Datetime(date.strftime('%Y/%m/%d'))
        pos = GeoPos('00n00', '0w00')
        chart = Chart(datetime, pos)
        sun = str(chart.getObject(SUN)).split(' ')[1]
        await send_text(client, message.channel, "If you were born on %s, then you're a %s!" % (date.strftime('%B %d, %Y'), sun))
    except Exception as e:
        logger.info(e)
        await send_text(client, message.channel, "Invalid date string")
          
TZWHERE_INST = tzwhere.tzwhere()
GEOLOCATOR = Nominatim()

async def cmd_chart(message):
    global TZWHERE_INST, GEOLOCATOR
    l = message.content.split(' ')
    date = parse(l[1])
    time = parse(l[2])
    pos = 3
    if l[3].lower() == 'am':
        pos += 1
    if l[3].lower() == 'pm':
        pos += 1
        time.replace(hour=time.hour + 12)
    place = ' '.join(l[pos:])
    location = GEOLOCATOR.geocode(place, addressdetails=True)
    timezone_str = TZWHERE_INST.tzNameAt(location.latitude, location.longitude)
    timezone = pytz.timezone(timezone_str)
    offset = str(timezone.utcoffset(date).total_seconds()/60/60).replace('.', ':')
    datetime = Datetime(date.strftime('%Y/%m/%d'), time.strftime('%H:%M'), offset)
    pos = GeoPos(location.latitude, location.longitude)
    chart = Chart(datetime, pos)
    response = ["%s, your chart is:" % (message.author.mention)]
    for const in LIST_OBJECTS:
        response += ['   %s: %s' % (const, str(chart.getObject(const).sign))]
    try:
        url, img = get_chart_image(date, time, location, message)
        response += [url]
        response += [img]
    except Exception as e:
        logger.critical(e)
        response += ["Couldn't generate your image :/"]
    logger.info("Sending message: %s" % '\n'.join(response))
    await send_text(client, message.channel, '\n'.join(response))

async def send_text(client, channel, text):
    logger.info('Sending message: %s' % text)
    await client.send_message(channel, text)


def get_chart_image(date, time, location, message):
    country = location.raw['address']['country']
    town = location.raw['address']['city'] if 'city' in location.raw['address'].keys() else location.raw['address']['town']
    if len(country.split(' ')) > 1:
        country = ''.join([x[0] for x in country.split(' ') if x[0].isupper()])
    params = {'INPUT1': message.author.nick,
              'INPUT2': '',
              'GENDER': '',
              'MONTH': date.month,
              'DAY': date.day,
              'HOUR': time.hour % 12,
              'YEAR': date.year,
              'MINUTE': time.minute,
              'AMPM': 'AM' if time.hour < 12 else 'PM',
              'TOWN': town,
              'COUNTRY': country,
              'INPUT9': 'Submit',
              'Submit': 'Submit'
    }
    if country == 'USA':
        params['STATE'] = us.states.lookup(location.raw['address']['state']).abbr
    r = requests.get('https://www.alabe.com/cgi-bin/chart/astrobot.cgi', params=params)
    img = re.findall(r'(pics\/[0-9]*.gif)', r.text)[0]
    return (r.url, 'https://www.alabe.com/cgi-bin/chart/%s' % img)

async def cmd_help(message):
    await send_text(client, message.channel,
'''
Current commands:
    !sun [mm/dd/yy]
        Gives you your sun sign
    !chart [mm/dd/yy] [hh:mm] [location in many words]
        Gives you your full chart
''')

@asyncio.coroutine
def on_error(self, event_method, *args, **kwargs):
    rollbar.report_exc_info()
    logger.error('Ignoring exception in {}'.format(event_method))

if __name__ == '__main__':
    client.on_error = on_error
    client.run(secrets.CLIENT_TOKEN)
