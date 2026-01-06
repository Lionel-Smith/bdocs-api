import os

FLASK_ENV = "production"


class OracleDB:
    userName = "online_claims"
    password = "Welcome1"
    host = "JUMV3TSTDBSRV01.nib-bahamas.com"
    port = 1531
    sid = "v3train"
    connectionString = f"(DESCRIPTION = (ADDRESS = (PROTOCOL = TCP)(HOST = {host})(PORT = {port})) (CONNECT_DATA = (SERVER = DEDICATED) (SERVICE_NAME = {sid})))"
    dbaUser = "quincya"
    dbaPassword = "Welcome1"


class PostgresDB:
    host = "localhost"
    port = 5432
    username = "postgres"
    password = "postgres"
    database = "flask_backend"


class JWTConfig:
    secret = "jwt_secret"


class Flask:
    host = "0.0.0.0"  # '172.16.1.172'
    port = 5000
    protocol = "http" if FLASK_ENV == "development" else "https"
    admin_host = "staging-claims-admin-api.nib-bahamas.com"
    admin_port = 443
    admin_url = (
        f"{admin_host}:{admin_port}"
        if FLASK_ENV == "development"
        else f"{protocol}://{admin_host}"
    )


class FileRepo:
    path = os.path.join(os.sep, "C:" + os.sep, "uploads")


class NIBEmailService:
    api_key = "eTmCMxVP3K4bWKXtors8zw"
    app_name = "ONLINE_CLAIMS"
    protocol = "https" if FLASK_ENV == "production" else "http"
    host = (
        "staging-customer-email-api.nib-bahamas.com"
        if FLASK_ENV == "production"
        else "localhost:5003"
    )
    port = "3006"
    root_url = (
        f"{protocol}://{host}"
        if FLASK_ENV == "production"
        else f"{protocol}://{host}:{port}"
    )
    templates = {
        "application_confirmation": 3,
        "user_account_updated": 7,
        "reuploaded_notification": 17,
    }


class RateLimiter:
    default = "100/minute"  # Fixed property for easier access

    @property
    def DEAFULT_RATE_LIMIT(self):  # Kept for backwards compatibility
        return "100/minute"


class RedisDB:
    host = "localhost"  # Changed from "redis" to "localhost" for local development
    port = 6379
    REDIS_URL = f"redis://{host}:{port}"


class MinIO:
    access_key = "Abt3JX9SHJEOUSrLN7kw"
    secret_key = "LOownDA13UkRQ3LOLO4b0gGq0w8yxiKYadtgqf0y"
    claims_applications_bucket = "online-claims-applications"
    host = "192.168.100.123"
    port = "9005"
    ssl = FLASK_ENV in ["production", "staging"]
    cert_check = False


class Sentry:
    dsn = "https://12fc5bf50ac54223cdeaba371247a71e@o4506667039326208.ingest.sentry.io/4506734138490880"


class NIBOnlinePortal:
    url = "https://nibonline.nib-bahamas.com/"


class AdminService:
    host = (
        "staging-claims-admin-api.nib-bahamas.com"
        if FLASK_ENV == "production"
        else "localhost:5001"
    )
    protocol = "https" if FLASK_ENV == "production" else "http"
    root_url = f"{protocol}://{host}"
