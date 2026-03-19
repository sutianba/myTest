from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    print('启动简单Flask应用...')
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f'应用启动失败: {str(e)}')
        import traceback
        traceback.print_exc()