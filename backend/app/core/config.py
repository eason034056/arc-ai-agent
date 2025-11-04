"""
Configuration Module

This module loads and validates all environment variables using Pydantic.
It provides type-safe access to configuration throughout the application.

Key Features:
- Automatic .env file loading
- Type validation and conversion
- Default values for optional settings
- Environment-specific configurations
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings
    
    This class defines all configuration variables with:
    - Type annotations for validation
    - Default values where appropriate
    - Documentation for each field
    
    Usage:
        from app.core.config import get_settings
        
        settings = get_settings()
        print(settings.env)  # "dev" or "staging" or "production"
    """
    
    # ========================================
    # GENERAL SETTINGS
    # ========================================
    # env: Application environment
    # - dev: Development with debug logging
    # - staging: Pre-production testing
    # - production: Production deployment
    env: Literal["dev", "staging", "production"] = Field(
        default="dev",
        description="Application environment"
    )
    
    # tz: Timezone for scheduled jobs
    # Used by the scheduler to run payroll at specific times
    tz: str = Field(
        default="America/Chicago",
        description="Timezone for scheduled jobs"
    )
    
    # ========================================
    # DATABASE CONFIGURATION
    # ========================================
    # database_url: PostgreSQL connection string
    # Format: postgresql+psycopg2://user:password@host:port/database
    database_url: str = Field(
        ...,  # ... means required (no default value)
        description="PostgreSQL database connection URL"
    )
    
    # redis_url: Redis connection string
    # Format: redis://host:port/database
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis cache connection URL"
    )
    
    # ========================================
    # SLACK CONFIGURATION
    # ========================================
    # slack_bot_token: Bot OAuth token from Slack app
    # Get from: https://api.slack.com/apps > OAuth & Permissions
    slack_bot_token: str = Field(
        ...,
        description="Slack bot OAuth token"
    )
    
    # slack_signing_secret: Used to verify Slack requests
    # Get from: https://api.slack.com/apps > Basic Information
    slack_signing_secret: str = Field(
        ...,
        description="Slack signing secret for request verification"
    )
    
    # slack_approval_channel: Channel ID for approval messages
    # Right-click channel > View channel details > Copy ID
    slack_approval_channel: str = Field(
        default="",
        description="Slack channel ID for payroll approvals"
    )
    
    # ========================================
    # BLOCKCHAIN CONFIGURATION
    # ========================================
    # arc_rpc_url: Arc Testnet RPC endpoint
    # This is where all blockchain transactions are sent
    arc_rpc_url: str = Field(
        ...,
        description="Arc Testnet RPC URL"
    )
    
    # private_key: Operator account private key
    # SECURITY: Never commit this value! Use .env file
    private_key: str = Field(
        ...,
        description="Private key for blockchain transactions"
    )
    
    # payroll_contract_address: Deployed PayrollVault contract address
    payroll_contract_address: str = Field(
        ...,
        description="PayrollVault contract address on Arc Testnet"
    )
    
    # payroll_contract_abi_path: Path to contract ABI JSON file
    payroll_contract_abi_path: str = Field(
        default="/app/abi/PayrollVault.json",
        description="Path to PayrollVault ABI file"
    )
    
    # usdc_decimals: Number of decimals for USDC token
    # Standard USDC uses 6 decimals (1 USDC = 1,000,000 smallest units)
    usdc_decimals: int = Field(
        default=6,
        description="USDC token decimal places"
    )
    
    # usdc_address: USDC token contract address
    usdc_address: str = Field(
        default="",
        description="USDC token contract address"
    )
    
    # ========================================
    # AI / LLM CONFIGURATION
    # ========================================
    # openai_api_key: OpenAI API key for anomaly detection
    # Optional: System works without AI features if not provided
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for AI features"
    )
    
    # openai_model: Which OpenAI model to use
    openai_model: str = Field(
        default="gpt-4",
        description="OpenAI model name"
    )
    
    # ========================================
    # EXPENSE SYSTEM INTEGRATION
    # ========================================
    # expense_webhook_url: URL to send transaction results
    # Optional: Can be empty if no external expense system
    expense_webhook_url: str = Field(
        default="",
        description="Expense system webhook URL"
    )
    
    # expense_webhook_token: Authentication token for webhook
    expense_webhook_token: str = Field(
        default="",
        description="Expense system webhook authentication token"
    )
    
    # ========================================
    # PAYROLL POLICIES
    # ========================================
    # batch_size: Maximum recipients per blockchain transaction
    # Smaller = more reliable, Larger = more efficient
    batch_size: int = Field(
        default=50,
        description="Maximum recipients per transaction"
    )
    
    # approval_timeout_minutes: How long to wait for approval
    # After this time, the batch is automatically rejected
    approval_timeout_minutes: int = Field(
        default=120,
        description="Approval timeout in minutes"
    )
    
    # anomaly_threshold: Anomaly detection sensitivity (0.0 to 1.0)
    # Higher = stricter (more items flagged as anomalies)
    anomaly_threshold: float = Field(
        default=0.7,
        ge=0.0,  # Greater than or equal to 0.0
        le=1.0,  # Less than or equal to 1.0
        description="Anomaly detection threshold"
    )
    
    # ========================================
    # API CONFIGURATION
    # ========================================
    # api_host: Host to bind the API server
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    
    # api_port: Port to bind the API server
    api_port: int = Field(
        default=8080,
        description="API server port"
    )
    
    # api_secret_key: Secret key for JWT tokens
    api_secret_key: str = Field(
        default="change-this-secret-key",
        description="API secret key for authentication"
    )
    
    # cors_origins: Allowed CORS origins (comma-separated)
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # ========================================
    # LOGGING CONFIGURATION
    # ========================================
    # log_level: Logging verbosity
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # log_format: Log output format
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log output format"
    )
    
    # ========================================
    # PYDANTIC CONFIGURATION
    # ========================================
    # Configure how Pydantic loads settings
    model_config = SettingsConfigDict(
        # Load from .env file
        env_file=".env",
        
        # Don't ignore extra fields in .env
        extra="ignore",
        
        # Make settings case-insensitive
        case_sensitive=False
    )
    
    # ========================================
    # VALIDATORS
    # ========================================
    @field_validator("private_key")
    @classmethod
    def validate_private_key(cls, v: str) -> str:
        """
        Validate that private key is properly formatted
        
        Args:
            v: Private key string
            
        Returns:
            Validated private key
            
        Raises:
            ValueError: If private key format is invalid
        """
        # Ensure private key starts with 0x
        if not v.startswith("0x"):
            v = "0x" + v
        
        # Validate length (64 hex chars + 0x prefix = 66 total)
        if len(v) != 66:
            raise ValueError("Private key must be 64 hex characters (with or without 0x prefix)")
        
        return v
    
    @field_validator("payroll_contract_address", "usdc_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        """
        Validate Ethereum address format
        
        Args:
            v: Ethereum address string
            
        Returns:
            Validated address (lowercase for consistency)
        """
        if v and not v.startswith("0x"):
            v = "0x" + v
        
        if v and len(v) != 42:
            raise ValueError("Ethereum address must be 40 hex characters (with or without 0x prefix)")
        
        # Return lowercase for consistency
        return v.lower() if v else v
    
    # ========================================
    # HELPER PROPERTIES
    # ========================================
    @property
    def is_dev(self) -> bool:
        """Check if running in development mode"""
        return self.env == "dev"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.env == "production"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached)
    
    This function uses @lru_cache to create a singleton.
    The settings are loaded only once and reused throughout the application.
    
    Returns:
        Settings: Application configuration instance
        
    Usage:
        from app.core.config import get_settings
        
        settings = get_settings()
        print(f"Running in {settings.env} mode")
        print(f"Database: {settings.database_url}")
    """
    return Settings()

