import shutil
from pathlib import Path
from typing import Dict, Any, List

from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment


class FileCreateTool(Tool):
    def __init__(self):
        super().__init__("fs.write")
        # 1. 定义工具参数：path 和 content
        self.schema.register_argument(
            ToolArgument("path", "The path of the file to create or overwrite.", True, str)
        )
        self.schema.register_argument(
            ToolArgument("content", "The content to write to the file.", True, str)
        )

    def initialize(self, env: AgentEnvironment):
        # 2. 初始化安全检查所需的环境变量
        self.working_dir = env.get_working_dir()
        self.protected_files = env.get_config_value("protected_files", [])

    def description(self) -> str:
        # 3. 提供工具描述
        return "Creates or overwrites a file with specified content. Creates parent directories if needed."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 4. 执行核心逻辑
        path_str = input["path"]
        content = input["content"]

        try:
            full_path = (self.working_dir / path_str).resolve()

            # --- 安全检查 1: 路径验证 ---
            if not str(full_path).startswith(str(self.working_dir.resolve())):
                return {"ok": False, "error": f"Path is outside the working directory: {path_str}"}

            # --- 安全检查 2: 受保护文件检查 ---
            if path_str in self.protected_files:
                return {"ok": False, "error": f"File is protected and cannot be written to: {path_str}"}

            # 确保父目录存在，如果不存在则创建
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件内容
            full_path.write_text(content, encoding='utf-8')

            return {
                "ok": True,
                "data": {"message": f"Successfully wrote to file {path_str}."}
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to write file: {str(e)}"}


class FileDeleteTool(Tool):
    def __init__(self):
        super().__init__("fs.delete")
        # 1. 定义工具参数：path
        self.schema.register_argument(
            ToolArgument("path", "The path of the file to delete.", True, str)
        )

    def initialize(self, env: AgentEnvironment):
        # 2. 初始化安全检查所需的环境变量
        self.working_dir = env.get_working_dir()
        self.protected_files = env.get_config_value("protected_files", [])

    def description(self) -> str:
        # 3. 提供工具描述
        return "Deletes a specified file."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 4. 执行核心逻辑
        path_str = input["path"]

        try:
            full_path = (self.working_dir / path_str).resolve()

            # --- 安全检查 1: 路径验证 ---
            if not str(full_path).startswith(str(self.working_dir.resolve())):
                return {"ok": False, "error": f"Path is outside the working directory: {path_str}"}

            # --- 安全检查 2: 受保护文件检查 ---
            if path_str in self.protected_files:
                return {"ok": False, "error": f"File is protected and cannot be deleted: {path_str}"}

            if not full_path.exists():
                return {"ok": False, "error": f"File not found: {path_str}"}
            if not full_path.is_file():
                return {"ok": False, "error": f"Path is not a file, cannot be deleted with fs.delete: {path_str}"}

            # 删除文件
            full_path.unlink()

            return {
                "ok": True,
                "data": {"message": f"Successfully deleted file {path_str}."}
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to delete file: {str(e)}"}


class FileReadTool(Tool):
    def __init__(self):
        super().__init__("fs.read")
        # 1. 定义工具的参数 (Schema)
        self.schema.register_argument(
            ToolArgument("path", "The path to the file to read.", True, str)
        )

    def initialize(self, env: AgentEnvironment):
        # 2. 从环境中获取必要的信息以备后用
        self.working_dir = env.get_working_dir()
        # 虽然 fs.read 不需要检查受保护文件，但好习惯是在此初始化
        self.protected_files = env.get_config_value("protected_files", [])

    def description(self) -> str:
        # 3. 提供给 LLM 的工具描述
        return "Reads the content of a file. Returns the content, size, and line count."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 4. 执行工具的核心逻辑
        path_str = input["path"]
        
        try:
            full_path = (self.working_dir / path_str).resolve()

            # --- 安全检查 1: 路径验证 ---
            if not str(full_path).startswith(str(self.working_dir.resolve())):
                return {"ok": False, "error": f"Path is outside the working directory: {path_str}"}

            if not full_path.exists():
                return {"ok": False, "error": f"File not found: {path_str}"}
            if not full_path.is_file():
                return {"ok": False, "error": f"Path is not a file: {path_str}"}
            
            # 读取文件内容和元数据
            content = full_path.read_text(encoding='utf-8')
            size = full_path.stat().st_size
            line_count = len(content.splitlines())

            return {
                "ok": True,
                "data": {
                    "content": content,
                    "size": size,
                    "line_count": line_count,
                    "message": f"Successfully read file {path_str}."
                }
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to read file: {str(e)}"}

class FileEditTool(Tool):
    def __init__(self):
        super().__init__("fs.edit")
        # 1. 定义工具参数
        self.schema.register_argument(
            ToolArgument("path", "The path of the file to edit.", True, str)
        )
        self.schema.register_argument(
            ToolArgument("old_text", "The text to be replaced.", True, str)
        )
        self.schema.register_argument(
            ToolArgument("new_text", "The new text to replace the old_text with.", True, str)
        )

    def initialize(self, env: AgentEnvironment):
        # 2. 初始化安全检查所需的环境变量
        self.working_dir = env.get_working_dir()
        self.protected_files = env.get_config_value("protected_files", [])

    def description(self) -> str:
        # 3. 提供工具描述
        return "Edits a file by replacing the first occurrence of old_text with new_text."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 4. 执行核心逻辑
        path_str = input["path"]
        old_text = input["old_text"]
        new_text = input["new_text"]

        try:
            full_path = (self.working_dir / path_str).resolve()

            # --- 安全检查 1: 路径验证 ---
            if not str(full_path).startswith(str(self.working_dir.resolve())):
                return {"ok": False, "error": f"Path is outside the working directory: {path_str}"}

            # --- 安全检查 2: 受保护文件检查 ---
            if path_str in self.protected_files:
                return {"ok": False, "error": f"File is protected and cannot be edited: {path_str}"}
            
            if not full_path.is_file():
                return {"ok": False, "error": f"File not found: {path_str}"}

            # 读取文件内容
            content = full_path.read_text(encoding='utf-8')

            # 使用 .replace(..., ..., 1) 只替换第一次出现的内容
            new_content = content.replace(old_text, new_text, 1)

            # 检查内容是否真的被改变了
            if content == new_content:
                return {"ok": False, "error": f"Text to be replaced ('{old_text}') not found in file: {path_str}"}

            # 将修改后的内容写回文件
            full_path.write_text(new_content, encoding='utf-8')

            return {
                "ok": True,
                "data": {"message": f"Successfully edited file {path_str}."}
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to edit file: {str(e)}"}


class DirectoryCreateTool(Tool):
    def __init__(self):
        super().__init__("fs.mkdir")
        # 1. 定义工具参数：path
        self.schema.register_argument(
            ToolArgument("path", "The path of the directory to create.", True, str)
        )

    def initialize(self, env: AgentEnvironment):
        # 2. 初始化安全检查所需的环境变量
        self.working_dir = env.get_working_dir()

    def description(self) -> str:
        # 3. 提供工具描述
        return "Creates a new directory. It will also create parent directories if they do not exist."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 4. 执行核心逻辑
        path_str = input["path"]

        try:
            full_path = (self.working_dir / path_str).resolve()

            # --- 安全检查 1: 路径验证 ---
            if not str(full_path).startswith(str(self.working_dir.resolve())):
                return {"ok": False, "error": f"Path is outside the working directory: {path_str}"}

            # 创建目录，parents=True 会自动创建父目录, exist_ok=True 意味着如果目录已存在也不会报错
            full_path.mkdir(parents=True, exist_ok=True)

            return {
                "ok": True,
                "data": {"message": f"Successfully created directory {path_str}."}
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to create directory: {str(e)}"}


class DirectoryDeleteTool(Tool):
    def __init__(self):
        super().__init__("fs.rmdir")
        # 1. 定义工具参数：path 和可选的 recursive
        self.schema.register_argument(
            ToolArgument("path", "The path of the directory to delete.", True, str)
        )
        self.schema.register_argument(
            ToolArgument("recursive", "If true, deletes directory and all its contents.", False, bool)
        )

    def initialize(self, env: AgentEnvironment):
        # 2. 初始化安全检查所需的环境变量
        self.working_dir = env.get_working_dir()

    def description(self) -> str:
        # 3. 提供工具描述
        return "Deletes a directory. Use the 'recursive' argument (boolean) to delete non-empty directories."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 4. 执行核心逻辑
        path_str = input["path"]
        # 使用 .get() 为 recursive 参数提供默认值 False
        recursive = input.get("recursive", False)

        try:
            full_path = (self.working_dir / path_str).resolve()

            # --- 安全检查 1: 路径验证 ---
            if not str(full_path).startswith(str(self.working_dir.resolve())):
                return {"ok": False, "error": f"Path is outside the working directory: {path_str}"}
            
            # --- 安全检查 2: 防止删除工作目录本身 ---
            if full_path == self.working_dir.resolve():
                return {"ok": False, "error": "Cannot delete the root working directory."}

            if not full_path.exists():
                return {"ok": False, "error": f"Directory not found: {path_str}"}
            if not full_path.is_dir():
                return {"ok": False, "error": f"Path is not a directory: {path_str}"}

            if recursive:
                # 递归删除整个目录树
                shutil.rmtree(full_path)
                message = f"Successfully recursively deleted directory {path_str}."
            else:
                # 只删除空目录
                full_path.rmdir()
                message = f"Successfully deleted empty directory {path_str}."

            return {"ok": True, "data": {"message": message}}
        
        except OSError:
             # 如果非递归删除时目录不为空，会触发 OSError
            return {"ok": False, "error": f"Directory not empty. Use recursive=True to delete it: {path_str}"}
        except Exception as e:
            return {"ok": False, "error": f"Failed to delete directory: {str(e)}"}


class DirectoryListTool(Tool):
    def __init__(self):
        super().__init__("fs.ls")
        # 1. 定义工具参数：path
        self.schema.register_argument(
            ToolArgument("path", "The path of the directory to list.", True, str)
        )

    def initialize(self, env: AgentEnvironment):
        # 2. 初始化安全检查所需的环境变量
        self.working_dir = env.get_working_dir()

    def description(self) -> str:
        # 3. 提供工具描述
        return "Lists contents of a directory, showing name, type ('file' or 'dir'), and size for each entry."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 4. 执行核心逻辑
        path_str = input["path"]

        try:
            full_path = (self.working_dir / path_str).resolve()

            # --- 安全检查 1: 路径验证 ---
            if not str(full_path).startswith(str(self.working_dir.resolve())):
                return {"ok": False, "error": f"Path is outside the working directory: {path_str}"}

            if not full_path.is_dir():
                return {"ok": False, "error": f"Path is not a directory: {path_str}"}

            entries = []
            # 遍历目录中的每一个项目
            for item in full_path.iterdir():
                # 判断是文件还是目录
                item_type = "dir" if item.is_dir() else "file"
                # 获取大小
                item_size = item.stat().st_size
                
                # 按照要求格式添加信息到列表
                entries.append({
                    "name": item.name,
                    "type": item_type,
                    "size": item_size,
                })

            return {
                "ok": True,
                "data": {"entries": entries}
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to list directory contents: {str(e)}"}


class DirectoryTreeTool(Tool):
    def __init__(self):
        super().__init__("fs.tree")
        self.schema.register_argument(
            ToolArgument("path", "The path of the directory to display as a tree.", False, str)
        )

    def initialize(self, env: AgentEnvironment):
        self.working_dir = env.get_working_dir()

    def description(self) -> str:
        return "Displays the directory structure as a tree, starting from the given path or current directory."

    def _build_tree(self, directory: Path, prefix: str = "") -> List[str]:
        """Helper function to recursively build the tree string."""
        tree_lines = []
        # .iterdir() returns an unsorted iterator, so we sort it to have a consistent output
        items = sorted(list(directory.iterdir()), key=lambda p: p.name.lower())
        for i, item in enumerate(items):
            is_last = i == (len(items) - 1)
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{item.name}")
            
            if item.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                tree_lines.extend(self._build_tree(item, new_prefix))
        return tree_lines

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        path_str = input.get("path", ".")

        try:
            full_path = (self.working_dir / path_str).resolve()

            if not str(full_path).startswith(str(self.working_dir.resolve())):
                return {"ok": False, "error": f"Path is outside the working directory: {path_str}"}

            if not full_path.is_dir():
                return {"ok": False, "error": f"Path is not a directory: {path_str}"}
            
            tree_lines = [path_str] + self._build_tree(full_path)

            return {
                "ok": True,
                "data": {"tree": tree_lines}
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to generate directory tree: {str(e)}"}


# Standard Tool Sets
def standard_fs_tools() -> List[Tool]:
    return [
        FileCreateTool(),
        FileDeleteTool(),
        FileReadTool(),
        FileEditTool(),
        DirectoryCreateTool(),
        DirectoryDeleteTool(),
        DirectoryListTool(),
        DirectoryTreeTool()
    ]