import os
import json
import urllib.request
import urllib.parse
from urllib.error import HTTPError
import ssl
from flask import Flask, request, Response, send_file

app = Flask(__name__)

HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SARMAAN_Dashboard_Enhanced.html')


@app.route('/')
def index():
    return send_file(HTML_FILE)


@app.route('/proxy', methods=['OPTIONS'])
def proxy_preflight():
    return Response('', status=200, headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    })


@app.route('/proxy', methods=['GET'])
def proxy():
    kobo_url = request.args.get('url', '').strip()
    if not kobo_url:
        return Response(
            json.dumps({'error': 'Missing url parameter'}),
            status=400, mimetype='application/json',
            headers={'Access-Control-Allow-Origin': '*'},
        )

    is_xlsx = '.xlsx' in kobo_url.lower()
    is_csv  = '.csv'  in kobo_url.lower()

    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    if is_xlsx:
        req_headers['Accept'] = (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, */*'
        )
    elif is_csv:
        req_headers['Accept'] = 'text/csv, application/csv, text/plain, */*'
    else:
        req_headers['Accept'] = 'application/json, */*'

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(kobo_url, headers=req_headers)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=60) as resp:
            data = resp.read()

        content_type = (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            if is_xlsx else 'text/csv' if is_csv else 'application/json'
        )
        return Response(data, status=200, mimetype=content_type,
                        headers={'Access-Control-Allow-Origin': '*'})

    except HTTPError as e:
        body = json.dumps({'error': f'KoboToolbox returned HTTP {e.code}',
                           'message': str(e.reason)})
        return Response(body, status=e.code, mimetype='application/json',
                        headers={'Access-Control-Allow-Origin': '*'})

    except Exception as e:
        body = json.dumps({'error': 'Proxy error', 'message': str(e)})
        return Response(body, status=500, mimetype='application/json',
                        headers={'Access-Control-Allow-Origin': '*'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8765))
    app.run(host='0.0.0.0', port=port, debug=False)
