class GoogleTokens(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expiry = Column(DateTime)
