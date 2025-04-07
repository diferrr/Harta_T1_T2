import pymysql
import pyodbc
import requests
import lxml.etree
from pymysql.cursors import DictCursor

# ============ КОНФИГ ============
MYSQL_CONFIG = {
    'host': '10.1.1.174',
    'user': 'victor',
    'password': 'Sursa2@!',
    'database': 'access_user',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

SQLSERVER_CONFIG = {
    'driver': '{SQL Server}',
    'server': '10.1.1.124',
    'database': 'TERMOCOM5',
    'uid': 'disp',
    'pwd': 'disp123'
}

IPS = {
    1: "sql",
    2: "10.1.1.214",
    3: "10.1.1.173",
    4: "10.1.1.242",
    5: "10.2.1.153",
    6: "10.2.1.154",
    7: "10.3.1.139"
}

# ============ CONNECTORS ============
def connect_mysql():
    return pymysql.connect(**MYSQL_CONFIG)

def connect_sql_server():
    conn_str = f"DRIVER={SQLSERVER_CONFIG['driver']};" \
               f"SERVER={SQLSERVER_CONFIG['server']};" \
               f"DATABASE={SQLSERVER_CONFIG['database']};" \
               f"UID={SQLSERVER_CONFIG['uid']};PWD={SQLSERVER_CONFIG['pwd']}"
    return pyodbc.connect(conn_str)

# ============ HELPERS ============
def get_scada_value(ip, param_id):
    try:
        url = f"http://{ip}/cgi-bin/xml/getcv.pl?params={param_id}"
        xml = requests.get(url, timeout=5).content
        root = lxml.etree.fromstring(xml)
        for val in root.findall("value"):
            return round(float(val.text), 2)
    except Exception as e:
        print(f"[SCADA ERROR] {ip} param={param_id} → {e}")
        return None

def get_sqlserver_temperatures():
    data = {}
    conn = connect_sql_server()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            u.UNIT_NAME as name, 
            ROUND(mc.MC_T1_VALUE_INSTANT, 2) as T1, 
            ROUND(mc.MC_T2_VALUE_INSTANT, 2) as T2
        FROM UNITS u
        LEFT JOIN MULTICAL_CURRENT_DATA mc ON u.UNIT_ID = mc.UNIT_ID
    """)
    for row in cursor.fetchall():
        name = row[0].replace("PT_", "").lower()
        data[name] = {'T1': row[1], 'T2': row[2]}
    conn.close()
    return data

# ============ API FUNCTION ============
def get_live_temperature(param_name):
    name = param_name.lower().replace("pt_", "")
    sql_fallback = get_sqlserver_temperatures()

    with connect_mysql() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    REPLACE(m.param_name, 'PT_', '') as name,
                    m.id_T1, m.id_T2,
                    m.datasource_id as ips,
                    d.address as ip
                FROM map_markers m
                JOIN datasources_http d ON m.datasource_id = d.id
                WHERE LOWER(REPLACE(m.param_name, 'PT_', '')) = %s
            """, (name,))
            row = cursor.fetchone()

    if not row:
        return None, None

    ip_id = row['ips']
    param_T1 = row['id_T1']
    param_T2 = row['id_T2']

    t1 = t2 = None

    if ip_id == 1:
        temps = sql_fallback.get(name, {})
        t1 = temps.get('T1')
        t2 = temps.get('T2')
    else:
        ip = IPS.get(ip_id)
        if ip and param_T1:
            t1 = get_scada_value(ip, param_T1)
        if ip and param_T2:
            t2 = get_scada_value(ip, param_T2)

    return t1, t2

# ============ MAIN FUNCTION ============
def get_all_temperatures():
    sql_fallback = get_sqlserver_temperatures()

    with connect_mysql() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    REPLACE(m.param_name, 'PT_', '') as name,
                    m.id_T1, m.id_T2,
                    m.datasource_id as ips,
                    d.address as ip
                FROM map_markers m
                JOIN datasources_http d ON m.datasource_id = d.id
            """)
            rows = cursor.fetchall()

    for row in rows:
        name = row['name'].lower()
        ip_id = row['ips']
        param_T1 = row['id_T1']
        param_T2 = row['id_T2']

        t1 = t2 = None

        if ip_id == 1:
            temps = sql_fallback.get(name, {})
            t1 = temps.get('T1')
            t2 = temps.get('T2')
        else:
            ip = IPS.get(ip_id)
            if ip and param_T1:
                t1 = get_scada_value(ip, param_T1)
            if ip and param_T2:
                t2 = get_scada_value(ip, param_T2)

        print(f"▶ Объект: PT_{name.upper()} (ID: {ip_id})")
        print(f"   T1: {t1 if t1 is not None else '—'} °C")
        print(f"   T2: {t2 if t2 is not None else '—'} °C\n")

if __name__ == "__main__":
    get_all_temperatures()
