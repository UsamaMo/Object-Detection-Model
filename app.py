"""Web entry point: python app.py, or gunicorn app:app."""
import base64
from functools import lru_cache
from io import BytesIO
import math
import os
from threading import BoundedSemaphore
from time import perf_counter

import cv2
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import HTTPException

from detector import catalog, detect, encode, evaluate, read_image, stitch

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
processing = BoundedSemaphore(1)


def find_image(kind, name):
    for path in catalog(kind):
        if path.stem == name:
            return path
    raise ValueError('Image not found in the project library.')


def image_url(data):
    return 'data:image/jpeg;base64,' + base64.b64encode(data).decode('ascii')


@lru_cache(maxsize=64)
def preview(kind, name):
    return encode(read_image(find_image(kind, name), 900))


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/api/catalog')
def get_catalog():
    return {kind: [{'id': p.stem, 'name': f'{"Scene" if kind == "scenes" else "Object"} {p.stem[1:]}',
                    'url': f'/api/image/{kind}/{p.stem}'} for p in catalog(kind)] for kind in ('scenes', 'objects')}


@app.get('/api/image/<kind>/<name>')
def get_image(kind, name):
    if kind not in ('scenes', 'objects'):
        raise ValueError('Unknown image library.')
    return send_file(BytesIO(preview(kind, name)), mimetype='image/jpeg', max_age=3600)


def limited_work(work):
    if not processing.acquire(blocking=False):
        return jsonify(error='Another analysis is running. Please try again shortly.'), 429
    try:
        return work()
    finally:
        processing.release()


@app.post('/api/detect')
def run_detection():
    def work():
        started = perf_counter()
        try:
            ratio = float(request.form.get('ratio', '.7'))
            minimum = int(request.form.get('min_inliers', '7'))
        except (ValueError, TypeError):
            raise ValueError('Detection settings must be numbers.')
        if not math.isfinite(ratio) or not .4 <= ratio <= .85 or not 4 <= minimum <= 30:
            raise ValueError('Ratio must be 0.40–0.85 and minimum inliers must be 4–30.')
        upload = request.files.get('image')
        if upload:
            scene = read_image(upload.stream)
            name = 'Uploaded scene'
        else:
            name = request.form.get('scene', 'S1')
            scene = read_image(find_image('scenes', name))
        rows, images, keypoints = detect(scene, ratio, minimum)
        return {'scene': name, 'objects': rows, 'keypoints': keypoints,
                'seconds': round(perf_counter() - started, 2), 'width': scene.shape[1], 'height': scene.shape[0],
                'settings': {'ratio': ratio, 'min_inliers': minimum},
                'images': {key: image_url(value) for key, value in images.items()},
                'original': image_url(encode(scene))}
    return limited_work(work)


@app.post('/api/stitch')
def run_stitch():
    def work():
        payload = request.get_json(silent=True)
        names = payload.get('scenes') if isinstance(payload, dict) else None
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names) or not 2 <= len(names) <= 6 or len(set(names)) != len(names):
            raise ValueError('Choose 2–6 different overlapping scenes.')
        result = stitch([read_image(find_image('scenes', name), 1200) for name in names])
        return {'image': image_url(encode(result)), 'width': result.shape[1], 'height': result.shape[0]}
    return limited_work(work)


@app.post('/api/evaluate')
def run_evaluation():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or any(not isinstance(payload.get(k), list) or not all(isinstance(v, str) for v in payload[k]) for k in ('detected', 'expected')):
        raise ValueError('Supply detected and expected object lists.')
    return evaluate(payload['detected'], payload['expected'], [p.stem for p in catalog('objects')])


@app.errorhandler(ValueError)
def invalid_input(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(HTTPException)
def http_error(error):
    message = 'Upload is too large. The request limit is 20 MB.' if error.code == 413 else error.description
    return jsonify(error=message), error.code


@app.errorhandler(cv2.error)
def vision_error(error):
    app.logger.exception('OpenCV processing failed')
    return jsonify(error='Image processing failed. Try a different image or scene selection.'), 422


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '8000')))
