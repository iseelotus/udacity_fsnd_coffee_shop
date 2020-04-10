import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = [drink.short() for drink in Drink.query.order_by(Drink.id).all()]
    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(token):
    drinks = [drink.long() for drink in Drink.query.order_by(Drink.id).all()]

    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(token):
    body = request.get_json()
    title = body['title']
    recipe = body['recipe']
    if type(recipe) is dict:
        recipe = [recipe]

    new_drink = Drink(title=title, recipe=json.dumps(recipe))

    new_drink.insert()
    return jsonify({
        'success': True,
        'drinks': Drink.long(new_drink)
    })


'''
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(token, id):
    body = request.get_json()
    drink = Drink.query.get(id)
    if not drink:
        abort(404, {"message": f"Drink with id {id} not found"})
    else:
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)
        if new_title:
            drink.title = new_title
        if new_recipe:
            if type(new_recipe) is dict:
                new_recipe = [new_recipe]
            drink.recipe = new_recipe
        drink.update()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })


'''
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(token, id):
    body = request.get_json()
    drink = Drink.query.get(id)
    if not drink:
        abort(404, {"message": f"Drink with id {id} not found"})
    else:
        drink.delete()
        return jsonify({
            "success": True,
            "delete": id
        })


# Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(401)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Not authorized"
    }), 401


@app.errorhandler(AuthError)
def auth_error(e):
    return jsonify(e.error), e.status_code
