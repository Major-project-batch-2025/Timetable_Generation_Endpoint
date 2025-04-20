from flask import Flask, request, jsonify
from generate_timetable import solve_timetable

app = Flask(__name__)

@app.route('/generate-timetable', methods=['POST'])
def generate():
    data = request.json
    print("Received data:", data)
    result = solve_timetable(data)
    print("Generated result:", result)
    if result["status"] == "failed":
        return jsonify(result), 400
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
