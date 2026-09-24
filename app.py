import os
from mcp.server.fastmcp import FastMCP
from e2b_code_interpreter import Sandbox

E2B_KEY = os.environ.get("E2B_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

mcp = FastMCP("E2B Cloud Sandbox", host="0.0.0.0", port=PORT)

@mcp.tool()
def execute_python_code(code: str) -> str:
    """تشغيل كود Python داخل بيئة لينكس سحابية معزولة."""
    if not E2B_KEY:
        return "خطأ: مفتاح E2B_API_KEY غير محدد في متغيرات البيئة."
    
    os.environ["E2B_API_KEY"] = E2B_KEY
    try:
        # استخدام Sandbox.create() لإنشاء الجلسة بشكل صحيح
        with Sandbox.create(api_key=E2B_KEY) as sandbox:
            execution = sandbox.run_code(code)
            return execution.text if execution.text else "تم التنفيذ بنجاح."
    except Exception as e:
        return f"حدث خطأ أثناء تشغيل البيئة السحابية: {str(e)}"

@mcp.tool()
def execute_shell_command(command: str) -> str:
    """تنفيذ أمر Terminal (Bash) في البيئة السحابية لبناء وتثبيت المشاريع."""
    if not E2B_KEY:
        return "خطأ: مفتاح E2B_API_KEY غير محدد في متغيرات البيئة."
    
    os.environ["E2B_API_KEY"] = E2B_KEY
    try:
        # استخدام Sandbox.create() لإنشاء الجلسة بشكل صحيح
        with Sandbox.create(api_key=E2B_KEY) as sandbox:
            proc = sandbox.commands.run(command)
            out = (proc.stdout or "") + (proc.stderr or "")
            return out if out else "تم تنفيذ الأمر بنجاح."
    except Exception as e:
        return f"حدث خطأ أثناء تنفيذ أمر Shell: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse")
