from enum import Enum

from pydantic import StringConstraints
from typing_extensions import Annotated


class BankCode(Enum):
    """
    https://www.bot.or.th/Thai/Statistics/DataManagementSystem/Standard/StandardCode/Pages/default.aspx
    """
    BBL = "002"
    KBANK = "004"


AnyBankCode = Annotated[str, StringConstraints(min_length=3, max_length=3)]
