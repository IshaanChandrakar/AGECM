"""Read-only local fixture server. No real channel IDs or credentials."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from datetime import datetime,timezone,timedelta
import json,time
# Absolute-time entry IDs remain monotonic across fixture-server restarts.
LABELS=['Temp','Humidity','CO max','CH4 max','Dist Now','Dev max','Status worst','Fault any']
def entry(channel,n):
 node=1 if channel==100 else 2
 phase=n%40
 values=[20+node+phase/100,50+node,0,0,100+node,phase/10,n//10%3,n%2]
 return dict(entry_id=n,created_at=datetime.fromtimestamp(n*3,timezone.utc).isoformat(),**{f'field{i}':str(v) for i,v in enumerate(values,1)})
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  parsed=urlparse(self.path);parts=parsed.path.split('/');query=parse_qs(parsed.query)
  try:
   channel=int(parts[2]);node=1 if channel==100 else 2
   if channel not in (100,200) or query.get('api_key',[''])[0]!=f'fixture-read-{node}':raise ValueError()
   count=max(1,min(8000,int(query.get('results',['100'])[0])))
   latest=int(time.time()/3)
   body={'channel':dict(id=channel,**{f'field{i}':v for i,v in enumerate(LABELS,1)}),'feeds':[entry(channel,n) for n in range(max(1,latest-min(count,100)+1),latest+1)]}
   self.send_response(200)
  except (ValueError,IndexError):self.send_response(401);body={'error':'Fixture authorization failed'}
  self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(body).encode())
ThreadingHTTPServer(('0.0.0.0',8090),Handler).serve_forever()
