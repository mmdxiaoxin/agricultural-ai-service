from waitress import serve
from app import app

if __name__ == "__main__":
    print(f"Starting server on {app.config['HOST']}:{app.config['PORT']}")
    serve(
        app,
        host=app.config["HOST"],
        port=app.config["PORT"],
        threads=4,
        connection_limit=1000,
        channel_timeout=app.config["REQUEST_TIMEOUT"],
        url_scheme="http",
        ident="Agricultural AI Service",
    )
