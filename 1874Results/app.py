from chalice import Chalice
from datetime import datetime
from bs4 import BeautifulSoup
from twilio.rest import Client
import boto3
import requests
import re

app = Chalice(app_name='1874Results')


def get_latest_result_next_fixture(posts):
    prev_results = []
    future_fixtures = []
    for post in posts:
        regex = re.compile(r'(\d+ - \d+)|(Postponed)')
        if regex.match(str(post.find('td', class_='data-time').a.text)):
            result = {'date':        post.date.text,
                      'fixture':     post.find('td', class_='data-event').text.strip(),
                      'league':      post.find('td', class_='data-league').text.strip(),
                      'score':       post.find('td', class_='data-time').a.text,
                      'writeup_url': post.find('td', class_='data-time').a['href']
                      }
            prev_results.append(result)
        else:
            kick_off = post.find('td', class_='data-time').a.text
            kick_off = ':'.join(str(kick_off).strip('<date>').strip('</').strip().split(':')[:2])
            fixture = {'date':        post.date.text,
                       'fixture':     post.find('td', class_='data-event').text.strip(),
                       'league':      post.find('td', class_='data-league').text.strip(),
                       'kick_off':    kick_off,
                       'writeup_url': post.find('td', class_='data-time').a['href']
                       }
            future_fixtures.append(fixture)
    return prev_results[-1], future_fixtures[0]


def send_message(msg, params):
    client = Client(params['twilio_account_sid'], params['twilio_auth_token'])
    message = client.messages.create(body=msg, from_=params['twilio_number'], to=params['twilio_recipient_number'])
    return message.sid, message.date_created, message.date_sent, message.price, message.price_unit, message.status


@app.schedule('cron(0 22 ? * TUE,SAT *)')
def results(event):
    param_names = ['twilio_account_sid', 'twilio_auth_token', 'twilio_number', 'twilio_recipient_number']
    params = {}
    ssm = boto3.client('ssm')
    for param_name in param_names:
        resp = ssm.get_parameter(
            Name=param_name,
            WithDecryption=True
        )
        params[param_name] = resp['Parameter']['Value']

    date_format = '%Y-%m-%d %H:%M:%S'
    today = datetime.now().strftime(date_format)
    year = today[:4]  # obtain year part of today string
    next_year = str(int(year) + 1)[-2:]  # set next year string to the 2 digit version of year + 1 (e.g. 20 for 2020)

    src = requests.get(f'https://1874northwich.com/{year}-{next_year}-fixtures-results/').text
    soup = BeautifulSoup(src, 'lxml')
    all_posts = soup.find_all('tr', class_='sp-post')

    latest_result, next_fixture = get_latest_result_next_fixture(all_posts)

    notification_string = f"LATEST RESULT:\n{latest_result['date']}\n{latest_result['fixture']}\n" \
                          f"{latest_result['league']}\n{latest_result['score']}\n" \
                          f"{latest_result['writeup_url']}\n\nNEXT_FIXTURE:\n{next_fixture['date']}\n" \
                          f"{next_fixture['fixture']}\n{latest_result['league']}\n{next_fixture['kick_off']}\n" \
                          f"{next_fixture['writeup_url']}"

    sid, date_created, date_sent, price, price_unit, status = send_message(notification_string, params)
    resp = {
        "sid": sid,
        "date_created": str(date_created),
        "date_sent": str(date_sent),
        "price": price,
        "price_unit": price_unit,
        "status": status
    }
    return resp
