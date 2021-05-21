import requests
from time import sleep
from json import dumps

IP_SERVICE = 'https://api.ipify.org?format=json'  # Get your ip
API_URL = 'https://api.cloudflare.com/client/v4/zones/'  # Cloudflare api zone link
HOSTNAME = ''  # Your Hostname
API_TOKEN = ''  # API Token for cloudflare
ZONE_ID = ''  # Zone ID
ID = ''  # Record ID
TTL = 1800  # int, TTL for the record in seconds
TIME = 30  # Time in minutes to wait between checks
PROXY = True  # bool, Proxy through cloudflare
ERR_TIME = 1  # Initial time in minutes to try again between errors
ERR_TIME_INC = 5  # Timeout difference between attempts in minutes
ERR_MAX_A = -1  # Number of max attempts after erring -1 for none
ERR_MAX_T = 60  # Max timeout between attempts in minutes

# Program variables no touchy
currTry = 0
currTime = ERR_TIME
currIp = ''
headers = {'Authorization': 'Bearer ' + API_TOKEN, 'Content-Type': "application/json"}
url = API_URL + ZONE_ID + '/dns_records/' + ID


def ResetErr():
    global currTry, currTime
    currTry = 0
    currTime = ERR_TIME


def TickErr(e):
    if str(e).find('FATAL') != -1:
        raise e
    global currTry, currTime
    currTry += 1
    if ERR_MAX_A != -1 and currTry > ERR_MAX_A:
        raise e
    print(f'error {e} encountered, trying again in:{currTime} minutes')
    sleep(currTime * 60)
    currTime += ERR_TIME_INC
    if currTime > ERR_MAX_T:
        currTime = ERR_MAX_T


def dictToList(dic):
    a = []
    for item in dic.items():
        a += list(item)
    b = []
    for item in a:
        b.append(str(item))
    return b


# Main Loop
while True:
    response = None
    # Get Current IP
    while True:
        try:
            response = requests.get(url, headers=headers)
            json = response.json()
            if not json['success']:
                raise Exception('Api returned errors: ' + ', '.join(dictToList(json['errors'][0])))
            if json['result']['name'] != HOSTNAME:
                raise Exception('FATAL: ZONE_ID or ID Do not belong to Hostname:' + HOSTNAME)
            currIp = json['result']['content']
            ResetErr()
            break
        except Exception as e:
            TickErr(e)
    # Get external ip
    while True:
        try:
            response = requests.get(IP_SERVICE)
            if response.status_code != 200:
                raise Exception(f'Error getting external ip:{response.status_code}')  # Raises an exception if an error has occured getting ip
            ResetErr()
            break
        except Exception as e:
            TickErr(e)
    ip = response.json()['ip']
    if currIp != ip:
        while True:
            try:
                data = {'type': 'A', 'name': HOSTNAME, 'content': ip, 'ttl': TTL, 'proxied': PROXY}
                response = requests.put(url, headers=headers, data=dumps(data))
                json = response.json()
                if not json['success']:
                    raise Exception('Api returned errors: ' + ', '.join(dictToList(json['errors'][0])))
                print(f'Changed ip from {currIp} to {ip}')
                ResetErr()
                break
            except Exception as e:
                TickErr(e)
    else:
        print(f'Ip in DNS: {currIp}. Ip from {IP_SERVICE}: {ip}')
    print(f'Waiting {TIME} Minutes...')
    sleep(TIME * 60)


