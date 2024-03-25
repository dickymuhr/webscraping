def get_db_connection():
    conn = {
        'login': 'postgres',
        'password': 'newpassword',
        'host': '34.128.124.94',
        'port': '5432',
        'schema': 'external'
    }
    # Corrected access to dictionary values within the f-string
    conn_url = f"postgresql+psycopg2://{conn['login']}:{conn['password']}@{conn['host']}:{conn['port']}/{conn['schema']}"
    print(conn_url)

get_db_connection()
