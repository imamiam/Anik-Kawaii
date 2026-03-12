import os
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import NotFound
from jinja2 import Environment, FileSystemLoader
from werkzeug.serving import run_simple

BASE_URL = "" 

env = Environment(loader=FileSystemLoader("templates"))

def render(template, **context):
    context.update({"base_url": BASE_URL})
    return Response(env.get_template(template).render(**context), content_type="text/html")

url_map = Map([
    Rule("/", endpoint="home"),
    Rule("/products", endpoint="products"),
    Rule("/services", endpoint="services"),
    Rule("/contactus", endpoint="contactus"),
    Rule("/thecompany", endpoint="thecompany"),
    Rule("/thehistory", endpoint="thehistory"),
    Rule("/register", endpoint="register"),
])

# View Functions
def home(request): return render("home.html", title="Home")

def products(request): 
    # This dictionary must be defined and passed as 'categories'
    categories = {
        "Keychains": [
            {"id": 101, "name": "My Melody Plush", "price": 150, "image": "mymelody.jpg"},
            {"id": 102, "name": "Rilakkuma Corn", "price": 100, "image": "rilakkuma_corn.jpg"},
            {"id": 103, "name": "Kirby Star", "price": 120, "image": "kirby_star.jpg"},
            {"id": 104, "name": "Keroppi Plush", "price": 130, "image": "keroppi.jpg"},
        ],
        "Figurines": [
            {"id": 201, "name": "Sora Figure", "price": 850, "image": "sora.jpg"},
            {"id": 202, "name": "No Face Figure", "price": 450, "image": "noface.jpg"},
            {"id": 203, "name": "Chopper Figure", "price": 350, "image": "chopper.jpg"},
            {"id": 204, "name": "Nobara Figure", "price": 400, "image": "nobara.jpg"},
        ],
        "Plushies": [
            {"id": 301, "name": "Jiji Cat Plush", "price": 500, "image": "jiji.jpg"},
            {"id": 302, "name": "Kirby Plush", "price": 450, "image": "kirby_plush.jpg"},
            {"id": 303, "name": "Kuromi Bunny", "price": 600, "image": "kuromi.jpg"},
            {"id": 304, "name": "Pikmin Mug", "price": 300, "image": "pikmin.jpg"},
        ]
    }
    # IMPORTANT: Change 'product_items=items' to 'categories=categories'
    return render("products.html", title="Products", categories=categories)

def services(request): return render("services.html", title="Services")
def contactus(request): return render("contactus.html", title="Contact Us")
def thecompany(request): return render("thecompany.html", title="The Company")
def thehistory(request): return render("thehistory.html", title="The History")

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

@Request.application
def app_logic(request):
    adapter = url_map.bind_to_environ(request.environ)
    try:
        endpoint, values = adapter.match()
        return globals()[endpoint](request, **values)
    except NotFound:
        return Response("404 Not Found", status=404)

app = SharedDataMiddleware(app_logic, {
    '/static': os.path.join(os.path.dirname(__file__), 'static')
})

if __name__ == "__main__":
    print("Anik Kawaii is running at http://127.0.0.1:5048")
    run_simple("127.0.0.1", 5048, app, use_reloader=True)