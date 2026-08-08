# core/settings.py
"""Settings du moteur — source unique des credentials et paramètres,
consommés par providers/ et services/. Tout arrive en variables d'environnement :
userConfig du plugin en production, variables shell pour un test en dev."""

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Fournisseur LLM gratuit (protocole OpenAI-compatible — voir providers/) ---
    # Chaque classe provider déclare EXPLICITEMENT son champ (`api_key = settings.x_api_key`).
    # Clé absente → échec explicite chez l'appelant (configuration_issue).
    mistral_api_key: SecretStr | None = Field(default=None, env="MISTRAL_API_KEY")

    @field_validator("*", mode="before")
    @classmethod
    def _empty_or_unsubstituted_is_absent(cls, value):
        """Champ userConfig laissé vide ("") ou non substitué ("${user_config...}")
        → traité comme absent : défaut du code appliqué, jamais de valeur cassée."""
        if isinstance(value, str) and (value == "" or value.startswith("${")):
            return None
        return value

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
