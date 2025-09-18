Video Tutorial - https://youtu.be/XmLAJXERNNA

\## Docker compose



command to run `docker compose up -d`



\## Database



PGAdmin - `http://localhost:5050/login?next=/`



\- \*\*Login to pgAdmin\*\*

&nbsp;   

&nbsp;   - Email: `admin@admin.com`

&nbsp;   - Password: `admin`

&nbsp;       

\- \*\*Add a connection to your Postgres server\*\*

&nbsp;   

&nbsp;   - In the left panel ("Browser"), right-click \*\*Servers → Register → Server\*\*.

&nbsp;   - In the \*\*General\*\* tab:

&nbsp;       - Name: `Postgres Local` (or any name you like).

&nbsp;   - In the \*\*Connection\*\* tab:

&nbsp;       - Host name/address: `db` (inside Docker network) or `localhost` (if connecting directly)

&nbsp;       - Port: `5432`

&nbsp;       - Username: `admin`

&nbsp;       - Password: `admin`

&nbsp;   - Click \*\*Save\*\*.

&nbsp;       

\- \*\*Create a new database\*\*

&nbsp;   

&nbsp;   - Expand your server → \*\*Databases\*\*.

&nbsp;   - Right-click \*\*Databases → Create → Database\*\*.

&nbsp;   - Fill in:

&nbsp;       - Database name: e.g., `notes`

&nbsp;       - Owner: `admin`

&nbsp;   - Click \*\*Save\*\*.



```

-- Database: notes



-- DROP DATABASE IF EXISTS notes;



CREATE DATABASE notes

&nbsp;   WITH

&nbsp;   OWNER = admin

&nbsp;   ENCODING = 'UTF8'

&nbsp;   LC\_COLLATE = 'en\_US.utf8'

&nbsp;   LC\_CTYPE = 'en\_US.utf8'

&nbsp;   LOCALE\_PROVIDER = 'libc'

&nbsp;   TABLESPACE = pg\_default

&nbsp;   CONNECTION LIMIT = -1

&nbsp;   IS\_TEMPLATE = False;

```



create table named notes



```

CREATE TABLE notes (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   title VARCHAR(255) NOT NULL,

&nbsp;   content TEXT NOT NULL,

&nbsp;   tags TEXT,

&nbsp;   create\_date TIMESTAMP NOT NULL DEFAULT CURRENT\_TIMESTAMP,

&nbsp;   due\_date TIMESTAMP

);

```



```sql

select \* from notes;

```



\## MCP Server setup



Install UV



```

powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

```



Create project



```

\# Create a new directory for our project

uv init notes

cd notes



\# Create virtual environment and activate it

uv venv

.venv\\Scripts\\activate



\# Install dependencies

uv add mcp\[cli] psycopg2





\## Run Inspector



To run the inspector enter the command



```

npx @modelcontextprotocol/inspector uv run main.py

```





\## Use mcp in the vscode co-pilot



Connect from the vscode copilot



&nbsp;	enter `ctrl+shift+P`

&nbsp;		search `>mcp`

&nbsp;			uv --directory C:/learning/mcp/notes run main.py





\# MCP Client



\## Client Setup



`uv init notes-client`



`cd notes-client`



`uv venv`



Create .env file



Add the API key and model



```

OPENAI\_API\_KEY=



OPENAI\_MODEL=gpt-4o

```



echo ".env" >> .gitignore



`.venv\\Scripts\\activate`



`uv add mcp python-dotenv psycopg2 openai`







