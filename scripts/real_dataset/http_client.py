"""Serial, cached, bounded Wikimedia reads. No authentication or write APIs."""
import gzip,io,json,re,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from .core import HOSTS,atomic_json,load_json,sha_bytes
class CollectionBlocked(RuntimeError):pass
class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        old,new=urllib.parse.urlsplit(req.full_url),urllib.parse.urlsplit(newurl)
        if new.scheme!='https' or new.hostname!=old.hostname:raise CollectionBlocked('Cross-host redirect refused')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def validate_contact(contact):
    if not contact or len(contact)>300 or any(ch in contact for ch in '\r\n'):raise CollectionBlocked('Wikimedia requires a user-supplied operator contact')
    email=re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',contact)
    url=urllib.parse.urlsplit(contact)
    wiki=re.fullmatch(r'\([\w:.-]+; User:[^\r\n]+\)',contact)
    if not (email or wiki or (url.scheme=='https' and url.hostname)):raise CollectionBlocked('Contact must be an email, HTTPS project URL or Wikimedia user reference')
    if re.search(r'example\.(?:com|org|net)|<|>|YOUR_|\.invalid',contact,re.I):raise CollectionBlocked('Placeholder contact is not valid')
    return contact
class ApiClient:
    def __init__(self,host,cache_dir,user_agent,interval=1.0,retries=3,max_requests=300,transport=None,sleep=time.sleep,clock=time.monotonic):
        if host not in HOSTS:raise ValueError('Source not allowlisted')
        self.host=host;self.cache=Path(cache_dir);self.ua=user_agent;self.interval=interval;self.retries=retries;self.max_requests=max_requests;self.requests=0;self.sleep=sleep;self.clock=clock;self.last=None
        self.transport=transport or self._network
    def _network(self,url):
        req=urllib.request.Request(url,headers={'User-Agent':self.ua,'Accept':'application/json','Accept-Encoding':'gzip'})
        with urllib.request.build_opener(SameHostRedirect()).open(req,timeout=25) as response:
            body=response.read(20_000_001)
            if len(body)>20_000_000:raise CollectionBlocked('API response size limit')
            if response.headers.get('Content-Encoding')=='gzip':body=gzip.GzipFile(fileobj=io.BytesIO(body)).read(30_000_001)
            if len(body)>30_000_000:raise CollectionBlocked('Decompressed API response size limit')
            return json.loads(body)
    def get(self,params):
        if params.get('action') not in ('query','paraminfo','discussiontoolspageinfo'):raise ValueError('Read-only API allowlist')
        params={**params,'format':'json','formatversion':2,'maxlag':5}
        query=urllib.parse.urlencode(sorted(params.items()));key=sha_bytes((self.host+'?'+query).encode());path=self.cache/(key+'.json')
        if path.exists():return load_json(path),sha_bytes(path.read_bytes())
        url='https://'+self.host+'/w/api.php?'+query
        for attempt in range(self.retries):
            if self.requests>=self.max_requests:raise CollectionBlocked('Request budget exhausted')
            if self.last is not None:self.sleep(max(0,self.interval-(self.clock()-self.last)))
            self.requests+=1;self.last=self.clock()
            try:
                data=self.transport(url)
                if 'error' in data:
                    if data['error'].get('code') in ('maxlag','ratelimited','readonly'):
                        self.sleep(min(30,2**(attempt+1)));continue
                    raise CollectionBlocked('API error: '+str(data['error'].get('code','unknown')))
                atomic_json(path,data);return data,sha_bytes(path.read_bytes())
            except urllib.error.HTTPError as exc:
                if exc.code not in (429,500,502,503,504):raise CollectionBlocked('HTTP '+str(exc.code)) from None
                retry=exc.headers.get('Retry-After','0') if exc.headers else '0'
                self.sleep(min(60,max(2**(attempt+1),int(retry) if retry.isdigit() else 0)))
            except (urllib.error.URLError,TimeoutError):
                self.sleep(min(30,2**(attempt+1)))
        raise CollectionBlocked('Bounded retries exhausted')
