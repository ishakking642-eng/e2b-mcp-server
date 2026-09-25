import os
import httpx
from mcp.server.fastmcp import FastMCP

# إنشاء خادم MCP
mcp = FastMCP("Daytona Sandbox Manager")

# البيانات الخاصة بك
DAYTONA_API_KEY = "dtn_365790d2012d44b234ebce2874961b9c87a05239b978412c84409a2276b1e1f5"
SANDBOX_ID = "b082dcc5-1d81-49c5-bodf-f87a0dbo0171"  # من شاشة Daytona[span_2](start_span)[span_2](end_span)

@mcp.tool()
def wake_up_sandbox() -> str:
    """إيقاظ الـ Sandbox وتجهيز البيئة عند بدء المحادثة"""
    headers = {
        "Authorization": f"Bearer {DAYTONA_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"https://app.daytona.io/api/workspace/{SANDBOX_ID}"

    try:
        # فحص الحالة
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
        return f"حدث خطأ: {str(e)}"

if __name__ == "__main__":
    # تشغيل السيرفر على Port 8000
    mcp.run(transport="sse", port=8000)
