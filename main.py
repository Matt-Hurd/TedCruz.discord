import discord
import asyncio
import secrets

from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
import flatlib.const
from geopy.geocoders import Nominatim
import pytz
from tzwhere import tzwhere

from dateutil.parser import parse

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    l = message.content.split(' ')
    print(l)
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
        await client.send_message(message.channel, "If you were born on %s, then you're a %s!" % (date.strftime('%B %d, %Y'), sun))
    except Exception as e:
        print(e)
        await client.send_message(message.channel, "Invalid date string")


consts = [flatlib.const.SUN,
          flatlib.const.MOON,
          flatlib.const.MERCURY,
          flatlib.const.VENUS,
          flatlib.const.MARS,
          flatlib.const.JUPITER,
          flatlib.const.SATURN,
          flatlib.const.URANUS,
          flatlib.const.NEPTUNE,
          flatlib.const.PLUTO,
          flatlib.const.CHIRON,
          flatlib.const.NORTH_NODE,
          flatlib.const.SOUTH_NODE,
          flatlib.const.SYZYGY,
          flatlib.const.PARS_FORTUNA]

async def cmd_chart(message):
    l = message.content.split(' ')
    try:
        date = parse(l[1])
        time = parse(l[2])
        place = ' '.join(l[3:])
        geolocator = Nominatim()
        location = geolocator.geocode(place)
        tzwhere_inst = tzwhere.tzwhere()
        timezone_str = tzwhere_inst.tzNameAt(location.latitude, location.longitude)
        timezone = pytz.timezone(timezone_str)
        offset = str(timezone.utcoffset(date).total_seconds()/60/60).replace('.', ':')
        datetime = Datetime(date.strftime('%Y/%m/%d'), time.strftime('%H:%M'), offset)
        pos = GeoPos(location.latitude, location.longitude)
        chart = Chart(datetime, pos)
        response = ["Your chart is:"]
        for const in consts:
            try:
                response += ['   %s: %s' % (const, str(chart.getObject(const).sign))]
            except:
                pass
        await client.send_message(message.channel, '\n'.join(response))
    except Exception as e:
        raise e
        await client.send_message(message.channel, "Usage: !chart dd/mm/yy hh/mm location")


async def cmd_help(message):
    await client.send_message(message.channel,
'''
Current commands:
    !sun [mm/dd/yy]
        Gives you your sun sign
''')
if __name__ == '__main__':
    client.run(secrets.CLIENT_TOKEN)
