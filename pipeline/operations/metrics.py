"""Safe counters only: no URLs, parameters, payloads or exception strings."""
from collections import Counter

class Metrics:
    def __init__(self):
        self.api_request_count=0; self.api_response_seconds=0.0
        self.public_page_request_count=0; self.public_page_response_seconds=0.0
        self.retry_count=0; self.errors=Counter()

    def record(self,kind,seconds,error=None):
        if kind=='api':
            self.api_request_count+=1; self.api_response_seconds+=seconds
        else:
            self.public_page_request_count+=1; self.public_page_response_seconds+=seconds
        if error: self.errors[error]+=1

    def report(self):
        return {'api_request_count':self.api_request_count,'public_page_request_count':self.public_page_request_count,'total_http_request_count':self.api_request_count+self.public_page_request_count,'retry_count':self.retry_count,'api_response_seconds':round(self.api_response_seconds,6),'average_api_response_seconds':round(self.api_response_seconds/self.api_request_count,6) if self.api_request_count else None,'public_page_response_seconds':round(self.public_page_response_seconds,6),'transport_error_summary':dict(self.errors)}
