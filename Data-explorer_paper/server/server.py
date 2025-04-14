from http.server import HTTPServer, BaseHTTPRequestHandler
import glob
import json
import cgi
import os
import matplotlib as mpl
import matplotlib.style as mplstyle
import mpld3
import webbrowser

import helper


class Serv(BaseHTTPRequestHandler):
    namespace = {}

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def init(self):
        scripts = []
        step = 1
        for filename in glob.glob('..\\scripts\\*.py'):
            with open(filename, 'r') as f:  # open in readonly mode
                text = f.read()
                name = filename.replace("..\\scripts\\", "").replace(".py", "")
                scripts.append({'name': name, 'skript': text})
                step += 1

        mpl.rcParams['path.simplify'] = True
        mpl.rcParams['path.simplify_threshold'] = 1.0
        mplstyle.use('fast')
        initial_script_ns = {
            'mpl': mpl,
            'mplstyle': mplstyle
        }

        res = helper.exec_code_as_string(open('./initialScript.py').read(), initial_script_ns, False)

        plots = []

        if 'plt' in initial_script_ns:
            plt = initial_script_ns['plt']
            fig1 = plt.gcf()
            plot_height = max(5, len(fig1.get_axes()) * 1.5)
            fig1.set_size_inches(15, plot_height)
            fig1.tight_layout(pad=0.1)
            plot1 = mpld3.fig_to_dict(fig1)
            fig2 = plt.gcf()
            fig2.set_size_inches(6, plot_height)
            fig2.tight_layout(pad=0.1)
            plot2 = mpld3.fig_to_dict(fig2)
            plt.close('all')
            plots.append(plot1)
            plots.append(plot2)

        self._set_headers()
        self.wfile.write(bytes(json.dumps({
            'plots': plots,
            'scripts': scripts,
            'error': res['error'],
            'console': res['console']
        }), 'utf-8'))

    def run_script(self, message):
        script = message['script']

        if 'isResetNameSpace' in message and message['isResetNameSpace'] is True:
            print('reset namespace')
            self.namespace.clear()


        res = helper.exec_code_as_string(script, self.namespace, True)

        self._set_headers()
        self.wfile.write(bytes(json.dumps(res), 'utf-8'))

    def save_initial_script(self, message):
        initial_script = message['initialScript']
        initial_script_file = open('./initialScript.py', 'w')
        initial_script_file.write(initial_script)
        initial_script_file.close()

        self._set_headers()
        self.wfile.write(bytes(json.dumps(message), 'utf-8'))

    def create_or_update_script(self, message):
        script_name = message['scriptName']
        script_text = message['scriptText']
        script_file = open('../scripts/' + script_name + '.py', 'w')
        script_file.write(script_text)
        script_file.close()

        self._set_headers()
        self.wfile.write(bytes(json.dumps(message), 'utf-8'))

    def delete_script(self, message):
        script_name = message['scriptName']
        file_path = '../scripts/' + script_name + '.py'

        if os.path.exists(file_path):
            os.remove(file_path)

        self._set_headers()

    def do_GET(self):
        print('GET', self.path)
        if self.path == '/':
            self.path = '/index.html'

        if self.path == '/initData':
            self.init()
        elif self.path == '/initialScript':
            try:
                print('toOpen', './initialScript.py' + self.path)
                file_to_open = open('./initialScript.py').read()
                self.send_response(200)
            except:
                file_to_open = "File not found"
                self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes(file_to_open, 'utf-8'))
        else:
            try:
                print('toOpen', '../frontend/dist' + self.path)
                file_to_open = open('../frontend/dist' + self.path).read()
                self.send_response(200)
            except:
                file_to_open = "File not found"
                self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes(file_to_open, 'utf-8'))

    def do_POST(self):
        print('POST', self.path)
        ctype, pdict = cgi.parse_header(self.headers.get_content_type())

        # refuse to receive non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return

        # read the message and convert it into a python dictionary
        length = int(self.headers.get_all('content-length')[0])
        message = json.loads(self.rfile.read(length))

        if self.path == '/script':
            self.run_script(message)
        elif self.path == '/initialScript':
            self.save_initial_script(message)
        elif self.path == '/createOrUpdateScript':
            self.create_or_update_script(message)
        elif self.path == '/deleteScript':
            self.delete_script(message)


webbrowser.open_new('http://localhost:8080')
httpd = HTTPServer(('localhost', 8080), Serv)
httpd.serve_forever()

