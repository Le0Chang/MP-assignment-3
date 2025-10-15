import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment


# 定义一个常量，方便在多个工具中引用
TODO_FILE = ".waa/todo.json"


class TodoAddTool(Tool):
    def __init__(self):
        super().__init__("todo.add")
        self.schema.register_argument(
            ToolArgument("description", "The description of the TODO item.", True, str)
        )

    def initialize(self, env: AgentEnvironment):
        self.todo_file = env.get_working_dir() / TODO_FILE

    def description(self) -> str:
        return "Add a new TODO item. Generate unique ID, set status to 'pending', record creation timestamp."

    def _read_todos(self) -> List[Dict]:
        """Helper function to read the todo list from JSON file."""
        if not self.todo_file.exists():
            return []
        with open(self.todo_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_todos(self, todos: List[Dict]):
        """Helper function to write the todo list to JSON file."""
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            json.dump(todos, f, indent=2)

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            todos = self._read_todos()
            # Generate a new ID by finding the max existing ID and adding 1
            new_id = max([todo.get('id', 0) for todo in todos] + [0]) + 1
            new_todo = {
                "id": new_id,
                "description": input["description"],
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
            }
            todos.append(new_todo)
            self._write_todos(todos)
            return {"ok": True, "data": {"message": f"TODO item added with ID: {new_id}."}}
        except Exception as e:
            return {"ok": False, "error": f"Failed to add TODO item: {str(e)}"}


class TodoListTool(Tool):
    def __init__(self):
        super().__init__("todo.list")
        self.schema.register_argument(
            ToolArgument("status", "Filter by status: 'pending', 'completed', or 'all'. Defaults to 'all'.", False, str)
        )

    def initialize(self, env: AgentEnvironment):
        self.todo_file = env.get_working_dir() / TODO_FILE

    def description(self) -> str:
        return "List TODO items. Support optional status filter: 'pending', 'completed', or 'all' (default)."
    
    def _read_todos(self) -> List[Dict]:
        if not self.todo_file.exists():
            return []
        with open(self.todo_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            status_filter = input.get("status", "all")
            allowed_statuses = ["pending", "completed", "all"]
            if status_filter not in allowed_statuses:
                return {"ok": False, "error": f"Invalid status filter. Must be one of: {allowed_statuses}"}

            todos = self._read_todos()
            
            if status_filter != "all":
                filtered_todos = [todo for todo in todos if todo.get('status') == status_filter]
            else:
                filtered_todos = todos

            count = len(filtered_todos)
            
            return {
                "ok": True, 
                "data": {
                    "todos": filtered_todos,
                    "count": count
                }
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to list TODO items: {str(e)}"}


class TodoCompleteTool(Tool):
    def __init__(self):
        super().__init__("todo.complete")
        self.schema.register_argument(
            ToolArgument("id", "The ID of the item to mark as completed.", True, int)
        )

    def initialize(self, env: AgentEnvironment):
        self.todo_file = env.get_working_dir() / TODO_FILE

    def description(self) -> str:
        return "Mark item as completed by ID. Update status and record completion timestamp."

    def _read_todos(self) -> List[Dict]:
        if not self.todo_file.exists():
            return []
        with open(self.todo_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_todos(self, todos: List[Dict]):
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            json.dump(todos, f, indent=2)

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item_id = input["id"]
            todos = self._read_todos()
            item_found = False
            for todo in todos:
                if todo.get("id") == item_id:
                    todo["status"] = "completed"
                    todo["completed_at"] = datetime.now().isoformat()
                    item_found = True
                    break
            
            if not item_found:
                return {"ok": False, "error": f"TODO item with ID {item_id} not found."}

            self._write_todos(todos)
            return {"ok": True, "data": {"message": f"TODO item {item_id} marked as completed."}}
        except Exception as e:
            return {"ok": False, "error": f"Failed to complete TODO item: {str(e)}"}


class TodoRemoveTool(Tool):
    def __init__(self):
        super().__init__("todo.remove")
        self.schema.register_argument(
            ToolArgument("id", "The ID of the item to remove.", True, int)
        )

    def initialize(self, env: AgentEnvironment):
        self.todo_file = env.get_working_dir() / TODO_FILE

    def description(self) -> str:
        return "Remove a TODO item by ID."

    def _read_todos(self) -> List[Dict]:
        if not self.todo_file.exists():
            return []
        with open(self.todo_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_todos(self, todos: List[Dict]):
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            json.dump(todos, f, indent=2)

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item_id = input["id"]
            todos = self._read_todos()
            
            initial_len = len(todos)
            todos_after_removal = [todo for todo in todos if todo.get("id") != item_id]

            if len(todos_after_removal) == initial_len:
                return {"ok": False, "error": f"TODO item with ID {item_id} not found."}

            self._write_todos(todos_after_removal)
            return {"ok": True, "data": {"message": f"TODO item {item_id} removed."}}
        except Exception as e:
            return {"ok": False, "error": f"Failed to remove TODO item: {str(e)}"}
            

def standard_todo_tools() -> List[Tool]:
    return [
        TodoAddTool(),
        TodoListTool(),
        TodoCompleteTool(),
        TodoRemoveTool()
    ]