import os
from mcp.server.fastmcp import FastMCP
from daytona import Daytona, DaytonaConfig

DAYTONA_KEY = os.environ.get("DAYTONA_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

mcp = FastMCP("Daytona Cloud Sandbox", host="0.0.0.0", port=PORT)

def get_sandbox():
    if not DAYTONA_KEY:
        raise ValueError("خطأ: مفتاح DAYTONA_API_KEY غير محدد في متغيرات البيئة.")
    config = DaytonaConfig(api_key=DAYTONA_KEY)
    daytona = Daytona(config)
    
    # استخدام البيئة ishak الجاهزة في حسابك
    try:
        return daytona.get_sandbox("ishak")
    except Exception:
        return daytona.create()

@mcp.tool()
def execute_python_code(code: str) -> str:
    """تشغيل كود Python داخل بيئة Daytona السحابية."""
    try:
        sandbox = get_sandbox()
        response = sandbox.process.code_run(code)
        if response.exit_code != 0:
            return f"خطأ أثناء التنفيذ: {response.result}"
        return response.result if response.result else "تم تنفيذ كود Python بنجاح."
    except Exception as e:
        return f"حدث خطأ: {str(e)}"

@mcp.tool()
def execute_shell_command(command: str) -> str:
    """تنفيذ أمر Bash داخل بيئة Daytona السحابية."""
    try:
        sandbox = get_sandbox()
        response = sandbox.process.exec(command)
        if response.exit_code != 0:
            return f"خطأ أثناء تنفيذ الأمر: {response.result}"
        return response.result if response.result else "تم تنفيذ أمر Shell بنجاح."
    except Exception as e:
        return f"حدث خطأ: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse")
