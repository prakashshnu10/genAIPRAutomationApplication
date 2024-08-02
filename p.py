from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sonar:sonarqube@65.1.55.202/sonarqube'
db = SQLAlchemy(app)

class CodeComplexity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String, nullable=False)
    complexity_level = db.Column(db.String, nullable=False)
    details = db.Column(db.String, nullable=False)

class ApiVersioning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String, nullable=False)
    versioning_followed = db.Column(db.String, nullable=False)
    analysis = db.Column(db.String, nullable=False)

class SwaggerDocumentation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String, nullable=False)
    swagger_implemented = db.Column(db.String, nullable=False)
    details = db.Column(db.String, nullable=False)

@app.route('/api/code_complexity/<int:pr_number>', methods=['GET'])
def get_code_complexity(pr_number):
    data = CodeComplexity.query.filter_by(pr_number=pr_number).all()
    return jsonify([{
        'file_path': item.file_path,
        'complexity_level': item.complexity_level,
        'details': item.details
    } for item in data])

@app.route('/api/api_versioning/<int:pr_number>', methods=['GET'])
def get_api_versioning(pr_number):
    data = ApiVersioning.query.filter_by(pr_number=pr_number).all()
    return jsonify([{
        'file_path': item.file_path,
        'versioning_followed': item.versioning_followed,
        'analysis': item.analysis
    } for item in data])

@app.route('/api/swagger_documentation/<int:pr_number>', methods=['GET'])
def get_swagger_documentation(pr_number):
    data = SwaggerDocumentation.query.filter_by(pr_number=pr_number).all()
    return jsonify([{
        'file_path': item.file_path,
        'swagger_implemented': item.swagger_implemented,
        'details': item.details
    } for item in data])

if __name__ == '__main__':
    app.run(debug=True)
