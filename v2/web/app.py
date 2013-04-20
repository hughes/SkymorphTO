from flask import Flask, request, redirect, session, url_for, render_template, Response, jsonify, make_response
from flask.ext.assets import Environment
import json
import simplekml


import api
from skymorph import skymorph

app = Flask(__name__)
app.secret_key = 'not a secret key'

# bundling
assets = Environment(app)


def convert(triplet_str):
    a = [float(t) for t in triplet_str.split()]
    result = a[0] + a[1] / 60 + a[2] / 3600
    if a[0] < 0:
        result = -result
    return result


# main routes/api routes
@app.route("/")
def index():
    return render_template('index.html')


@app.route("/friendly")
def friendly():
    return render_template('friendly.html')


@app.route("/api/kml/search")
def kml_search():
    target = request.args.get('target')
    # Get skymorph images (this takes quite some time)
    results = skymorph.search_target(target)

    images = []

    kml = simplekml.Kml()
    # This is KML for Google Sky
    kml.hint = 'target=sky'

    # Iterate over each image result and simplify it
    for img in results:
        i = {}
        i['src'] = 'http://www.asterank.com/api/skymorph/image?key=%s' % img['key']
        i['ra'] = convert(img['center_ra'])
        i['dec'] = convert(img['center_dec'])
        i['east'] = i['ra'] + 0.5
        i['west'] = i['ra'] - 0.5
        i['north'] = i['dec'] + 0.5
        i['south'] = i['dec'] - 0.5

        # TODO: fix this
        i['rotation'] = 0

        i['time'] = img['time']

        i['placemarkX'] = convert(img['predicted_ra'])
        i['placemarkY'] = convert(img['predicted_dec'])

        images.append(i)

        overlay = kml.newgroundoverlay(name=target)
        overlay.icon.viewboundscale = 0.75
        overlay.icon.href = i.get('src')

        # full opacity!
        overlay.color = 'ffffffff'

        overlay.lookat = simplekml.LookAt()
        overlay.lookat.longitude = i.get('ra')
        overlay.lookat.latitude = i.get('dec')
        overlay.lookat.tilt = 0
        # TODO: fix this
        overlay.lookat.range = 110658
        overlay.lookat.gxaltitudemode = 'relativeToSeaFloor'
        overlay.lookat.gxtimestamp = simplekml.GxTimeStamp(when=i.get('time'))

        overlay.latlonbox = simplekml.LatLonBox(
            north=i.get('north'),
            south=i.get('south'),
            east=i.get('east'),
            west=i.get('west'),
            rotation=0)  # TODO: rotation

        kml.newpoint(name=target, coords=[
            (i.get('placemarkX'), i.get('placemarkY'))
        ])

    return Response(kml.kml(), mimetype='application/vnd.google-earth.kml+xml')


@app.route('/api/mpc')
def api_mpc():
    try:
        query = json.loads(request.args.get('query'))
        limit = min(1000, int(request.args.get('limit')))
        json_resp = json.dumps(api.mpc(query, limit))
        return Response(json_resp, mimetype='application/json')
    except:
        resp = jsonify({'error': 'bad request'})
        resp.status_code = 500
        return resp


@app.route('/api/kepler')
def api_kepler():
    try:
        query = json.loads(request.args.get('query'))
        limit = min(1000, int(request.args.get('limit')))
        json_resp = json.dumps(api.kepler(query, limit))
        return Response(json_resp, mimetype='application/json')
    except:
        resp = jsonify({'error': 'bad request'})
        resp.status_code = 500
        return resp


@app.route('/api/exoplanets')
def api_exoplanets():
    try:
        query = json.loads(request.args.get('query'))
        limit = min(1000, int(request.args.get('limit')))
        json_resp = json.dumps(api.exoplanets(query, limit))
        return Response(json_resp, mimetype='application/json')
    except ValueError:
        resp = jsonify({'error': 'bad request'})
        resp.status_code = 500
        return resp


@app.route('/api/asterank')
def api_asterank():
    try:
        query = json.loads(request.args.get('query'))
        limit = min(1000, int(request.args.get('limit')))
        json_resp = json.dumps(api.asterank(query, limit))
        return Response(json_resp, mimetype='application/json')
    except:
        resp = jsonify({'error': 'bad request'})
        resp.status_code = 500
        return resp


@app.route('/api/rankings')
def rankings():
    try:
        limit = int(request.args.get('limit')) or 10
        results = api.rankings(request.args.get('sort_by'), limit)
        json_resp = json.dumps(results)
        return Response(
            json_resp,
            mimetype='application/json',
            headers={'Cache-Control': 'max-age=432000'})  # 5 days
    except:
        resp = jsonify({'error': 'bad request'})
        resp.status_code = 500
        return resp


@app.route('/api/autocomplete')
def autocomplete():
    results = api.autocomplete(request.args.get('query'), 10)
    json_resp = json.dumps(results)
    return Response(
        json_resp,
        mimetype='application/json',
        headers={'Cache-Control': 'max-age=432000'})  # 5 days


@app.route('/api/compositions')
def compositions():
    json_resp = json.dumps(api.compositions())
    return Response(json_resp, mimetype='application/json')


@app.route('/jpl/lookup')
def horizons():
    query = request.args.get('query')
    result = api.jpl_lookup(query)
    if result:
        json_resp = json.dumps(result)
        return Response(json_resp, mimetype='application/json')
    else:
        return Response('{}', mimetype='application/json')


# Skymorph routes
@app.route('/api/skymorph/search')
def skymorph_search_target():
    return jsonify({'results': skymorph.search_target(request.args.get('target'))})


@app.route('/api/skymorph/search_orbit')
def skymorph_search_orbit():
    search_results = skymorph.search_ephem(
        request.args.get('epoch'),
        request.args.get('ecc'),
        request.args.get('per'),
        request.args.get('per_date'),
        request.args.get('om'),
        request.args.get('w'),
        request.args.get('i'),
        request.args.get('H'),
    )
    ret = {'results': search_results}
    return jsonify(ret)


@app.route('/api/skymorph/search_position')
def skymorph_search_time():
    search_results = skymorph.search_position(
        request.args.get('ra'),
        request.args.get('dec'),
        request.args.get('time'),
    )
    ret = {'results': search_results}
    return jsonify(ret)


@app.route('/api/skymorph/image')
def skymorph_image():
    ret = skymorph.get_image(request.args.get('key'))
    if ret:
        response = make_response(ret)
        response.headers["Content-type"] = "image/gif"
        return response
    else:
        return jsonify(ret)

# Kepler


@app.route('/exoplanets')
@app.route('/kepler3d')
def kepler3d():
    return render_template('kepler3d.html')


# Misc Pages
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/feedback')
@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/mpc')
def mpc():
    return render_template('mpc.html')


@app.route('/kepler')
def kepler():
    return render_template('kepler.html')


@app.route('/exoplanets')
def exoplanets():
    return render_template('exoplanets.html')


@app.route('/neat')
def neat_docs():
    return redirect('/skymorph')


@app.route('/skymorph')
def skymorph_docs():
    return render_template('skymorph.html')


@app.route('/api')
def api_route():
    return render_template('api.html')
