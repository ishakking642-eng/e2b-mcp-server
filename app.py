import os
import httpx
from mcp.server.fastmcp import FastMCP

# 1. إنشاء خادم MCP
mcp = FastMCP("Daytona Sandbox Manager")

# 2. البيانات الخاصة ببيئة Daytona
# يُفضل ضبط هذه البيانات كـ Environment Variables داخل منصة Render
DAYTONA_API_KEY = os.getenv("DAYTONA_API_KEY", "dtn_365790d2012d44b234ebce2874961b9c87a05239b978412c84409a2276b1e1f5")
DAYTONA_API_URL = os.getenv("DAYTONA_API_URL", "https://app.daytona.io/api")
SANDBOX_ID = os.getenv("SANDBOX_ID", "b082dcc5-1d81-49c5-bodf-f87a0dbo0171")

# 3. أداة إيقاظ الـ Sandbox
@mcp.tool()
def wake_up_sandbox() -> str:
    """إيقاظ الـ Sandbox وتجهيز البيئة عند بدء المحادثة"""
    headers = {
        "Authorization": f"Bearer {DAYTONA_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{DAYTONA_API_URL}/workspace/{SANDBOX_ID}"
    
    try:
        # فحص حالة الـ Sandbox
        res = httpx.get(url, headers=headers)
        if res.status_code == 200:
            state = res.json().get("state")
            if state != "started":
                # تشغيل البيئة إذا كانت متوقفة
                httpx.post(f"{url}/start", headers=headers)
                return "تم إيقاظ الـ Sandbox بنجاح وهو جاهز للعمل الآن."
            return "الـ Sandbox يعمل ونشط بالفعل."
        return f"تعذر الاتصال بـ Daytona: {res.status_code}"
    except Exception as e:
        return f"حدث خطأ أثناء الاتصال: {str(e)}"

# 4. تشغيل الخادم مع إعدادات Render الصحيحة
if __name__ == "__main__":
    # استخراج رقم البورت المخصص تلقائياً من Render
    port = int(os.environ.get("PORT", 8000))
    
    # ضبط الإعدادات المباشرة لخادم FastMCP
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    
    # تشغيل الخدمة عبر بروتوكول SSE
    mcp.run(transport="sse")
