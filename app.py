import os
import sqlite3
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import NotFound, MethodNotAllowed
from jinja2 import Environment, FileSystemLoader
from werkzeug.serving import run_simple
from werkzeug.utils import redirect

BASE_URL = "" 
DATABASE = "products.db"
USER_DB = "users.db"

env = Environment(loader=FileSystemLoader("templates"))

def render(template, **context):
    context.setdefault("is_admin", context.get("is_admin", False))
    context.update({"base_url": BASE_URL})
    return Response(env.get_template(template).render(**context), content_type="text/html")

url_map = Map([
    Rule("/", endpoint="home"),
    Rule("/products", endpoint="products"),
    Rule("/contactus", endpoint="contactus"),
    Rule("/thecompany", endpoint="thecompany"),
    Rule("/register", endpoint="register", methods=["GET", "POST"]),
    Rule("/login", endpoint="login", methods=["GET", "POST"]),
    Rule("/add_product", endpoint="add_product", methods=["GET", "POST"]), 
    Rule("/edit/<int:id>", endpoint="edit_product", methods=["GET", "POST"]),
    Rule("/delete/<int:id>", endpoint="delete_product"),
])

def home(request): 
    return render("home.html", title="Home")

def login(request):
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        with sqlite3.connect(USER_DB, timeout=20) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and user['password'] == password:
            admin_status = True if user['is_admin'] == 1 else False
            return redirect(f"/products?msg=Welcome+back!&admin={admin_status}")
        else:
            error = "Invalid credentials. Please try again! 🌸"
    return render("login.html", title="Login", error=error)

def products(request):
    msg = request.args.get('msg')
    is_admin = request.args.get('admin') == 'True'
    with sqlite3.connect(DATABASE, timeout=20) as conn:
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, name, brand, price, stock, image, 
                COALESCE(category, 'Uncategorized') as category 
                FROM products
            """)
            product_items = cursor.fetchall()
        except sqlite3.OperationalError:
            product_items = []
    return render("products.html", title="Products", product_items=product_items, msg=msg, is_admin=is_admin)

def add_product(request):
    if request.method == "POST":
        name = request.form.get("name")
        brand = request.form.get("brand")
        price = float(request.form.get("price", 0))
        stock = int(request.form.get("stock", 0))
        image = request.form.get("image")
        category = request.form.get("category")
        with sqlite3.connect(DATABASE, timeout=20) as conn:
            conn.execute(
                "INSERT INTO products (name, brand, price, stock, image, category) VALUES (?, ?, ?, ?, ?, ?)",
                (name, brand, price, stock, image, category)
            )
        # FIXED: Added the admin=True flag to the redirect so you stay an admin after adding!
        return redirect(f"{BASE_URL}/products?msg=Product+Added!+✨&admin=True")
    return render("add_product.html", title="Add New Product")

def edit_product(request, id):
    if request.method == "POST":
        name = request.form.get("name")
        brand = request.form.get("brand")
        price = float(request.form.get("price", 0))
        stock = int(request.form.get("stock", 0))
        image = request.form.get("image")
        category = request.form.get("category")
        with sqlite3.connect(DATABASE, timeout=20) as conn:
            conn.execute(
                "UPDATE products SET name=?, brand=?, price=?, stock=?, image=?, category=? WHERE id=?",
                (name, brand, price, stock, image, category, id)
            )
        return redirect("/products?msg=Changes+Saved!+🌸&admin=True")
    with sqlite3.connect(DATABASE, timeout=20) as conn:
        conn.row_factory = sqlite3.Row
        product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()
    if product is None:
        return Response("Product Not Found", status=404)
    return render("edit_product.html", title="Edit Merch", product=product)

def delete_product(request, id):
    with sqlite3.connect(DATABASE, timeout=20) as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (id,))
    return redirect("/products?msg=Item+Deleted.+🗑️&admin=True")

def register(request):
    error = None
    success = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        if not email or not password:
            error = "Both email and password are required!"
        else:
            try:
                with sqlite3.connect(USER_DB, timeout=20) as conn:
                    conn.execute("INSERT INTO users (email, password, is_admin) VALUES (?, ?, 0)", (email, password))
                success = f"Welcome to Anik Kawaii, {email}!"
            except sqlite3.IntegrityError:
                error = "That email is already registered!"
    return render("register.html", title="Register", error=error, success=success)

def contactus(request): return render("contactus.html", title="Contact Us")
def thecompany(request): return render("thecompany.html", title="About Us")

@Request.application
def app_logic(request):
    adapter = url_map.bind_to_environ(request.environ)
    try:
        endpoint, values = adapter.match()
        return globals()[endpoint](request, **values)
    except NotFound: return Response("404 Not Found", status=404)
    except MethodNotAllowed: return Response("405 Method Not Allowed", status=405)

app = SharedDataMiddleware(app_logic, {
    '/static': os.path.join(os.path.dirname(__file__), 'static')
})

if __name__ == "__main__":
    run_simple("0.0.0.0", 5048, app, use_reloader=True)