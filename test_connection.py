import pyodbc

server = "depi-ecommerce-server-2026.database.windows.net"
database = "ECommerceDataWarehouse"

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Authentication=ActiveDirectoryInteractive;"
    "UID=za30612200107519@depi.eui.edu.eg;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    cursor.execute("SELECT DB_NAME()")
    print("Connected Database:", cursor.fetchone()[0])

    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'bronze'
    """)

    print("\nBronze Tables:")
    for row in cursor.fetchall():
        print(row[0])

    conn.close()

except Exception as e:
    print("Connection failed:", e)