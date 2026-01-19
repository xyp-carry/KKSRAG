import http.server
import socketserver
import webbrowser
import os

# ================= 配置区域 =================
# 设置端口号，如果被占用可以修改为 8001, 9000 等
PORT = 12251
# 设置启动后是否自动打开浏览器
AUTO_OPEN_BROWSER = True
# ===========================================


# 自定义请求处理类，方便你后续扩展逻辑
class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 示例：后续你可以在这里添加拦截逻辑
        # 比如：打印每次访问的路径

        # 调用父类方法处理静态文件
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def end_headers(self):
        # 解决后续可能遇到的跨域问题（CORS）
        self.send_header("Access-Control-Allow-Origin", "*")
        http.server.SimpleHTTPRequestHandler.end_headers(self)


def run_server():
    # 确保脚本在当前目录运行
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 使用 ThreadingMixIn 允许并发请求（虽然静态页面用不上，但好习惯）
    Handler = MyRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"服务器已启动在端口: {PORT}")
        print(f"请在浏览器访问: http://localhost:{PORT}")
        print("按 Ctrl+C 停止服务器")

        if AUTO_OPEN_BROWSER:
            webbrowser.open(f"http://localhost:{PORT}")

        try:
            # 保持服务器运行
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止。")
            httpd.server_close()


if __name__ == "__main__":
    run_server()
