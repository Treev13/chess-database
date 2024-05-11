import psycopg2
import os
from dotenv import load_dotenv

connection = psycopg2.connect(database=os.getenv("DATABASE"),
                              user=os.getenv("USER"),
                              password=os.getenv("PASSWORD"),
                              host=os.getenv("HOST"),
                              port=os.getenv("PORT"))