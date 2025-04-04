import requests
import pymysql
from lxml import etree
from datetime import datetime, timedelta
import pytz

# ==== НАСТРОЙКИ БД ====
DB_CONFIG = {
    'host': '10.1.1.174',
    'user': 'victor',
    'password': 'Sursa2@!',  # Укажи свой
    'database': 'access_user',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# ==== ВРЕМЯ (UTC → сейчас - 1 час) ====
chisinau = pytz.timezone("Europe/Chisinau")
now = datetime.now(tz=pytz.utc)
start_ts = int((now - timedelta(hours=1)).timestamp())
stop_ts = int(now.timestamp())

# ==== SCADA URL ====
URL_TEMPLATE = "http://{ip}/cgi-bin/xml/getrep.pl?param={param}&start={start}&stop={stop}"

# ==== ПАРСИНГ XML ====
def get_latest_value_from_xml(xml_content):
    root = etree.fromstring(xml_content)
    records = root.findall(".//record")
    if not records:
        return None
    last = records[-1]
    return last.findtext("value")

# ==== ОСНОВНОЙ СКРИПТ ====
def show_temperatures():
    connection = pymysql.connect(**DB_CONFIG)
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT m.param_name, m.id_T1, m.id_T2, d.address as ip
                FROM map_markers m
                JOIN datasources_http d ON m.datasource_id = d.id
            """)
            markers = cursor.fetchall()

            for row in markers:
                name = row['param_name']
                id_T1 = row['id_T1']
                id_T2 = row['id_T2']
                ip = row['ip']
                new_t1 = new_t2 = None

                if id_T1:
                    try:
                        url1 = URL_TEMPLATE.format(ip=ip, param=id_T1, start=start_ts, stop=stop_ts)
                        xml1 = requests.get(url1, timeout=5).content
                        new_t1 = get_latest_value_from_xml(xml1)
                    except Exception as e:
                        print(f"[T1] Ошибка: {ip} → {e}")

                if id_T2:
                    try:
                        url2 = URL_TEMPLATE.format(ip=ip, param=id_T2, start=start_ts, stop=stop_ts)
                        xml2 = requests.get(url2, timeout=5).content
                        new_t2 = get_latest_value_from_xml(xml2)
                    except Exception as e:
                        print(f"[T2] Ошибка: {ip} → {e}")

                print(f"▶ Объект: {name} (IP: {ip})")
                print(f"   T1: {new_t1 or '—'} °C")
                print(f"   T2: {new_t2 or '—'} °C\n")

if __name__ == "__main__":
    show_temperatures()
