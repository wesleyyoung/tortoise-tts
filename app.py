import os
import uuid
from flask import Flask, request, jsonify, send_file

from audio.transformer import process_video
from tasks import do_tts
from flask_rq2 import RQ

from tortoise.api import MODELS_DIR

app = Flask('CHUCKWALLA')
app.config['RQ_REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
rq = RQ(app)

DEFAULT_RESULT_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'tortoise', 'results')
RESULT_DIR = os.environ.get('RESULT_DIR', DEFAULT_RESULT_DIR)
READ_QUEUE_NAME = 'read'


@app.route('/read', methods=['GET'])
def post_endpoint():
    try:
        random_uid = uuid.uuid4()
        uid = str(random_uid)
        voice = request.args.get('voice')
        preset = request.args.get('preset', default='fast')
        candidates = request.args.get('candidates', default=3)
        text = request.args.get('text')
        seed = request.args.get('seed', default=None)
        cvvp_amount = request.args.get('cvvp_amount', default=.0)
        job_timeout = request.args.get('job_timeout', default=3600)
        candidates = int(candidates)
        job_timeout = int(job_timeout)

        job = rq.get_queue(READ_QUEUE_NAME).enqueue(
            do_tts,
            args=(uid, voice, text, candidates, preset, seed, cvvp_amount),
            job_timeout=job_timeout,
        )

        return jsonify({"uid": uid, "status": job.get_status(), "id": job.id})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/model/<voice>', methods=['POST'])
def upload_files(voice):
    if 'files' not in request.files:
        return jsonify({'error': 'No files part in the request'}), 400

    files = request.files.getlist('files')

    for file in files:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        process_video(file, os.path.join('tortoise/voices', voice))

    return jsonify({'message': 'Files uploaded successfully'})


@app.route('/jobs', methods=['GET'])
def get_jobs():
    queue = rq.get_queue(READ_QUEUE_NAME)
    jobs = queue.jobs
    job_data = [{"args": job.args, 'id': job.id, 'status': job.get_status()} for job in jobs]

    return jsonify({'jobs': job_data})


@app.route('/job_status/<job_id>', methods=['GET'])
def job_status(job_id):
    queue = rq.get_queue(READ_QUEUE_NAME)
    job = queue.fetch_job(job_id)
    if job is None:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({'job_id': job.id, 'status': job.get_status(), 'args': job.args})


@app.route('/cancel_job/<job_id>', methods=['POST'])
def cancel_job(job_id):
    queue = rq.get_queue(READ_QUEUE_NAME)
    job = queue.fetch_job(job_id)

    if job is None:
        return jsonify({'error': 'Job not found'}), 404

    try:
        job.cancel()
        return jsonify({'message': 'Job canceled successfully'})
    except Exception as e:
        return jsonify({'error': f'Error canceling job: {str(e)}'}), 500


@app.route('/failed_jobs', methods=['GET'])
def get_failed_jobs():
    queue = rq.get_queue(READ_QUEUE_NAME)
    job_data = extract_registry(queue, queue.failed_job_registry)

    return jsonify({'jobs': job_data})


@app.route('/finished_jobs', methods=['GET'])
def get_finished_jobs():
    queue = rq.get_queue(READ_QUEUE_NAME)
    job_data = extract_registry(queue, queue.finished_job_registry)

    return jsonify({'jobs': job_data})


@app.route('/started_jobs', methods=['GET'])
def get_started_jobs():
    queue = rq.get_queue(READ_QUEUE_NAME)
    job_data = extract_registry(queue, queue.started_job_registry)

    return jsonify({'jobs': job_data})


@app.route('/list/<uid>', methods=['GET'])
def list_dir(uid):
    try:
        directory_path = os.path.join(RESULT_DIR, uid)
        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]

        return jsonify({"files": files})

    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route('/download/<uid>/<filename>', methods=['GET'])
def download_file(uid, filename):
    file_path = os.path.join(RESULT_DIR, uid, filename)
    return send_file(file_path, as_attachment=True, download_name=filename)


def extract_registry(queue, registry):
    jobs = [queue.fetch_job(job_id) for job_id in registry.get_job_ids()]
    return [{"args": job.args, 'id': job.id, 'status': job.get_status()} for job in jobs]


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port, host='0.0.0.0')
