"""
    web server
    为使用者提供一个类，
    使用这可以快速的搭建web服务，
    展示自己的网页

功能类的设计：
1. 明确类要实现什么功能
   多个步骤实现
   分情况讨论实现

2. 这个类使用者需要怎么用
   实例化对象 （自动实现一些属性的设置和配置）
   通过对象有序的调用一些方法实现某些功能

3. 在满足功能时，那些是我能够替使用者决定的，那些是使用者必须自己决定的
   尽量让使用者变得简单 （继承 重写 多态）
   不能替用户决定的用户自己决定 （传参，设置配置文件）

4. 如何设定属性和拆分方法
    属性在哪设置
    拆分功能
"""
from socket import *
from select import select
import re


# 主体功能
class HTTPServer:
    def __init__(self, host='0.0.0.0', port=8080, dir=None):
        self.host = host
        self.port = port
        self.dir = dir
        # 多路复用列表
        self.rlist = []
        self.wlist = []
        self.xlist = []
        # 套接字的准备
        self._create_socket()
        self._bind()

    def _create_socket(self):
        self.sock = socket()  # 创建tcp套接字
        self.sock.setblocking(False)

    def _bind(self):
        self.address = (self.host, self.port)
        self.sock.bind(self.address)

    # 启动服务即准备好接收客户端请求
    def start(self):
        self.sock.listen(5)
        print("Listen the port %d" % self.port)
        # IO 多路复用并发
        self.rlist.append(self.sock)
        while True:
            rs, ws, xs = select(self.rlist,
                                self.wlist,
                                self.xlist)
            for r in rs:
                if r is self.sock:
                    # 监听套接字就绪 (有客户端链接)
                    connfd, addr = r.accept()
                    print("Connect from", addr)
                    connfd.setblocking(False)  # 防止消息收的太慢影响了其他IO执行
                    self.rlist.append(connfd)  # 每当有一个客户端链接，就将这个链接套接字加入监控
                else:
                    self.handle(r)  # 处理客户端http请求

    # 处理请求
    def handle(self, connfd):
        # 接收客户端（浏览器）请求
        request = connfd.recv(1024 * 10).decode()
        # print(request)

        # 解析客户端发送的请求 (从请求中需要获取什么信息)
        # 通过正则表达式获取请求内容
        pattern = r"[A-Z]+\s+(?P<info>/\S*)"
        try:
            info = re.match(pattern, request).group("info")
            print("请求内容:", info)
        except:
            # 客户端断开
            self.rlist.remove(connfd)
            connfd.close()
            return
        else:
            # 回发数据
            self.send_data(connfd, info)

    # 给浏览器发送
    def send_data(self, connfd, info):
        # 根据请求组织数据内容 info --> /   /xxxx
        if info == '/':
            html = self.dir + "/index.html"
        else:
            html = self.dir + info

        # 将数据内容形成http响应格式返回给浏览器
        try:
            f = open(html, 'rb')
        except:
            # 请求内容不存在
            response = "HTTP/1.1 404 Not Found\r\n"
            response += "Content-Type:text/html\r\n"
            response += '\r\n'
            response += "<h1>Sorry...</h1>"
            response = response.encode()
        else:
            # 请求内容存在
            data = f.read()
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type:text/html\r\n"
            response += "Content-Length:%d\r\n" % len(data)
            response += '\r\n'
            response = response.encode() + data
        # 无论是否异常都要执行 finally:
        finally:
            # 将其发送个客户端
            connfd.send(response)


if __name__ == '__main__':
    # 需要用户决定 ： 网络地址 和要发送的数据
    host = '0.0.0.0'
    port = 8000
    dir = "./static"  # 数据位置

    # 实例化对象，调用方法启动服务
    httpd = HTTPServer(host=host, port=port, dir=dir)
    httpd.start()  # 启动服务
