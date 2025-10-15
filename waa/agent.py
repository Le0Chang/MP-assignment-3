import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
# 加入作业提供的工具
from .tools.fs import standard_fs_tools
from .tools.todo import standard_todo_tools
from .tools.server import standard_server_tools
from .tools.supertest import standard_supertest_tools
from .tools.playwright import standard_playwright_tools

from .llm import LanguageModel, GeminiLanguageModel, MockLanguageModel
from .tool import ToolRegistry
from .history import HistoryEntry, SystemPrompt, UserInstruction, LLMResponse, ToolCallResult
from .logger import Logger
from .env import AgentEnvironment

class Agent:
    working_dir: Path
    llm: LanguageModel
    tool_registry: ToolRegistry
    config: Dict[str, Any]
    max_turns: int
    history: List[HistoryEntry]
    logger: Logger
    env: AgentEnvironment
    debug: bool

    def __init__(self, working_dir: Path, debug: bool = False):
        self.working_dir = working_dir
        self.config = None
        self.debug = debug
        self.llm = None
        self.tool_registry = None
        self.max_turns = 0
        self.history = []
        self.logger = None
        self.env = None

    def initialize_environment(self):
        config_path = self.working_dir / ".waa" / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.env = AgentEnvironment(self.working_dir, self.config)
        self.max_turns = self.env.get_config_value("max_turns", 50)

    def initialize_llm(self):
        llm_type = self.config.get("llm_type", "mock")
        if llm_type == "gemini":
            model_name = self.config.get("model", "gemini-2.0-flash-thinking-exp-01-21")
            api_key = self.config.get("api_key", os.getenv("GEMINI_API_KEY"))
            return GeminiLanguageModel(model_name=model_name, api_key=api_key)
        elif llm_type == "mock":
            responses = self.config.get("mock_responses")
            return MockLanguageModel(responses=responses)
        else:
            raise ValueError(f"Unknown llm_type: {llm_type}. Use 'gemini' or 'mock'.")

    def initialize_logger(self):
        log_path = self.working_dir / ".waa" / "agent.log"
        if log_path.exists():
            raise RuntimeError(f"Log file already exists: {log_path}. Remove it to start a new run.")

        self.logger = Logger(log_path, self.debug)
        self.logger.log("Agent initialization started")
        self.logger.log(f"Working directory: {self.working_dir}")
        self.logger.log(f"Debug mode: {self.debug}")
        self.logger.log(f"Max turns: {self.max_turns}")

    def initialize_tool_registry(self):
        self.tool_registry = ToolRegistry()
        allowed_tools = self.env.get_config_value("allowed_tools", None)
        #########################################################
        # TODO: Load the tools into the tool registry           #
        #########################################################
        # 将所有标准工具集合到一个列表里
        all_tools = (
            standard_fs_tools() +
            standard_todo_tools() +
            standard_server_tools() +
            standard_supertest_tools() +
            standard_playwright_tools()
        )

        for tool in all_tools:
            # 如果 config.json 中没有限制 "allowed_tools"，或者当前工具在允许列表中
            if allowed_tools is None or tool.name in allowed_tools:
                # 就注册这个工具
                tool.initialize(self.env)
                self.tool_registry.register_tool(tool)
                self.logger.log(f"Tool registered: {tool.name}")

    def load_system_prompt(self):
        #########################################################
        # TODO: Load the system prompt in to the history        #
        #########################################################
        # 1. 定义提示语的静态部分 (协议、策略等)
        prompt_parts = [
            "You are WAA, an AI agent that builds and tests web applications.",
            "Your goal is to complete the user's instructions in as few turns as possible.",
            "\n# Tool Calling Protocol",
            "To use a tool, output a <tool_call> XML tag with the tool name and arguments in a JSON block:",
            '<tool_call>{"tool": "TOOL_NAME", "arguments": {"arg1": "value1", "arg2": "value2"}}</tool_call>',
            "\n# Termination Protocol",
            "When you have fully completed the user's instructions, output the <terminate> tag.",
            "<terminate>Final answer or summary of work done.</terminate>",
            "\n# Available Tools"
        ]

        # 2. 动态生成所有已注册工具的描述
        all_tools = self.tool_registry.list_tools()
        if not all_tools:
            prompt_parts.append("No tools are available.")
        else:
            for tool in all_tools:
                # 格式化每个工具的描述
                arg_schemas = [
                    f'"{arg.name}": "{arg.type.__name__}"' 
                    for arg in tool.schema.arguments.values()
                ]
                tool_desc = (
                    f"- {tool.name}: {tool.description()}\n"
                    f"  Arguments: {{{', '.join(arg_schemas)}}}"
                )
                prompt_parts.append(tool_desc)

        # 3. 将所有部分合并成一个最终的提示语字符串
        final_prompt = "\n".join(prompt_parts)

        # 4. 创建一个 SystemPrompt 对象并添加到历史记录中
        system_prompt_entry = SystemPrompt(final_prompt)
        self.history.append(system_prompt_entry)
        # self.logger.log("System prompt built and loaded")
        self.logger.log_system_prompt(final_prompt) 

    def load_instruction(self):
        #########################################################
        # TODO: Load the user instruction in to the history     #
        #########################################################
        # 构建指令文件的固定路径
        instruction_path = self.working_dir / ".waa" / "instruction.md"
        
        if not instruction_path.exists():
            raise FileNotFoundError(f"Instruction file not found at conventional path: {instruction_path}")
        
        # 读取文件内容
        with open(instruction_path, 'r', encoding='utf-8') as f:
            instruction_content = f.read()

        # 创建一个 UserInstruction 对象并添加到历史记录中
        user_instruction = UserInstruction(instruction_content)
        self.history.append(user_instruction)
        # self.logger.log(f"User instruction loaded from: {instruction_path.relative_to(self.working_dir)}")
        self.logger.log_user_instruction(instruction_content)

    def initialize(self):
        self.initialize_environment()
        # self.initialize_llm()
        self.llm = self.initialize_llm()
        self.initialize_logger()
        self.initialize_tool_registry()

        self.load_system_prompt()
        self.load_instruction()

    def query_llm(self, turn: int):
        #########################################################
        # TODO: Query the LLM                                   #
        #########################################################
        # 1. 将历史记录中的所有条目转换为 LLM 需要的字典格式
        messages = [entry.to_json() for entry in self.history]

        # 2. 调用 LLM 的 generate 方法
        self.logger.log("Querying LLM...")
        try:
            response_content = self.llm.generate(messages)
            # self.logger.log(f"LLM response:\n{response_content}")
            self.logger.log_llm_response(turn, response_content)
        except Exception as e:
            self.logger.log(f"LLM query failed: {e}")
            return None

        # 3. 将 LLM 的响应封装成 LLMResponse 对象并存入历史
        llm_response = LLMResponse(response_content)
        self.history.append(llm_response)

        # 4. 返回原始的响应字符串，以便 run 方法进行解析
        return response_content

    def execute_tool(self, tool_call: Dict[str, Any]):
        #########################################################
        # TODO: Execute the tool                                #
        #########################################################
        tool_name = tool_call.get("tool")
        tool_args = tool_call.get("arguments", {})
        error = None
        result = None

        if not tool_name:
            # 如果解析出的工具调用没有名字，就记录一个错误
            error = "Malformed tool call: missing 'tool' name."
            self.logger.log_error(error)
        else:
            try:
                # 1. 从工具注册表中查找工具
                tool = self.tool_registry.get_tool(tool_name)
                tool.schema.validate(tool_args)
                self.logger.log_tool_call(tool_name, tool_args)
                
                # 2. 执行工具
                result = tool.execute(tool_args)

            except Exception as e:
                # 如果查找或执行过程中出错
                error_str = f"Error executing tool {tool_name}: {str(e)}"
                self.logger.log_error(error_str, e)
                # 保持结果格式统一
                result = {"ok": False, "error": error_str}

        # 3. 将工具执行结果封装成 ToolCallResult 对象并存入历史
        self.logger.log_tool_result(tool_name, result, error)
        
        tool_result_entry = ToolCallResult(tool_name, tool_args, result)
        self.history.append(tool_result_entry)

    @staticmethod
    def _parse_tool_call(response: str) -> Optional[Dict[str, Any]]:
        if response.startswith("<tool_call>") and response.endswith("</tool_call>"):
            # 提取标签中间的 JSON 字符串
            json_str = response[len("<tool_call>"):-len("</tool_call>")]
            try:
                # 解析 JSON
                return json.loads(json_str)
            except json.JSONDecodeError:
                return None
        return None
    
    def run(self):
        #########################################################
        # TODO: Run the agent                                   #
        # 1. initialize the agent                               #
        # 2. enter the agentic loop                             #
        #########################################################
        # 初始化
        self.initialize()
        self.logger.log("Agent initialization complete")

        try:
            for turn in range(self.max_turns):
                self.logger.log(f"--- Turn {turn+1}/{self.max_turns} ---")

                # 1. 查询 LLM
                llm_response_content = self.query_llm(turn)

                if llm_response_content is None:
                    self.logger.log("LLM response was empty. Terminating.")
                    break
                
                # 2. 检查是否需要终止
                if "<terminate>" in llm_response_content:
                    self.logger.log("Agent decided to terminate.")
                    # 可以在这里提取并记录最终答案
                    final_answer = llm_response_content.replace("<terminate>", "").strip()
                    self.logger.log(f"Final Answer: {final_answer}")
                    break
                
                # 3. 解析并执行工具调用
                tool_call = self._parse_tool_call(llm_response_content)
                if tool_call:
                    self.execute_tool(tool_call)
                else:
                    # 如果不是工具调用也不是终止，可以看作是模型的思考过程
                    self.logger.log(f"Agent thought: {llm_response_content}")

            else:
                self.logger.log("Max turns reached. Terminating.")

        finally:
            self.logger.log("Agent run finished.")
