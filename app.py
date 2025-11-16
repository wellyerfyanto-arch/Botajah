from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import json
import time
import threading
import os
from session_manager import SessionManager
import logging
from datetime import datetime

app = Flask(__name__)

# Global variables
automation_thread = None
is_running = False
current_session = None
session_stats = {
    'sessions_completed': 0,
    'tabs_opened': 0,
    'ads_clicked': 0,
    'start_time': None
}

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamLogger:
    def __init__(self):
        self.listeners = []
    
    def log(self, message, level='info'):
        log_entry = {
            'type': 'log',
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        }
        self._emit(log_entry)
        logger.info(f"{level.upper()}: {message}")
    
    def update_stats(self, stats):
        stats_entry = {
            'type': 'stats',
            'data': stats
        }
        self._emit(stats_entry)
    
    def update_status(self, status):
        status_entry = {
            'type': 'status',
            'message': status
        }
        self._emit(status_entry)
    
    def _emit(self, data):
        for listener in self.listeners:
            try:
                listener.append(json.dumps(data) + '\n')
            except:
                self.listeners.remove(listener)

stream_logger = StreamLogger()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_automation():
    global automation_thread, is_running, current_session, session_stats
    
    if is_running:
        return jsonify({'success': False, 'error': 'Automation is already running'})
    
    config = request.json
    stream_logger.log('Starting automation session...', 'info')
    
    # Reset stats
    session_stats = {
        'sessions_completed': 0,
        'tabs_opened': 0,
        'ads_clicked': 0,
        'start_time': datetime.now().isoformat()
    }
    
    is_running = True
    current_session = SessionManager()
    
    automation_thread = threading.Thread(
        target=run_automation_session,
        args=(config,)
    )
    automation_thread.daemon = True
    automation_thread.start()
    
    return jsonify({'success': True})

@app.route('/stop', methods=['POST'])
def stop_automation():
    global is_running
    
    if not is_running:
        return jsonify({'success': False, 'error': 'No automation running'})
    
    is_running = False
    stream_logger.log('Stopping automation...', 'info')
    stream_logger.update_status('Stopping')
    
    return jsonify({'success': True})

@app.route('/stream')
def stream():
    def generate():
        messages = []
        stream_logger.listeners.append(messages)
        try:
            while True:
                if messages:
                    message = messages.pop(0)
                    yield f"data: {message}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                    time.sleep(1)
        except GeneratorExit:
            if messages in stream_logger.listeners:
                stream_logger.listeners.remove(messages)
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/status')
def status():
    return jsonify({
        'running': is_running,
        'stats': session_stats
    })

def run_automation_session(config):
    global is_running, session_stats
    
    try:
        # Prepare search queries
        search_queries = [config.get('search_query', 'python programming')]
        custom_urls = config.get('custom_urls', [])
        if custom_urls:
            search_queries.extend([url.strip() for url in custom_urls if url.strip()])
        
        session_count = config.get('session_count', 1)
        search_queries_list = [search_queries] * session_count
        
        stream_logger.log(f'Starting {len(search_queries_list)} sessions', 'info')
        stream_logger.update_status('Running')
        
        # Run sessions
        for i, queries in enumerate(search_queries_list):
            if not is_running:
                break
                
            stream_logger.log(f'Session {i+1} started', 'info')
            
            # Update config for this session
            session_config = {
                'tab_count': config.get('tab_count', 3),
                'device_type': config.get('device_type', 'random'),
                'vpn_extension': config.get('vpn_extension', 'random')
            }
            
            # Run session
            success = current_session.create_session(queries, session_config)
            
            if success:
                session_stats['sessions_completed'] += 1
                session_stats['tabs_opened'] += session_config['tab_count']
                # Simulate some ads clicked
                session_stats['ads_clicked'] += 1
                stream_logger.update_stats(session_stats)
                stream_logger.log(f'Session {i+1} completed successfully', 'success')
            else:
                stream_logger.log(f'Session {i+1} failed', 'error')
            
            # Wait between sessions if not last session
            if i < len(search_queries_list) - 1 and is_running:
                wait_time = 10  # 10 seconds between sessions for demo
                stream_logger.log(f'Waiting {wait_time} seconds before next session...', 'info')
                for j in range(wait_time):
                    if not is_running:
                        break
                    time.sleep(1)
        
        if is_running:
            stream_logger.log('All sessions completed!', 'success')
            stream_logger.update_status('Completed')
        else:
            stream_logger.log('Automation stopped by user', 'info')
            stream_logger.update_status('Stopped')
            
    except Exception as e:
        stream_logger.log(f'Automation error: {str(e)}', 'error')
        stream_logger.update_status('Error')
    
    finally:
        is_running = False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
