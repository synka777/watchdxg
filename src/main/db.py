from psycopg2 import sql, errors, Error
from config import settings, env
import subprocess
import platform
import psycopg2
import getpass
import re


###################
# Helper functions

def start_pgsql_w_brew():
    brew_start = subprocess.run(
        ['brew', 'services', 'start', 'postgresql'],
        capture_output=True, text=True
    )
    if brew_start.returncode != 0:
        raise RuntimeError(f"Command failed: {brew_start.stderr}")

    if 'Successfully started' in brew_start.stdout:
        print('[INFO] Successfully started postgresql brew service')
        return True
    else:
        return False


def brew_pgsql_started(result):
    brew_pgsql_started_pttrn = re.compile(r'postgresql(@\d{1,2})?\s+started', re.MULTILINE)

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")

    if brew_pgsql_started_pttrn.search(result.stdout):
        print('[INFO] pgsql service already running')
        return True
    return False


def pgsql_installed_by_brew(result):
    brew_pgsql_inst_pttrn = re.compile(r'postgresql(@\d{1,2})?\s+none', re.MULTILINE)

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")

    if brew_pgsql_inst_pttrn.search(result.stdout):
        return True
    return False


def execute_query(connection, query, params=None, fetch=False, fetchone=False):
    try:
        with connection.cursor() as cur:
            cur.execute(query, params)

            if fetch:
                return cur.fetchall()
            if fetchone:
                return cur.fetchone()
    except errors.UniqueViolation as uve:
        print(f'[INFO] Skipped duplicate: {uve}')
        connection.rollback()
        return True
    except Error as e:
        print(f'[ERROR] Database error: {e}')
        connection.rollback()
        return None


######################
# Database management

# Function to connect to PostgreSQL
def get_default_connection(init=False):
    """
    Establishes a connection to the PostgreSQL server.

    Returns:
        psycopg2 connection object.
    """
    user = settings['db']['user']
    if init:
        current_os = platform.uname().system
        if current_os == 'Darwin':
            brew_services = subprocess.run(
                ['brew', 'services', 'list'],
                capture_output=True, text=True
            )
            if not brew_pgsql_started(brew_services):
                if pgsql_installed_by_brew(brew_services):
                    if start_pgsql_w_brew():
                        print('[INFO] PostgreSQL service started successfully.')
                else:
                    raise RuntimeError('[ERROR] PostgreSQL does not appear to be installed with brew.')

            # Now, if brew pgsql is running, we use macOS user
            user = getpass.getuser()

    password = settings['db']['password'] if not init else ''
    try:
        # Connect to the PostgreSQL server (without specifying a database for now)
        connection = psycopg2.connect(
            dbname='postgres',  # Connect to the default database before creating a new one
            user=user,
            password=password,
            host=settings['db']['host'],
            port=settings['db']['port']
        )
        connection.autocommit = True

        return connection
    except Exception as e:
        print(f'Error: Could not establish connection to PostgreSQL server: {e}')
        return None


# Function to connect to the created database
def get_connection():
    """
    Establishes a connection to the PostgreSQL database.

    Returns:
        psycopg2 connection object.
    """
    dbname = settings['db']['dbname']

    try:
        # Connect to the created database
        connection = psycopg2.connect(
            dbname=settings['db']['dbname'],
            user=settings['db']['user'],
            password=settings['db']['password'],
            host=settings['db']['host'],
            port=settings['db']['port']
        )
        connection.autocommit = True

        return connection
    except Exception as e:
        print(f'Error: Could not establish connection to database {dbname}: {e}')
        return None


# Function to create the database
def create_database():
    """
    Creates the database for storing user data.
    """
    dbname = settings['db']['dbname']
    connection = get_default_connection(init=True)
    success = True

    if connection is None:
        print('Could not establish connection to PostgreSQL. Exiting...')
        return

    cursor = connection.cursor()

    # Create the database if it doesn't exist
    try:
        cursor.execute('SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s', (dbname,))
        result = cursor.fetchone()
        if not result:
            cursor.execute(f'CREATE DATABASE {dbname};')
            print(f'Database "{dbname}" created successfully.')

        else:
            print(f'Database "{dbname}" already exists.')
    except Exception as e:
        success = False
        print(f'Error: Could not create database: {e}')
    finally:
        cursor.close()
        connection.close()
        return success


# Function to create a new database user
def create_db_user():
    """
    Creates a new PostgreSQL user with specified username and password.

    Args:
        username (str): The username for the new user.
        password (str): The password for the new user.
    """
    connection = get_default_connection(init=True)
    username = settings['db']['user']
    password = settings['db']['password']
    success = True

    if connection is None:
        print('Could not establish connection to PostgreSQL. Exiting...')
        return

    cursor = connection.cursor()

    # Create the new user if it doesn't exist
    try:
        cursor.execute(sql.SQL('SELECT 1 FROM pg_catalog.pg_user WHERE usename = %s'), (username,))
        result = cursor.fetchone()
        if not result:
            cursor.execute(sql.SQL('CREATE ROLE {} WITH LOGIN PASSWORD %s').format(sql.Identifier(username)), (password,))
            print(f'User "{username}" created successfully.')
        else:
            print(f'User "{username}" already exists.')
    except Exception as e:
        success = False
        print(f'Error: Could not create user: {e}')
    finally:
        cursor.close()
        connection.close()
        return success


# Function to grant privileges to a user
def grant_privileges():
    """
    Grants all privileges on the database to the specified user.

    Args:
        username (str): The username to whom privileges will be granted.
    """
    connection = get_connection()
    username = settings['db']['user']
    dbname = settings['db']['dbname']
    success = True

    if connection is None:
        print('Could not establish connection to the database. Exiting...')
        return

    cursor = connection.cursor()

    # Grant privileges on the database to the user
    try:
        cursor.execute(
            sql.SQL('GRANT ALL PRIVILEGES ON DATABASE {} TO {}').format(
                sql.Identifier(dbname), sql.Identifier(username)
            )
        )
        cursor.execute(
            sql.SQL('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {}').format(sql.Identifier(username))
        )

        # Allows user to insert rows into tables with SERIAL (or BIGSERIAL) fields, by having
        # permission to call NEXTVAL() on the sequence to get the next id.
        cursor.execute(
            sql.SQL('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {}').format(sql.Identifier(username))
        )
        connection.commit()
        print(f'Granted all privileges on the "{dbname}" database to user "{username}".')
    except Exception as e:
        success = False
        print(f'Error: Could not grant privileges: {e}')
    finally:
        cursor.close()
        connection.close()
        return success


# Function to create the X account's table
def create_account_table():
    """
    Creates a table to store X accounts that need to be managed
    """
    connection = get_connection()
    success = True

    if connection is None:
        print('Could not establish connection to database. Exiting...')
        return

    cursor = connection.cursor()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS accounts (
        id SERIAL PRIMARY KEY,
        handle VARCHAR(255),
        UNIQUE (handle)
    );
    """

    try:
        cursor.execute(create_table_query)
        print('Accounts table created successfully.')
    except Exception as e:
        success = False
        print(f'Error: Could not create table: {e}')
    finally:
        cursor.close()
        connection.close()
        return success

# Function to create the table to store user data
def create_users_table():
    """
    Creates a table for storing user data in the database.
    """
    connection = get_connection()
    success = True

    if connection is None:
        print('Could not establish connection to database. Exiting...')
        return

    cursor = connection.cursor()

    # SQL to create the table (you can modify the columns as needed)
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
        handle VARCHAR(255),
        username VARCHAR(255),
        certified BOOLEAN,
        bio TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        following_count INTEGER,
        followers_count INTEGER,
        featured_url VARCHAR,
        follower BOOLEAN,
        UNIQUE (handle, created_at)
    );
    """

    try:
        cursor.execute(create_table_query)
        connection.commit()
        print('Users table created successfully.')
    except Exception as e:
        success = False
        print(f'Error: Could not create table: {e}')
    finally:
        cursor.close()
        connection.close()
        return success


def register_get_uid():
    add_acc_query = 'INSERT INTO accounts (handle) VALUES (%s) RETURNING id'
    res = execute_query(
        get_connection(),
        add_acc_query,
        # The trailing comma after username is important so that Python understand it's in a tuple
        (env.str('USERNAME'),),
        fetchone=True
    )

    if res and type(res) == bool:
        res = execute_query(
            get_connection(),
            'SELECT id FROM accounts WHERE handle = %s;',
            (env.str('USERNAME'),),
            fetchone=True
        )
        uid = res[0]
    else:
        print(f'[INFO] Registered {env.str("USERNAME")} into the accounts table')
        uid = res[0]

    return uid


# if __name__ == '__main__':
def setup_db():
    if not create_database():
        print('[ERROR] Failed to create database.')
        return False
    if not create_db_user():
        print('[ERROR] Failed to create DB user.')
        return False
    if not grant_privileges():
        print('[ERROR] Failed to grant privileges.')
        return False
    if not create_account_table():
        print('[ERROR] Failed to create account table.')
        return False
    if not create_users_table():
        print('[ERROR] Failed to create users table.')
        return False

    return True