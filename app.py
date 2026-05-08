import os
import requests
import urllib3
from flask import Flask, request, Response, send_file

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'SARMAAN_Dashboard_Enhanced.html'))


@app.route('/proxy')
def proxy():
    url = request.args.get('url', '').strip()
    if not url:
        return 'Missing url parameter', 400
    try:
        resp = requests.get(
            url,
            verify=False,
            timeout=60,
            headers={
                'User-Agent': 'SARMAAN-Dashboard/1.0',
                'Accept': (
                    'application/vnd.openxmlformats-officedocument'
                    '.spreadsheetml.sheet, application/json, */*'
                ),
            },
        )
        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get(
                'Content-Type', 'application/octet-stream'
            ),
            headers={'Access-Control-Allow-Origin': '*'},
        )
    except Exception as exc:
        return str(exc), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
