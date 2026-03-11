import json
from datetime import datetime
from typing import Dict, List
from urllib import error, request

from app.models.task import Task


STATUS_TEXT = {
    "todo": "待办",
    "doing": "进行中",
    "done": "已完成",
}


class ReportService:
    def build_daily_prompt(self, tasks: List[Task], template_text: str) -> str:
        lines = []
        for idx, task in enumerate(tasks, start=1):
            lines.append(
                f"{idx}. 标题: {task.title}\n"
                f"   状态: {STATUS_TEXT.get(task.status, task.status)}\n"
                f"   优先级: {task.priority}\n"
                f"   截止时间: {task.due_date or '-'}\n"
                f"   更新时间: {task.updated_at}\n"
                f"   描述: {task.description or '-'}"
            )

        task_text = "\n".join(lines)
        today = datetime.now().strftime("%Y-%m-%d")

        return template_text.replace("{date}", today).replace("{tasks}", task_text)

    def generate_daily_report(
        self,
        tasks: List[Task],
        prompt_template: Dict,
        model_config: Dict,
    ) -> str:
        if not tasks:
            raise RuntimeError("没有可用于生成日报的任务")

        prompt = self.build_daily_prompt(tasks, str(prompt_template["template_text"]))
        endpoint = self._build_endpoint(str(model_config["base_url"]))

        payload = {
            "model": model_config["model_name"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": float(model_config.get("temperature") or 0.7),
        }

        max_tokens = model_config.get("max_tokens")
        if max_tokens:
            payload["max_tokens"] = int(max_tokens)

        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {model_config['api_key']}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"AI接口请求失败（HTTP {exc.code}）: {detail[:240]}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"AI接口连接失败: {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError("AI接口请求超时") from exc

        choices = data.get("choices")
        if not choices:
            raise RuntimeError("AI接口返回格式异常：缺少 choices")

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("AI接口返回为空")

        return content.strip()

    @staticmethod
    def _build_endpoint(base_url: str) -> str:
        cleaned = base_url.strip().rstrip("/")
        if not cleaned.startswith("https://"):
            raise RuntimeError("Base URL 必须以 https:// 开头")

        if cleaned.endswith("/chat/completions"):
            return cleaned

        return f"{cleaned}/chat/completions"
