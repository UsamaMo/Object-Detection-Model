from io import BytesIO
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
import pytest
from app import app
from detector import detect, encode, evaluate, read_image, stitch, valid_polygon

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()


def test_catalog_and_image(client):
    assert client.get('/').status_code == 200
    assert client.get('/health').json == {'status': 'ok'}
    data = client.get('/api/catalog').json
    assert len(data['objects']) == 15 and len(data['scenes']) == 20
    assert data['scenes'][1]['id'] == 'S2'
    response = client.get(data['scenes'][0]['url'])
    assert response.status_code == 200 and response.mimetype == 'image/jpeg'
    assert client.get('/api/image/scenes/unknown').status_code == 400


@pytest.mark.parametrize('form', [{'ratio':'nan'}, {'ratio':'0.99'}, {'min_inliers':'bad'}, {'min_inliers':'3'}, {'scene':'../README'}])
def test_invalid_settings(client, form):
    assert client.post('/api/detect', data=form).status_code == 400


def test_invalid_upload(client):
    response = client.post('/api/detect', data={'image': (BytesIO(b'bad'), 'fake.png')})
    assert response.status_code == 400


def test_blank_scene(client):
    image = encode(np.zeros((200, 300, 3), dtype=np.uint8))
    response = client.post('/api/detect', data={'image': (BytesIO(image), 'blank.jpg')})
    assert response.status_code == 200
    assert response.json['keypoints'] == 0
    assert not any(row['detected'] for row in response.json['objects'])


def test_known_object_localization(tmp_path):
    rng = np.random.default_rng(8)
    obj = rng.integers(0, 256, (260, 260, 3), dtype=np.uint8)
    for i in range(20):
        cv2.circle(obj, (int(rng.integers(15,245)), int(rng.integers(15,245))), 8, (255,255,255), 2)
    path = tmp_path / 'O1.png'
    cv2.imwrite(str(path), obj)
    scene = np.full((600, 700, 3), 100, dtype=np.uint8)
    scene[150:410, 210:470] = obj
    rows, _, _ = detect(scene, references=[path])
    assert rows[0]['detected']
    assert np.allclose(rows[0]['polygon'], [[210,150], [469,150], [469,409], [210,409]], atol=4)


def test_reject_invalid_geometry():
    assert not valid_polygon(np.array([[0,0],[100,100],[0,100],[100,0]],dtype=np.float32), (200,200))
    assert not valid_polygon(np.full((4,2), np.nan), (200,200))


def test_evaluation(client):
    result = evaluate(['O1','O2'], ['O1','O3'], ['O1','O2','O3','O4'])
    assert result == dict(tp=1,fp=1,fn=1,tn=1,precision=.5,recall=.5,f1=.5,accuracy=.5)
    assert client.post('/api/evaluate', json={'detected':[], 'expected':['O99']}).status_code == 400
    assert client.post('/api/evaluate', json=[]).status_code == 400


@pytest.mark.parametrize('payload', [None, [], {'scenes':['S1']}, {'scenes':['S1','S1']}, {'scenes':[{},{}]}])
def test_stitch_validation(client, payload):
    assert client.post('/api/stitch', json=payload).status_code == 400


def test_stitch_failure():
    with pytest.raises(ValueError, match='could not be stitched'):
        stitch([np.zeros((200,200,3), dtype=np.uint8)] * 2)
