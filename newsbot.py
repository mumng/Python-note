import discord
import asyncio

# collection 레벨에서 API 이용 데이터 수집
# https://docs.opensea.io/reference/get_collection_stats
import requests

from datetime import datetime, timedelta
import json

intents = discord.Intents.default()  # 모든 기본 intents 활성화
intents.messages = True              # 메시지를 받기 위해
intents.message_content = True       # 메시지 내용에 접근하기 위해
intents.members = True               # 서버의 멤버 리스트에 접근하기 위해

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    # 1분간격으로 특정 디스코드 채널에 메세지 입력
    channel = client.get_channel(986431193933316182)
    while True:
        await channel.send('정기 - daily nft news 메세지 입니다' + '\n' + document_content)
        await asyncio.sleep(60)

@client.event
async def on_message(message):
    # 봇이 보낸 메시지인 경우 무시
    if message.author == client.user:
        return
    
    # '!hello' 메시지에 반응
    if message.content.startswith('!뉴스'):
        await message.channel.send('반응형 - daily nft news 메세지 입니다' + '\n' + document_content)

def opensea_api_data(url):
    headers = {
        "accept": "application/json",
        "x-api-key": "14f8b22ea12a4d0da370b5372e9c7112"
    }
    
    response = requests.get(url, headers=headers)

    # JSON 형식으로 응답 데이터 파싱
    data = response.json()

    # 결과 출력
#    print(data)
    return data

def process_data(data):
    # 'asset_events' 키에서 거래 내역을 추출합니다.
    events = data['asset_events']

    # 현재 시간을 구하고, 24시간 전의 시간을 계산합니다.
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)

    # 최근 24시간 동안의 거래만 필터링합니다.
    recent_events = [event for event in events if datetime.fromtimestamp(event['event_timestamp']) > one_day_ago]

    # 거래 정보와 컬렉션별 횟수를 저장할 리스트를 준비합니다.
    transaction_data = []
    collection_count = {}

    # 필터링된 거래 정보를 리스트에 추가하고, 컬렉션별 횟수를 계산합니다.
    for event in recent_events:
        event_time = datetime.fromtimestamp(event['event_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        collection_name = event['nft']['collection']
        payment_amount = int(event['payment']['quantity']) / (10**event['payment']['decimals'])
        
        # 컬렉션별 횟수를 계산
        if collection_name in collection_count:
            collection_count[collection_name] += 1
        else:
            collection_count[collection_name] = 1
        
        # 거래 정보를 리스트에 추가
        transaction_data.append({
            "event_time": event_time,
            "seller": event['seller'],
            "buyer": event['buyer'],
            "nft_name": event['nft']['name'],
            "collection": collection_name,
            "payment_amount": payment_amount,
            "payment_currency": event['payment']['symbol'],
            "transaction_id": event['transaction']
        })

    # print(transaction_data)
    # print(collection_count)
    data_json = json.dumps({
        "transaction_data": transaction_data,
        "collection_count": collection_count
    })

    return data_json

def ask_chatgpt(data_json):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",  # 여기서 YOUR_API_KEY에 실제 API 키를 넣어주세요.
        "Content-Type": "application/json",
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "당신은 NFT와 블록체인 분야에 대해 모든 것을 알고 있고 매우 뛰어난 능력을 가진 기자입니다. 당신은 주어진 NFT에 관한 데이터를 기반으로 알기쉽고, 체계적이며, 전문성 있는 기사를 만들어줍니다."},
            {"role": "user", "content": "최근 24시간 동안의 NFT 거래 데이터를 기반으로 트렌드를 알려주는 기사를 만들어줘. NFT 관련자 및 투자자들에게 흥미있고, 투자에 도움이 될 기사를 만들어줘. 제목은 최근 24시간 OPENSEA NFT 거래 트렌드이고, 항목은 1. 전체 거래 횟수와 거래량, 2. 거래횟수 상위 컬랙션 및 NFT, 3. 거래금액 상위 컬렉션 및 NFT, 4. 거래금액 상위 투자자 및 거래금액, 5. 총평 등 형식으로 구체적 데이터를 기반으로 읽기쉽고 보기좋게 기사를 만들어 주세요. 여기 데이터입니다: " + data_json}
        ]
    }
    response = requests.post(api_url, headers=headers, json=data)
    
    if response.status_code != 200:
        print("Failed to get a valid response:", response.status_code)
        print(response.text)  # 오류 메시지를 확인하기 위해 응답 내용을 출력합니다.
        return None
    try:
        return response.json()['choices'][0]['message']['content']
    except KeyError:
        print("KeyError in response:", response.json())  # KeyError가 발생한 경우 응답 내용을 출력
        return None

# opensea api에서 collection data 받아오기
opensea_data = opensea_api_data("https://api.opensea.io/api/v2/events?event_type=sale")

# data 처리
data_json = process_data(opensea_data)

# data를 chtGPT에게 전달해서 기사 리턴
global document_content
document_content = ask_chatgpt(data_json)

# 봇을 실행합니다. 여기서 'YOUR_TOKEN_HERE'는 실제 봇 토큰으로 교체해야 합니다.
client.run('MTIyOTYxMTMxOTUxMTIyNDQwNA.GRX5qD.LpBF0bMAi3pgl_hwuevA49HwAn8VLk1Gb02J4A')
