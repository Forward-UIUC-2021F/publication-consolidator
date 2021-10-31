"""
This module stores Open Academic Graph (OAG) publication data on an intermediary MySQL Database.

NOTE: You will need to be connected to the University of Illinois network using a VPN in order to 
connect to the database.
"""
import crawl_OAG
import pandas as pd
import sql_helper

def oag_to_sql_server(pub_file_path, author_file_path):
  """ Updates the SQL server with latest OAG knowledge base data.

    Args:
        file_path (str): Path to the OAG knowledge base file.

    Returns:
        1 (int): SQL query was successful
       -1 (int): SQL query was not successful

  """
  # Use helper functions from crawl_OAG.py to pull data
  publications = crawl_OAG.publication_crawler(pub_file_path)
  authors = crawl_OAG.author_crawler(author_file_path)

  # Insert into publications table
  for index, row in publications.iterrows():
    citations = row["citations"]
    if citations == "":
      citations = 0

    else:
      citations = int(citations)
    
    sql_helper.connection.ping()  # reconnecting mysql
    with sql_helper.connection.cursor() as cursor:         
        sql = "INSERT IGNORE INTO publication_data (id, title, authors, abstract, doi, citations) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (row["id"], row["title"], row["authors"], row["abstract"], row["doi"], citations)
        cursor.execute(sql, val)

    # Connection is not autocommit by default. So you must commit to save your changes.
    sql_helper.connection.commit()

  # Insert into authors and publication_authors table.
  for index, row in authors.iterrows():
    sql_helper.connection.ping()  # reconnecting mysql
    with sql_helper.connection.cursor() as cursor:         
        # Insert into authors table
        sql = "INSERT IGNORE INTO author_data (id, name, org) VALUES (%s, %s, %s)"
        val = (row["id"], row["name"], row["org"])
        cursor.execute(sql, val)

        # Insert into publication_authors table
        for x in range(len(row["pubs"])):
          sql = "INSERT IGNORE INTO publication_author (publication_id, author_id) VALUES (%s, %s)"
          val = (row["pubs"][x]["i"], row["id"])
          cursor.execute(sql, val)

    # Connection is not autocommit by default. So you must commit to save your changes.
    sql_helper.connection.commit()

def test_intermediary_database():
  """Testing suite for intermediary database."""
  sql_helper.open_ssh_tunnel()
  sql_helper.mysql_connect()

  oag_to_sql_server("data\oag_test.txt", "data\oag_authors.txt")
  df = sql_helper.run_query("SELECT * FROM publication_data;")
  assert 'Data mining: concepts and techniques' in df.values
  assert 'Jiawei Han' in df.values

  sql_helper.mysql_disconnect()
  sql_helper.close_ssh_tunnel()
  
  print("All intermediary database tests passed.")

test_intermediary_database()