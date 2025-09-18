import json
from typing import Any
import psycopg2
from mcp.server.fastmcp import FastMCP
from datetime import datetime
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from mcp.types import SamplingMessage, TextContent
import logging
from psycopg2.extras import DictCursor


mcp = FastMCP("notes")
logging.basicConfig(
   level=logging.INFO,
   filename="C:/learning/code/mcp/notes/tmp/notes-mcp.log",
   filemode="a",
   format="%(asctime)s %(levelname)s %(message)s",
   force=True,
)


@mcp.tool(description="Create a new note with title, content, tags, and due date.")
async def create_notes(title: str, content: str, tags: list[str], due_date: str) -> str:
   """
   Create a new note in the database.

   Args:
       title (str): The title of the note.
       content (str): The content/body of the note.
       tags (list[str]): A list of tags for the note.
       due_date (str, optional): Due date in ISO format (YYYY-MM-DD). Can be None.

   Returns:
       str: Confirmation message with note details.
   """

   logging.info(f"Received: title={title}, content={content}, tags={tags}, due_date={due_date}")
   conn = psycopg2.connect(
       dbname="notes",
       user="admin",
       password="admin",
       host="127.0.0.1",
       port="5432"
   )

   logging.info(f"Creating note with title: {title}, content: {content}, tags: {tags}, due_date: {due_date}")
   # Create a new note
   note = {
       "title": title,
       "content": content,
       "tags": tags,
       "due_date": due_date
   }
   # Save the note to a database named notes and table name notes in ms-sql running in localhost username sa and password Password12

   cursor = conn.cursor()
   # add create_time as system date time
   cursor.execute(
       "INSERT INTO notes (title, content, tags, due_date, create_date) VALUES (%s, %s, %s, %s, %s)",
       (note["title"], note["content"], ",".join(note["tags"]), note["due_date"], datetime.now())
   )
   conn.commit()
   cursor.close()
   conn.close()

   return f"Note created: {note}"


@mcp.resource("notes://get_all", description="Retrieve all notes from the database as JSON")
def get_notes() -> str:
    """
    get all the notes from the database and return it as json

    Returns:
       str: all notes as json array.
     """
    conn = psycopg2.connect(
       dbname="notes",
       user="admin",
       password="admin",
       host="127.0.0.1",
       port="5432"
    )

    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM notes;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"title": row['title'], "content": row['content'], "tags": row['tags'], "due_date": row['due_date']} for row in rows]

@mcp.resource("notes://{title}")
def get_note(title: str) -> str:
   conn = psycopg2.connect(
       dbname="notes",
       user="admin",
       password="admin",
       host="127.0.0.1",
       port="5432"
   )
   cursor = conn.cursor(cursor_factory=DictCursor)
   # Use %s as the placeholder for the parameter
   cursor.execute("SELECT * FROM notes WHERE title = %s;", (title,))
   row = cursor.fetchone()
   cursor.close()
   conn.close()
   if row:
       return json.dumps({
           "title": row['title'],
           "content": row['content'],
           "tags": row['tags'].split(",") if row['tags'] else [],
           "due_date": row['due_date'].isoformat() if row['due_date'] else None
       })
   return json.dumps({"error": "Note not found"})

#sampling
@mcp.tool()
async def generate_note(title: str, ctx: Context[ServerSession, None]) -> str:
   """Generate a notes for the title."""
   prompt = f"Return only json with properties title, content, tags and due_date with generated content and tags for the {title}"

   result = await ctx.session.create_message(
       messages=[
           SamplingMessage(
               role="assistant",
               content=TextContent(type="text", text=prompt),
           )
       ],
       max_tokens=100,
   )

   logging.info(result)
   logging.info(result.content.type)
   logging.info(result.content.text)

   if result.content.type == "text":
       note_json = json.loads(result.content.text.strip())
       logging.info(note_json)
       create_notes_result = await create_notes(title=note_json["title"], content=note_json["content"], tags=note_json["tags"], due_date=None)
       logging.info(create_notes_result)
   return str(result.content.type)


@mcp.prompt()
def relevant_content(title: str) -> str:
   """Generate a content prompt"""
   return f"Please write a relevant note content for the title - {title}."

if __name__ == "__main__":

    # Initialize and run the server
    mcp.run(transport='stdio')