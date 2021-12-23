from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index(): 
    test = 20
    return render_template("index.html", template_test=test)    

@app.route("/login")
def login(): pass

@app.route("/wnd/<handle>")
def wndinfo(): pass

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)