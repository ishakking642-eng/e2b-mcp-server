import os
from mcp.server.fastmcp import FastMCP
from e2b_code_interpreter import Sandbox

E2B_KEY = os.environ.get("E2B_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

# تهيئة خادم FastMCP
mcp = FastMCP("E2B Cloud Sandbox", host="0.0.0.0", port=PORT)

@mcp.tool()
def execute_python_code(code: str) -> str:
    """تشغيل كود Python داخل بيئة لينكس سحابية معزولة."""
    if not E2B_KEY:
        return "خطأ: مفتاح E2B_API_KEY غير محدد في متغيرات البيئة."
    
    # ضمان وجود المفتاح في متغيرات البيئة للـ Sandbox
    os.environ["E2B_API_KEY"] = E2B_KEY
    
    # استدعاء Sandbox() بدون تمرير api_key كمعامل مباشر
    with Sandbox() as sandbox:
        execution = sandbox.run_code(code)
        return execution.text if execution.text else "تم التنفيذ بنجاح."

@mcp.tool()
def execute_shell_command(command: str) -> str:
    """تنفيذ أمر Terminal (Bash) في البيئة السحابية لبناء وتثبيت المشاريع."""
    if not E2B_KEY:
        return "خطأ: مفتاح E2B_API_KEY غير محدد في متغيرات البيئة."
    
    os.environ["E2B_API_KEY"] = E2B_KEY
    
    with Sandbox() as sandbox:
        proc = sandbox.commands.run(command)
        return proc.stdout + proc.stderr

if __name__ == "__main__":
    mcp.run(transport="sse")
