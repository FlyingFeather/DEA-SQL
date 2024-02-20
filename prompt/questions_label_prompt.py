# -*- coding: utf-8 -*-
# Project : DEASQL 
# File    : questions_label_prompt.py
# Author  : 
# Email   : 
# Time    : 2023/11/16 20:24


QUESTION_LABEL_MULTI = "For the given question that requires writing SQL, classify it with two labels. " \
                       "You can choose the first label from NON-JOIN and JOIN and choose the second label from " \
                       "NON-NESTED and NESTED.\n\n" \
                        "### Some table infos and examples\n" \
                          "Q: What are the names and revenues of the companies with the highest revenues in each headquarter city?" \
                          """table_info: CREATE TABLE MANUFACTURERS (
  code INTEGER
  name VARCHAR(255) NOT NULL
  headquarter VARCHAR(255) NOT NULL
  founder VARCHAR(255) NOT NULL
  revenue REAL
  PRIMARY KEY (code)   
);

CREATE TABLE PRODUCTS (
  code INTEGER
  name VARCHAR(255) NOT NULL 
  price DECIMAL NOT NULL 
  manufacturer INTEGER NOT NULL
  PRIMARY KEY (code), 
  FOREIGN KEY (manufacturer) REFERENCES Manufacturers(code)
);""" \
                          "A: Let’s think step by step. The SQL query for the question 'What are the names and " \
                          "revenues of the companies with the highest revenues in each headquarter city?' needs these " \
                          "tables and columns = [MANUFACTURERS.name, MANUFACTURERS.revenue, MANUFACTURERS.headquarter]," \
                          "so we don’t need joint condition and label it as NON-JOIN.\n" \
                          "Plus, it doesn’t require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN). " \
                          "so we label it as NON-NESTED\n" \
                          "Thus the SQL query can be classified as NON-JOIN, NON-NESTED\n" \
                          "Label: NON-JOIN, NON-NESTED\n\n" \
                          "Q: Which studios have an average gross of over 4500000?" \
"""table_info: CREATE TABLE FILM (
studio text
gross_in_dollar int
PRIMARY KEY (Film_ID)
);""" \
                          "A: Let’s think step by step. The SQL query for the question 'Which studios have an " \
                          "average gross of over 4500000?' needs these table and column = [FILM.studio, " \
                          "AVG(FILM.gross_in_dollar)], so we don’t need joint condition and label it as NON-JOIN.\n" \
                          "Plus, it doesn’t require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN). " \
                          "So we label it as NON-NESTED.\n" \
                          "Thus the SQL query can be classified as NON-JOIN, NON-NESTED\n" \
                          "Label: NON-JOIN, NON-NESTED\n\n" \
                          "Q: What are the products with the maximum page size A4 that also have a pages per minute color smaller than 5?" \
"""table_info: CREATE TABLE PRODUCT (
product_id int
product text
dimensions text
dpi real
pages_per_minute_color real
max_page_size text
interface text
PRIMARY KEY (product_id)
);""" \
                          "A: Let’s think step by step. The SQL query for the question 'What are the products with " \
                          "the maximum page size A4 that also have a pages per minute color smaller than 5?' needs " \
                          "these table and columns = [PRODUCT.product, PRODUCT.max_page_size, " \
                          "PRODUCT.pages_per_minute_color], so we don’t need joint condition and label it as NON-JOIN.\n" \
                          "Plus, it requires nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and we need the answer" \
                          " to the questions = ['What is the maximum page size A4 of the products']." \
                          "So it need nested queries and we label it as NESTED.\n" \
                          "Thus the SQL query can be classified as NON-JOIN, NESTED.\n" \
                          "Label: NON-JOIN, NESTED\n\n" \
                          "Q: Show names for all stadiums except for stadiums having a concert in year 2014." \
"""table_info: CREATE TABLE STADIUM (
stadium_ID int
location text
name text
capacity int
highest int
lowest int
average int
PRIMARY KEY (Stadium_ID)
);

CREATE TABLE CONCERT (
concert_ID int
concert_Name text
theme text
stadium_ID text
year text
PRIMARY KEY (concert_ID),
FOREIGN KEY (stadium_ID) REFERENCES stadium(stadium_ID)
);""" \
                          "A: Let’s think step by step. The SQL query for the question 'Show names for all stadiums " \
                          "except for stadiums having a concert in year 2014.' needs " \
                          "these table and columns = [STADIUM.name, CONCERT.year], so we need a JOIN operation on the " \
                          "STADIUM and CONCERT tables using the stadium_ID column because we we need to exclude " \
                          "stadiums with concerts in 2014. So we label it as JOIN.\n" \
                          "Plus, it requires nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and " \
                          "we need the answer to the questions = ['What is the stadiums having a concert in year 2014']." \
                          "So it need nested queries and we label it as NESTED.\n" \
                          "Thus the SQL query can be classified as JOIN, NESTED.\n" \
                          "Label: JOIN, NESTED\n\n" \
                          "Q: How many songs have a shared vocal?" \
"""table_info: CREATE TABLE SONGS ( 
  SongId INTEGER PRIMARY KEY, 
);

CREATE TABLE VOCALS ( 
  SongId INTEGER 
  Bandmate INTEGER 
  PRIMARY KEY(SongId, Bandmate),
  FOREIGN KEY (SongId) REFERENCES Songs(SongId),
  FOREIGN KEY (Bandmate) REFERENCES Band(Id)
);""" \
                          "A: Let’s think step by step. The SQL query for the question 'How many songs have a shared vocal?' needs " \
                        "these table and columns = [SONGS.SongId, VOCALS.Bandmate], so we need a JOIN operation on the " \
                        "SONGS and VOCALS tables using the SongId column because we need to count the number of songs " \
                        "with a shared vocal. So we label it as JOIN.\n" \
                        "Plus, it does not require nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), " \
                        "so we label it as NON-NESTED.\n" \
                        "Thus the SQL query can be classified as JOIN, NON-NESTED.\n" \
                        "Label: JOIN, NON-NESTED\n\n" \
                      "Q: How many users who did not leave any review." \
"""table_info: CREATE TABLE USERACCT (
  u_id integer NOT NULL
  name varchar(128) DEFAULT NULL
  PRIMARY KEY (u_id)
);

CREATE TABLE REVIEW (
  a_id integer NOT NULL PRIMARY KEY
  u_id integer NOT NULL
  FOREIGN KEY (u_id) REFERENCES useracct(u_id)
  FOREIGN KEY (i_id) REFERENCES item(i_id)

);""" \
                       "A: The SQL query for the question 'How many users who did not leave any review.' needs " \
                        "these table and columns = [USERACCT.name, REVIEW.u_id], so we need a JOIN operation on the " \
                        "USERACCT and REVIEW tables using the u_id column because we need to find users who did not leave any review. " \
                        "So we label it as JOIN.\n" \
                        "Plus, it requires nested queries with (INTERSECT, UNION, EXCEPT, IN, NOT IN), and " \
                        "we need the answer to the questions = ['What is the list of u_id who left a review?']." \
                        "So it needs nested queries and we label it as NESTED.\n" \
                        "Thus the SQL query can be classified as JOIN, NESTED.\n" \
                        "Label: JOIN, NESTED\n\n" \
                       "### Issues you should be concerned about:" \
                        "\ntable info:\n{table_info}\n" \
                        "Q: {query}" \
                        "A: "
