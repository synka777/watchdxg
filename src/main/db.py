from pathlib import Path
from psycopg2 import sql, errors, Error
from config import settings, env
from tools.logger import logger
from config import parse_args
import subprocess
import platform
import psycopg2
import getpass
import re


dev_mode: bool = True if parse_args().dev else False


###################
# Helper functions

def get_host():
    return settings['db']['host'] if dev_mode else 'psql_srvc'


def get_db_password():
    if dev_mode: # If dev mode, we run on MACOS and the default postgres pwd is empty
        return ''

    if not dev_mode:
        password_file = '/run/secrets/.pg_password'
    else:
        root_dir = Path(__file__).resolve().parent.parent.parent
        password_file = f'{root_dir}/.pg_password'

    with open(password_file, 'r') as f:
        return f.read().strip()


def get_default_db_user():
    if dev_mode:
        current_os = platform.uname().system
        if current_os == 'Darwin':
            brew_services = subprocess.run(
                ['brew', 'services', 'list'],
                capture_output=True, text=True
            )

            if not brew_pgsql_started(brew_services):
                if pgsql_installed_by_brew(brew_services):
                    if start_pgsql_w_brew():
                        logger.info('PostgreSQL service started successfully.')
                else:
                    raise RuntimeError('PostgreSQL does not appear to be installed with brew.')

            # Now, if brew pgsql is running, we use macOS user
            return getpass.getuser()

    return 'postgres'


def start_pgsql_w_brew():
    brew_start = subprocess.run(
        ['brew', 'services', 'start', 'postgresql'],
        capture_output=True, text=True
    )
    if brew_start.returncode != 0:
        raise RuntimeError(f"Command failed: {brew_start.stderr}")

    if 'Successfully started' in brew_start.stdout:
        logger.info('Successfully started postgresql brew service')
        return True
    else:
        return False


def brew_pgsql_started(result):
    brew_pgsql_started_pttrn = re.compile(r'postgresql(@\d{1,2})?\s+started', re.MULTILINE)

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")

    if brew_pgsql_started_pttrn.search(result.stdout):
        logger.info('pgsql service already running')
        return True
    return False


def pgsql_installed_by_brew(result):
    brew_pgsql_inst_pttrn = re.compile(r'postgresql(@\d{1,2})?\s+none', re.MULTILINE)

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")

    if brew_pgsql_inst_pttrn.search(result.stdout):
        return True
    return False


def execute_query(connection, query, params=None, fetch=False, fetchone=False, do_raise=False):
    try:
        with connection.cursor() as cur:
            cur.execute(query, params)

            if fetch:
                return cur.fetchall()
            elif fetchone:
                return cur.fetchone()
            else:
                return True
    except errors.UniqueViolation as uve:
        connection.rollback()
        if do_raise:
            raise
        return True
    except Error as e:
        logger.error(f'Database error: {e}')
        connection.rollback()
        return None


######################
# Database management

# Function to connect to PostgreSQL
def get_default_connection(do_raise=False):
    """
    Establishes a connection to the PostgreSQL server.

    Returns:
        psycopg2 connection object.
    """
    user = get_default_db_user()
    password = get_db_password()

    try:
        # Connect to the PostgreSQL server (without specifying a database for now)
        connection = psycopg2.connect(
            dbname='postgres',  # Connect to the default database before creating a new one
            user=user,
            password=password,
            host=get_host(),
            port=settings['db']['port']
        )
        connection.autocommit = True

        return connection
    except Exception as e:
        logger.critical(f'Could not establish connection to PostgreSQL server: {e}')
        if do_raise:
            raise
        else:
            return None


def change_schema_owner():
    connection = psycopg2.connect(
        dbname=settings['db']['dbname'],
        user=get_default_db_user(),  # Database owner
        password=get_db_password(),
        host=get_host(),
        port=settings['db']['port']
    )
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(
            sql.SQL('ALTER SCHEMA public OWNER TO {}').format(sql.Identifier(settings['db']['pipeline_user']))
        )
        connection.commit()
        logger.info(f'Changed owner of schema public to {settings["db"]["pipeline_user"]}')
        return True
    except Exception as e:
        logger.critical(f'Error: Could not change schema owner: {e}')
    finally:
        cursor.close()
        connection.close()


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
            user=settings['db']['pipeline_user'],
            password=get_db_password(),
            host=get_host(),
            port=settings['db']['port']
        )
        connection.autocommit = True

        return connection
    except Exception as e:
        logger.critical(f'Could not establish connection to database {dbname}: {e}')
        return None


# Function to create the database
def create_database():
    """
    Creates the database for storing user data.
    """
    dbname = settings['db']['dbname']
    connection = get_default_connection()
    success = True

    if connection is None:
        logger.critical('Could not establish connection to PostgreSQL. Exiting...')
        return

    cursor = connection.cursor()

    # Create the database if it doesn't exist
    try:
        cursor.execute('SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s', (dbname,))
        result = cursor.fetchone()
        if not result:
            cursor.execute(f'CREATE DATABASE {dbname};')
            logger.info(f'Database "{dbname}" created successfully.')

        else:
            logger.info(f'Database "{dbname}" already exists.')
    except Exception as e:
        success = False
        logger.error(f'Could not create database: {e}')
    finally:
        cursor.close()
        connection.close()
        return success


# Function to create a new database user
def create_db_user():
    """
    Creates a new PostgreSQL user with specified username and password.
    """
    connection = get_default_connection()
    username = settings['db']['pipeline_user']
    password = get_db_password()
    success = True

    if connection is None:
        logger.critical('Could not establish connection to PostgreSQL. Exiting...')
        return

    cursor = connection.cursor()

    # Create the new user if it doesn't exist
    try:
        cursor.execute(sql.SQL('SELECT 1 FROM pg_catalog.pg_user WHERE usename = %s'), (username,))
        result = cursor.fetchone()
        if not result:
            cursor.execute(sql.SQL('CREATE ROLE {} WITH LOGIN PASSWORD %s').format(sql.Identifier(username)), (password,))
            logger.info(f'User "{username}" created successfully.')
        else:
            logger.info(f'User "{username}" already exists.')
    except Exception as e:
        success = False
        logger.critical(f'Error: Could not create user: {e}')
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
    username = settings['db']['pipeline_user']
    dbname = settings['db']['dbname']
    success = True

    if connection is None:
        logger.critical('Could not establish connection to the database. Exiting...')
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
        logger.info(f'Granted all privileges on the "{dbname}" database to user "{username}".')
    except Exception as e:
        success = False
        logger.critical(f'Error: Could not grant privileges: {e}')
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
        logger.info(f'Added a new account into the accounts table')
        uid = res[0]

    return uid


def setup_db():
    #################
    # Setup database

    if not create_database():
        logger.critical('Failed to create database.')
        return False

    if not create_db_user():
        logger.critical('Failed to create DB user.')
        return False

    if not change_schema_owner():
        logger.critical('Unable to change public schema ownership.')
        return False

    if not grant_privileges():
        logger.critical('Failed to grant privileges.')
        return False

    ################
    # Create tables

    src_dir = Path(__file__).resolve().parent.parent
    connection = get_connection()

    with open(f'{src_dir}/sql/accounts.sql', 'r') as f:
        schema_sql = f.read()
        if not execute_query(connection, schema_sql):
            logger.critical('Failed to create accounts table.')
            return False

    with open(f'{src_dir}/sql/users.sql', 'r') as f:
        schema_sql = f.read()
        if not execute_query(connection, schema_sql):
            logger.critical('Failed to create users table.')
            return False

    # Add a trigger to the users table to update last_updated on UPDATE operations
    with open(f'{src_dir}/sql/setup_trigger.sql', 'r') as f:
        schema_sql = f.read()
        if not execute_query(connection, schema_sql):
            logger.critical('Unable to add trigger to the users table.')
            return False

    with open(f'{src_dir}/sql/posts.sql', 'r') as f:
        schema_sql = f.read()
        if not execute_query(connection, schema_sql):
            logger.critical('Failed to create posts table.')
            return False

    with open(f'{src_dir}/sql/classification.sql', 'r') as f:
        schema_sql = f.read()
        if not execute_query(connection, schema_sql):
            logger.critical('Failed to create classification table.')
            return False

    with open(f'{src_dir}/sql/actions.sql', 'r') as f:
        schema_sql = f.read()
        if not execute_query(connection, schema_sql):
            logger.critical('Failed to create actions table.')
            return False

    return True