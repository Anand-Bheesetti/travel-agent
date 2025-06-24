import os
import requests
from typing import Any, Dict
from langchain.tools import tool


class CurrencyConverter:
  """
  A tool to convert currencies using the ExchangeRate-API.
  """

  API_URL = "https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/{to_currency}/{amount}"

  @staticmethod
  @tool
  def convert(amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
    """
    Converts a given amount from one currency to another using ExchangeRate-API.

    Args:
        amount (float): The amount of money to convert.
        from_currency (str): The currency code to convert from (e.g., 'USD').
        to_currency (str): The currency code to convert to (e.g., 'EUR').

    Returns:
        Dict[str, Any]: Dictionary with converted amount, rate, from, and to currency codes.
    """
    api_key = os.getenv("EXCHANGERATE_API_KEY")
    if not api_key:
      raise ValueError(
        "EXCHANGERATE_API_KEY not set. Currency converter cannot function."
      )
    url = CurrencyConverter.API_URL.format(
      api_key=api_key,
      from_currency=from_currency,
      to_currency=to_currency,
      amount=amount
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("result") != "success":
      raise ValueError(f"Currency conversion failed: {data}")
    return {
      "converted_amount": data.get("conversion_result"),
      "rate": data.get("conversion_rate"),
      "from": from_currency,
      "to": to_currency
    }