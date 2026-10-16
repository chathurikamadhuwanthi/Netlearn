import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-this-later")

    # Certificate එකේ signature එක යටින් පෙන්නන නම (ඔයාගේ නම දාන්න)
    CREATOR_NAME = "WL.Chathurika Madhuwanthi"