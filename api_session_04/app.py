
from flask import Flask, jsonify, request, render_template_string
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from marshmallow import Schema, fields

app = Flask(__name__)

# Du lieu mau
TASKS = [
    {
        "id": 1,
        "title": "Hoc Flask",
        "description": "Tim hieu Flask REST API",
        "status": "in_progress"
    },
    {
        "id": 2,
        "title": "Hoc OpenAPI",
        "description": "Viet API specification",
        "status": "pending"
    }
]


# Schemas
class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str()
    status = fields.Str(
        validate=lambda x: x in [
            "pending", "in_progress", "completed"
        ]
    )


class CreateTaskSchema(Schema):
    title = fields.Str(required=True)
    description = fields.Str()
    status = fields.Str(
        load_default="pending",
        validate=lambda x: x in [
            "pending", "in_progress", "completed"
        ]
    )


class UpdateTaskSchema(Schema):
    title = fields.Str()
    description = fields.Str()
    status = fields.Str(
        validate=lambda x: x in [
            "pending", "in_progress", "completed"
        ]
    )


task_schema = TaskSchema()
create_task_schema = CreateTaskSchema()
update_task_schema = UpdateTaskSchema()


def find_task(task_id):
    return next(
        (task for task in TASKS if task["id"] == task_id),
        None
    )


def validate_json(schema):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, (jsonify({
            "error": "Request body must be a JSON object"
        }), 400)

    errors = schema.validate(data)
    if errors:
        return None, (jsonify({"errors": errors}), 422)

    result = schema.load(data)
    return result, None


# GET /tasks
@app.get("/tasks")
def list_tasks():
    return jsonify(TASKS), 200


# GET /tasks/{taskId}
@app.get("/tasks/<int:task_id>")
def get_task(task_id):
    task = find_task(task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(task), 200


# POST /tasks
@app.post("/tasks")
def create_task():
    data, error = validate_json(create_task_schema)

    if error:
        return error

    task = {
        "id": max((t["id"] for t in TASKS), default=0) + 1,
        "title": data["title"],
        "description": data.get("description", ""),
        "status": data.get("status", "pending")
    }

    TASKS.append(task)

    response = jsonify(task)
    response.status_code = 201
    response.headers["Location"] = f"/tasks/{task['id']}"

    return response


# OpenAPI specification
spec = APISpec(
    title="Tasks API",
    version="1.0.0",
    openapi_version="3.0.3",
    info={
        "description": "Task management REST API"
    },
    plugins=[MarshmallowPlugin()]
)

spec.components.schema("Task", schema=TaskSchema)
spec.components.schema("CreateTask", schema=CreateTaskSchema)
spec.components.schema("UpdateTask", schema=UpdateTaskSchema)

task_ref = {"$ref": "#/components/schemas/Task"}
create_ref = {"$ref": "#/components/schemas/CreateTask"}
update_ref = {"$ref": "#/components/schemas/UpdateTask"}

spec.path(
    path="/tasks",
    operations={
        "get": {
            "tags": ["tasks"],
            "operationId": "listTasks",
            "summary": "Get all tasks",
            "responses": {
                "200": {
                    "description": "List of tasks",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": task_ref
                            }
                        }
                    }
                }
            }
        },
        "post": {
            "tags": ["tasks"],
            "operationId": "createTask",
            "summary": "Create a task",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": create_ref
                    }
                }
            },
            "responses": {
                "201": {"description": "Task created"},
                "400": {"description": "Invalid JSON"},
                "422": {"description": "Invalid fields"}
            }
        }
    }
)

spec.path(
    path="/tasks/{taskId}",
    operations={
        "get": {
            "tags": ["tasks"],
            "operationId": "getTask",
            "summary": "Get task details",
            "parameters": [{
                "in": "path",
                "name": "taskId",
                "required": True,
                "schema": {"type": "integer"}
            }],
            "responses": {
                "200": {
                    "description": "Task details",
                    "content": {
                        "application/json": {
                            "schema": task_ref
                        }
                    }
                },
                "404": {"description": "Task not found"}
            }
        },
    }
)


@app.get("/openapi.json")
def openapi_json():
    return jsonify(spec.to_dict()), 200


SWAGGER_UI_HTML = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Tasks API - Swagger UI</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = () => SwaggerUIBundle({
            url: "/openapi.json",
            dom_id: "#swagger-ui"
        });
    </script>
</body>
</html>
"""


@app.get("/docs")
def docs():
    return render_template_string(SWAGGER_UI_HTML)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
