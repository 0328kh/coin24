import threading
import time
import pyupbit
import datetime
import schedule
from prophet import Prophet

access = "ASNWxupj3DmBAJUrx4j7MqQS0gQgFHQj7BkF4r4e"
secret = "fobm7pIUKXMjuVCWkJbWWnjfugl9lkxctVBQlaIl"

stop_event = threading.Event()  # 스레드 종료를 위한 이벤트

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = pyupbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def trade_crypto(ticker, k):
    """코인 자동매매 로직"""
    predicted_close_price = 0
    def predict_price():
        nonlocal predicted_close_price
        df = pyupbit.get_ohlcv(ticker, interval="minute60")
        df = df.reset_index()
        df['ds'] = df['index']
        df['y'] = df['close']
        data = df[['ds','y']]
        model = Prophet()
        model.fit(data)
        future = model.make_future_dataframe(periods=24, freq='H')
        forecast = model.predict(future)
        closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
        if len(closeDf) == 0:
            closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
        closeValue = closeDf['yhat'].values[0]
        predicted_close_price = closeValue

    predict_price()
    schedule.every().hour.do(predict_price)

    # 로그인
    upbit = pyupbit.Upbit(access, secret)
    print(f"autotrade start for {ticker}")

    # 자동매매 시작
    while not stop_event.is_set():  # 스레드 종료 시 stop_event로 루프 빠져나옴
        try:
            now = datetime.datetime.now()
            start_time = get_start_time(ticker)
            end_time = start_time + datetime.timedelta(days=1)
            schedule.run_pending()

            if start_time < now < end_time - datetime.timedelta(seconds=10):
                target_price = get_target_price(ticker, k)
                current_price = get_current_price(ticker)
                print(f"{ticker}: target {target_price}, current {current_price}, closeValue {predicted_close_price}")
                if target_price < current_price and current_price < predicted_close_price:
                    krw = get_balance("KRW")
                    if krw > 5000:
                        upbit.buy_market_order(ticker, krw*0.9995)
                        print(f"{ticker}: 샀다")
            else:
                crypto_balance = get_balance(ticker.split('-')[1])
                if crypto_balance > 0.00008:
                    upbit.sell_market_order(ticker, crypto_balance*0.9995)
            time.sleep(1)
        except Exception as e:
            print(f"Error on {ticker}: {e}")
            time.sleep(1)

# 여러 코인을 동시에 자동매매 실행
tickers = ["KRW-BTC","KRW-SOL","KRW-XRP","KRW-DOGE","KRW-ETH"]
k_value = 0.5 

threads = []
for ticker in tickers:
    thread = threading.Thread(target=trade_crypto, args=(ticker, k_value))
    thread.start()
    threads.append(thread)

try:
    # 메인 스레드가 대기하도록 함
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Keyboard Interrupt detected, stopping threads...")
    stop_event.set()  # 스레드 종료 신호 보내기

# 모든 스레드가 종료될 때까지 대기
for thread in threads:
    thread.join()

print("Program terminated")
