"""Reusable SIFT reference-image detection and panorama pipeline."""
from functools import lru_cache
from pathlib import Path
import warnings

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
MAX_SIDE = 1600
Image.MAX_IMAGE_PIXELS = 25_000_000
cv2.setNumThreads(2)


def catalog(kind):
    folder = ROOT / {'scenes': 'Scenes', 'objects': 'Objects'}[kind]
    return sorted(folder.glob('*.png'), key=lambda p: int(p.stem[1:]))


def read_image(source, max_side=MAX_SIDE):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(source) as original:
                if original.format not in {'PNG', 'JPEG', 'WEBP'}:
                    raise ValueError('Use a PNG, JPEG, or WebP image.')
                img = ImageOps.exif_transpose(original).convert('RGB')
                img.thumbnail((max_side, max_side))
                return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError('Cannot read this image. Use PNG, JPEG, or WebP, up to 25 megapixels.') from exc


def encode(image):
    ok, data = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise ValueError('Could not encode the result image.')
    return data.tobytes()


def features(image):
    return cv2.SIFT_create(nfeatures=6000).detectAndCompute(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), None)


@lru_cache(maxsize=32)
def reference(path, modified):
    image = read_image(path)
    kp, desc = features(image)
    return image, kp, desc


def valid_polygon(points, shape):
    if not np.isfinite(points).all():
        return False
    h, w = shape[:2]
    polygon = points.astype(np.float32).reshape(4, 2)
    if not cv2.isContourConvex(polygon):
        return False
    area = abs(cv2.contourArea(polygon))
    return (100 < area < w * h * 0.9 and
            np.all(polygon[:, 0] >= -0.1 * w) and np.all(polygon[:, 0] <= 1.1 * w) and
            np.all(polygon[:, 1] >= -0.1 * h) and np.all(polygon[:, 1] <= 1.1 * h))


def detect(scene, ratio=0.7, min_inliers=7, references=None):
    scene_kp, scene_desc = features(scene)
    annotated = scene.copy()
    rows, visualizations = [], {}
    paths = catalog('objects') if references is None else references
    for index, path in enumerate(paths):
        obj, obj_kp, obj_desc = reference(str(path), path.stat().st_mtime_ns)
        good, inliers, polygon = [], [], None
        if obj_desc is not None and scene_desc is not None and len(scene_desc) >= 2:
            pairs = cv2.BFMatcher(cv2.NORM_L2).knnMatch(obj_desc, scene_desc, k=2)
            candidates = [pair[0] for pair in pairs if len(pair) == 2 and pair[0].distance < ratio * pair[1].distance]
            # One scene feature must not count as independent evidence for many object features.
            seen = set()
            for match in sorted(candidates, key=lambda m: m.distance):
                if match.trainIdx not in seen:
                    good.append(match)
                    seen.add(match.trainIdx)
            if len(good) >= 4:
                src = np.float32([obj_kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                dst = np.float32([scene_kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                matrix, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
                if matrix is not None and mask is not None and np.isfinite(matrix).all():
                    inliers = [m for m, keep in zip(good, mask.ravel()) if keep]
                    h, w = obj.shape[:2]
                    projected = cv2.perspectiveTransform(np.float32([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]]).reshape(-1, 1, 2), matrix)
                    if len(inliers) >= min_inliers and len(inliers) / len(good) >= 0.4 and valid_polygon(projected, scene.shape):
                        polygon = projected.reshape(4, 2)
        color = tuple(int(x) for x in cv2.cvtColor(np.uint8([[[index * 12 % 180, 190, 245]]]), cv2.COLOR_HSV2BGR)[0, 0])
        if polygon is not None:
            cv2.polylines(annotated, [polygon.astype(np.int32)], True, color, 3, cv2.LINE_AA)
            x, y = np.maximum(polygon.min(axis=0), 0).astype(int)
            y = max(25, y)
            cv2.rectangle(annotated, (x, y-24), (x+100, y+4), color, -1)
            cv2.putText(annotated, f'Object {path.stem[1:]}', (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, .5, (20,20,20), 1, cv2.LINE_AA)
        rows.append({'id': path.stem, 'name': f'Object {path.stem[1:]}', 'detected': polygon is not None,
                     'matches': len(good), 'inliers': len(inliers),
                     'inlier_ratio': round(len(inliers) / len(good), 3) if good else 0,
                     'polygon': polygon.round(1).tolist() if polygon is not None else None})
        match_img = cv2.drawMatches(obj, obj_kp, scene, scene_kp, inliers[:60], None,
                                   matchColor=(90, 220, 150), flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        visualizations[path.stem] = encode(match_img)
    keypoints = cv2.drawKeypoints(scene, scene_kp, None, color=(90, 220, 150))
    return rows, {'detection': encode(annotated), 'keypoints': encode(keypoints), **visualizations}, len(scene_kp)


def stitch(images):
    if not 2 <= len(images) <= 6:
        raise ValueError('Choose between 2 and 6 overlapping scenes.')
    stitcher = cv2.Stitcher_create(cv2.Stitcher_SCANS)
    stitcher.setCompositingResol(0.6)
    status, result = stitcher.stitch(images)
    if status != cv2.Stitcher_OK or result is None:
        raise ValueError('These scenes could not be stitched. Try 2–3 views with more overlap and less change in viewpoint.')
    return result


def evaluate(detected, expected, universe):
    detected, expected, universe = set(detected), set(expected), set(universe)
    if not expected <= universe or not detected <= universe:
        raise ValueError('Evaluation labels must belong to the reference object library.')
    tp, fp, fn = len(detected & expected), len(detected - expected), len(expected - detected)
    tn = len(universe - (detected | expected))
    return {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'precision': tp / (tp + fp) if tp + fp else 0,
            'recall': tp / (tp + fn) if tp + fn else 0,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0,
            'accuracy': (tp + tn) / len(universe) if universe else 0}
