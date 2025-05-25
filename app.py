import os
import time
import socket
from flask import Flask, request, render_template, send_file, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import qrcode
from PIL import ImageTk
import threading
import tkinter as tk

app = Flask(__name__)
app.secret_key = "your-secret-key-here"

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def show_qr_gui(url):
    def create_window():
        root = tk.Tk()
        root.title("服务器访问地址")
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        tk_img = ImageTk.PhotoImage(img)
        
        label = tk.Label(root, image=tk_img)
        label.pack()
        
        addr_label = tk.Label(root, text=f"访问地址: {url}")
        addr_label.pack()
        
        root.update_idletasks()
        window_width = root.winfo_width()
        window_height = root.winfo_height()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        root.geometry(f"+{x}+{y}")
        root.protocol("WM_DELETE_WINDOW", lambda: root.destroy())
        root.mainloop()

    thread = threading.Thread(target=create_window, daemon=True)
    thread.start()


def allowed_file(filename):
    return True


@app.route("/")
def index():
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "files[]" not in request.files:
        return jsonify({"success": False, "message": "没有选择文件"}), 400

    files = request.files.getlist("files[]")
    if not files or files[0].filename == "":
        return jsonify({"success": False, "message": "没有选择文件"}), 400

    try:
        client_start_time = float(request.form.get('start_time', time.time()))
        server_start_time = time.time()
        
        uploaded_files = []

        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                if filename:
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    uploaded_files.append(filename)

        server_end_time = time.time()
        total_elapsed_time = server_end_time - client_start_time
        
        if total_elapsed_time < 0.1:
            total_elapsed_time = 0.1
            
        total_size = sum(
            os.path.getsize(os.path.join(app.config["UPLOAD_FOLDER"], f))
            for f in uploaded_files
        )
        
        upload_speed = total_size / total_elapsed_time / (1024 * 1024)
        display_speed = min(upload_speed, 300)

        message = f"成功上传 {len(uploaded_files)} 个文件！上传速度：{display_speed:.2f} MB/s"
        return jsonify({"success": True, "message": message}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"上传失败: {str(e)}"}), 500


@app.route("/download/<filename>")
def download_file(filename):
    try:
        client_start_time = float(request.args.get('start_time', time.time()))
        server_start_time = time.time()
        
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 {filename} 不存在")
            
        file_size = os.path.getsize(file_path)
        response = send_file(file_path, as_attachment=True)
        
        @response.call_on_close
        def on_close():
            server_end_time = time.time()
            total_elapsed_time = server_end_time - client_start_time
            
            if total_elapsed_time < 0.1:
                total_elapsed_time = 0.1
                
            download_speed = file_size / total_elapsed_time / (1024 * 1024)
            app.logger.info(f"下载速度: {min(download_speed, 300):.2f} MB/s")
            
        return response

    except Exception as e:
        return redirect(url_for("index"))


@app.route("/delete/<filename>")
def delete_file(filename):
    try:
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        app.logger.info(f"删除文件 {filename} 成功")
        flash("文件删除成功！")
    except Exception as e:
        app.logger.error(f"删除文件 {filename} 失败：{str(e)}")
        flash("文件删除失败")
    return redirect(url_for("index"))


@app.route("/speed_test", methods=["POST"])
def speed_test():
    try:
        test_size = 100 * 1024 * 1024
        test_data = os.urandom(test_size)
        
        start_time = time.time()
        
        response = app.response_class(
            response=test_data,
            status=200,
            mimetype='application/octet-stream'
        )
        
        @response.call_on_close
        def calculate_speed():
            end_time = time.time()
            elapsed_time = end_time - start_time
            if elapsed_time < 0.1:
                elapsed_time = 0.1
                
            speed_mbps = (test_size * 8) / (elapsed_time * 1000 * 1000)
            if speed_mbps > 1000:
                speed_mbps = 1000
            
        return response
        
    except Exception as e:
        return jsonify({"error": str(e), "speed": 0, "unit": "Mbps"})


if __name__ == "__main__":
    host = get_local_ip()
    port = 80
    url = f"http://{host}:{port}"
    
    show_qr_gui(url)

    app.run(host=host, port=port, debug=True, use_reloader=False)

    