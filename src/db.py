from pathlib import Path
from psycopg2 import sql
import subprocess
import platform
import psycopg2
import getpass
import json
import re

settings = {}


###################
# Helper functions

def get_settings():
    global settings
    current_dir = Path(__file__).resolve().parent
    if len(settings) == 0:
        with open(f'{current_dir}/settings.json', 'r') as read_settings:
            for key, val in json.load(read_settings).items():
                settings[key] = val
    return settings


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


######################
# Database management

# Function to connect to PostgreSQL
def get_connection(init=False):
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
                    raise RuntimeError("[ERROR] PostgreSQL does not appear to be installed with brew.")

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
        return connection
    except Exception as e:
        print(f'Error: Could not establish connection to PostgreSQL server: {e}')
        return None


# Function to connect to the created database
def get_db_connection():
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
        return connection
    except Exception as e:
        print(f'Error: Could not establish connection to database {dbname}: {e}')
        return None


# Function to create the database
def create_database():
    """
    Creates the database for storing follower data.
    """
    dbname = settings['db']['dbname']
    connection = get_connection()

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
        print(f'Error: Could not create database: {e}')
    finally:
        cursor.close()
        connection.close()


# Function to create a new database user
def create_db_user():
    """
    Creates a new PostgreSQL user with specified username and password.

    Args:
        username (str): The username for the new user.
        password (str): The password for the new user.
    """
    connection = get_connection(init=True)
    username = settings['db']['user']
    password = settings['db']['password']

    if connection is None:
        print('Could not establish connection to PostgreSQL. Exiting...')
        return

    cursor = connection.cursor()

    # Create the new user if it doesn't exist
    try:
        cursor.execute(sql.SQL('SELECT 1 FROM pg_catalog.pg_user WHERE usename = %s'), (username,))
        result = cursor.fetchone()
        if not result:
            cursor.execute(sql.SQL('CREATE USER {} WITH PASSWORD %s').format(sql.Identifier(username)), (password,))
            print(f'User "{username}" created successfully.')
        else:
            print(f'User "{username}" already exists.')
    except Exception as e:
        print(f'Error: Could not create user: {e}')
    finally:
        cursor.close()
        connection.close()


# Function to grant privileges to a user
def grant_privileges():
    """
    Grants all privileges on the database to the specified user.

    Args:
        username (str): The username to whom privileges will be granted.
    """
    connection = get_db_connection()
    username = settings['db']['user']
    dbname = settings['db']['dbname']

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
        print(f'Granted all privileges on the "{dbname}" database to "{username}".')
    except Exception as e:
        print(f'Error: Could not grant privileges: {e}')
    finally:
        cursor.close()
        connection.close()


# Function to create the X account's table
def create_account_table():
    """
    Creates a table to store X accounts that need to be managed
    """
    connection = get_db_connection()

    if connection is None:
        print('Could not establish connection to database. Exiting...')
        return

    cursor = connection.cursor()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS accounts (
        id SERIAL PRIMARY KEY,
        handle VARCHAR(255),
        password VARCHAR(255)
    );
    """

    try:
        cursor.execute(create_table_query)
        connection.commit()
        print('Followers table created successfully.')
    except Exception as e:
        print(f'Error: Could not create table: {e}')
    finally:
        cursor.close()
        connection.close()


# Function to create the table to store follower data
def create_follower_table():
    """
    Creates a table for storing follower data in the database.
    """
    connection = get_db_connection()

    if connection is None:
        print('Could not establish connection to database. Exiting...')
        return

    cursor = connection.cursor()

    # SQL to create the table (you can modify the columns as needed)
    create_table_query = """
    CREATE TABLE IF NOT EXISTS followers (
        id SERIAL PRIMARY KEY,
        account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
        handle VARCHAR(255),
        username VARCHAR(255),
        bio TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        following_count INTEGER,
        follower_count INTEGER,
        featured_url VARCHAR
    );
    """

    try:
        cursor.execute(create_table_query)
        connection.commit()
        print('Followers table created successfully.')
    except Exception as e:
        print(f'Error: Could not create table: {e}')
    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    get_settings()

    # Create the user
    create_db_user()

    # Create the database before creating the user
    create_database()

    # Grant privileges to the user
    grant_privileges()

    # Then create tables
    create_account_table()
    create_follower_table()