from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    vapi_api_key: str
    vapi_webhook_secret: str
    stripe_api_key: str
    stripe_webhook_secret: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    google_maps_api_key: str
    openai_api_key: str
    tiliter_api_key: str
    jobber_client_id: str
    jobber_client_secret: str

    class Config:
        env_file = ".env"
        
        
settings = Settings()