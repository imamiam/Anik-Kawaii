import os
import sqlite3
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import NotFound, MethodNotAllowed
from jinja2 import Environment, FileSystemLoader
from werkzeug.serving import run_simple

# ------------------------
# Configuration
# ------------------------
BASE_URL = "" 

env = Environment(loader=FileSystemLoader("templates"))

def render(template, **context):
    context.update({"base_url": BASE_URL})
    return Response(env.get_template(template).render(**context), content_type="text/html")

# ------------------------
# URL Routing
# ------------------------
url_map = Map([
    Rule("/", endpoint="home"),
    Rule("/products", endpoint="products"),
    Rule("/contactus", endpoint="contactus"),
    Rule("/thecompany", endpoint="thecompany"),
    Rule("/register", endpoint="register", methods=["GET", "POST"]),
])

# ------------------------
# View Functions
# ------------------------
def home(request): 
    return render("home.html", title="Home")

def products(request):
    conn = sqlite3.connect("products.db")
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name, brand, price, stock, image FROM products")
        product_items = cursor.fetchall()
    except sqlite3.OperationalError:
        product_items = []
    finally:
        conn.close()

    return render("products.html", title="Products", product_items=product_items)

def contactus(request): 
    return render("contactus.html", title="Contact Us")

def thecompany(request): 
    return render("thecompany.html", title="About Us")

def register(request):
    error = None
    success = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            error = "Email is required!"
        else:
            success = f"Welcome to Anik Kawaii, {email}!"
    return render("register.html", title="Register", error=error, success=success)

# ------------------------
# Application Logic
# ------------------------
@Request.application
def app_logic(request):
    adapter = url_map.bind_to_environ(request.environ)
    try:
        endpoint, values = adapter.match()
        return globals()[endpoint](request, **values)
    except NotFound:
        return Response("404 Not Found", status=404)
    except MethodNotAllowed:
        return Response("405 Method Not Allowed", status=405)

app = SharedDataMiddleware(app_logic, {
    '/static': os.path.join(os.path.dirname(__file__), 'static')
})

if __name__ == "__main__":
    print("Anik Kawaii is running at http://0.0.0.0:5048")
    run_simple("0.0.0.0", 5048, app, use_reloader=True)