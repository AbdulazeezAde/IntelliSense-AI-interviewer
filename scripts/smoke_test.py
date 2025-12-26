from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
print('GET / ->', c.get('/').status_code)
print('POST /v1/sessions/start ->', c.post('/v1/sessions/start', json={'session_id':'demo','user_id':'u1','interview_type':'behavioral','persona':'friendly'}).status_code)
print('POST /v1/tts/generate ->', c.post('/v1/tts/generate', json={'session_id':'demo','text':'Hello there','persona':'friendly'}).status_code)

# Test websocket sim_transcript
with c.websocket_connect('/v1/ws/audio/demo') as ws:
    ws.send_json({'type':'sim_transcript','transcript':'I was nervous but I fixed it'})
    msg = ws.receive_json()
    print('WS received type', msg.get('type'))
    if msg.get('type') == 'turn_result':
        print('turn_result contains stt:', 'stt' in msg['result'])

print('smoke tests done')
