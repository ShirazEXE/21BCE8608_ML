from flask import Flask
from flask_restful import Api, Resources

app = Flask(__name__)
api = Api(app)

class HealthCheck(Resource):
    def get(self):
        return{"status":"ok"}, 200
    
api.add_resource(HealthCheck, '/health')

if __name__ == '__main__':
    app.run(debug=True)
