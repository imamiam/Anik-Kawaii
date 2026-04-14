import os
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import NotFound, MethodNotAllowed
from jinja2 import Environment, FileSystemLoader
from werkzeug.serving import run_simple
from werkzeug.utils import redirect
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_URL = "" 
PROD_DB_URL = "sqlite:///products.db"
USER_DB_URL = "sqlite:///users.db"

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    brand = Column(String)
    price = Column(Float)
    stock = Column(Integer)
    image = Column(String)
    category = Column(String)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    is_admin = Column(Integer, default=0)

prod_engine = create_engine(PROD_DB_URL)
user_engine = create_engine(USER_DB_URL)

SessionProd = sessionmaker(bind=prod_engine)
SessionUser = sessionmaker(bind=user_engine)

Base.metadata.create_all(prod_engine)
Base.metadata.create_all(user_engine)

env = Environment(loader=FileSystemLoader("templates"))

def render(template, request, **context):
    is_admin = request.args.get('admin') == 'True' or request.form.get('admin') == 'True'
    user_id = request.args.get('user_id') or request.form.get('user_id')
    
    context['is_admin'] = is_admin
    context['user_id'] = user_id
    context['base_url'] = BASE_URL
    
    if 'session' not in context:
        context['session'] = {'user_id': user_id} if user_id else {}
        
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
], strict_slashes=False)

def home(request): 
    return render("home.html", request, title="Home")

def login(request):
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db_session = SessionUser()
        user = db_session.query(User).filter_by(email=email).first()
        
        if user and user.password == password:
            is_admin = True if user.is_admin == 1 else False
            uid = user.id
            db_session.close()
            return redirect(f"/products?msg=Welcome+back!&admin={is_admin}&user_id={uid}")
        else:
            db_session.close()
            error = "Invalid credentials. Please try again! 🌸"
    return render("login.html", request, title="Login", error=error)

def products(request):
    msg = request.args.get('msg')
    db_session = SessionProd()
    try:
        product_items = db_session.query(Product).all()
    except:
        product_items = []
    db_session.close()
    return render("products.html", request, title="Products", product_items=product_items, msg=msg)

def add_product(request):
    is_admin = request.args.get('admin') == 'True' or request.form.get('admin') == 'True'
    user_id = request.args.get('user_id') or request.form.get('user_id')

    if request.method == "POST":
        db_session = SessionProd()
        new_product = Product(
            name=request.form.get("name"),
            brand=request.form.get("brand"),
            price=float(request.form.get("price", 0)),
            stock=int(request.form.get("stock", 0)),
            image=request.form.get("image"),
            category=request.form.get("category")
        )
        db_session.add(new_product)
        db_session.commit()
        db_session.close()
        return redirect(f"/products?msg=Product+Added!+✨&admin={is_admin}&user_id={user_id}")
    return render("add_product.html", request, title="Add New Product")

def edit_product(request, id):
    is_admin = request.args.get('admin') == 'True' or request.form.get('admin') == 'True'
    user_id = request.args.get('user_id') or request.form.get('user_id')

    db_session = SessionProd()
    product = db_session.query(Product).get(id)

    if request.method == "POST":
        product.name = request.form.get("name")
        product.brand = request.form.get("brand")
        product.price = float(request.form.get("price", 0))
        product.stock = int(request.form.get("stock", 0))
        product.image = request.form.get("image")
        product.category = request.form.get("category")
        db_session.commit()
        db_session.close()
        return redirect(f"/products?msg=Changes+Saved!+🌸&admin={is_admin}&user_id={user_id}")
    
    return render("edit_product.html", request, title="Edit Merch", product=product)

def delete_product(request, id):
    is_admin = request.args.get('admin') == 'True'
    user_id = request.args.get('user_id')
    db_session = SessionProd()
    product = db_session.query(Product).get(id)
    if product:
        db_session.delete(product)
        db_session.commit()
    db_session.close()
    return redirect(f"/products?msg=Item+Deleted.+🗑️&admin={is_admin}&user_id={user_id}")

def register(request):
    error = None
    success = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        if not email or not password:
            error = "Both email and password are required!"
        else:
            db_session = SessionUser()
            try:
                new_user = User(email=email, password=password, is_admin=0)
                db_session.add(new_user)
                db_session.commit()
                success = f"Welcome to Anik Kawaii, {email}!"
            except:
                error = "That email is already registered!"
            finally:
                db_session.close()
    return render("register.html", request, title="Register", error=error, success=success)

def contactus(request): return render("contactus.html", request, title="Contact Us")
def thecompany(request): return render("thecompany.html", request, title="About Us")

@Request.application
def app_logic(request):
    adapter = url_map.bind_to_environ(request.environ)
    try:
        endpoint, values = adapter.match()
        return globals()[endpoint](request, **values)
    except NotFound:
        if request.path == '/favicon.ico': return Response(status=404)
        return Response("404 Not Found", status=404)
    except Exception as e:
        print(f"500 Error: {e}")
        return Response(f"An error occurred: {e}", status=500)

app = SharedDataMiddleware(app_logic, {
    '/static': os.path.join(os.path.dirname(__file__), 'static')
})

if __name__ == "__main__":
    run_simple("0.0.0.0", 5048, app, use_reloader=True)