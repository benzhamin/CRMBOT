from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:1972@localhost:5432/crmglass"
engine = create_engine(DATABASE_URL) 
Session = sessionmaker(bind = engine) 



Base = declarative_base() 

