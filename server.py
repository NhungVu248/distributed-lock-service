from flask import Flask, request, jsonify
from lock_manager import LockManager

app = Flask(__name__)
lock_manager = LockManager()


@app.route('/lock', methods=['POST'])
def lock():
    data = request.get_json()
    client_id = data.get('client_id')
    resource = data.get('resource')
    ttl = data.get('ttl', 30)
    wait = data.get('wait', False)

    if not client_id or not resource:
        return jsonify({"success": False, "message": "client_id and resource are required"}), 400

    result = lock_manager.acquire_lock(client_id, resource, ttl, wait)
    return jsonify(result)


@app.route('/unlock', methods=['POST'])
def unlock():
    data = request.get_json()
    client_id = data.get('client_id')
    resource = data.get('resource')

    if not client_id or not resource:
        return jsonify({"success": False, "message": "client_id and resource are required"}), 400

    result = lock_manager.release_lock(client_id, resource)
    return jsonify(result)


@app.route('/status/<resource>', methods=['GET'])
def status(resource):
    result = lock_manager.get_status(resource)
    return jsonify(result)


@app.route('/locks', methods=['GET'])
def locks():
    result = lock_manager.get_all_locks()
    return jsonify({"locks": result})


@app.route('/logs', methods=['GET'])
def logs():
    return jsonify({"logs": lock_manager.get_logs()})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
