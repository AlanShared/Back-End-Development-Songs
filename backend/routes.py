from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

# GET /health endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status":"ok"}), 200


# GET /count endpoint
@app.route('/count', methods=['GET'])
def count_songs():
    try:
        count = db.songs.count_documents({})
        return jsonify({"count": count}), 200
    except Exception as e:
        return {"error": str(e)}, 500

# GET /song endpoint
@app.route('/song', methods=['GET'])
def songs():
    try:
        songlist = list(db.songs.find({}))
        return {"songs": parse_json(songlist)}, 200
    except Exception as e:
        return {"error": str(e)}, 500


# GET /song by ID endpoint
@app.route('/song/<int:id>', methods=['GET'])
def get_song_by_id(id):
    try:
        song = db.songs.find_one({"id": id})
        if not song:
            return jsonify({"message": f"Song with id:{id} not found"}), 404
        return parse_json(song), 200
    except Exception as e:
        return {"error": str(e)}, 500

# POST /song endpoint
@app.route('/song', methods=['POST'])
def create_song():
    new_song = request.json
    existant = db.songs.find_one({'id': new_song['id']})
    if existant:
        return {"Message": f"Song with id:{new_song['id']} already present"}, 302
    try:
        db.songs.insert_one(new_song)
        # This parsed object was just to get the exact same
        # output for the exercise, otherwise I would not 
        # have spent 3hrs for this endpoint :(
        parsed= parse_json(db.songs.find_one({'id': new_song['id']}))
        return jsonify({"inserted id": parsed['_id']}), 201
    except Exception as e:
        return jsonify({"Error": f"Data not writen to db, error code:{str(e)}."}), 500

# PUT /song endpoint
@app.route('/song/<int:id>', methods=['PUT'])
def update_song(id):
    data = request.json
    song = db.songs.find_one({"id": id})
    if not song:
        return jsonify({"message":"song not found"}), 404
    try:
        updatal = db.songs.update_one({'id': id},{'$set':data})
        updated_song = db.songs.find_one({'id': id})
        if updatal.modified_count == 0:
            return jsonify({"message":"song found but nothing updated"}), 200
        return parse_json(updated_song), 201
    except Exception as e:
        return jsonify({"Error": f"Data not writen to db, error code:{str(e)}."}), 500

# DELETE /song endpoint
@app.route('/song/<int:id>', methods=['DELETE'])
def delete_song(id):
    try:
        deletion = db.songs.delete_one({'id': id}) 
        if deletion.deleted_count == 0:
            return jsonify({"message": "song not found"}), 404
        else:
            return "", 204
    except Exception as e:
        return jsonify({"Error": f"Data not deleted error code:{str(e)}."}), 500
