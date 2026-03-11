import subprocess
from typing import Optional


def _pwsh_escape(value: str) -> str:
    return value.replace("'", "''")


class WindowsNotifier:
    def __init__(self, app_id: str = "Taskbook"):
        self.app_id = app_id

    def notify(self, title: str, message: str) -> bool:
        title_safe = _pwsh_escape(title)
        message_safe = _pwsh_escape(message)
        app_id_safe = _pwsh_escape(self.app_id)

        script = (
            "$ErrorActionPreference='Stop'; "
            f"$title='{title_safe}'; "
            f"$msg='{message_safe}'; "
            f"$appId='{app_id_safe}'; "
            "[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]; "
            "[void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]; "
            "$template='<toast><visual><binding template=""ToastGeneric""><text>'+[Security.SecurityElement]::Escape($title)+'</text><text>'+[Security.SecurityElement]::Escape($msg)+'</text></binding></visual></toast>'; "
            "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
            "$xml.LoadXml($template); "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
            "$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId); "
            "$notifier.Show($toast);"
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return result.returncode == 0
        except Exception:
            return False


def build_windows_notifier() -> Optional[WindowsNotifier]:
    try:
        return WindowsNotifier()
    except Exception:
        return None
